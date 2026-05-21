from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.contrib.auth.models import User
from .models import Conversation
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Message
from django.utils import timezone
import re
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time

@login_required
def inbox(request):
    """Список диалогов пользователя"""
    conversations = request.user.conversations.all()
    
    # Добавляем информацию о непрочитанных сообщениях
    for conv in conversations:
        conv.unread = conv.unread_count(request.user)
        conv.last_msg = conv.last_message()
        # Получаем собеседника
        conv.other_user = conv.participants.exclude(id=request.user.id).first()
    
    return render(request, 'messaging/inbox.html', {
        'conversations': conversations
    })

@login_required
def conversation_with_user(request, username):
    """Начать или продолжить диалог с пользователем по его username"""
    from django.contrib.auth.models import User
    from .models import Conversation
    
    other_user = get_object_or_404(User, username=username)
    
    # Ищем существующий диалог между пользователями
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()
    
    # Если диалога нет — создаём
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    # Перенаправляем на существующую функцию с conversation_id
    return redirect('messaging:conversation', conversation_id=conversation.id)

import re

@login_required
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.user not in conversation.participants.all():
        messages.error(request, 'У вас нет доступа к этому диалогу.')
        return redirect('messaging:inbox')
    
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content and content.strip():
            # Замена [sticker:...] на HTML
            import re
            def replace_sticker(match):
                img_url = match.group(1)
                return f'<img src="{img_url}" class="message-sticker">'
            
            new_content = re.sub(r'\[sticker:(.*?)\]', replace_sticker, content)
            
            print("Оригинал:", content)      # отладка
            print("После замены:", new_content) # отладка
            
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=new_content.strip()
            )
            return redirect('messaging:conversation', conversation_id=conversation.id)
    
    # Помечаем непрочитанные сообщения
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    for msg in unread_messages:
        msg.mark_as_read()
    
    messages_list = conversation.messages.all()
    
    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'messages': messages_list,  
        'other_user': other_user
    })

@login_required
def start_conversation(request, username):
    """Начать новый диалог с пользователем"""
    other_user = get_object_or_404(User, username=username)
    
    # Проверяем, нельзя начать диалог с самим собой
    if request.user == other_user:
        messages.error(request, 'Нельзя начать диалог с самим собой.')
        return redirect('messaging:inbox')
    
    # Ищем существующий диалог между этими пользователями
    conversations = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
    
    if conversations.exists():
        # Диалог уже существует
        conversation = conversations.first()
        return redirect('messaging:conversation', conversation_id=conversation.id)
    
    # Создаём новый диалог
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)
    conversation.save()
    
    messages.success(request, f'Диалог с {other_user.username} создан!')
    return redirect('messaging:conversation', conversation_id=conversation.id)

@login_required
def send_message_from_profile(request, username):
    """Отправить сообщение из профиля пользователя"""
    other_user = get_object_or_404(User, username=username)
    
    if request.user == other_user:
        messages.error(request, 'Нельзя отправить сообщение самому себе.')
        return redirect('accounts:profile', username=request.user.username)
    
    # Ищем или создаём диалог
    conversations = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
    
    if conversations.exists():
        conversation = conversations.first()
    else:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content and content.strip():
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content.strip()
            )
            messages.success(request, 'Сообщение отправлено!')
            return redirect('messaging:conversation', conversation_id=conversation.id)
    
    return render(request, 'messaging/send_message.html', {
        'recipient': other_user,
        'conversation': conversation if conversations.exists() else None
    })

@require_POST
@login_required
def edit_message(request, message_id):
    """Редактирование сообщения (только свои, в течение 5 минут)"""
    message = get_object_or_404(Message, id=message_id)
    
    # Проверяем, что пользователь — отправитель
    if message.sender != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    
    # Проверяем время
    if not message.can_edit():
        return JsonResponse({'success': False, 'error': 'Время редактирования истекло (5 минут)'}, status=403)
    
    import json
    data = json.loads(request.body)
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return JsonResponse({'success': False, 'error': 'Сообщение не может быть пустым'}, status=400)
    
    message.content = new_content
    message.edited_at = timezone.now()
    message.save()
    
    return JsonResponse({'success': True})

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@login_required
def delete_message(request, message_id):
    """Удаление своего сообщения"""
    message = get_object_or_404(Message, id=message_id)
    
    # Проверяем, что пользователь — отправитель
    if message.sender != request.user:
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    
    message.delete()
    return JsonResponse({'success': True})

@require_POST
@login_required
def delete_conversation(request, conversation_id):
    """Удаление всего диалога"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверяем, что пользователь участник диалога
    if request.user not in conversation.participants.all():
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    
    conversation.delete()
    return JsonResponse({'success': True})

@require_POST
@login_required
def send_photo(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    
    photo = request.FILES.get('photo')
    if not photo:
        return JsonResponse({'error': 'Файл не загружен'}, status=400)
    
    # Сохраняем фото
    ext = photo.name.split('.')[-1]
    filename = f'chat_photos/{conversation.id}_{int(time.time())}.{ext}'
    saved_path = default_storage.save(filename, ContentFile(photo.read()))
    photo_url = default_storage.url(saved_path)
    
    # Создаём сообщение
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=f'<img src="{photo_url}" class="message-photo">'
    )
    
    return redirect('messaging:conversation', conversation_id=conversation.id)

def unread_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'messages_count': 0})
    
    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    
    return JsonResponse({'messages_count': count})

