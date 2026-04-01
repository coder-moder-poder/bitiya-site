from django.contrib.sitemaps import Sitemap
from .models import Article  # Замени Article на название твоей модели статей

class ArticleSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        # Возвращает все статьи
        return Article.objects.all()

    def lastmod(self, obj):
        # Возвращает дату последнего изменения
        # Если у тебя есть поле updated_at, используй его
        return obj.created_at  # Или obj.pub_date