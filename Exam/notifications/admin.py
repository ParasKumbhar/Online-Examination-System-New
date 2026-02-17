"""
Admin configuration for notifications.
"""

from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['created_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_exam_reminders', 'email_results', 'disable_until']
    list_filter = ['email_exam_reminders', 'email_results']
    search_fields = ['user__username']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'method', 'status', 'sent_at']
    list_filter = ['notification_type', 'method', 'status', 'sent_at']
    search_fields = ['user__username']
    readonly_fields = ['sent_at']
