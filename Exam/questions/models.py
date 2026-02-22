from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from datetime import datetime
from .questionpaper_models import Question_Paper
from django import forms

class Exam_Model(models.Model):
    professor = models.ForeignKey(User, limit_choices_to={'groups__name': "Professor"}, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    total_marks = models.IntegerField(default=0, blank=True)
    question_paper = models.ForeignKey(Question_Paper, on_delete=models.CASCADE, related_name='exams')
    start_time = models.DateTimeField(default=datetime.now())
    end_time = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return self.name


class ExamForm(ModelForm):
    def __init__(self,professor,*args,**kwargs):
        super (ExamForm,self ).__init__(*args,**kwargs) 
        self.fields['question_paper'].queryset = Question_Paper.objects.filter(professor=professor)
        self.fields['question_paper'].empty_label = "Select Question Paper"

    class Meta:
        model = Exam_Model
        fields = '__all__'
        exclude = ['professor', 'total_marks']
        labels = {
            'name': 'Exam Name',
            'question_paper': 'Question Paper',
        }
        widgets = {
            'name': forms.TextInput(attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary'}),
            'start_time': forms.DateTimeInput(attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary', 'type': 'datetime-local'}),
            'question_paper': forms.Select(attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary'})
        }
