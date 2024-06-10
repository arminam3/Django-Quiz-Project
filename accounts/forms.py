from django import forms
from django.contrib.auth import get_user_model

from .models import Profile
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

class RegisterForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'password1', 'password2')


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('discipline', 'gender', 'term')


class CustomPasswordResetForm(forms.Form):

    new_password1 = forms.PasswordInput()
    new_password2 = forms.PasswordInput()