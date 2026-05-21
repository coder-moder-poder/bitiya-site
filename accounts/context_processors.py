from .models import Notification, ProfileView


def unread_notifications_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_count': count}
    return {'unread_count': 0}

def profile_views_count(request):
    if request.user.is_authenticated:
        # Считаем новые (непросмотренные) просмотры профиля
        count = ProfileView.objects.filter(viewed_profile=request.user, is_new=True).count()
        return {'new_profile_views_count': count}
    return {'new_profile_views_count': 0}