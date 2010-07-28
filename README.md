syndication-view
================

syndication-view is a refactor of Django's syndication contrib app, primarily to 
turn feeds into class-based views, but also fixes a number of [long standing 
tickets](http://code.djangoproject.com/query?status=new&status=assigned&status=reopened&component=RSS+framework&order=priority).

As of [revision 
12338](http://github.com/django/django/commit/5d592a351fe66a225a25), 
syndication-view is a part of Django and is included in version 1.2. This 
repository is maintained as a backport for Django 1.1.x.

Installation
------------

    $ python setup.py install

Usage
-----

`articles/feeds.py`:

    from syndication.views import Feed
    from articles.models import Article, Category

    class ArticleFeed(Feed):
        title = "example.com news"
        link = "/sitenews/"
        description = "Latest news from example.com."

        def items(self):
            return Article.objects.all()[:15]
        
    class CategoryArticleFeed(ArticleFeed):
        def title(self, obj):
            return 'example.com: %s' % obj
        
        def get_object(self, request, slug):
            return Category.objects.get(slug=slug)
        
        def items(self, obj):
            return Article.objects.filter(category=obj)[:15]

`urls.py`:

    from articles.feeds import ArticleFeed, CategoryArticleFeed

    urlpatterns = patterns('',
        # ...
        (r'^articles/feed/$', ArticleFeed()),
        (r'^articles/feed/(?P<slug>[a-z0-9\-]+)/$', CategoryArticleFeed()),
        # ...
    )


The API for the feed object in syndication.views is almost identical to that in 
[Django's contrib app](http://docs.djangoproject.com/en/dev/ref/contrib/syndication/), except get_object() takes the request and any arguments passed
to it from the URL rather than the "bits".
