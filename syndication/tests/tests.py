import datetime
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils.feedgenerator import Atom1Feed
from django.utils import tzinfo
from syndication import feedgenerator, feeds
from syndication.tests.models import Entry
from xml.dom import minidom

try:
    set
except NameError:
    from sets import Set as set

class FeedTestCase(TestCase):
    fixtures = ['test_entries.json']

    def assertChildNodes(self, elem, expected):
        actual = set([n.nodeName for n in elem.childNodes])
        expected = set(expected)
        self.assertEqual(actual, expected)
    
    def assertChildNodeContent(self, elem, expected):
        for k, v in expected.items():
            self.assertEqual(
                elem.getElementsByTagName(k)[0].firstChild.wholeText, v)


######################################
# Feed view
######################################

class SyndicationFeedTest(FeedTestCase):
    def test_rss_feed(self):
        response = self.client.get('/rss/')
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
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item', 'atom:link'])
       
       # Ensure the content of the channel is correct
        self.assertChildNodeContent(chan, {
            'title': 'My blog',
            'link': 'http://testserver/blog/',
        })
        
        # Check feed_url is passed
        self.assertEqual(
            chan.getElementsByTagName('atom:link')[0].getAttribute('href'),
            'http://testserver/rss/'
        )
        
        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())
        for item in items:
            self.assertChildNodes(item, ['title', 'link', 'description', 'guid'])
    
    def test_atom_feed(self):
        response = self.client.get('/atom/')
        doc = minidom.parseString(response.content)
        
        feed = doc.firstChild
        self.assertEqual(feed.nodeName, 'feed')
        self.assertEqual(feed.getAttribute('xmlns'), 'http://www.w3.org/2005/Atom') 
        self.assertChildNodes(feed, ['title', 'link', 'id', 'updated', 'entry'])
        for link in feed.getElementsByTagName('link'):
            if link.getAttribute('rel') == 'self':
                self.assertEqual(link.getAttribute('href'), 'http://testserver/atom/')
        
        entries = feed.getElementsByTagName('entry')
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertChildNodes(entry, ['title', 'link', 'id', 'summary'])
            summary = entry.getElementsByTagName('summary')[0]
            self.assertEqual(summary.getAttribute('type'), 'html')
    
    def test_custom_feed_generator(self):
        response = self.client.get('/custom/')
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
        Tests that the base url for a complex feed doesn't raise a 500
        exception.
        """
        response = self.client.get('/complex/bar/')
        self.assertEquals(response.status_code, 404)
 
    def test_title_escaping(self):
        """
        Tests that titles are escaped correctly in RSS feeds.
        """
        response = self.client.get('/rss/')
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
        response = self.client.get('/naive-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText        
        tz = tzinfo.LocalTimezone(datetime.datetime.now())
        now = datetime.datetime.now(tz)
        self.assertEqual(updated[-6:], str(now)[-6:])
        
    def test_aware_datetime_conversion(self):
        """
        Test that datetimes with timezones don't get trodden on.
        """
        response = self.client.get('/aware-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText
        self.assertEqual(updated[-6:], '+00:42')
    
    def test_feed_url(self):
        """
        Test that the feed_url can be overridden.
        """
        response = self.client.get('/feedurl/')
        doc = minidom.parseString(response.content)
        for link in doc.firstChild.getElementsByTagName('link'):
            if link.getAttribute('rel') == 'self':
                self.assertEqual(link.getAttribute('href'), 'http://example.com/customfeedurl/')
    
    def test_item_link_error(self):
        """
        Test that a ImproperlyConfigured is raised if no link could be found
        for the item(s).
        """
        self.assertRaises(ImproperlyConfigured,
                          self.client.get,
                          '/articles/')


######################################
# feedgenerator
######################################

class FeedgeneratorTest(TestCase):
    def test_get_tag_uri(self):
        self.assertEqual(
            feedgenerator.get_tag_uri('http://www.example.org:8000/2008/11/14/django#headline', datetime.datetime(2008, 11, 14, 13, 37, 0)),
            u'tag:www.example.org,2008-11-14:/2008/11/14/django/headline')


######################################
# Depreciated feeds
######################################

class DepreciatedSyndicationFeedTest(FeedTestCase):
    def test_empty_feed_dict(self):
        """
        Test that an empty feed_dict raises a 404.
        """
        response = self.client.get('/depr-feeds-empty/aware-dates/')
        self.assertEquals(response.status_code, 404)

    def test_nonexistent_slug(self):
        """
        Test that a non-existent slug raises a 404.
        """
        response = self.client.get('/depr-feeds/foobar/')
        self.assertEquals(response.status_code, 404)
    
    def test_rss_feed(self):
        response = self.client.get('/depr-feeds/rss/')
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName('rss')[0]
        self.assertEqual(feed.getAttribute('version'), '2.0')
        
        chan = feed.getElementsByTagName('channel')[0]
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item', 'atom:link'])
    
        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())
    
    def test_complex_base_url(self):
        """
        Tests that the base url for a complex feed doesn't raise a 500 
        exception.
        """
        response = self.client.get('/depr-feeds/complex/')
        self.assertEquals(response.status_code, 404)

