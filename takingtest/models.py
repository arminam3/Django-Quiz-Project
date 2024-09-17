from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from exam.models import Quiz, Question

class QuizHistory(models.Model):
    CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    )
    exam_number = models.UUIDField(null=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    user_answer = models.CharField(choices=CHOICES, max_length=1)
    datetime_created = models.DateTimeField(default=timezone.now)
    datetime_edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.quiz}  |  {self.user}'
    
class QuizResult(models.Model):
    exam_number = models.UUIDField(null=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="quiz_result")
    datetime_created = models.DateTimeField(auto_now_add=True)
    score = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quiz.name} | {self.user}'

    def quiz_result_score_percent(self):
        user_result_percent = 0
        quiz_question_count = QuizHistory.objects.filter(exam_number=self.exam_number).count()
        try:
            user_result_percent = int(self.score / quiz_question_count * 100 ) 
        except:
            pass
        
        return user_result_percent
    

class LikeDislike(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='user_like_dislike', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='quiz_like_dislike', on_delete=models.CASCADE)
    like = models.BooleanField()
    datetime_created = models.DateTimeField(auto_now_add=True)

    def __str__(self) :
        return f'{self.user.username} | {self.quiz.name}'
     
          
