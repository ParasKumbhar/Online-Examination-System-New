from django.contrib import admin
from .models import Exam_Model
from .questionpaper_models import Question_Paper
from .question_enhancements import QuestionTag

admin.site.register(QuestionTag)
admin.site.register(Question_Paper)
admin.site.register(Exam_Model)