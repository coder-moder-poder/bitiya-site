from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Conversation

@receiver(pre_delete, sender=User)
def delete_user_conversations(sender, instance, **kwargs):
    """Удаляем все диалоги пользователя при его удалении"""
    Conversation.objects.filter(participants=instance).delete()