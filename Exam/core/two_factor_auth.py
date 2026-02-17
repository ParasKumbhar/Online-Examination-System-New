"""
Two-Factor Authentication (2FA) utilities.
Supports Email OTP and SMS OTP.
"""

import secrets
import logging
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import string

logger = logging.getLogger('app')


class OTPGenerator:
    """Generate and verify One-Time Passwords (OTP)."""
    
    @staticmethod
    def generate_otp(length=6):
        """
        Generate a random OTP.
        
        Args:
            length: OTP length (default 6)
        
        Returns:
            str: Random OTP
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def send_email_otp(user_email, user_name=None):
        """
        Send OTP via email.
        
        Args:
            user_email: Email address to send OTP to
            user_name: User's name (optional)
        
        Returns:
            dict: {'success': bool, 'message': str, 'otp': str}
        """
        
        try:
            # Generate OTP
            otp = OTPGenerator.generate_otp()
            
            # Store in cache with expiry
            cache_key = f'otp_{user_email}'
            cache.set(
                cache_key,
                otp,
                timeout=settings.OTP_EXPIRY_TIME
            )
            
            # Prepare email
            subject = 'Your Two-Factor Authentication Code'
            message = f"""
Hello {user_name or 'User'},

Your One-Time Password (OTP) is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Exam System Team
            """
            
            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                fail_silently=False,
            )
            
            logger.info(f'OTP sent to {user_email}')
            
            return {
                'success': True,
                'message': 'OTP sent to your email',
                'otp': otp if settings.DEBUG else None,  # Don't expose in production
            }
        
        except Exception as e:
            logger.error(f'Error sending OTP: {str(e)}')
            return {
                'success': False,
                'message': 'Failed to send OTP',
                'error': str(e),
            }
    
    @staticmethod
    def verify_otp(user_email, provided_otp):
        """
        Verify provided OTP.
        
        Args:
            user_email: Email address to verify
            provided_otp: OTP provided by user
        
        Returns:
            dict: {'valid': bool, 'message': str}
        """
        
        cache_key = f'otp_{user_email}'
        stored_otp = cache.get(cache_key)
        
        if not stored_otp:
            return {
                'valid': False,
                'message': 'OTP expired. Please request a new one.',
            }
        
        if str(provided_otp).strip() != str(stored_otp).strip():
            return {
                'valid': False,
                'message': 'Invalid OTP. Please try again.',
            }
        
        # Clear OTP after successful verification
        cache.delete(cache_key)
        
        logger.info(f'OTP verified for {user_email}')
        
        return {
            'valid': True,
            'message': 'OTP verified successfully.',
        }


class TwoFactorAuth:
    """Manage 2FA settings for users."""
    
    @staticmethod
    def enable_2fa(user, method='email'):
        """
        Enable 2FA for a user.
        
        Args:
            user: User object
            method: 'email' or 'sms'
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        
        if method == 'email':
            return OTPGenerator.send_email_otp(user.email, user.first_name)
        else:
            return {
                'success': False,
                'message': 'SMS method not yet implemented',
            }
    
    @staticmethod
    def is_2fa_enabled(user):
        """Check if 2FA is enabled for user."""
        return getattr(user.userprofile, 'two_factor_enabled', False)
    
    @staticmethod
    def require_2fa_verification(user):
        """Mark user as requiring 2FA verification."""
        cache_key = f'2fa_required_{user.id}'
        cache.set(cache_key, True, timeout=300)  # 5 minutes
    
    @staticmethod
    def clear_2fa_requirement(user):
        """Clear 2FA verification requirement."""
        cache_key = f'2fa_required_{user.id}'
        cache.delete(cache_key)
    
    @staticmethod
    def is_2fa_required(user):
        """Check if user requires 2FA verification."""
        cache_key = f'2fa_required_{user.id}'
        return cache.get(cache_key, False)
