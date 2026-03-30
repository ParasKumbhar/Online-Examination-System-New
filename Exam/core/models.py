from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class IPWhitelist(models.Model):
    """IP Whitelist model for admin/users."""
    ip_address = models.GenericIPAddressField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "IP Whitelist"

    def __str__(self):
        return f"{self.ip_address} - {self.description}"


class ActiveUserSession(models.Model):
    """Maintain one active session among all devices for each user."""

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='active_session')
    session_key = models.CharField(max_length=255, unique=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Active session for {self.user.username}: {self.session_key}"

class LoginAudit(models.Model):
    """Audit log for login attempts."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=64)
    success = models.BooleanField()
    suspicious = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Login Audits"

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.user or 'Anonymous'} - {status} - {self.ip_address}"

class AuditLog(models.Model):
    """General audit log for all user actions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=50)  # LOGIN, CREATE_EXAM, SUBMIT_ANSWER, etc.
    target_model = models.CharField(max_length=100, blank=True)  # Exam, Question, etc.
    target_id = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.action} - {self.timestamp}"


class OTPSession(models.Model):
    """
    Track OTP sessions for each login attempt.
    Links OTP to specific login attempt context.
    """
    user_email = models.EmailField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='otp_sessions')
    
    # Session tracking
    session_id = models.CharField(max_length=64, unique=True)  # Unique identifier for this login attempt
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=64, blank=True)
    
    # OTP status
    otp_generated_at = models.DateTimeField(auto_now_add=True)
    otp_expires_at = models.DateTimeField()
    otp_verified = models.BooleanField(default=False)
    otp_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Resend tracking
    resend_count = models.PositiveIntegerField(default=0)
    last_resend_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "OTP Sessions"
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user_email']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        status = "Verified" if self.otp_verified else "Pending"
        return f"OTP Session {self.session_id[:10]}... for {self.user_email} ({status})"
    
    def is_expired(self):
        """Check if OTP session has expired."""
        return timezone.now() > self.otp_expires_at
    
    def can_resend(self, resend_interval_seconds=30):
        """Check if user can resend OTP (rate limiting)."""
        if not self.last_resend_at:
            return True
        time_since_last_resend = timezone.now() - self.last_resend_at
        return time_since_last_resend.total_seconds() >= resend_interval_seconds
    
    def invalidate(self):
        """Invalidate this OTP session."""
        self.is_active = False
        self.save(update_fields=['is_active'])


class OTPAttempt(models.Model):
    """
    Track individual OTP verification attempts.
    Enforce retry limits to prevent brute-force attacks.
    """
    session = models.ForeignKey(OTPSession, on_delete=models.CASCADE, related_name='attempts')
    ip_address = models.GenericIPAddressField()
    
    # Attempt tracking
    attempt_number = models.PositiveIntegerField()
    success = models.BooleanField(default=False)
    reason = models.CharField(
        max_length=50,
        choices=[
            ('INVALID_OTP', 'Invalid OTP'),
            ('EXPIRED_OTP', 'Expired OTP'),
            ('CORRECT', 'Correct OTP'),
        ],
        blank=True
    )
    
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name_plural = "OTP Attempts"
        indexes = [
            models.Index(fields=['session', 'attempted_at']),
        ]
    
    def __str__(self):
        status = "✓ Success" if self.success else "✗ Failed"
        return f"Attempt #{self.attempt_number} {status} ({self.reason})"

