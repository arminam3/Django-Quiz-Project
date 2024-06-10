from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .models import IpAdress


class DoNotHaveProfileMixin:
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile:
            return HttpResponse('شما از قبل پروفایل دارید')
        else:
            return super().dispatch(request, *args, **kwargs)
        
class CheckHavingProfileMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(
                self.request,
                f"<strong>توجه !</strong> لطفا ابتد به حساب کاربری خود وارد شوید."
                )
            return redirect('login')
        elif not hasattr(request.user, 'profile'):
            messages.warning(
                self.request,
                f"<strong>توجه !</strong> برای ورود به این صفحه باید پروفایل خود را تکمیل کنید."
                )
            return redirect('profile_create')
        else:
            return super().dispatch(request, *args, **kwargs)
        
class SmsSendLimitByIpMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get('username'):
            today = timezone.now().date()

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            ip_address = IpAdress.objects.create(ip=ip)
            total_request = IpAdress.objects.filter(ip=ip, datetime_created__date=today).count()
            if total_request > 5:
                messages.error(
                    self.request,
                    f"<strong>توجه !</strong> شما بیبش از حد مجاز درخواست ارسال پیامک داشته اید . فردا دوباره امتحان کنید."
                    )
                return JsonResponse({'error': 'try tomorrow!'}, status=500)
            return super().dispatch(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)
        

class IsStaffUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponse('شما مجاز به دسترسی به این صفحه نیستید')
    

class IsStaffOrQuizMakerUserMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if not hasattr(request.user, 'profile'):
                messages.warning(
                    self.request,
                    f"<strong>توجه !</strong> برای ورود به این صفحه باید پروفایل خود را تکمیل کنید."
                    )
                return redirect('profile_create')
            if user.profile.is_quiz_maker or user.is_staff :
                return super().dispatch(request, *args, **kwargs)
        return HttpResponse('شما مجاز به دسترسی به این صفحه نیستید ')


