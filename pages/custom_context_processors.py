from pages.models import Notification


def notificaiton(request):
    if request.user.is_authenticated:
        user_notification = Notification.objects.filter(receptor=request.user, is_read=False).order_by('-datetime_created')
    else:
        user_notification = ""


    return {
        "notificaitons": user_notification,
    }