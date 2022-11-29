from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords
from .models import Post


class LatestPostsFeed(Feed):
    title = 'My blog'
    link = '/blog/'
    description = 'New posts of my blog.'

    def items(self):
        """Объект которые будут в рассылке"""
        return Post.published.all()[:5]

    def item_title(self, item):
        """ Заголовок из объектов items """
        return item.title

    def item_description(self, item):
        """ Статья из объектов items """
        return truncatewords(item.body, 30)  # ограничиваем статью 30 словами
