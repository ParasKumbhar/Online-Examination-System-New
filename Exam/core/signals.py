from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Automatically create default groups (Professor and Student) after migrations.
    This signal runs whenever 'python manage.py migrate' is executed.
    """
    # Only run for the core app's migrations
    if sender.name == 'core':
        try:
            call_command('create_groups', verbosity=1)
        except Exception as e:
            print(f"Error creating groups: {str(e)}")
