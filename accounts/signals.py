from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.apps import apps

@receiver(pre_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    """Удаляем профиль при удалении пользователя"""
    Profile = apps.get_model('accounts', 'Profile')
    if hasattr(instance, 'profile'):
        instance.profile.delete()