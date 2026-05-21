from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import RegisterForm, ProfileForm, UserForm
from django.db.models import Q
from .models import Friend
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import Notification
from django.core.paginator import Paginator
from django.db import models
from .models import Gift, UserGift
import json
from .models import ProfileView 
from datetime import timedelta
from .models import Profile

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # 👇 СОЗДАЁМ ПРОФИЛЬ СРАЗУ ПОСЛЕ РЕГИСТРАЦИИ
            Profile.objects.get_or_create(user=user)
            
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
    
    # Исправленный способ получения друзей
    friendships = Friend.objects.filter(
        status='accepted'
    ).filter(
        models.Q(from_user=user) | models.Q(to_user=user)
    )
    
    friends = []
    for friendship in friendships:
        if friendship.from_user == user:
            friends.append(friendship.to_user)
        else:
            friends.append(friendship.from_user)
    
    # Проверяем, друзья ли мы с этим пользователем
    is_friend = Friend.objects.filter(
        status='accepted'
    ).filter(
        (models.Q(from_user=request.user, to_user=user) |
         models.Q(from_user=user, to_user=request.user))
    ).exists()
    
    # Проверяем, отправлял ли текущий пользователь заявку этому человеку
    has_pending_request = Friend.objects.filter(
        from_user=request.user,
        to_user=user,
        status='pending'
    ).exists()

     # Получаем подарки пользователя
    received_gifts = UserGift.objects.filter(to_user=user).select_related('gift', 'from_user')[:10]

    # Формируем JSON для JavaScript
    import json
    gifts_json = json.dumps([
        {'url': gift.gift.image.url, 'name': gift.gift.name}
        for gift in received_gifts
    ])

    # 👇 НОВЫЙ КОД: Логируем просмотр профиля
    if request.user.is_authenticated and request.user != user:
        from .models import ProfileView
        from django.utils import timezone
        
        # Убираем пометку "новое" со старых просмотров от этого же гостя
        ProfileView.objects.filter(
            viewed_profile=user, 
            viewer=request.user, 
            is_new=True
        ).update(is_new=False)

        # Удаляем записи старше 30 дней
        cutoff_date = timezone.now() - timedelta(days=30)
        ProfileView.objects.filter(viewed_profile=user, viewed_at__lt=cutoff_date).delete()
        
        # Создаём новый просмотр
        ProfileView.objects.create(
            viewer=request.user, 
            viewed_profile=user
        )
    
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'articles': articles,
        'friends': friends,
        'is_friend': is_friend,
        'has_pending_request': has_pending_request,  # проверка заявки
        'received_gifts': received_gifts,    # ← если нужно в шаблоне
        'gifts_json': gifts_json,
    })

@login_required
def profile_edit(request):
    # 👇 ГАРАНТИРУЕМ, ЧТО ПРОФИЛЬ ЕСТЬ
    Profile.objects.get_or_create(user=request.user)
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

def user_search(request):
    query = request.GET.get('q', '')
    users = []  # ← ИНИЦИАЛИЗИРУЕМ ПУСТЫМ СПИСКОМ
    all_users = User.objects.all()[:20]  # для автодополнения (не больше 20)
    
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)  # исключаем текущего пользователя
    
    return render(request, 'accounts/user_search.html', {
        'query': query,
        'users': users,
        'all_users': all_users,  # ← добавляем для datalist
    })

def send_friend_request(request, username):
    to_user = get_object_or_404(User, username=username)
    
    if request.user == to_user:
        messages.error(request, 'Нельзя добавить самого себя в друзья')
        return redirect('accounts:profile', username=username)
    
    # Проверяем, есть ли уже активная (не отклонённая) заявка
    existing_request = Friend.objects.filter(
        from_user=request.user, 
        to_user=to_user
    ).exclude(status='rejected').first()
    
    if existing_request:
        messages.warning(request, 'Вы уже отправили заявку этому пользователю')
    else:
        # Удаляем старую отклонённую заявку, если есть
        Friend.objects.filter(
            from_user=request.user, 
            to_user=to_user, 
            status='rejected'
        ).delete()
        
        # Создаём новую заявку
        Friend.objects.create(from_user=request.user, to_user=to_user, status='pending')
        
        # Создаём уведомление
        create_notification(
            user=to_user,
            notification_type='friend_request',
            from_user=request.user,
            text=f'{request.user.username} хочет добавить вас в друзья',
            link=f'/accounts/profile/{request.user.username}/'
        )
        
        messages.success(request, f'Заявка в друзья отправлена пользователю {to_user.username}')
    
    return redirect('accounts:profile', username=username)

@login_required
def accept_friend_request(request, notification_id):
    """Принять заявку в друзья по ID уведомления"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Находим заявку по отправителю и получателю
    friend_request = get_object_or_404(
        Friend,
        from_user=notification.from_user,
        to_user=request.user,
        status='pending'
    )
    
    friend_request.status = 'accepted'
    friend_request.save()
    
    # Отмечаем уведомление как прочитанное
    notification.is_read = True
    notification.save()
    
    # Создаём уведомление для отправителя
    create_notification(
        user=friend_request.from_user,
        notification_type='friend_accepted',
        from_user=request.user,
        text=f'{request.user.username} принял(а) вашу заявку в друзья',
        link=f'/accounts/profile/{request.user.username}/'
    )
    
    messages.success(request, f'Вы приняли заявку в друзья от {friend_request.from_user.username}')
    return redirect('accounts:notifications')

@login_required
def reject_friend_request(request, notification_id):
    """Отклонить заявку в друзья по ID уведомления"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    friend_request = get_object_or_404(
        Friend,
        from_user=notification.from_user,
        to_user=request.user,
        status='pending'
    )
    
    friend_request.status = 'rejected'
    friend_request.save()
    
    notification.is_read = True
    notification.save()
    
    messages.warning(request, f'Вы отклонили заявку от {friend_request.from_user.username}')
    return redirect('accounts:notifications')

@login_required
def friend_requests(request):
    """Страница с заявками в друзья"""
    received_requests = Friend.objects.filter(to_user=request.user, status='pending')
    return render(request, 'accounts/friend_requests.html', {
        'received_requests': received_requests,
    })

def create_notification(user, notification_type, from_user, text, link=''):
    """Создаёт уведомление для пользователя"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        from_user=from_user,
        text=text,
        link=link
    )

@login_required
def notifications_view(request):
    filter_type = request.GET.get('filter', 'all')
    
    notifications = Notification.objects.filter(user=request.user)
    profile_views = []  # ← для просмотров профиля
    
    # Добавляем статус заявки для каждого уведомления
    for notification in notifications:
        if notification.notification_type == 'friend_request':
            friend_request = Friend.objects.filter(
                from_user=notification.from_user,
                to_user=request.user
            ).first()
            notification.friend_request_status = friend_request.status if friend_request else None
        else:
            notification.friend_request_status = None
    
    # Фильтрация
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'friend':
        notifications = notifications.filter(notification_type__in=['friend_request', 'friend_accepted'])
    elif filter_type == 'gift':
        notifications = notifications.filter(notification_type='gift')
    elif filter_type == 'view':
        # Вместо уведомлений — показываем просмотры профиля
        profile_views = ProfileView.objects.filter(viewed_profile=request.user).select_related('viewer')[:50]
        # Помечаем как прочитанные (убираем is_new)
        ProfileView.objects.filter(viewed_profile=request.user, is_new=True).update(is_new=False)
    else:
        # 'all' — показываем всё как обычно
        pass
    
    # Пагинация для уведомлений
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/notifications.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'filter': filter_type,
        'profile_views': profile_views,  # ← передаём просмотры
    })

@login_required
def mark_notification_read(request, notif_id):
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notif_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('accounts:notifications')

@login_required
def friends_list(request, username):
    """Страница со всеми друзьями пользователя"""
    profile_user = get_object_or_404(User, username=username)
    friends = profile_user.profile.get_friends()
    
    return render(request, 'accounts/friends_list.html', {
        'profile_user': profile_user,
        'friends': friends,
    })

def unread_notifications_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def send_gift(request, username):
    recipient = get_object_or_404(User, username=username)
    gifts = Gift.objects.filter(is_active=True)
    return render(request, 'accounts/send_gift.html', {
        'recipient': recipient,
        'gifts': gifts,
    })

@login_required
def send_gift_confirm(request, username, gift_id):
    recipient = get_object_or_404(User, username=username)
    gift = get_object_or_404(Gift, id=gift_id, is_active=True)
    
    # Создаём запись о подарке
    user_gift = UserGift.objects.create(
        from_user=request.user,
        to_user=recipient,
        gift=gift
    )
    
    # Увеличиваем счётчик подарков у получателя
    recipient.profile.gifts_count += 1
    recipient.profile.save()
    
    # Уведомление
    create_notification(
        user=recipient,
        notification_type='gift',
        from_user=request.user,
        text=f'{request.user.username} отправил вам подарок "{gift.name}"',
        link=f'/accounts/profile/{request.user.username}/'
    )
    
    messages.success(request, f'Подарок "{gift.name}" отправлен {recipient.username}!')
    return redirect('accounts:profile', username=recipient.username)

def gifts_gallery(request, username):
    user = get_object_or_404(User, username=username)
    received_gifts = UserGift.objects.filter(to_user=user).select_related('gift', 'from_user')
    return render(request, 'accounts/gifts_gallery.html', {
        'profile_user': user,
        'received_gifts': received_gifts,
    })

@login_required
def clear_profile_views(request):
    """Очистить всю историю просмотров профиля"""
    if request.method == 'POST':
        ProfileView.objects.filter(viewed_profile=request.user).delete()
        messages.success(request, 'История просмотров очищена')
    return redirect('/accounts/notifications/?filter=view')