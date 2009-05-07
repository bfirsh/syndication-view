# Tests for backwards compatibility with <=1.1 feeds

import datetime
from xml.dom import minidom
from syndication import feeds
from syndication.models import Entry
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils.feedgenerator import Atom1Feed
from django.utils import tzinfo

try:
    set
except NameError:
    from sets import Set as set

class ComplexFeed(feeds.Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return None
 
class TestRssFeed(feeds.Feed):
    link = "/blog/"
    title = 'My blog'
    
    def items(self):
        from syndication.models import Entry
        return Entry.objects.all()
        
    def item_link(self, item):
        return "/blog/%s/" % item.pk
 
class TestAtomFeed(TestRssFeed):
    feed_type = Atom1Feed
 
class MyCustomAtom1Feed(Atom1Feed):
    """
    Test of a custom feed generator class.
    """    
    def root_attributes(self):
        attrs = super(MyCustomAtom1Feed, self).root_attributes()
        attrs[u'django'] = u'rocks'
        return attrs
        
    def add_root_elements(self, handler):
        super(MyCustomAtom1Feed, self).add_root_elements(handler)
        handler.addQuickElement(u'spam', u'eggs')
        
    def item_attributes(self, item):
        attrs = super(MyCustomAtom1Feed, self).item_attributes(item)
        attrs[u'bacon'] = u'yum'
        return attrs
        
    def add_item_elements(self, handler, item):
        super(MyCustomAtom1Feed, self).add_item_elements(handler, item)
        handler.addQuickElement(u'ministry', u'silly walks')
    
class TestCustomFeed(TestAtomFeed):
    feed_type = MyCustomAtom1Feed
    
class NaiveDatesFeed(TestAtomFeed):
    """
    A feed with naive (non-timezone-aware) dates.
    """
    def item_pubdate(self, item):
        return item.date
        
class TZAwareDatesFeed(TestAtomFeed):
    """
    A feed with timezone-aware dates.
    """
    def item_pubdate(self, item):
        # Provide a weird offset so that the test can know it's getting this
        # specific offset and not accidentally getting on from 
        # settings.TIME_ZONE.
        return item.date.replace(tzinfo=tzinfo.FixedOffset(42))


class DepreciatedSyndicationFeedTest(TestCase):
    fixtures = ['feeddata.json']
    urls = 'syndication.tests.urls'
 
    def assertChildNodes(self, elem, expected):
        actual = set([n.nodeName for n in elem.childNodes])
        expected = set(expected)
        self.assertEqual(actual, expected)
 
    def test_rss_feed(self):
        response = self.client.get('/depr-feeds/rss/')
        doc = minidom.parseString(response.content)
        
        # Making sure there's only 1 `rss` element and that the correct
        # RSS version was specified.
        feed_elem = doc.getElementsByTagName('rss')
        self.assertEqual(len(feed_elem), 1)
        feed = feed_elem[0]
        self.assertEqual(feed.getAttribute('version'), '2.0')
        
        # Making sure there's only one `channel` element w/in the
        # `rss` element.
        chan_elem = feed.getElementsByTagName('channel')
        self.assertEqual(len(chan_elem), 1)
        chan = chan_elem[0]
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item'])
    
        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())
        for item in items:
            self.assertChildNodes(item, ['title', 'link', 'description', 'guid'])
    
    def test_atom_feed(self):
        response = self.client.get('/depr-feeds/atom/')
        doc = minidom.parseString(response.content)
        
        feed = doc.firstChild
        self.assertEqual(feed.nodeName, 'feed')
        self.assertEqual(feed.getAttribute('xmlns'), 'http://www.w3.org/2005/Atom') 
        self.assertChildNodes(feed, ['title', 'link', 'id', 'updated', 'entry'])        
        
        entries = feed.getElementsByTagName('entry')
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertChildNodes(entry, ['title', 'link', 'id', 'summary'])
            summary = entry.getElementsByTagName('summary')[0]
            self.assertEqual(summary.getAttribute('type'), 'html')
    
    def test_custom_feed_generator(self):
        response = self.client.get('/depr-feeds/custom/')
        doc = minidom.parseString(response.content)
        
        feed = doc.firstChild
        self.assertEqual(feed.nodeName, 'feed')
        self.assertEqual(feed.getAttribute('django'), 'rocks')
        self.assertChildNodes(feed, ['title', 'link', 'id', 'updated', 'entry', 'spam'])        
        
        entries = feed.getElementsByTagName('entry')
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertEqual(entry.getAttribute('bacon'), 'yum')
            self.assertChildNodes(entry, ['title', 'link', 'id', 'summary', 'ministry'])
            summary = entry.getElementsByTagName('summary')[0]
            self.assertEqual(summary.getAttribute('type'), 'html')
        
    def test_complex_base_url(self):
        """
        Tests that that the base url for a complex feed doesn't raise a 500
        exception.
        """
        response = self.client.get('/depr-feeds/complex/')
        self.assertEquals(response.status_code, 404)
 
    def test_title_escaping(self):
        """
        Tests that titles are escaped correctly in RSS feeds.
        """
        response = self.client.get('/depr-feeds/rss/')
        doc = minidom.parseString(response.content)
        for item in doc.getElementsByTagName('item'):
            link = item.getElementsByTagName('link')[0]
            if link.firstChild.wholeText == 'http://example.com/blog/4/':
                title = item.getElementsByTagName('title')[0]
                self.assertEquals(title.firstChild.wholeText, u'A &amp; B &lt; C &gt; D')
                
    def test_naive_datetime_conversion(self):
        """
        Test that datetimes are correctly converted to the local time zone.
        """
        # Naive date times passed in get converted to the local time zone, so
        # check the recived zone offset against the local offset.
        response = self.client.get('/depr-feeds/naive-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText        
        tz = tzinfo.LocalTimezone(datetime.datetime.now())
        now = datetime.datetime.now(tz)
        self.assertEqual(updated[-6:], str(now)[-6:])
        
    def test_aware_datetime_conversion(self):
        """
        Test that datetimes with timezones don't get trodden on.
        """
        response = self.client.get('/depr-feeds/aware-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText
        self.assertEqual(updated[-6:], '+00:42')
