from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('conversation/user/<str:username>/', views.conversation_with_user, name='conversation_with_user'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('conversation/<str:username>/', views.conversation_view, name='conversation'),
    path('message/edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('conversation/delete/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('send_photo/<int:conversation_id>/', views.send_photo, name='send_photo'),
    path('unread_count/', views.unread_count, name='unread_count'),
]