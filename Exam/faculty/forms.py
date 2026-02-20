from django import forms 
from .models import FacultyInfo
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator

class FacultyForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'id_password',
            'tabindex': '3',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all',
            'placeholder': 'Enter password (min 8 chars, uppercase, lowercase, number, special char)',
            'pattern': '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            'title': 'Password must contain: at least 8 characters, one uppercase, one lowercase, one number and one special character'
        }),
        validators=[
            MinLengthValidator(8),
            RegexValidator(
                regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                message='Password must contain at least: 8 characters, one uppercase, one lowercase, one number and one special character (@$!%*?&)'
            )
        ]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'id': 'id_confirm_password',
            'tabindex': '4',
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta():
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'email' : forms.EmailInput(attrs = {'id':'id_email','tabindex': '2','class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'}),
            'username' : forms.TextInput(attrs = {'id':'id_username','tabindex': '1','class':'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all'})
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data

class FacultyInfoForm(forms.ModelForm):
    class Meta():
        model = FacultyInfo
        fields = ['picture']
        widgets = {
            'picture': forms.FileInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all', 'tabindex': '5'})
        }
