from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from articles import views
from django.views.generic import TemplateView
from articles.sitemaps import ArticleSitemap
from django.contrib.sitemaps.views import index, sitemap

sitemaps = {
    'articles': ArticleSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('articles/', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    path('messages/', include('messaging.urls')),
    path('yandex_1bbf0002d59d9074.html', TemplateView.as_view(template_name='yandex_1bbf0002d59d9074.html', content_type='text/html')),
    
    # Правильный способ для Django 6.0.3:
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap_section'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)