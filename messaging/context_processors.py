from .models import Message

def unread_messages_count(request):
    """Количество непрочитанных сообщений для текущего пользователя"""
    if request.user.is_authenticated:
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(
            sender=request.user
        ).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}