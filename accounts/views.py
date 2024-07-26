from django.forms import BaseModelForm
from django.http import JsonResponse
from django.http.response import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.urls import reverse_lazy, reverse
from django.contrib.auth import views as admin_views
from django.db.models import Avg, Sum, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import views as admin_views
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required


from .models import Profile, VerificationCode
from .forms import RegisterForm, CustomPasswordResetForm, ProfileUpdateForm
from .mixins import (
                        DoNotHaveProfileMixin, 
                        CheckHavingProfileMixin, 
                        SmsSendLimitByIpMixin, 
                        IsStaffUserMixin
                    )
from .send_code import send_code
from exam.models import Lesson

from takingtest.models import QuizResult,QuizHistory
from exam.models import Quiz

class RegisterView(CreateView):
    model = get_user_model()
    template_name = "registration/register.html"
    form_class = RegisterForm

    def get_success_url(self):
        messages.success(
            self.request,
            "<strong>خوش آمدید !</strong>  اطلاعات شما با موفقیت ثبت شد. برای دسترسی به صفخات سامانه لظفا پروفایل خود را تکمیل کنید."
        )
        login(self.request, self.object)
        return reverse('profile_create')  


class CustomPasswordChangeView(admin_views.PasswordChangeView):
    success_url = reverse_lazy('password_change_don')


class ProfileDetailView(CheckHavingProfileMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)

        user_score_sum = QuizResult.objects.filter(user=user).aggregate(score_avg=Sum("score"))['score_avg']
        user_question_answered_count = QuizHistory.objects.filter(user=user).count()
        
        try:
            user_score_avg = round(user_score_sum / user_question_answered_count * 100)
        except:
            user_score_avg = 0
        user_quiz_count = QuizResult.objects.filter(user=user).count()

        
        term_user_score_sum = QuizResult.objects.filter(user=user, quiz__lesson__term=user.profile.term).aggregate(score_avg=Sum("score"))['score_avg']
        term_user_question_answered_count = QuizHistory.objects.filter(user=user, quiz__lesson__term=user.profile.term).count()
        try:
            term_user_score_avg = round(term_user_score_sum / term_user_question_answered_count * 100)
        except:
            term_user_score_avg = 0

        term_user_quiz_count = QuizResult.objects.filter(user=user, quiz__lesson__term=user.profile.term).count()
        
        context['user_score_avg'] =  user_score_avg
        context['term_user_score_avg'] =  term_user_score_avg
        
        context['user_quiz_count'] = user_quiz_count
        context['term_user_quiz_count'] = term_user_quiz_count
        return context


class ProfileUpdateView(CheckHavingProfileMixin, UpdateView):
    model = Profile
    template_name = "accounts/profile_update.html"
    form_class = ProfileUpdateForm

    def get_success_url(self):
        messages.success(
            self.request,
            f"<strong>اطلاعات شما با موفقیت تغییر یافت .</strong>"
        )
        return reverse('profile')

    def post(self, request, *args, **kwargs):
        posted_data = self.request.POST
        # tyr to change user data else create a error message
        try:
            user = self.request.user
            user.first_name = posted_data.get('first_name')
            user.last_name = posted_data.get('last_name')
            user.email = posted_data.get('email')
            user.save()
        except:
            messages.error(
            self.request,
            f"<strong>خطا !</strong> اطلاعات را کامل و به شکل صحیح وارد کنید."
            )

        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        return super().form_valid(form)
    
    def form_invalid(self, form) :
        # create a message that say your form have a problem
        messages.error(
            self.request,
            f"<strong>خطا !</strong> اطلاعات را کامل و به شکل صحیح وارد کنید."
        )
        return super().form_invalid(form)
    

    

class ProfileCreateView(LoginRequiredMixin, DoNotHaveProfileMixin, CreateView):
    model = Profile
    template_name = "accounts/profile_create.html"
    fields = ('term', 'phone_number', 'gender')

    def get(self, request, *args, **kwargs):
        # if get request have phone_number send verification code 
        if request.GET.get('phone_number'):
            phone_number = request.GET.get('phone_number')
            verification_code = VerificationCode.objects.filter(user=request.user).order_by('-datetime_created')
           
            # check user can send only one sms per 2 minutes 
            if verification_code:
                time_diffrence = timezone.now() - verification_code[0].datetime_created
                if time_diffrence.total_seconds() < 1 :
                    messages.error(
                        request,
                        f"<strong>خطا !</strong> هر دو دقیقه یکبار می توانید درخواست ارسال کد داشته باشید."
                    )
                    return JsonResponse({'error': 'some error'}, status=500)
            verification_code = send_code(request, phone_number)

            print(verification_code)
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(
            self.request,
            "<strong>خوش آمدید !</strong>  اطلاعات شما با موفقیت ثبت شد"
                    )
        return reverse('profile') 
    
    def post(self, request, *args, **kwargs):
        posted_data = request.POST
        # check the sented code
        phone_number = posted_data.get('phone_number')
        email = posted_data.get('email')
        profile_exist = Profile.objects.filter(phone_number=phone_number)
        check_unique_user_email = get_user_model().objects.filter(email=email)

        # error if phone_number is not unique
        if profile_exist:
            messages.error(
                    request,
                    f"<strong>خطا !</strong> شماره تلفن قبلا در سیستم ثبت شده است ."
                )
            return redirect('profile_create')
        
        # error if emeil is not unique
        if check_unique_user_email:
            messages.error(
                    request,
                    f"<strong>خطا !</strong> ایمیل قبلا در سیستم ثبت شده است ."
                )
            return redirect('profile_create')
        
        # check correct code
        if not send_code(request, phone_number,posted_data.get('user_code')):
            messages.error(
                    request,
                    f"<strong>خطا !</strong> کد وارد شده غلط است ."
                )
            return redirect('profile_create')
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        posted_data = self.request.POST
        user = self.request.user
        form.instance.user = user
        form.instance.phone_number_confirm = True

        # try to set user values 
        try:
            user.first_name = posted_data.get('first_name')
            user.last_name = posted_data.get('last_name')
            user.email = posted_data.get('email')
            user.save()
        except:
            self.form_invalid()
        return super().form_valid(form)
    

    def form_invalid(self, form) :
        # create a message that say your form have a problem
        posted_data = self.request.POST
        user_entries = {
        'first_name': posted_data.get('first_name'),
        'last_name': posted_data.get('last_name'),
        'email': posted_data.get('email'),
        'term': posted_data.get('term'),
        'phone_number': posted_data.get('phone_number'),
        'gender': posted_data.get('gender'),
        'error_message': 1,
        'fields':{
                'term': 0,
                'phone_number': 0,
                'gender': 0,

        }
                    }
        # handeling error by every fields
        # this code is not using
        if not form.cleaned_data.get('phone_number'):
            user_entries['fields']['phone_number'] = 'تلفن همراه <br>'
        if not form.cleaned_data.get('term'):
            user_entries['fields']['term'] = 'ترم <br>'
        if not form.cleaned_data.get('gender'):
            user_entries['fields']['gender'] = 'جنسیت <br>'
    
        self.request.session['user_entries'] = user_entries
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_entries'] = self.request.session.get('user_entries')

        
        #if ther is any error show it and then delete the error form sessions to don't show it again 
        if user_entries := self.request.session.get('user_entries'):
            if user_entries.get('error_message'):
                messages.error(
                self.request,
                f"<strong>اخطار !</strong> لطفا اطلاعات وارد شده را اصلاح کنید"
                )
                del self.request.session['user_entries']
        return context
    

class CustomLoginView(admin_views.LoginView):
    def post(self, request, *args: str, **kwargs):
        posted_data = request.POST
        # if username is not exist return error message
        try:
            requested_user = get_user_model().objects.get(username=posted_data['username'])
        except:
            messages.error(
            self.request,
            f"<strong>خطا !</strong>نام کاربری وارد شده وجود ندارد."
            )
            return super().post(request, *args, **kwargs)
        # return error message when pssword is incorrect
        if not requested_user.check_password(posted_data['password']):
            messages.error(
            self.request,
            f"<strong>خطا !</strong>رمز وارد شده صحیح نمی باشد . "
            )
        return super().post(request, *args, **kwargs)



class CheckCodeView(SmsSendLimitByIpMixin, TemplateView):
    success_url = reverse_lazy('profile')
    template_name = "registration/send_reset_code.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('username'):
            username = request.GET.get('username')  
            verification_code = VerificationCode.objects.filter(user__username=username).order_by('-datetime_created')

            # check user can send only one sms per 2 minutes
            if verification_code:
                time_diffrence = timezone.now() - verification_code[0].datetime_created
                if time_diffrence.total_seconds() < 1    :
                    messages.error(
                        request,
                        f"<strong>خطا !</strong> هر دو دقیقه یکبار می توانید درخواست ارسال کد داشته باشید."
                    )
                    return JsonResponse({'error': 'some error'}, status=500)
            # check user have phone number
            try:
                phone_number = get_user_model().objects.get(username=username).profile.phone_number
            except:
                messages.error(
                    request,
                    f"<strong>خطا !</strong> کاربر وارد شده غلط می باشد. دوباره امتحان کنید:"
                )
                return JsonResponse({'error': 'some error'}, status=500)
            verification_code = send_code(request, phone_number)

            print(verification_code)
              
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        posted_code = request.POST.get('verification_code')
        username = request.POST.get('username')

        # check user exist
        try:
            user = get_user_model().objects.get(username=username)
        except:
            messages.error(
            self.request,
            f"<strong>خطا !</strong>کاربری با این مشخصات یافت نشد ."
        )
            return redirect('check_code')
        
        # if user code is valide, then login and can change its password
        valide_code = send_code(request, user.profile.phone_number, posted_code)
        if valide_code:
            login(request, user)
            messages.success(
            self.request,
            f"<strong>تایید شد .</strong> رمز جدید خود را وارد نمایید"
        )
            return redirect('password_reset_confirm')
        
        messages.error(
            self.request,
            f"<strong>خطا !</strong> کد وارد شده غلط می باشد. دوباره امتحان کنید:"
        )
        return redirect('check_code')
    


# *** validate the passwords ***
def validate_custom_password(password):
    errors = False
    for validator in settings.AUTH_PASSWORD_VALIDATORS:
        try:
            validate_password(password, validator)
        except ValidationError as e:
            # errors.append(e)
            errors = True
            break

    return errors


def CustomResetPasswordConfirmView(request):
    posted_data = request.POST
    reset_form = CustomPasswordResetForm()
    user = request.user
    context = {
        'form': reset_form
    }

    if request.method == "POST":
        new_password = posted_data.get('new_password1')
        error_password = validate_custom_password(new_password)
        if reset_form.is_valid :
            print(error_password)
            #    *** check for length of password and not be in common password ***
            if not error_password:
                #   *** check equale two given passwords ***
                if posted_data.get('new_password1') == posted_data.get('new_password2') and posted_data.get('new_password1') != None:
                    
                    user.set_password(new_password)
                    user.save()
                    messages.success(
                        request,
                        f"<strong>تایید شد .</strong> رمز شما با موفقیت تغییر یافت."
                    )
                    login(request, request.user)
                    return redirect('profile')
                        
                messages.error(
                    request,
                    f"<strong> خطا !</strong>لطفا دو مقدار برابر وارد کنید ."
                )
                return redirect('password_reset_confirm')
            
            elif validate_custom_password:
                messages.warning(
                    request,
                    f"<strong> هشدار !</strong>توجه کنید که رمز عبور باید حداقل 8 حرف داشته باشد . <br>&nbsp;&nbsp;  همچنین رمز عبور ساده پذیرفته نیست."
                )
                return redirect('password_reset_confirm')

        
        return render(request, 'registration/custom_password_reset_confirm.html', context)

    else :
        return render(request, 'registration/custom_password_reset_confirm.html', context)



class AdminQuizListView(IsStaffUserMixin, ListView):
    template_name = "accounts/admin_quiz_list.html"
    context_object_name = "quiz_list"

    def get_queryset(self):
        return Quiz.objects.filter(is_deleted=False)
    

class AdminUserListView(IsStaffUserMixin, ListView):
    model = get_user_model()
    template_name = "accounts/admin_user_list.html"
    context_object_name = "user_list"


class AdminLessonListView(IsStaffUserMixin, TemplateView):
    # model = Lesson
    template_name = "accounts/admin_lesson_list.html"
    # context_object_name = "lesson_list"

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        lessons = Lesson.objects.filter()
        context['lesson_list'] = lessons
        return context


@login_required
def change_user_level_view(request):
    choosen_user = get_object_or_404(get_user_model(), id=request.GET.get('user_id'))
    action = request.GET.get('action')
    user = request.user
 
    try:
        Profile.objects.get(user=choosen_user)
    except:
        # Set is_active = False for user that dont have profile . for othere user show error
        if action == 'deactivate':
            choosen_user.is_active = False
            messages.success(
            request,
            f"<strong> درخواست موفق . </strong> کاربر تغییر یافت ."
            )
            return JsonResponse({'success': 'some error'}, status=200)
        else:
            messages.error(
                request,
                f"<strong> خطا !</strong> کاربر پروفایل ندارد . برای ارتقا باید کاربر پروفایل داشته باشد ."
            )
            return JsonResponse({'error': 'some error'}, status=500)
    profile = choosen_user.profile

        
        


    if action == 'deactivate':
        if user.is_staff or user.is_superuser:
            choosen_user.is_active = False
            choosen_user.is_staff = False
            choosen_user.is_superuser = False
            profile.is_quiz_maker = False
            choosen_user.save()
            profile.save()
        else:
            messages.error(
                    request,
                    f"<strong> خطا !</strong>لطفا دو مقدار برابر وارد کنید ."
                )
            return JsonResponse({'error': 'some error'}, status=500)


    elif action == 'activate':
        if user.is_staff or user.is_superuser:
            choosen_user.is_active = True
            choosen_user.is_staff = False
            choosen_user.is_superuser = False
            profile.is_quiz_maker = False
            choosen_user.save()
            profile.save()
        else:
            messages.error(
                    request,
                    f"<strong> خطا !</strong>تغییر مورد نظر شما ممکن نیست ."
                )
            return JsonResponse({'error': 'some error'}, status=500)


    elif action == 'BeQuizMaker':
        if user.is_staff or user.is_superuser:
            choosen_user.is_active = True
            choosen_user.is_staff = False
            choosen_user.is_superuser = False
            profile.is_quiz_maker = True
            choosen_user.save()
            profile.save()
        else:
            messages.error(
                    request,
                    f"<strong> خطا !</strong>تغییر مورد نظر شما ممکن نیست ."
                )
            return JsonResponse({'error': 'some error'}, status=500)


    elif action == 'BeStaff':
        if user.is_superuser:
            choosen_user.is_active = True
            choosen_user.is_staff = True
            choosen_user.is_superuser = False
            profile.is_quiz_maker = True
            choosen_user.save()
            profile.save()
        else:
            messages.error(
                    request,
                    f"<strong> خطا !</strong>تغییر مورد نظر شما ممکن نیست ."
                )
            return JsonResponse({'error': 'some error'}, status=500)


    elif action == 'BeStudent':
        if user.is_staff or user.is_superuser:
            choosen_user.is_active = True
            choosen_user.is_staff = False
            choosen_user.is_superuser = False
            profile.is_quiz_maker = False
            choosen_user.save()
            profile.save()
        else:
            messages.error(
                    request,
                    f"<strong> خطا !</strong>تغییر مورد نظر شما ممکن نیست ."
                )
            
            return JsonResponse({'error': 'some error'}, status=500)
        
    messages.success(
            request,
            f"<strong> درخواست موفق . </strong>کاربر تغییر یافت ."
        )
    return JsonResponse({'success': 'ok'}, status=200)
    









