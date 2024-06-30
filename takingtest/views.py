import uuid
import asyncio

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, ListView, TemplateView, DetailView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.template.response import TemplateResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator





from .models import QuizHistory, QuizResult, LikeDislike
from exam.models import Quiz
from .forms import QuizHistoryForm

from accounts.mixins import CheckHavingProfileMixin, IsStaffOrQuizMakerUserMixin, DoNotHaveProfileMixin


class QuizHistoryCreateView(IsStaffOrQuizMakerUserMixin, CreateView):
    model = QuizHistory
    template_name = "takingtest/take_an_exam.html"
    form_class = QuizHistoryForm
    success_url = reverse_lazy('home')

    def post(self, request, *args, **kwargs):
        exam_number = uuid.uuid4()
        quiz = get_object_or_404(Quiz, pk=self.kwargs.get('pk'))
        posted_data = self.request.POST
        user = self.request.user
        score = 0

        for question in quiz.questions.filter(is_deleted=False):
            user_answer = posted_data.get(str(question.id))
            try:
                QuizHistory.objects.create(
                                            exam_number=exam_number,
                                            quiz=quiz,
                                            question=question,
                                            user=user,
                                            user_answer=user_answer,
                                           )
                if user_answer == question.answer:
                    score +=1
            except:
                return HttpResponseBadRequest("درخواست غلط")
        quiz_result = QuizResult.objects.create(
                                exam_number = exam_number,
                                quiz = quiz,
                                user = user,
                                score=score
        )

        return redirect(reverse('quiz_result', args=[quiz_result.exam_number]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = get_object_or_404(Quiz, pk=self.kwargs.get('pk'))
        return context

# @method_decorator(cache_page(60*s15), name='dispatch')
class TermQuizListView(CheckHavingProfileMixin, ListView):
    model = Quiz
    template_name = "takingtest/term_quiz_list.html"
    context_object_name = "quiz_list"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # filter quizes for user by it's term and discipline that have more than 0 questions
        quiz_list = Quiz.objects.filter(
                        is_deleted=False, lesson__term=user.profile.term, 
                        lesson__discipline=user.profile.discipline
                                        ).annotate(num_questions=Count('questions')).filter(num_questions__gt=0)
        
        paginator = Paginator(quiz_list, 10)
        page = self.request.GET.get('page')

        try:
            quiz_list = paginator.page(page)
        except PageNotAnInteger:
            quiz_list = paginator.page(1)
        except EmptyPage:
            quiz_list = paginator.page(paginator.num_pages)
        

        quiz_list.page_range = paginator.page_range
        try:
            quiz_list.current_page = int(page)
        except:
            quiz_list.current_page = 1
        try:
            quiz_list.minus_last_2 = paginator.num_pages - int(page)
        except:
            quiz_list.minus_last_2 = 0
            
        return quiz_list

class QuizResultView(CheckHavingProfileMixin, TemplateView):
    template_name = "takingtest/quiz_result.html"
  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        quiz_result =get_object_or_404(QuizResult, exam_number=self.kwargs.get('pk'))

        quiz_score_avg_dic = QuizResult.objects.filter(quiz=quiz_result.quiz).aggregate(quiz_score_avg=Avg("score"))
        quiz_score_avg = quiz_score_avg_dic['quiz_score_avg']

        quiz_history_count =QuizHistory.objects.filter(exam_number=self.kwargs.get('pk')).count()
        
        user_result_percent = 0
        try:
            user_result_percent = int(quiz_result.score / quiz_result.quiz.questions.count() * 100 ) 
        except:
            context['user_result_percent'] = 5
            
        try:
            score_avg = int(round(quiz_score_avg / quiz_history_count  * 100, 0))
        except:
            score_avg = 0
            
        context['score_avg'] = score_avg
        context['quiz_result'] = quiz_result
        context['user_result_percent'] = user_result_percent

        return context

class TakenExamDetail(CheckHavingProfileMixin, TemplateView):
    template_name = "takingtest/taken_exam_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam_number = self.kwargs.get('pk')
        quiz_histories = QuizHistory.objects.filter(exam_number=exam_number)
        context['quiz_histories'] = quiz_histories
        context['quiz_his'] = quiz_histories[0]
        return  context

class QuickQuizView(CheckHavingProfileMixin, DetailView):
    model = Quiz
    template_name = "takingtest/quick_quiz.html"
    context_object_name = 'quiz'


class QuizResultListView(CheckHavingProfileMixin, ListView):
    template_name = "takingtest/quiz_result_list.html"
    context_object_name = "quiz_result_list"

    def get_queryset(self):
        quiz_result_list = QuizResult.objects.filter(user=self.request.user)
                
        paginator = Paginator(quiz_result_list, 20)
        page = self.request.GET.get('page')

        try:
            quiz_result_list = paginator.page(page)
        except PageNotAnInteger:
            quiz_result_list = paginator.page(1)
        except EmptyPage:
            quiz_result_list = paginator.page(paginator.num_pages)
        

        quiz_result_list.page_range = paginator.page_range
        try:
            quiz_result_list.current_page = int(page)
        except:
            quiz_result_list.current_page = 1
        try:
            quiz_result_list.minus_last_2 = paginator.num_pages - int(page)
        except:
            quiz_result_list.minus_last_2 = 0
        return quiz_result_list


class LikeDislikeView(CheckHavingProfileMixin, TemplateView):
    model = LikeDislike
    
    def get(self, request, *args, **kwargs):
        quiz_result_id = request.GET.get('quiz_result_id')
        action = request.GET.get('action')
        print(action)
        quiz = get_object_or_404(QuizResult, id=request.GET.get('quiz_result_id')).quiz
        user = request.user
        like = False

        if action == 'like':
            like = True
        
        LikeDislike.objects.update_or_create(
            user=user,
            quiz=quiz,
            defaults={'like':like}

        )
        return JsonResponse({'success': 'ok'}, status=200)
        
# def search_view(request):
#     query = request.GET.get('query', '')
#     results = Quiz.objects.filter(name__icontains=query)
#     data = [{'title': result.name, 'description': result.quiz_maker} for result in results]
#     return JsonResponse(data, safe=False)




    