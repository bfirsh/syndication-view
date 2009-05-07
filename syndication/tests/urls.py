from syndication.tests import depreciated, feeds

from django.conf.urls.defaults import *
 
feed_dict = {
    'complex': depreciated.ComplexFeed,
    'rss': depreciated.TestRssFeed,
    'atom': depreciated.TestAtomFeed,
    'custom': depreciated.TestCustomFeed,
    'naive-dates': depreciated.NaiveDatesFeed,
    'aware-dates': depreciated.TZAwareDatesFeed,    
}
urlpatterns = patterns('',
    (r'^complex/(?P<foo>.*)/$', feeds.ComplexFeed()),
    (r'^rss/$', feeds.TestRssFeed()),
    (r'^atom/$', feeds.TestAtomFeed()),
    (r'^custom/$', feeds.TestCustomFeed()),
    (r'^naive-dates/$', feeds.NaiveDatesFeed()),
    (r'^aware-dates/$', feeds.TZAwareDatesFeed()),
    (r'^depr-feeds/(?P<url>.*)/$', 'syndication.views.feed', {'feed_dict': feed_dict})
)
