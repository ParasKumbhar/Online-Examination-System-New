from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Keep default groups synchronized after migrations for apps that own
    the configured permissions.
    """
    if kwargs.get('raw', False):
        return

    relevant_apps = {
        'core',
        'questions',
        'faculty',
        'course',
        'resultprocessing',
        'notifications',
        'student',
        'studentPreferences',
        'tuition',
        'auth',
        'contenttypes',
    }

    if sender.name not in relevant_apps:
        return

    try:
        call_command('create_groups', verbosity=0)
    except Exception as e:
        print(f"Error creating groups: {str(e)}")
