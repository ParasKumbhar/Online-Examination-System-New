"""
Test suite for email validation across registration forms.
Tests ensure email validation works correctly for all registration types.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from core.email_validators import (
    validate_email_format,
    validate_email_unique,
    validate_email_complete,
    get_email_error_messages
)
from student.forms import StudentForm
from faculty.forms import FacultyForm
from admission.forms import ApplicantRegistrationForm, StudentAdmissionForm


class EmailValidatorTests(TestCase):
    """Test email validation utility functions."""
    
    def setUp(self):
        """Set up test user for uniqueness checks."""
        self.existing_user = User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='TestPass123@'
        )
    
    # Email Format Validation Tests
    def test_valid_email_format(self):
        """Test that valid emails pass format validation."""
        valid_emails = [
            'user@example.com',
            'john.doe@example.co.uk',
            'user+tag@domain.org',
            'test_email@sub.example.com',
            'name123@test.io',
        ]
        
        for email in valid_emails:
            try:
                result = validate_email_format(email)
                self.assertEqual(result, email.lower())
            except ValidationError:
                self.fail(f"Valid email '{email}' failed validation")
    
    def test_invalid_email_format(self):
        """Test that invalid emails fail format validation."""
        invalid_emails = [
            'plainaddress',           # No @
            'user@',                  # No domain
            '@example.com',           # No username
            'user @example.com',      # Space
            'user@example',           # No TLD
            'user@.com',              # No domain name
            'user@example..com',      # Double dot
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                validate_email_format(email)
    
    def test_email_format_case_normalization(self):
        """Test that emails are converted to lowercase."""
        emails = [
            'USER@EXAMPLE.COM',
            'John.Doe@Example.Com',
            'TEST@TEST.ORG',
        ]
        
        for email in emails:
            result = validate_email_format(email)
            self.assertEqual(result, email.lower())
    
    def test_empty_email_validation(self):
        """Test that empty email raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_email_format('')
        
        with self.assertRaises(ValidationError):
            validate_email_format(None)
    
    # Email Uniqueness Tests
    def test_duplicate_email_detection(self):
        """Test that duplicate emails are detected."""
        with self.assertRaises(ValidationError) as context:
            validate_email_unique('test@example.com')
        
        self.assertIn('already registered', str(context.exception))
    
    def test_unique_email_passes(self):
        """Test that unique emails pass validation."""
        try:
            validate_email_unique('newuser@example.com')
        except ValidationError:
            self.fail("Unique email failed validation")
    
    def test_exclude_user_id_in_uniqueness_check(self):
        """Test that excluding a user ID allows same email."""
        # This should pass because we exclude the existing user
        try:
            validate_email_unique('test@example.com', exclude_user_id=self.existing_user.id)
        except ValidationError:
            self.fail("Email validation failed when excluding same user")
    
    # Complete Validation Tests
    def test_complete_validation_success(self):
        """Test complete validation with valid, unique email."""
        result = validate_email_complete('newuser@example.com')
        self.assertEqual(result, 'newuser@example.com')
    
    def test_complete_validation_duplicate_fails(self):
        """Test complete validation fails for duplicate emails."""
        with self.assertRaises(ValidationError):
            validate_email_complete('test@example.com')
    
    def test_complete_validation_invalid_format_fails(self):
        """Test complete validation fails for invalid format."""
        with self.assertRaises(ValidationError):
            validate_email_complete('invalidemail@')
    
    # Error Messages Tests
    def test_error_messages_available(self):
        """Test that error messages are available."""
        messages = get_email_error_messages()
        
        required_keys = ['required', 'invalid_format', 'already_registered', 'no_duplicates']
        for key in required_keys:
            self.assertIn(key, messages)
            self.assertIsInstance(messages[key], str)
            self.assertTrue(len(messages[key]) > 0)


class StudentFormEmailValidationTests(TestCase):
    """Test email validation in StudentForm."""
    
    def setUp(self):
        """Set up test user."""
        self.existing_user = User.objects.create_user(
            username='existing',
            email='taken@example.com',
            password='TestPass123@'
        )
    
    def test_student_form_valid_email(self):
        """Test StudentForm accepts valid, unique email."""
        form_data = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_student_form_duplicate_email(self):
        """Test StudentForm rejects duplicate email."""
        form_data = {
            'username': 'newstudent',
            'email': 'taken@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already registered', str(form.errors['email']))
    
    def test_student_form_invalid_email_format(self):
        """Test StudentForm rejects invalid email format."""
        form_data = {
            'username': 'newstudent',
            'email': 'notanemail',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_student_form_email_case_normalization(self):
        """Test StudentForm normalizes email to lowercase."""
        form_data = {
            'username': 'newstudent',
            'email': 'STUDENT@EXAMPLE.COM',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'student@example.com')


class FacultyFormEmailValidationTests(TestCase):
    """Test email validation in FacultyForm."""
    
    def setUp(self):
        """Set up test user."""
        self.existing_user = User.objects.create_user(
            username='existing',
            email='taken@example.com',
            password='TestPass123@'
        )
    
    def test_faculty_form_valid_email(self):
        """Test FacultyForm accepts valid, unique email."""
        form_data = {
            'username': 'newfaculty',
            'email': 'faculty@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = FacultyForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_faculty_form_duplicate_email(self):
        """Test FacultyForm rejects duplicate email."""
        form_data = {
            'username': 'newfaculty',
            'email': 'taken@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = FacultyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_faculty_form_invalid_email_format(self):
        """Test FacultyForm rejects invalid email format."""
        form_data = {
            'username': 'newfaculty',
            'email': 'invalid.email@',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = FacultyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class RegistrationEmailConflictTests(TestCase):
    """Test that emails can't be duplicated across student and faculty."""
    
    def test_student_then_faculty_same_email_fails(self):
        """Test that faculty can't use email from existing student."""
        # Create a student first
        User.objects.create_user(
            username='student1',
            email='shared@example.com',
            password='TestPass123@'
        )
        
        # Try to create faculty with same email
        form_data = {
            'username': 'faculty1',
            'email': 'shared@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = FacultyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_faculty_then_student_same_email_fails(self):
        """Test that student can't use email from existing faculty."""
        # Create a faculty first
        User.objects.create_user(
            username='faculty1',
            email='shared@example.com',
            password='TestPass123@'
        )
        
        # Try to create student with same email
        form_data = {
            'username': 'student1',
            'email': 'shared@example.com',
            'password': 'TestPass123@',
            'confirm_password': 'TestPass123@',
        }
        form = StudentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


# Test execution: python manage.py test core.tests.email_validation
