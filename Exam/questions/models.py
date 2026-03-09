from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils import timezone
from .questionpaper_models import Question_Paper
from django import forms


def _now_rounded_to_minute():
    """Return current time rounded down to the nearest full minute."""
    now = timezone.now()
    return now.replace(second=0, microsecond=0)


class Exam_Model(models.Model):
    professor = models.ForeignKey(User, limit_choices_to={'groups__name': "Professor"}, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    total_marks = models.IntegerField(default=0, blank=True)
    question_paper = models.ForeignKey(Question_Paper, on_delete=models.CASCADE, related_name='exams')
    start_time = models.DateTimeField(default=_now_rounded_to_minute)
    end_time = models.DateTimeField(default=_now_rounded_to_minute)

    def __str__(self):
        return self.name


class ExamForm(ModelForm):
    def __init__(self, professor, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        self.fields['question_paper'].queryset = Question_Paper.objects.filter(professor=professor)
        self.fields['question_paper'].empty_label = "Select Question Paper"

        # Set minimum selectable datetime to now (rounded down to a whole minute) so browser validation does not reject the default value
        now_rounded = timezone.localtime().replace(second=0, microsecond=0)
        now_value = now_rounded.strftime("%Y-%m-%dT%H:%M")

        # Only set initial datetime values for new exams; when editing an existing exam, keep the stored values.
        if not getattr(self, 'instance', None) or not getattr(self.instance, 'pk', None):
            if 'start_time' in self.fields:
                self.fields['start_time'].initial = now_rounded
            if 'end_time' in self.fields:
                self.fields['end_time'].initial = now_rounded

        if 'start_time' in self.fields:
            self.fields['start_time'].widget.attrs.setdefault('min', now_value)
            self.fields['start_time'].widget.attrs.setdefault('step', 60)
        if 'end_time' in self.fields:
            self.fields['end_time'].widget.attrs.setdefault('min', now_value)
            self.fields['end_time'].widget.attrs.setdefault('step', 60)

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
            'start_time': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary', 'type': 'datetime-local'}),
            'question_paper': forms.Select(attrs = {'class':'w-full rounded-lg border-slate-300 text-slate-900 focus:ring-primary focus:border-primary'})
        }
