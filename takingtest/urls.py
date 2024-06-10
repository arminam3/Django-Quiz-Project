from django.urls import path


from .views import (
                    QuizHistoryCreateView,
                    TermQuizListView,
                    QuizResultView,
                    TakenExamDetail,
                    QuickQuizView,
                    QuizResultListView,
                    LikeDislikeView
                    # search_view
                    )

urlpatterns = [
    # path('search/', search_view, name='search'),
    path('take-an-exam/<str:pk>/', QuizHistoryCreateView.as_view(), name='take_an_exam'),
    path('term-quiz-list', TermQuizListView.as_view(), name='term_quiz_list'),
    path('quiz-result-list', QuizResultListView.as_view(), name='quiz_result_list'),
    path('quiz-result/<str:pk>/', QuizResultView.as_view(), name='quiz_result'),
    path('taken-exam-detail/<str:pk>/', TakenExamDetail.as_view(), name='taken_exam_detail'),
    path('quick-quiz/<str:pk>/', QuickQuizView.as_view(), name='quick_quiz'),
    path('like_dislike/', LikeDislikeView.as_view(), name='like_dislike'),
]