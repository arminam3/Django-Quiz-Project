from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import QestionReport, Question, Quiz
from pages.models import Notification

@receiver(post_save, sender=QestionReport)
def send_question_report_notification(sender, *args, **kwargs):
    question_report = get_object_or_404(QestionReport, id=kwargs.get('instance').id)
    question = question_report.question
    quiz = question_report.quiz
    link = reverse('question_update', args=[question.id])
    print('=======   ---   ======')
    print(question.question_maker)
    Notification.objects.create(
        receptor= question.question_maker,
        title='مشکل در سوال',
        text= f"به سوال شما درآزمون <b><a href=\"{link}\"  class=\"btn-outline-primary\" style=\"border-radius:2px;\">{quiz.name}</a></b>ایراد گرفته شده است."
    )

    # {'signal': <django.db.models.signals.ModelSignal object at 0x000001CE396765F0>, 
    #  'instance': <QestionReport: <bound method AbstractUser.get_full_name of <User: armin>>
    #    | مورد بهتر را انتخاب کنید .>, 'created': True, 
    #    'update_fields': None, 'raw': False, 'using': 'default'}