from django.forms import BaseModelForm
import requests
import array as arr

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import TemplateView, UpdateView, ListView, DetailView, CreateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404,redirect
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, DateTimeField
from django.db.models.functions import TruncDay
from django.utils import timezone

from .models import Notification
from .forms import NotificationCreateForm
from takingtest.models import QuizHistory

from datetime import datetime, timedelta





class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['theme'] = self.request.session.get('theme')

        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()) - timedelta(days=6)
        end_of_day = datetime.combine(today, datetime.max.time()) + timedelta(days=0)
        # questions_answered = QuizHistory.objects.filter(user=user, datetime_created__range=(start_of_day, end_of_day)).annotate(daily_question_count=Count('question'))
        activity_list = [0, 0, 0, 0, 0, 0, 0]
        def manipulate_list(lst, num):
            num = num % len(lst)
            lst = lst[-num:] + lst[:-num]
            return [x for x in lst]
        
        if timezone.now().strftime('%A') == 'Saturday':
            day_name_moderator = 6
        elif timezone.now().strftime('%A') == 'Sunday':
            day_name_moderator = 5
        elif timezone.now().strftime('%A') == 'Monday':
            day_name_moderator = 4
        elif timezone.now().strftime('%A') == 'Tuesday':
            day_name_moderator = 3
        elif timezone.now().strftime('%A') == 'Wednesday':
            day_name_moderator = 2
        elif timezone.now().strftime('%A') == 'Thursday':
            day_name_moderator = 1
        elif timezone.now().strftime('%A') == 'Friday':
            day_name_moderator = 0

        if user.is_authenticated:
            week_activity = QuizHistory.objects.filter(user=user, datetime_created__range=(start_of_day, end_of_day)).annotate(day=TruncDay('datetime_created')) \
                .values('day') \
                .annotate(count=Count('id')) \
                .order_by('day')


                    
            for activity in week_activity:
            
                if activity['day'].strftime('%A') == 'Saturday':
                    try:
                        activity_list[0] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Sunday':
                    try:
                        activity_list[1] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Monday':
                    try:
                        activity_list[2] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Tuesday':
                    try:
                        activity_list[3] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Wednesday':
                    try:
                        activity_list[4] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Thursday':
                    try:
                        activity_list[5] = activity['count']
                    except:
                        pass
                elif activity['day'].strftime('%A') == 'Friday':
                    try:
                        activity_list[6] = activity['count']
                    except:
                        pass

        context['week_activity'] = manipulate_list(activity_list, day_name_moderator)
            
        # get name of 7 past days
        day_names = []
        for i in range(0, 7):
            past_date = timezone.now() - timedelta(days=i)
            if past_date.strftime('%A')=='Saturday':
                day_name = 'شنبه' 
            elif past_date.strftime('%A')=='Sunday':
                day_name = '۱شنبه' 
            elif past_date.strftime('%A')=='Monday':
                day_name = '۲شنبه'
            elif past_date.strftime('%A')=='Tuesday':
                day_name = '۳شنبه'
            elif past_date.strftime('%A')=='Wednesday':
                day_name = '۴شنبه'
            elif  past_date.strftime('%A')=='Thursday':
                day_name = '۵شنبه'
            elif past_date.strftime('%A')=='Friday':
                day_name =  'جمعه'
            day_names.append(day_name)  # %A gives the full weekday name

        context['day_names'] = day_names[::-1]
        return context
    

def theme_change_view(request):
    if request.method == "POST":
        session_theme = request.session.get('theme')
        if session_theme == 'light':
            request.session['theme'] = 'dark'
        else:
            request.session['theme'] = 'light'
    return HttpResponseRedirect(request.POST.get('next_url'))


class NotificationCreateView(LoginRequiredMixin, CreateView):
    model = Notification
    template_name = 'pages/notif_creation.html'
    form_class = NotificationCreateForm
    
    def get_success_url(self):
        return reverse('home')
    
    def post(self, request, *args, **kwargs):
        posted_data = request.POST
        num = 1
        while(posted_data.get(f'user-{num}')):
            receptor = get_object_or_404(get_user_model(), username=posted_data.get(f'user-{num}'))
            new_notification = Notification.objects.create(
                receptor=receptor,
                sender=request.user,
                title=posted_data.get('title'),
                text=posted_data.get('text')
                )
                        
            num += 1
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        messages.success(
            self.request,
            f"<strong>تایید </strong>با موفقیت ارسال شد ."
        )
        return super().form_valid(form)

def multi_notification_sender(num=0):
    user = f'user-{num}'
    context = {
        'user': user, 
    }

    return context

@login_required
def search_users(request):
    query = request.GET.get('query', '')
    users = get_user_model().objects.filter(username__icontains=query).order_by('username')[:4:]
    users_list = list(users.values('username'))
    return JsonResponse(users_list, safe=False)


class SeenNotificationView(TemplateView):
    model = Notification
    fields = ('is_read') 
    template_name = 'pages/home.html'

    def get(self, request, *args, **kwargs):
        notification = get_object_or_404(Notification, id=request.GET.get('id'))
        notification.is_read = True
        notification.save()
        return super().get(request, *args, **kwargs)
    
class NotificationListView(ListView):
    model = Notification
    context_object_name = "notification_list"
    template_name = "pages/notif_list.html"

    def get_queryset(self):
        notifications = Notification.objects.filter(receptor=self.request.user).order_by('is_read')
        return notifications
    

