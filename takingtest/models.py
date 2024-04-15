from django.db import models
from django.contrib.auth import get_user_model

from exam.models import Quiz, Question

class QuizHistory(models.Model):
    CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    )
    exam_number = models.UUIDField(null=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True, related_name="history")
    user_answer = models.CharField(choices=CHOICES, max_length=1)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.quiz}  |  {self.user}'
    
class QuizResult(models.Model):
    exam_number = models.UUIDField(null=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    datetime_created = models.DateTimeField(auto_now_add=True)
    score = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quiz.name} | {self.user}'
    

    def quiz_result_score_percent(self):
        user_result_percent = 0
        try:
            user_result_percent = int(self.score / self.quiz.questions.count() * 100 ) 
        except:
            pass
        
        return user_result_percent
    
    
            
