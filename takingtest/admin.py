from django.contrib import admin

from .models import QuizHistory, QuizResult, LikeDislike

@admin.register(QuizHistory)
class QuizHistoryAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'datetime_created')
    # list_editable = ('datetime_created',)


@admin.register(QuizResult)
class QuizResultyAdmin(admin.ModelAdmin):
    list_display = ('quiz','user')

    
@admin.register(LikeDislike)
class QuizResultyAdmin(admin.ModelAdmin):
    list_display = ('quiz','user', 'like')
