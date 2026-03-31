from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('send/<str:username>/', views.send_message_from_profile, name='send_message'),
]