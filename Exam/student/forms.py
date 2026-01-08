from django import forms
from .models import StudentInfo
from django.contrib.auth.models import User

class StudentForm(forms.ModelForm):
    
    class Meta():
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs = {'id':'passwordfield','class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'}),
            'email' : forms.EmailInput(attrs = {'id':'emailfield','class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'}),
            'username' : forms.TextInput(attrs = {'id':'usernamefield','class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'})
        }

class StudentInfoForm(forms.ModelForm):
    class Meta():
        model = StudentInfo
        fields = ['address','stream','picture']
        widgets = {
            'address': forms.Textarea(attrs = {'class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all', 'rows': 3}),
            'stream' : forms.TextInput(attrs = {'class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'}),
            'picture': forms.FileInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'})
        }