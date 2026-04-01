from django.contrib.sitemaps import Sitemap
from .models import Article  # У вас модель называется Article

class ArticleSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        # Берём только опубликованные статьи
        return Article.objects.filter(is_published=True)

    def lastmod(self, obj):
        # Используем поле updated_at, которое есть в модели
        return obj.updated_at