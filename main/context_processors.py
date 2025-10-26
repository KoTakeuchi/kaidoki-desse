from .models import Notification

def unread_count(request):
    if not request.user.is_authenticated:
        return {}
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"unread_count": count}
