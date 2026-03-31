from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.contrib.auth.models import User
from .models import Conversation, Message

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


def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.user not in conversation.participants.all():
        messages.error(request, 'У вас нет доступа к этому диалогу.')
        return redirect('messaging:inbox')
    
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content and content.strip():
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content.strip()
            )
            # НЕ ДОБАВЛЯЕМ СООБЩЕНИЕ В MESSAGES
            return redirect('messaging:conversation', conversation_id=conversation.id)
    
    # Помечаем непрочитанные сообщения
    unread_messages = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    for msg in unread_messages:
        msg.mark_as_read()
    
    messages_list = conversation.messages.all()
    
    return render(request, 'messaging/conversation.html', {
    'conversation': conversation,
    'messages': messages_list,  # ТОЛЬКО ОДИН РАЗ
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