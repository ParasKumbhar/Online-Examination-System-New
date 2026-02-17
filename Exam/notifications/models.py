"""
Notification System - Handle in-app and email notifications.
Integrates with Django signals for real-time updates.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('app')


class NotificationType(models.TextChoices):
    """Types of notifications."""
    EXAM_REMINDER = 'EXAM_REMINDER', 'Exam Reminder'
    EXAM_STARTED = 'EXAM_STARTED', 'Exam Started'
    EXAM_ENDING = 'EXAM_ENDING', 'Exam Ending Soon'
    RESULT_READY = 'RESULT_READY', 'Result Available'
    SECURITY_ALERT = 'SECURITY_ALERT', 'Security Alert'
    ADMIN_MESSAGE = 'ADMIN_MESSAGE', 'Admin Broadcast'
    CHEATING_DETECTED = 'CHEATING_DETECTED', 'Cheating Detection'


class Notification(models.Model):
    """In-app notification model."""
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    related_exam_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=1)  # 1=low, 5=critical
    action_url = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_pref')
    
    # Email notifications
    email_exam_reminders = models.BooleanField(default=True)
    email_results = models.BooleanField(default=True)
    email_security_alerts = models.BooleanField(default=True)
    
    # In-app notifications
    inapp_exam_reminders = models.BooleanField(default=True)
    inapp_results = models.BooleanField(default=True)
    inapp_security_alerts = models.BooleanField(default=True)
    
    # Notification frequency
    disable_until = models.DateTimeField(null=True, blank=True)  # Snooze period
    
    # Throttling
    max_notifications_per_hour = models.IntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class NotificationLog(models.Model):
    """Log of sent notifications for audit trail."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    method = models.CharField(max_length=20, choices=[('EMAIL', 'Email'), ('INAPP', 'In-App')])
    status = models.CharField(max_length=20, choices=[('SENT', 'Sent'), ('FAILED', 'Failed'), ('PENDING', 'Pending')])
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'sent_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.username}"


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    def send_notification(user, notification_type, title, message, **kwargs):
        """
        Send a notification to user (both in-app and email).
        
        Args:
            user: User object
            notification_type: NotificationType choice
            title: Notification title
            message: Notification message
            **kwargs: Additional options
                - send_email: bool (default True)
                - priority: int (1-5)
                - expires_in_minutes: int
                - action_url: str
                - related_exam_id: int
        """
        
        try:
            # Get user preferences
            prefs = NotificationPreference.objects.get_or_create(user=user)[0]
            
            # Check if user disabled notifications
            if prefs.disable_until and prefs.disable_until > datetime.now():
                logger.info(f"Notification silenced for {user.username}")
                return False
            
            # Create in-app notification
            notification = Notification.objects.create(
                recipient=user,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=kwargs.get('priority', 1),
                related_exam_id=kwargs.get('related_exam_id'),
                action_url=kwargs.get('action_url', ''),
            )
            
            # Set expiry if specified
            if 'expires_in_minutes' in kwargs:
                notification.expires_at = datetime.now() + timedelta(minutes=kwargs['expires_in_minutes'])
                notification.save()
            
            # Log notification
            NotificationLog.objects.create(
                user=user,
                notification_type=notification_type,
                method='INAPP',
                status='SENT'
            )
            
            # Send email if enabled
            send_email = kwargs.get('send_email', True)
            if send_email:
                NotificationService.send_email_notification(user, title, message, prefs, notification_type)
            
            logger.info(f"Notification sent to {user.username}: {title}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    @staticmethod
    def send_email_notification(user, title, message, prefs, notification_type):
        """Send email notification based on user preferences."""
        
        # Check if email is enabled for this type
        if notification_type == NotificationType.EXAM_REMINDER and not prefs.email_exam_reminders:
            return
        if notification_type == NotificationType.RESULT_READY and not prefs.email_results:
            return
        if notification_type == NotificationType.SECURITY_ALERT and not prefs.email_security_alerts:
            return
        
        try:
            email_subject = f"[Exam System] {title}"
            email_body = f"""
Dear {user.first_name or user.username},

{message}

Best regards,
Exam System Team

---
Manage notification preferences: {settings.SITE_URL}/preferences/
            """
            
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            # Log email
            NotificationLog.objects.create(
                user=user,
                notification_type=notification_type,
                method='EMAIL',
                status='SENT'
            )
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {str(e)}")
            NotificationLog.objects.create(
                user=user,
                notification_type=notification_type,
                method='EMAIL',
                status='FAILED',
                error_message=str(e)
            )
    
    @staticmethod
    def send_exam_reminder(exam, time_before_minutes):
        """
        Send reminder to all students for an exam.
        
        Args:
            exam: Exam_Model instance
            time_before_minutes: Send reminder X minutes before exam
        """
        
        # Calculate when to send
        reminder_time = exam.start_time - timedelta(minutes=time_before_minutes)
        
        if datetime.now() >= reminder_time and datetime.now() < exam.start_time:
            # Get all students enrolled in this batch
            students = User.objects.filter(groups__name='Student')
            
            title = f"Exam Reminder: {exam.name}"
            message = f"""
Exam '{exam.name}' will start in {time_before_minutes} minutes.

Total Marks: {exam.total_marks}
Start Time: {exam.start_time}

Click here to enter the exam room.
            """
            
            for student in students:
                NotificationService.send_notification(
                    student,
                    NotificationType.EXAM_REMINDER,
                    title,
                    message,
                    send_email=True,
                    related_exam_id=exam.id,
                    action_url=f'/exams/{exam.id}/'
                )
    
    @staticmethod
    def send_bulk_message(message, title, recipient_filter=None):
        """
        Send broadcast message to all or filtered users.
        
        Args:
            message: Message text
            title: Message title
            recipient_filter: Q object to filter users (optional)
        """
        
        if recipient_filter:
            users = User.objects.filter(recipient_filter)
        else:
            users = User.objects.all()
        
        for user in users:
            NotificationService.send_notification(
                user,
                NotificationType.ADMIN_MESSAGE,
                title,
                message,
                send_email=True,
                priority=2
            )


# Signal handlers for automatic notifications

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)


@receiver(post_save, sender=Notification)
def cleanup_expired_notifications(sender, instance, created, **kwargs):
    """Clean up expired notifications periodically."""
    if created:
        # Delete notifications older than 30 days
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=30)
        Notification.objects.filter(created_at__lt=cutoff_date).delete()
