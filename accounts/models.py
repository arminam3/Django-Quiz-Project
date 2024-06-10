import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from extensions.utils import jalali_convertor

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
#     CHOICES = (
#         ('light', 'light'),
#         ('dark', 'dark')
#     )
#     theme = models.CharField(choices=CHOICES, max_length=32, default='light')


class Profile(models.Model):
    CHOICES = (
        ('1', 'پزشکی'),
        ('2', 'پرستاری'),
    )
    GENDER_CHOICES = (
        ('1', 'آقا'),
        ('2', 'خانم'),
    )
    phone_number_validator=[RegexValidator(r'^[0-9]*$', 'Only numerical values are allowed.')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=11, unique=True, validators=phone_number_validator)
    phone_number_confirm = models.BooleanField(default=False)
    term = models.PositiveIntegerField(default=1)
    discipline = models.CharField(choices=CHOICES, max_length=7, default=1)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=7)
    is_quiz_maker = models.BooleanField(default=False)


    def j_datetime_joined(self):
        return jalali_convertor(self.user.last_login)
    

class VerificationCode(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="verification_code")
    code = models.CharField(max_length=255)
    datetime_created = models.DateTimeField(auto_now_add=True)


class IpAdress(models.Model):
    ip = models.CharField(max_length=255)
    datetime_created = models.DateTimeField(auto_now_add=True)
