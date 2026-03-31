from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from .models import Article, Category, Comment, Event, Like
from .forms import ArticleForm, CommentForm
from django.db.models import Q
from django.http import JsonResponse  # Добавьте в импорт
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import UploadedImage
import json
import os
from django.conf import settings



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
    """Страница со списком всех статей с поиском"""
    articles = Article.objects.filter(is_published=True).order_by('-created_at')
    
    # Поиск по статьям
    query = request.GET.get('q')
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |  # Поиск в заголовке
            Q(content__icontains=query) |  # Поиск в содержании
            Q(excerpt__icontains=query) |  # Поиск в кратком описании
            Q(author__username__icontains=query)  # Поиск по автору
        )
    
    # Пагинация
    paginator = Paginator(articles, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'article_list.html', {
        'articles': page_obj,
        'query': query  # Передаём поисковый запрос в шаблон
    })

def article_detail(request, slug):
    """Страница отдельной статьи с комментариями"""
    article = get_object_or_404(Article, slug=slug, is_published=True)
    
    # Увеличиваем счётчик просмотров
    article.views += 1
    article.save()
    
    # Получаем комментарии (только корневые, без ответов)
    comments = article.comments.filter(parent=None, is_approved=True)
    
    # Обработка комментария
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            
            # Проверка на ответ на комментарий
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            
            comment.save()
            messages.success(request, 'Ваш комментарий добавлен!')
            return redirect('articles:article_detail', slug=article.slug)
    else:
        form = CommentForm()
    
    return render(request, 'article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form,
    })

@login_required
def create_article(request):
    """Создание новой статьи (доступно всем авторизованным пользователям)"""
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            
            # Проверяем, что заголовок не пустой
            if not article.title:
                messages.error(request, 'Заголовок статьи не может быть пустым.')
                return render(request, 'articles/create_article.html', {
                    'form': form,
                    'categories': categories
                })
            
            # Создаём slug из заголовка
            article.slug = slugify(article.title)
            
            # Если slug получился пустым (например, только спецсимволы)
            if not article.slug:
                article.slug = f"article-{Article.objects.count() + 1}-{request.user.id}"
            
            # Проверяем уникальность slug
            original_slug = article.slug
            counter = 1
            while Article.objects.filter(slug=article.slug).exists():
                article.slug = f"{original_slug}-{counter}"
                counter += 1
            
            article.save()
            messages.success(request, f'Статья "{article.title}" успешно опубликована!')
            return redirect('articles:article_detail', slug=article.slug)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
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
            form.save()
            messages.success(request, 'Статья обновлена!')
            return redirect('articles:article_detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'articles/edit_article.html', {'form': form, 'article': article})

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
    article = get_object_or_404(Article, slug=slug)
    
    if request.user != article.author:
        messages.error(request, 'Вы можете редактировать только свои статьи.')
        return redirect('articles:article_detail', slug=article.slug)
    
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, f'Статья "{article.title}" успешно обновлена!')
            return redirect('articles:article_detail', slug=article.slug)
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