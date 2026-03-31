from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from articles import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('articles/', include('articles.urls')),
    path('accounts/', include('accounts.urls')),
    path('messages/', include('messaging.urls')),
    # path('ckeditor/', include('ckeditor_uploader.urls')),  # Добавьте эту строку
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)