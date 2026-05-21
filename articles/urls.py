from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('create/', views.create_article, name='create_article'),
    path('my-articles/', views.my_articles, name='my_articles'),
    path('edit/<slug:slug>/', views.edit_article, name='edit_article'),
    path('delete/<slug:slug>/', views.delete_article, name='delete_article'),
    path('like/<int:article_id>/', views.toggle_like, name='toggle_like'),
    path('upload-image/', views.upload_ckeditor_image, name='upload_ckeditor_image'),  
    path('<slug:slug>/', views.article_detail, name='article_detail'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]