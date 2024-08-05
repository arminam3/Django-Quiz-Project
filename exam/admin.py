from django.contrib import admin

from .models import Question, Lesson, Quiz, QestionReport

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
                     "text", "is_deleted", "image", "id",
                    # "choice_1","choice_2", "choice_3", "choice_4", 
                    # "answer", 
                    "question_maker", "datetime_created"
                    )
    
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("name", "is_deleted", "lesson", "quiz_maker", "datetime_created", "datetime_edited")
    list_editable = ("is_deleted",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("name", "master")

@admin.register(QestionReport)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("user",)
