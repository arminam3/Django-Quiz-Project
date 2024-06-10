from django.http import JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.urls import reverse_lazy, reverse
from django.contrib.auth import views as admin_views
from django.contrib.auth.views import PasswordResetConfirmView
from django.db.models import Avg, Sum, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import views as admin_views
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.utils import timezone


from .models import Profile, VerificationCode
from .forms import RegisterForm, CustomPasswordResetForm
from exam.models import Question
from takingtest.models import QuizResult,QuizHistory
from .mixins import DoNotHaveProfileMixin, CheckHavingProfileMixin, SmsSendLimitByIpMixin
# from .models import Profile
from .send_code import send_code

class RegisterView(CreateView):
    model = get_user_model()
    template_name = "registration/register.html"
    form_class = RegisterForm
    # success_url = reverse_lazy('profile_create')

    def get_success_url(self):
        messages.success(
            self.request,
            "<strong>خوش آمدید !</strong>  اطلاعات شما با موفقیت ثبت شد. برای دسترسی به صفخات سامانه لظفا پروفایل خود را تکمیل کنید."
        )
        login(self.request, self.object)
        return reverse('profile_create')
        
    # def post(self, request, *args, **kwargs):
    #     register_form = RegisterForm(request.POST)
    #     register_form.initial['password2'] = request.POST.get('password1')
    #     register_form.save()
        # mutable_post = request.POST.copy()  
        # request.POST['password2'] = request.POST.get('password1')
        # request.POST = mutable_post
        # return super().post(request, *args, **kwargs)

    


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
    fields = ('term', 'phone_number', 'gender')
    success_url = reverse_lazy('profile')


    def post(self, request, *args, **kwargs):
        posted_data = self.request.POST
        profile = Profile.objects.get(id=kwargs.get('pk'))

        try:
                
            profile.term = int(posted_data.get('term'))
            # profile.phone_number = posted_data.get('phone_number')
            profile.gender = posted_data.get('gender')
            profile.discipline = posted_data.get('discipline')
            profile.save()

            user = self.request.user
            user.first_name = posted_data.get('first_name')
            user.last_name = posted_data.get('last_name')
            user.email = posted_data.get('email')
            user.save()
        except:
            pass

        return super().post(request, *args, **kwargs)
    
    def form_invalid(self, form) :
        # create a message that say your form have a problem
        return super().form_invalid(form)
    

    

class ProfileCreateView(LoginRequiredMixin, DoNotHaveProfileMixin, CreateView):
    model = Profile
    template_name = "accounts/profile_create.html"
    fields = ('term', 'phone_number', 'gender')

    def get(self, request, *args, **kwargs):
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
        profile_exist = Profile.objects.filter(phone_number=phone_number)

        # error if phone_number is not unique
        if profile_exist:
            messages.error(
                    request,
                    f"<strong>خطا !</strong> شماره تلفن قبلا در سیستم ثبت شده است ."
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

        try:
            user.first_name = posted_data.get('first_name')
            user.last_name = posted_data.get('last_name')
            user.email = posted_data.get('first_name')
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
    def form_valid(self, form: admin_views.AuthenticationForm):
        posted_data = self.request.POST
        form.instance.username = posted_data.get('username')
        form.instance.password = posted_data.get('password')
        return super().form_valid(form)
    




class CheckCodeView(SmsSendLimitByIpMixin, TemplateView):
    # form_class = CustomPasswordResetForm
    success_url = reverse_lazy('profile')
    template_name = "registration/send_reset_code.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('username'):
            username = request.GET.get('username')  
            verification_code = VerificationCode.objects.filter(user__username=username).order_by('-datetime_created')
            # check user can send only one sms per 2 minutes
            if verification_code :
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










