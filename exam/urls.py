from django.urls import path
from django.views.generic import TemplateView

from .views import (
                    QuizQuestionUpdateView, 
                    QuestionUpdateView,
                    question_delete_view,
                    QuizCreateView,
                    QuizQuestionCreateView,
                    quiz_delete,
                    QuizUpdateView,

                    LessonCreateView,
                    LessonUpdateView
                    )

urlpatterns = [
    path('test/', TemplateView.as_view(template_name="exam/test.html"), name="test"),
    path('test2/', TemplateView.as_view(template_name="exam/quiz/quiz_question_create.html"), name="test"),

    path('lesson-create/', LessonCreateView.as_view(), name="lesson_create"),
    path('lesson-update/<str:pk>', LessonUpdateView.as_view(), name="lesson_update"),

    path('quiz-create/', QuizCreateView.as_view(), name="quiz_create"),
    path('quiz-delete/', quiz_delete, name="quiz_delete"),
    path('quiz-update/<str:pk>/', QuizUpdateView.as_view(), name="quiz_update"),
    # path('quiz-detail/<str:pk>/', QuizDetailView.as_view(), name="quiz_detail"),
    path('quiz-question-create/<str:pk>/', QuizQuestionCreateView.as_view(), name="quiz_question_create"),
    path('quiz-question-update/<str:pk>/', QuizQuestionUpdateView.as_view(), name="quiz_question_update"),

    # path('question-create/', QuestionCreateView.as_view(), name="question_create"),
    path('question-update/<str:pk>/', QuestionUpdateView.as_view(), name="question_update"),
    # path('question-detail/<str:pk>/', QuestionDetailView.as_view(), name="question_detail"),
    # path('question-list/', QuestionListView.as_view(), name="question_list"),

    path('question-delete/<str:pk>/', question_delete_view, name="question_delete"),
]