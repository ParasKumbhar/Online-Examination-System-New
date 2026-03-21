"""
Background Scheduler for Exam Reminders
Uses APScheduler to send exam reminders automatically
"""

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('app')


def send_exam_reminders_24hr():
    """
    Check for exams starting in ~24 hours
    Send reminder notifications to all students
    """
    try:
        from django.contrib.auth.models import User
        from questions.models import Exam_Model
        from notifications.models import Notification, NotificationService, NotificationType

        now = timezone.now()
        # Look for exams starting between 23 and 25 hours from now
        start_window = now + timedelta(hours=23, minutes=30)
        end_window = now + timedelta(hours=24, minutes=30)

        upcoming_exams = Exam_Model.objects.filter(
            start_time__gte=start_window,
            start_time__lte=end_window
        )

        for exam in upcoming_exams:
            # Get all students
            students = User.objects.filter(groups__name='Student')

            for student in students:
                # Check if reminder already sent (prevent duplicates)
                existing_notif = Notification.objects.filter(
                    recipient=student,
                    notification_type=NotificationType.EXAM_REMINDER,
                    related_exam_id=exam.id,
                    created_at__gte=now - timedelta(hours=1)  # Within last hour
                ).exists()

                if not existing_notif:
                    title = f"Exam Starting Tomorrow: {exam.name}"
                    message = f"""
Your exam '{exam.name}' is scheduled to start in approximately 24 hours.

📅 Date & Time: {exam.start_time.strftime('%B %d, %Y at %H:%M')}
⏱️ Duration: {(exam.end_time - exam.start_time).total_seconds() / 60:.0f} minutes
📝 Question Paper: {exam.question_paper.qPaperTitle if exam.question_paper else 'Not assigned'}
📊 Total Marks: {exam.question_paper.total_marks if exam.question_paper else 0}

Please log in and review the exam details. Make sure you have a stable internet connection.
                    """

                    NotificationService.send_notification(
                        student,
                        NotificationType.EXAM_REMINDER,
                        title,
                        message,
                        send_email=True,
                        related_exam_id=exam.id,
                        action_url=f'/exams/{exam.id}/',
                        priority=3,
                        expires_in_minutes=1440  # 24 hours
                    )

                    logger.info(f"24-hour exam reminder sent to {student.username} for exam {exam.name}")

    except Exception as e:
        logger.error(f"Error in send_exam_reminders_24hr: {str(e)}")


def send_exam_reminders_1hr():
    """
    Check for exams starting in ~1 hour
    Send urgent reminder notifications to all students
    """
    try:
        from django.contrib.auth.models import User
        from questions.models import Exam_Model
        from notifications.models import Notification, NotificationService, NotificationType

        now = timezone.now()
        # Look for exams starting between 55 minutes and 65 minutes from now
        start_window = now + timedelta(minutes=55)
        end_window = now + timedelta(minutes=65)

        upcoming_exams = Exam_Model.objects.filter(
            start_time__gte=start_window,
            start_time__lte=end_window
        )

        for exam in upcoming_exams:
            # Get all students
            students = User.objects.filter(groups__name='Student')

            for student in students:
                # Check if reminder already sent (prevent duplicates)
                existing_notif = Notification.objects.filter(
                    recipient=student,
                    notification_type=NotificationType.EXAM_REMINDER,
                    related_exam_id=exam.id,
                    created_at__gte=now - timedelta(minutes=10)  # Within last 10 minutes
                ).exists()

                if not existing_notif:
                    title = f"⏰ URGENT: Exam Starting Soon - {exam.name}"
                    message = f"""
🚨 Your exam '{exam.name}' is starting in approximately 1 hour!

⏱️ Start Time: {exam.start_time.strftime('%H:%M')} (in ~60 minutes)
📝 Question Paper: {exam.question_paper.qPaperTitle if exam.question_paper else 'Not assigned'}
📊 Total Marks: {exam.question_paper.total_marks if exam.question_paper else 0}

Please:
✓ Check your internet connection
✓ Close unnecessary applications
✓ Have your student ID ready
✓ Log in to the exam portal

Exam link: /exams/{exam.id}/
                    """

                    NotificationService.send_notification(
                        student,
                        NotificationType.EXAM_REMINDER,
                        title,
                        message,
                        send_email=True,
                        related_exam_id=exam.id,
                        action_url=f'/exams/{exam.id}/',
                        priority=5,  # Critical priority
                        expires_in_minutes=90  # 1.5 hours
                    )

                    logger.info(f"1-hour exam reminder sent to {student.username} for exam {exam.name}")

    except Exception as e:
        logger.error(f"Error in send_exam_reminders_1hr: {str(e)}")


def start_exam_reminder_scheduler():
    """
    Start the background scheduler for exam reminders
    Should be called in Django app's ready() method
    """
    scheduler = BackgroundScheduler()

    # Schedule 24-hour reminder check every 30 minutes
    scheduler.add_job(
        send_exam_reminders_24hr,
        'interval',
        minutes=30,
        id='exam_reminder_24hr',
        name='24-hour exam reminders',
        replace_existing=True
    )

    # Schedule 1-hour reminder check every 5 minutes (more responsive reminder delivery)
    scheduler.add_job(
        send_exam_reminders_1hr,
        'interval',
        minutes=5,
        id='exam_reminder_1hr',
        name='1-hour exam reminders',
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()
        logger.info("Exam reminder scheduler started successfully")

    return scheduler


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get the global scheduler instance"""
    global _scheduler
    if _scheduler is None or not _scheduler.running:
        _scheduler = start_exam_reminder_scheduler()
    return _scheduler
