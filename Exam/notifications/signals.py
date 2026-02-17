"""
Signal handlers for notifications.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import NotificationPreference


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """Create notification preferences when user is created."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)
