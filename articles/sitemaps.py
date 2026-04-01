from django.contrib.sitemaps import Sitemap
from .models import Article  # Убедитесь, что у вас модель называется Article

class ArticleSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Article.objects.all()

    def lastmod(self, obj):
        return obj.created_at