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

from .models import Notification
from .forms import NotificationCreateForm



class HomeView(TemplateView):
    template_name = "home.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['theme'] = self.request.session.get('theme')


        return context

def theme_change_view(request):
    if request.method == "POST":
        print(request.session.get('theme'))
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
    print('--0--')
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
    context_object_name = "notifications"
    template_name = "pages/notif_list.html"

    def get_queryset(self):
        notifications = Notification.objects.filter(receptor=self.request.user).order_by('is_read')
        return notifications