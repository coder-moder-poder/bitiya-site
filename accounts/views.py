from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import RegisterForm, ProfileForm, UserForm

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def custom_logout(request):
    """Пользовательский выход из аккаунта"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('home')

@login_required
def profile_view(request, username):
    """Просмотр профиля пользователя"""
    user = get_object_or_404(User, username=username)
    articles = user.articles.filter(is_published=True)
    
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'articles': articles,
    })

@login_required
def profile_edit(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('accounts:profile', username=request.user.username)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })