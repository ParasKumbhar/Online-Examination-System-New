from django.db import models
from django.contrib.auth.models import User
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

