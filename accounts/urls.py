from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LoginForm
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile-edit/', views.profile_edit, name='profile_edit'),  # Изменено с profile/edit/ на profile-edit/
    path('search/', views.user_search, name='user_search'),
    path('friend/send/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend/requests/', views.friend_requests, name='friend_requests'),
    path('friend/accept/<int:notification_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:notification_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notification/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('friends/<str:username>/', views.friends_list, name='friends_list'),
    path('unread_notifications_count/', views.unread_notifications_count, name='unread_notifications_count'),
    path('send_gift/<str:username>/', views.send_gift, name='send_gift'),
    path('send_gift_confirm/<str:username>/<int:gift_id>/', views.send_gift_confirm, name='send_gift_confirm'),
    path('gifts/<str:username>/', views.gifts_gallery, name='gifts_gallery'),
    path('clear-profile-views/', views.clear_profile_views, name='clear_profile_views'),
]