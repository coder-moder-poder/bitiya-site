from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from .models import Article, Category, Comment, Event, Like, Tag
from .forms import ArticleForm, CommentForm
from django.db.models import Q
from django.http import JsonResponse  # Добавьте в импорт
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedImage
import json
import os
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.core.paginator import Paginator


def home(request):
    """Главная страница - последние статьи и активное событие"""
    # Получаем последние 6 статей
    articles = Article.objects.filter(is_published=True).order_by('-created_at')[:6]
    
    # Получаем активное событие (если есть)
    active_event = Event.objects.filter(is_active=True).first()
    
    return render(request, 'home.html', {
        'articles': articles,
        'active_event': active_event
    })

def article_list(request):
    """Список всех статей с фильтром по категориям"""
    articles = Article.objects.filter(is_published=True)
    
    # Получаем slug категории из GET-параметра
    category_slug = request.GET.get('category')
    current_category = None
    
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        articles = articles.filter(category=current_category)
    
    # Сортируем по дате (новые сверху)
    articles = articles.order_by('-created_at')
    
    # Все категории для меню фильтра
    categories = Category.objects.annotate(
        article_count=Count('article', filter=models.Q(article__is_published=True))
    ).filter(article_count__gt=0)
    
    # Пагинация
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'articles/article_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': current_category,
    })

def article_detail(request, slug):
    """Детальная страница статьи"""
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    # Увеличиваем просмотры
    article.views += 1
    article.save()
    
    # Похожие статьи на основе тегов
    similar_articles = []
    if article.tags.exists():
        # Находим статьи с такими же тегами
        similar_articles = Article.objects.filter(
            tags__in=article.tags.all(),
            is_published=True
        ).exclude(
            id=article.id
        ).annotate(
            common_tags=Count('tags')
        ).order_by('-common_tags', '-created_at')[:4]
    
    # Комментарии
    comments = article.comments.filter(parent=None, is_approved=True)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = Comment.objects.get(id=parent_id)
            
            comment.save()
            return redirect('articles:article_detail', slug=article.slug)
    else:
        form = CommentForm()
    
    return render(request, 'articles/article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form,
        'similar_articles': similar_articles,  # ← добавляем похожие статьи
    })

from django.utils.text import slugify

@login_required
def create_article(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.is_published = True  # ← КЛЮЧЕВАЯ СТРОКА
            
            from django.utils.text import slugify
            base_slug = slugify(article.title)
            
            if not base_slug:
                base_slug = f"article-{Article.objects.count() + 1}"
            
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            article.slug = slug
            article.save()
            form.save_m2m()
            
            messages.success(request, f'Статья "{article.title}" успешно создана!')
            return redirect('articles:article_detail', slug=article.slug)
        else:
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')
    
    else:
        form = ArticleForm()
    
    return render(request, 'articles/create_article.html', {
        'form': form,
        'categories': categories
    })

@login_required
def my_articles(request):
    """Мои статьи"""
    articles = Article.objects.filter(author=request.user, is_published=True)
    
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'articles/my_articles.html', {'articles': page_obj})

@login_required
def edit_article(request, slug):
    """Редактирование статьи"""
    article = get_object_or_404(Article, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        
        if form.is_valid():
            # Сохраняем старый slug
            old_slug = article.slug
            
            article = form.save(commit=False)
            article.slug = old_slug  # Возвращаем старый slug
            
            # Явно сохраняем is_published из формы (если галочка есть)
            article.is_published = form.cleaned_data.get('is_published', article.is_published)
            
            # Дополнительная защита от пустого slug
            if not article.slug:
                article.slug = f"article-{article.id or 'temp'}"
            
            article.save()
            form.save_m2m()
            
            messages.success(request, 'Статья успешно обновлена!')
            return redirect('articles:article_detail', slug=article.slug)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'articles/edit_article.html', {
        'form': form,
        'article': article
    })

@login_required
def toggle_like(request, article_id):
    """Переключение лайка (добавить/удалить)"""
    article = get_object_or_404(Article, id=article_id)
    like, created = Like.objects.get_or_create(user=request.user, article=article)
    
    if not created:
        like.delete()
        messages.success(request, f'Лайк убран с "{article.title}"')
    else:
        messages.success(request, f'Вы поставили лайк статье "{article.title}"')
    
    return redirect('articles:article_detail', slug=article.slug)

@login_required
def edit_article(request, slug):
    """Редактирование статьи"""
    article = get_object_or_404(Article, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        
        if form.is_valid():
            article = form.save(commit=False)
            
            # Если заголовок изменился — обновляем slug
            from django.utils.text import slugify
            new_base_slug = slugify(article.title)
            
            if new_base_slug and new_base_slug != article.slug:
                slug = new_base_slug
                counter = 1
                while Article.objects.filter(slug=slug).exclude(id=article.id).exists():
                    slug = f"{new_base_slug}-{counter}"
                    counter += 1
                article.slug = slug
            
            article.save()
            form.save_m2m()
            messages.success(request, 'Статья обновлена!')
            return redirect('articles:article_detail', slug=article.slug)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'articles/edit_article.html', {
        'form': form,
        'article': article
    })

@login_required
def delete_article(request, slug):
    """Удаление своей статьи (с подтверждением)"""
    article = get_object_or_404(Article, slug=slug)
    
    if request.user != article.author:
        messages.error(request, 'Вы можете удалять только свои статьи.')
        return redirect('articles:article_detail', slug=article.slug)
    
    if request.method == 'POST':
        article_title = article.title
        article.delete()
        messages.success(request, f'Статья "{article_title}" удалена.')
        return redirect('accounts:profile', username=request.user.username)
    
    return render(request, 'articles/delete_article.html', {'article': article})


@csrf_exempt
@require_POST
def upload_ckeditor_image(request):
    """Загрузка изображения для CKEditor"""
    if request.method == 'POST' and request.FILES.get('upload'):
        image = request.FILES['upload']
        
        # Создаём путь для сохранения
        upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        # Сохраняем файл
        filename = image.name
        filepath = os.path.join(upload_path, filename)
        
        # Если файл с таким именем уже существует, добавляем номер
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            filepath = os.path.join(upload_path, filename)
            counter += 1
        
        with open(filepath, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # Возвращаем URL загруженного файла
        file_url = f"{settings.MEDIA_URL}uploads/{filename}"
        
        return JsonResponse({
            'url': file_url,
            'uploaded': True
        })
    
    return JsonResponse({'error': 'Файл не загружен'}, status=400)

def tag_detail(request, slug):
    """Страница со статьями по тегу"""
    tag = get_object_or_404(Tag, slug=slug)
    articles = tag.articles.filter(is_published=True).order_by('-created_at')
    
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'articles/tag_detail.html', {
        'tag': tag,
        'page_obj': page_obj,
    })

@require_POST
@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Проверяем, что пользователь — автор
    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    
    # Проверяем время (не больше 5 минут)
    if not comment.can_edit():
        return JsonResponse({'success': False, 'error': 'Время редактирования истекло (5 минут)'}, status=403)
    
    import json
    data = json.loads(request.body)
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return JsonResponse({'success': False, 'error': 'Комментарий не может быть пустым'}, status=400)
    
    comment.content = new_content
    comment.save()
    
    return JsonResponse({'success': True})

@require_POST
@login_required
def delete_comment(request, comment_id):
    """Удаление комментария (только автор)"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Проверяем, что пользователь — автор комментария
    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    
    comment.delete()
    return JsonResponse({'success': True})