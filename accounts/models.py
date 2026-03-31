from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Аватар', upload_to='avatars/', default='avatars/default.jpg', blank=True)
    bio = models.TextField('О себе', max_length=500, blank=True)
    birth_place = models.CharField('Откуда родом', max_length=100, blank=True, help_text='Например: Бития, Абатский район')
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f'Профиль {self.user.username}'