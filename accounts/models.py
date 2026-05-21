from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import pre_delete


class Profile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Аватар', upload_to='avatars/', default='avatars/default.png', blank=True)
    bio = models.TextField('О себе', max_length=500, blank=True)
    birth_place = models.CharField('Откуда родом', max_length=100, blank=True, help_text='Например: Бития, Абатский район')
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    gifts_count = models.IntegerField('Количество подарков', default=0)
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
    def get_friends(self):
        """Возвращает список друзей пользователя"""
        from django.db import models
        from .models import Friend  # чтобы избежать циклического импорта
        
        # Находим все принятые заявки, где пользователь участвует
        friendships = Friend.objects.filter(
            status='accepted'
        ).filter(
            models.Q(from_user=self.user) | models.Q(to_user=self.user)
        )
        
        friends = []
        for friendship in friendships:
            if friendship.from_user == self.user:
                friends.append(friendship.to_user)
            else:
                friends.append(friendship.from_user)
        
        return friends
    

class Friend(models.Model):
    """Модель для друзей и заявок"""
    STATUS_CHOICES = (
        ('pending', 'Ожидает подтверждения'),
        ('accepted', 'Друзья'),
        ('rejected', 'Отклонена'),
    )
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Дата отправки', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Друг'
        verbose_name_plural = 'Друзья'
        unique_together = ('from_user', 'to_user')  # чтобы не было дублей
    
    def __str__(self):
        return f'{self.from_user} -> {self.to_user} ({self.status})'
    

class Notification(models.Model):
    """Уведомления пользователя"""
    NOTIFICATION_TYPES = (
        ('friend_request', 'Заявка в друзья'),
        ('friend_accepted', 'Заявка принята'),
        ('gift', 'Подарок'),
        ('profile_view', 'Просмотр профиля'),
        ('message', 'Новое сообщение'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField('Тип уведомления', max_length=30, choices=NOTIFICATION_TYPES)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    text = models.CharField('Текст', max_length=255)
    is_read = models.BooleanField('Прочитано', default=False)
    link = models.CharField('Ссылка', max_length=255, blank=True)  # куда ведёт уведомление
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user} - {self.text[:50]}'
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(pre_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.delete()

class Gift(models.Model):
    """Подарки"""
    name = models.CharField('Название', max_length=100)
    image = models.ImageField('Изображение', upload_to='gifts/')
    price = models.IntegerField('Цена (внутренняя валюта)', default=0, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        verbose_name = 'Подарок'
        verbose_name_plural = 'Подарки'
    
    def __str__(self):
        return self.name


class UserGift(models.Model):
    """Отправленные подарки"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_gifts')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_gifts')
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    message = models.TextField('Сопроводительное сообщение', max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)
    
    class Meta:
        verbose_name = 'Отправленный подарок'
        verbose_name_plural = 'Отправленные подарки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.from_user} → {self.to_user}: {self.gift.name}'
    
class ProfileView(models.Model):
    """Модель для отслеживания просмотров профилей"""
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views', verbose_name='Кто посмотрел')
    viewed_profile = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_by', verbose_name='Чей профиль')
    viewed_at = models.DateTimeField('Время просмотра', auto_now_add=True)
    is_new = models.BooleanField('Новое уведомление', default=True)

    class Meta:
        verbose_name = 'Просмотр профиля'
        verbose_name_plural = 'Просмотры профилей'
        ordering = ['-viewed_at'] # Сначала самые новые

    def __str__(self):
        return f'{self.viewer} посмотрел(а) {self.viewed_profile} в {self.viewed_at}'