"""
Email validation utilities for user registration across the application.
Ensures:
1. Valid email format
2. No duplicate emails in User model
3. Consistent email validation rules
"""

import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def validate_email_format(email):
    """
    Validate email format with strict pattern matching.
    
    Args:
        email (str): Email address to validate
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email address is required.")
    
    # RFC 5322 simplified email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Please enter a valid email address (e.g., yourname@example.com).")
    
    return email.lower()


def validate_email_unique(email, exclude_user_id=None):
    """
    Check if email is already registered in the User model.
    
    Args:
        email (str): Email address to check
        exclude_user_id (int, optional): User ID to exclude from check (for updates)
        
    Raises:
        ValidationError: If email is already in use
    """
    query = User.objects.filter(email=email)
    
    if exclude_user_id:
        query = query.exclude(id=exclude_user_id)
    
    if query.exists():
        raise ValidationError(
            "This email address is already registered. Please use a different email or login to your existing account."
        )


def validate_email_complete(email, exclude_user_id=None):
    """
    Complete email validation: format + uniqueness check.
    
    Args:
        email (str): Email address to validate
        exclude_user_id (int, optional): User ID to exclude from uniqueness check
        
    Returns:
        str: Normalized email address (lowercase)
        
    Raises:
        ValidationError: If email is invalid or already in use
    """
    # Validate format
    normalized_email = validate_email_format(email)
    
    # Validate uniqueness
    validate_email_unique(normalized_email, exclude_user_id)
    
    return normalized_email


def get_email_error_messages():
    """Return standardized email validation error messages."""
    return {
        'required': "Email address is required.",
        'invalid_format': "Please enter a valid email address (e.g., yourname@example.com).",
        'already_registered': "This email address is already registered. Please use a different email or login to your existing account.",
        'no_duplicates': "Email addresses must be unique across the system."
    }
