from django.contrib.sitemaps import Sitemap
from .models import Post


class PostSitemap(Sitemap):
    changefreq = 'weekly'  # частота обновления страниц
    priority = 0.9  # степень совпадения с тематикой

    def items(self):
        """ Возвращает QuerySet объекты,
            которые будут отбражаться
            в карте сайта
        """
        return Post.published.all()

    def lastmod(self, obj):
        """ Принимает объекты из items и
            возвращает время модификации
        """
        return obj.updated
