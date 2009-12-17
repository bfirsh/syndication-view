from syndication.tests import feeds

from django.conf.urls.defaults import *
 
feed_dict = {
    'complex': feeds.DepreciatedComplexFeed,
    'rss': feeds.DepreciatedRssFeed,
}
urlpatterns = patterns('',
    (r'^complex/(?P<foo>.*)/$', feeds.ComplexFeed()),
    (r'^rss2/$', feeds.TestRss2Feed()),
    (r'^rss091/$', feeds.TestRss091Feed()),
    (r'^atom/$', feeds.TestAtomFeed()),
    (r'^custom/$', feeds.TestCustomFeed()),
    (r'^naive-dates/$', feeds.NaiveDatesFeed()),
    (r'^aware-dates/$', feeds.TZAwareDatesFeed()),
    (r'^feedurl/$', feeds.TestFeedUrlFeed()),
    (r'^articles/$', feeds.ArticlesFeed()),
    (r'^template/$', feeds.TemplateFeed()),
    
    (r'^depr-feeds/(?P<url>.*)/$', 'syndication.views.feed', {'feed_dict': feed_dict}),
    (r'^depr-feeds-empty/(?P<url>.*)/$', 'syndication.views.feed', {'feed_dict': None}),
)
