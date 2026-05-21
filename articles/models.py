from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class Category(models.Model):
    """Категории статей"""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', unique=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])
    
class Tag(models.Model):
    """Теги для статей"""
    name = models.CharField('Название', max_length=50, unique=True)
    slug = models.SlugField('URL', unique=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('articles:tag_detail', args=[self.slug])
    
class Article(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('URL', unique=True)
    content = RichTextUploadingField('Содержание')
    excerpt = models.TextField('Краткое описание', max_length=300, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='articles')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField('Превью', upload_to='articles/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    views = models.PositiveIntegerField('Просмотры', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)
    tags = models.ManyToManyField(Tag, verbose_name='Теги', blank=True, related_name='articles')

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('articles:article_detail', args=[self.slug])
    
    def total_likes(self):
        return self.likes.count()
    
    def save(self, *args, **kwargs):
    # Только при создании генерируем slug, если его нет
        if not self.pk and not self.slug:
            self.slug = slugify(self.title) or f"article-{id(self)}"
        
        # Защита от пустого slug
        if not self.slug:
            raise ValidationError("Slug не может быть пустым")
        
        super().save(*args, **kwargs)  # ← важно передать *args, **kwargs


class UploadedImage(models.Model):
    """Модель для хранения загруженных через редактор изображений"""
    image = models.ImageField('Изображение', upload_to='uploads/')
    uploaded_at = models.DateTimeField('Загружено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Загруженное изображение'
        verbose_name_plural = 'Загруженные изображения'
    
    def __str__(self):
        return self.image.name
    
class Like(models.Model):
    """Модель для лайков"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_likes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'article')  # Один пользователь - один лайк на статью
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
    
    def __str__(self):
        return f'{self.user.username} -> {self.article.title}'

class Comment(models.Model):
    """Комментарии к статьям"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name='Статья')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='Ответ на')
    content = models.TextField('Комментарий', max_length=1000)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    is_approved = models.BooleanField('Одобрен', default=True)
    
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def can_edit(self):
        """Можно ли редактировать комментарий (5 минут после создания)"""
        time_limit = self.created_at + timedelta(minutes=10)
        return timezone.now() < time_limit
    
    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'
    
class Event(models.Model):
    """События и новости деревни (баннер на главной)"""
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Описание')
    image = models.ImageField('Изображение', upload_to='events/', blank=True, null=True)
    is_active = models.BooleanField('Активно', default=True, help_text='Показывать на главной странице')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
