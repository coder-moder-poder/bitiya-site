from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from articles import views
from django.views.generic import TemplateView
from articles.sitemaps import ArticleSitemap
from django.contrib.sitemaps.views import sitemap

sitemaps = {
    'articles': ArticleSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('articles/', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    path('messages/', include('messaging.urls')),
    # path('ckeditor/', include('ckeditor_uploader.urls')),  # Добавьте эту строку
    path('yandex_123456.html', TemplateView.as_view(template_name='yandex_123456.html', content_type='text/html')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)