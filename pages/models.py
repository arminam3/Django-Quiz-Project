from django.db import models
from django.contrib.auth import get_user_model

from extensions.utils import jalali_convertor

class Notification(models.Model):
    sender = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL ,null=True, related_name='notification_sender')
    receptor = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL ,null=True, related_name='notification_receptor')
    title = models.CharField(max_length=127)
    text = models.TextField(max_length=1023, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)

    def j_datetime_created(self):
        return jalali_convertor(self.datetime_created)