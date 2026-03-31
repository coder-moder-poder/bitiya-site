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
]