from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Conversation(models.Model):
    """Модель диалога между двумя пользователями"""
    participants = models.ManyToManyField(User, related_name='conversations', verbose_name='Участники')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)
    
    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'Диалог между {", ".join([p.username for p in self.participants.all()])}'
    
    def get_absolute_url(self):
        return reverse('messaging:conversation', args=[self.id])
    
    def last_message(self):
        return self.messages.order_by('-created_at').first()
    
    def unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

class Message(models.Model):
    """Модель сообщения"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name='Диалог')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='Отправитель')
    content = models.TextField('Сообщение')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Отправлено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()