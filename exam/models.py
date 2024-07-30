import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import redirect
from django.core.exceptions import ValidationError

from extensions.utils import jalali_convertor, english_numbers_convertor

#  Managers
class QuestionManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset()
    
    def get_not_deleted(self, pk):
        return super().get_queryset().filter(is_deleted=False)



class Question(models.Model):
    # Custom Manager
    objects = QuestionManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    )

    text = models.CharField(max_length=1023)
    image = models.ImageField(upload_to='question/question_image', blank=True, null=True)
    choice_1 = models.CharField(max_length=511)
    choice_2 = models.CharField(max_length=511)
    choice_3 = models.CharField(max_length=511)
    choice_4 = models.CharField(max_length=511)
    choice_5 = models.CharField(max_length=1, null=True, blank=True)
    answer = models.CharField(max_length=1, choices=CHOICES)
    explanation = models.TextField(blank=True, null=True)
    question_maker = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True, )
    is_deleted = models.BooleanField(default=False)
    has_problem = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text[:10:]}    |    {self.question_maker}"




class Lesson(models.Model):
    CHOICES = (
        ('1', 'پزشکی'),
        ('2', 'پرستاری'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    master = models.CharField(max_length=255)
    term = models.IntegerField()
    discipline = models.CharField(max_length=1, choices=CHOICES)


    def __str__(self) -> str:        
        return f"{self.name}  |  {self.master}"
    
    def quiz_count(self):
        lesson_quiz_count = Quiz.objects.filter(lesson=self).count()
        return lesson_quiz_count



class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True ,related_name="quiz")
    questions = models.ManyToManyField(Question)
    image = models.ImageField(upload_to="quiz/quiz_image", null=True, blank=True)
    quiz_maker =models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    time = models.DurationField()
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_edited = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


    def __str__(self) -> str:
        return f"{self.lesson.name}  | quiz maker : {self.quiz_maker}"

    def j_datetime_created(self):
        return jalali_convertor(self.datetime_created)

    def j_datetime_edited(self):
        return jalali_convertor(self.datetime_edited)
    