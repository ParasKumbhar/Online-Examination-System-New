from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Applicant_Registration, Student
from core.email_validators import validate_email_format, validate_email_unique


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()


class ApplicantRegistrationForm(forms.ModelForm):
    """Form for Applicant Registration with email validation."""
    
    class Meta:
        model = Applicant_Registration
        fields = ['surname', 'first_Name', 'other_Name', 'email', 'phone', 'nationality', 'state_Origin', 'lga_Origin', 'gender']
    
    def clean_email(self):
        """Validate email format and check for duplicates across all registration systems."""
        email = self.cleaned_data.get('email')
        
        # Validate format
        normalized_email = validate_email_format(email)
        
        # Check if email is already registered in Applicant_Registration
        if Applicant_Registration.objects.filter(email=normalized_email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already registered. Please use a different email.")
        
        # Check if email is already used in the main User system
        validate_email_unique(normalized_email)
        
        return normalized_email


class StudentAdmissionForm(forms.ModelForm):
    """Form for Student model with email validation."""
    
    class Meta:
        model = Student
        fields = ['surname', 'first_Name', 'other_Name', 'email', 'phone', 'gender', 
                  'home_Address', 'nationality', 'state', 'local_Government', 'village_Name',
                  'mother_Maiden_name', 'admitted_programme', 'admitted_Department']
    
    def clean_email(self):
        """Validate email format and check for duplicates across all registration systems."""
        email = self.cleaned_data.get('email')
        
        # Validate format
        normalized_email = validate_email_format(email)
        
        # Check if email is already registered in Student model
        if Student.objects.filter(email=normalized_email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already registered. Please use a different email.")
        
        # Check if email is already used in the main User system
        validate_email_unique(normalized_email)
        
        return normalized_email
