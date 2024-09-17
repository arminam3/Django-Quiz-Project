import os
from datetime import timedelta ,datetime

from typing import Any
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse,  JsonResponse
from django.shortcuts import render, redirect,reverse
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView, TemplateView
from django.shortcuts import get_object_or_404, get_list_or_404
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

from accounts.mixins import IsStaffUserMixin, IsStaffOrQuizMakerUserMixin, CheckHavingProfileMixin

from .models import Question, Quiz, Lesson, QestionReport
from .forms import (
                    QuizQuestionForm, 
                    QuestionCreateForm, 
                    QuestionUpdateForm,
                    QuizQuestionCreateForm
                    )

class QuestionListView(ListView):
    model = Question
    template_name = "exam/quiz/quiz_list.html"


class QuizQuestionUpdateView(IsStaffOrQuizMakerUserMixin, DetailView):
    model = Quiz
    template_name = "exam/quiz/quiz_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user == self.get_object().quiz_maker:
            return super().dispatch(request, *args, **kwargs)
        elif request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden('شما اجازه دسترسی به این صفحه را ندارید')

    # change new answers for every question  
    def post(self, request, *args, **kwargs):
        posted_data = self.request.POST
        quiz = get_object_or_404(Quiz, id=self.kwargs["pk"])

        # delete question and remove it from quiz
        delete_question_id = posted_data.get('delete_question')
        if delete_question_id :
            question = Question.objects.get(pk=delete_question_id)
            question.is_deleted = True
            question.save()
            quiz.questions.remove(question)
            messages.success(
            self.request,
            f"<strong>. سوال مورد نظر حذف شد</strong>"
            )
            return redirect(reverse('quiz_question_update', args=[quiz.id]))
        
        # for every question check new data and last-answer. if data was new then change it.
        num = 0
        for question in quiz.questions.all():
            question_new_answer = posted_data.get(str(question.id))
            if question.answer != question_new_answer:
                question.answer = question_new_answer
                question.save()
                num += 1
        messages.success(
        self.request,
        f"<strong>پاسخ {num}سوال تغییر یافت . </strong>"
        )
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question_list = Question.objects.filter(quiz=self.get_object(), is_deleted=False)
        context['question_list'] = question_list
        return context


# update question values
class QuestionUpdateView(IsStaffOrQuizMakerUserMixin, UpdateView):
    template_name = "exam/question/question_update.html"
    form_class = QuestionUpdateForm
    context_object_name = "question"

    def get_queryset(self):
        question = Question.objects.filter(id=self.kwargs.get('pk'), is_deleted=False)
        return question

    # check staff user and quiz_maker allow to access this view
    def dispatch(self, request, *args, **kwargs):
        posted_data = self.request.POST
        question = get_object_or_404(Question, id=self.kwargs["pk"])
        if request.user == question.question_maker:
            return super().dispatch(request, *args, **kwargs)
        elif request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden('شما اجازه دسترسی به این صفحه را ندارید')

    def get_form_kwargs(self):
        obj = self.get_object()
        posted_data = self.request.POST

        kwargs =  super(QuestionUpdateView, self).get_form_kwargs()
        kwargs['user'] = obj.question_maker

        return kwargs
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        obj = self.get_object()
        posted_data = self.request.POST
        question = get_object_or_404(Question, id=self.kwargs["pk"])

        # delete image path and image file
        if obj.image is not None and  posted_data.get('delete_image') == 'on':
            # if os.path.isfile(obj.image.path):
            #     os.remove(obj.image.path)
            obj.image = None
            obj.save()

        if self.request.FILES.get('image'):
            if self.request.FILES.get('image').size > 200 * 1024:
                messages.error(
                    request,
                    f"<strong>حجم عکس باید کمتر از 200 kb باشد.</strong>"
                )
                return redirect(reverse('question_update', args=[self.get_object().id]))
        
        # delete question
        if posted_data.get('button-name') == 'delete_question':
            return redirect(reverse('question_delete', args=[question.id]))
        return super().post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question_report_list = QestionReport.objects.filter(question=self.get_object(), read=False)
        context['question_report_list'] = question_report_list
        return context

    # success_url = reverse_lazy('home')
    def get_success_url(self):
        messages.success(
        self.request,
        "<strong>سوال مورد نظر شما با موفقیت تغییر یافت .</strong>"
        )
        # mark question_report as read
        if self.request.POST.get('question_report_read'):
            question_report_read(self.request, self.get_object().id)
        return reverse('question_update', args=[self.get_object().id])
        

def question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk)

    question.is_deleted = True
    question.save()
    question_quiz = Quiz.objects.filter(questions__id=question.id)
    for quiz in question_quiz:
        quiz.questions.remove(question)
    return redirect(reverse('quiz_question_update', args=[question_quiz[0].pk]))


class QuizCreateView(IsStaffOrQuizMakerUserMixin, CreateView):
    model = Quiz
    template_name = "exam/quiz/quiz_create.html"
    fields = ('name', 'lesson', 'quiz_maker')
    
    def post(self, request, *args, **kwargs):
        posted_data = self.request.POST
        quiz_time = timedelta(minutes=int(posted_data.get('quiz_time')))
        quiz_image = self.request.FILES.get('quiz_image')
        user = self.request.user
        if quiz_image:
            if quiz_image.size > 200 * 1024:
                messages.error(
                    request,
                    f"<strong>حجم عکس باید کمتر از 200 kb باشد.</strong>"
                )
                return redirect('quiz_create')
        obj = Quiz.objects.create(
            name=posted_data['quiz_name'],
            lesson=Lesson.objects.get(pk=posted_data['lesson_id']),
            quiz_maker=user,
            time=quiz_time,
            image=quiz_image
            )
        return redirect(reverse('quiz_question_create', args=[obj.id]))


    def form_valid(self, form: BaseModelForm):
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['lessons'] = Lesson.objects.all()
        return context
    
    def get_success_url(self):
        return reverse('quiz_question_create', args=[self.get_object().id])


class QuizQuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    template_name = "exam/quiz/quiz_question_create.html"
    fields = ['text']
    
    def get_success_url(self) -> str:

        return reverse('quiz_question_update',args=[self.kwargs['pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz_pk'] = self.kwargs['pk']
        return context

    def post(self, request: HttpRequest, *args: str, **kwargs: Any):
        posted_data = request.POST
        posted_file = request.FILES
        user = request.user
        quiz = Quiz.objects.get(pk=self.kwargs['pk'])

        num = 0
        big_image = ''
        while(posted_data.get(f'text-{num}')):
            ques_val = multi_question_maker(num)
            if (posted_file.get(ques_val['image'])) and posted_file.get(ques_val['image']).size > 200 * 1024:
                # if :
                big_image += (f'{num+1} ,')
            else:
                new_question = Question.objects.create(
                    text=posted_data.get(ques_val['text']),
                    choice_1=posted_data.get(ques_val['choice_1']),
                    choice_2=posted_data.get(ques_val['choice_2']),
                    choice_3=posted_data.get(ques_val['choice_3']),
                    choice_4=posted_data.get(ques_val['choice_4']),
                    answer=posted_data.get(ques_val['answer']),
                    image=posted_file.get(ques_val['image']),
                    explanation=posted_data.get(ques_val['explanation']),
                    question_maker = user,
                    )
                    
                quiz.questions.add(new_question)
                
            num += 1
        quiz_question_count = quiz.questions.count()
        messages.success(
        self.request,
        f"<strong>  آزمون '{quiz.name}' با {quiz_question_count} سوال در سیستم ثبت شد</strong>"
            )
        if big_image:
            messages.error(
                request,
                f"<strong>سوال {big_image[:-1:]} به دلیل حجم بالای عکس (بالای 200 kb) ذخیره نشدند.</strong>"
            )
        return redirect(reverse('quiz_question_update',args=[self.kwargs['pk']]))
    
    
def multi_question_maker(num=0):
    text = f'text-{num}'
    choice_1 = f'choice_1-{num}'
    choice_2 = f'choice_2-{num}'
    choice_3 = f'choice_3-{num}'
    choice_4 = f'choice_4-{num}'
    answer = f'answer-{num}'
    image = f'image-{num}'
    explanation = f'explanation-{num}'
    context = {
        'text': text, 
        'choice_1': choice_1, 
        'choice_2': choice_2, 
        'choice_3': choice_3, 
        'choice_4': choice_4, 
        'answer': answer, 
        'image': image ,
        'explanation': explanation 
    }

    return context


def quiz_delete_view(request):
    user = request.user
    posted_data = request.POST
    quiz = get_object_or_404(Quiz, pk=posted_data.get('quiz_id_for_delete'))

    if user.is_staff or (quiz.quiz_maker == user):
        if request.method == "POST":
            for question in quiz.questions.all():
                question.is_deleted = True
                question.save()
            quiz.is_deleted = True
            quiz.save()
        return (redirect('quiz_list'))
    messages.error(
        request,
        f"<strong>شما اجازه حذف آزمون را ندارید.</strong>"
    )
    return JsonResponse({'message': 'not allowed!.'}, status=500)

def quiz_return_view(request, pk):
    user = request.user
    posted_data = request.POST
    quiz = get_object_or_404(Quiz, pk=pk)

    if user.is_staff or (quiz.quiz_maker == user):
        for question in quiz.questions.all():
            question.is_deleted = False
            question.save()
        quiz.is_deleted = False
        quiz.save()
        return (redirect('quiz_list'))
    messages.error(
        request,
        f"<strong>شما اجازه حذف آزمون را ندارید.</strong>"
    )
    return JsonResponse({'message': 'not allowed!.'}, status=500)


class QuizUpdateView(IsStaffOrQuizMakerUserMixin, UpdateView):
    model = Quiz
    fields = ('name', 'lesson', 'time')
    template_name = 'exam/quiz/quiz_update.html'
    context_object_name = 'quiz'

    def dispatch(self, request, *args, **kwargs):
        if (request.user == self.get_object().quiz_maker) or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
        return HttpResponse('شما اجازه دسترسی به این صفحه را ندارید .')
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        lessons = Lesson.objects.filter(term=user.profile.term,discipline=user.profile.discipline)
        context['lessons'] = lessons

        quiz_time = int(self.get_object().time.total_seconds() // 60)
        context['quiz_time'] = quiz_time
        return context
    
    def form_valid(self, form: BaseModelForm):
        quiz = self.get_object()
        new_image = self.request.FILES.get('image')
        posted_data = self.request.POST
        form.instance.time = timedelta(minutes=int(posted_data.get('time')))
        if new_image:
            if new_image.size > 200 * 1024:
                messages.error(
                    self.request,
                    f"<strong>حجم عکس باید کمتر از 200 kb باشد.</strong>"
                )
                return redirect(reverse('quiz_update', args=[quiz.id]))
            form.instance.image = self.request.FILES.get('image')
        elif quiz.image:
            form.instance.image = quiz.image
        return super().form_valid(form)
    
    def get_success_url(self):

        return reverse('quiz_update', args=[self.get_object().id])
    
class LessonCreateView(IsStaffUserMixin, CreateView):
    model = Lesson
    fields = ('name', 'master', 'discipline', 'term')
    template_name = 'exam/lesson_create.html'

    def get_success_url(self) -> str:
        return reverse('lesson_list')
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            f"<strong>لطفا مقادیر را به درستی وارد نمایید.</strong>"
        )
        return super().form_invalid(form)
    

class LessonUpdateView(IsStaffUserMixin, UpdateView):
    model = Lesson
    fields = ('name', 'master', 'discipline', 'term')
    template_name = 'exam/lesson_update.html'
    context_object_name = 'lesson'

    def get_success_url(self) -> str:
        return reverse('lesson_update', args=[self.get_object().id])
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            f"<strong>لطفا مقادیر را به درستی وارد نمایید.</strong>"
        )
        return super().form_invalid(form)
    
    def form_valid(self, form: BaseModelForm):
        return super().form_valid(form)



class QuizAddQuestionView(IsStaffOrQuizMakerUserMixin, CreateView):
    model = Question
    template_name = "exam/quiz/quiz_question_create.html"
    fields = ['text']


    def post(self, request: HttpRequest, *args, **kwargs):
        # another quiz_maker can't add quesions
        posted_data = request.POST
        posted_file = request.FILES
        user = request.user
        quiz = Quiz.objects.get(pk=self.kwargs['pk'])

        if (not user.is_staff) and (user.profile.is_quiz_maker != quiz.quiz_maker):
            return HttpResponse('شما اجازه ثبت سوال برای این آزمون را ندارید')

        num = 0
        big_image = ''
        while(posted_data.get(f'text-{num}')):
            ques_val = multi_question_maker(num)
            if (posted_file.get(ques_val['image'])) and posted_file.get(ques_val['image']).size > 200 * 1024:
                # if :
                big_image += (f'{num+1} ,')
            else:
                new_question = Question.objects.create(
                    text=posted_data.get(ques_val['text']),
                    choice_1=posted_data.get(ques_val['choice_1']),
                    choice_2=posted_data.get(ques_val['choice_2']),
                    choice_3=posted_data.get(ques_val['choice_3']),
                    choice_4=posted_data.get(ques_val['choice_4']),
                    answer=posted_data.get(ques_val['answer']),
                    image=posted_file.get(ques_val['image']),
                    explanation=posted_data.get(ques_val['explanation']),
                    question_maker = user,
                    )
                    
                quiz.questions.add(new_question)
                
            num += 1
        quiz_question_count = quiz.questions.count()
        messages.success(
        self.request,
        f"<strong>  آزمون '{quiz.name}' با {quiz_question_count} سوال در سیستم ثبت شد</strong>"
            )
        if big_image:
            messages.error(
                request,
                f"<strong>سوال {big_image[:-1:]} به دلیل حجم بالای عکس (بالای 200 kb) ذخیره نشدند.</strong>"
            )
        return redirect(reverse('quiz_question_update',args=[self.kwargs['pk']]))

    def get_success_url(self):
        return reverse('quiz_question_update',args=[self.kwargs['pk']])

@login_required
def question_report_create_view(request):
    if request.method == 'POST':
        user = request.user
        report_content = request.POST.get('report_content')
        quiz = get_object_or_404(Quiz, id=request.POST.get('quiz_id'))
        question = get_object_or_404(Question, id=request.POST.get('reported_question_id'))
        QestionReport.objects.create(user=user,quiz=quiz, question=question, content=report_content)

        messages.success(
            request,
            f"<strong>مشکل سوال ثبت شد .</strong>"
        )
        # redirect to last page
        return redirect(request.META.get('HTTP_REFERER'))
    
def question_report_read(request, pk):
    question = get_object_or_404(Question, id=pk)
    question_reports = QestionReport.objects.filter(question=question, read=False)
    question_reports.update(read=True)
    messages.success(
            request,
            f"<strong>رفع ایراد سوال ثبت شد.</strong>"
        )
    return redirect(reverse('question_update', args=[question.id]))

    
