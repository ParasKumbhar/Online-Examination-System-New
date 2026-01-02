from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django import forms

class Question_DB(models.Model):
    professor = models.ForeignKey(User, limit_choices_to={'groups__name': "Professor"}, on_delete=models.CASCADE, null=True)
    qno = models.AutoField(primary_key=True)
    question = models.CharField(max_length=100)
    optionA = models.CharField(max_length=100)
    optionB = models.CharField(max_length=100)
    optionC = models.CharField(max_length=100)
    optionD = models.CharField(max_length=100)
    answer = models.CharField(max_length=200)
    max_marks = models.IntegerField(default=0)

    def __str__(self):
        return f'Question No.{self.qno}: {self.question} \t\t Options: \nA. {self.optionA} \nB.{self.optionB} \nC.{self.optionC} \nD.{self.optionD} '


class QForm(ModelForm):
    answer = forms.ChoiceField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Question_DB
        fields = '__all__'
        exclude = ['qno', 'professor']
        widgets = {
            'question': forms.Textarea(attrs = {'class':'form-control', 'rows': 4}),
            'optionA': forms.TextInput(attrs = {'class':'form-control'}),
            'optionB': forms.TextInput(attrs = {'class':'form-control'}),
            'optionC': forms.TextInput(attrs = {'class':'form-control'}),
            'optionD': forms.TextInput(attrs = {'class':'form-control'}),
            'max_marks': forms.NumberInput(attrs = {'class':'form-control'}),
        }