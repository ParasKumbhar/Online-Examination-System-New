"""
Anti-Cheating System Models
Tracks focus loss, tab switches, and suspicious behavior during exams.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Exam_Model
import logging

logger = logging.getLogger('app')


class ExamFocusLog(models.Model):
    """Log of focus loss events during exam taking"""

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_logs')
    exam = models.ForeignKey(Exam_Model, on_delete=models.CASCADE, related_name='focus_logs')
    focus_loss_count = models.IntegerField(default=0)
    max_focus_losses = models.IntegerField(default=5)
    last_focus_loss_time = models.DateTimeField(null=True, blank=True)
    is_suspicious = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'exam')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.exam.name} - {self.focus_loss_count} losses"

    def exceeded_max_losses(self):
        """Check if student exceeded focus loss limit"""
        return self.focus_loss_count > self.max_focus_losses

    def record_focus_loss(self):
        """Record a focus loss event"""
        self.focus_loss_count += 1
        self.last_focus_loss_time = timezone.now()

        if self.focus_loss_count > self.max_focus_losses:
            self.is_suspicious = True
            self.reason = f"Exceeded maximum focus losses ({self.max_focus_losses})"

        self.save()
        logger.warning(f"Focus loss recorded: {self.student.username} in {self.exam.name} (count: {self.focus_loss_count})")


class FocusLossEvent(models.Model):
    """Individual focus loss event with timestamp"""

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_loss_events')
    exam = models.ForeignKey(Exam_Model, on_delete=models.CASCADE, related_name='focus_loss_events')
    event_type = models.CharField(
        max_length=20,
        choices=[
            ('TAB_SWITCH', 'Tab Switched Away'),
            ('WINDOW_BLUR', 'Window Lost Focus'),
            ('VISIBILITY', 'Page Hidden'),
        ],
        default='TAB_SWITCH'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    browser_timestamp = models.DateTimeField(null=True, blank=True)  # When event occurred client-side
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.event_type} at {self.timestamp}"


class ExamSecurityAlert(models.Model):
    """Security alert for suspicious exam behavior"""

    ALERT_LEVELS = [
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('BLOCKED', 'Exam Blocked'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_alerts')
    exam = models.ForeignKey(Exam_Model, on_delete=models.CASCADE, related_name='security_alerts')
    alert_type = models.CharField(max_length=50)
    level = models.CharField(max_length=20, choices=ALERT_LEVELS, default='WARNING')
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.alert_type} - {self.student.username} ({self.level})"


class ExamSession(models.Model):
    """Recorded exam session details for anti-cheating and logging."""

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_sessions')
    exam = models.ForeignKey(Exam_Model, on_delete=models.CASCADE, related_name='exam_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    ends_at = models.DateTimeField(null=True, blank=True)

    question_order = models.JSONField(default=list, blank=True)
    option_order = models.JSONField(default=dict, blank=True)  # {qno: ['B','A','D','C']}

    tab_switch_count = models.IntegerField(default=0)
    fullscreen_exit_count = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    suspicious_flags = models.JSONField(default=dict, blank=True)
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'exam')
        ordering = ['-started_at']

    def __str__(self):
        return f"ExamSession({self.student.username}, {self.exam.name}, submitted={self.is_submitted})"

    def mark_submitted(self):
        self.is_submitted = True
        self.submitted_at = timezone.now()
        self.save()

    def record_tab_switch(self):
        self.tab_switch_count += 1
        self.suspicious_flags['tab_switch'] = self.tab_switch_count
        if self.tab_switch_count >= 5:
            self.suspicious_flags['auto_submit'] = 'tab_switch_threshold_reached'
        self.save()

    def record_fullscreen_exit(self):
        self.fullscreen_exit_count += 1
        self.suspicious_flags['fullscreen_exit'] = self.fullscreen_exit_count
        if self.fullscreen_exit_count >= 3:
            self.suspicious_flags['fullscreen_alert'] = 'multiple_exits'
        self.save()


class ServerTimestampValidator:
    """
    Validates exam submission timestamps to prevent timer manipulation.
    Ensures that submitted answers' timestamps match actual exam duration.
    """

    @staticmethod
    def validate_submission_time(student, exam, submission_time_client):
        """
        Validate if submission time is legitimate.

        Args:
            student: User object
            exam: Exam_Model object
            submission_time_client: Time when client submitted the form (ISO format)

        Returns:
            (is_valid, message)
        """
        server_time = timezone.now()

        # Check if submission is within exam window
        if server_time < exam.start_time:
            return False, "Exam has not started yet"

        if server_time > exam.end_time:
            return False, "Exam time has expired on server"

        # Calculate expected duration
        expected_duration = (exam.end_time - exam.start_time).total_seconds()

        # Parse client timestamp
        try:
            from django.utils.dateparse import parse_datetime
            client_dt = parse_datetime(submission_time_client)
            if not client_dt:
                return False, "Invalid submission timestamp format"
        except:
            return False, "Could not parse submission timestamp"

        # Check if client timestamp is way off (more than 30 seconds)
        time_diff = abs((server_time - client_dt).total_seconds())
        if time_diff > 30:
            logger.warning(f"Suspicious timestamp: {student.username} - diff: {time_diff}s")
            return False, f"Client clock is out of sync ({time_diff}s difference)"

        logger.info(f"Submission timestamp validated: {student.username}")
        return True, "Timestamp valid"
