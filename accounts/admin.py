from django.contrib import admin
from .models import Profile, Friend, Notification
from .models import Gift, UserGift

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'birth_place', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'text', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'text']
    readonly_fields = ['created_at']


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status']

@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(UserGift)
class UserGiftAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'gift', 'created_at']
    list_filter = ['created_at']
    search_fields = ['from_user__username', 'to_user__username', 'gift__name']