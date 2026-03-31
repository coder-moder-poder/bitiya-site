from django.contrib import admin
from .models import Category, Article, Comment, Event, Like

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_at', 'views', 'is_published']
    list_filter = ['is_published', 'category', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'article', 'created_at']
    list_filter = ['created_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    fields = ['title', 'content', 'image', 'is_active']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'article__title']