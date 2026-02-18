import os
import django
import sys

# Ensure project root (Exam/) is on sys.path so Django can import project settings
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examProject.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

User = get_user_model()

username = 'test_student'
password = 'Testpass1234'

def ensure_user():
    user, created = User.objects.get_or_create(username=username, defaults={'email':'test@example.com'})
    if created:
        user.set_password(password)
        user.is_active = True
        user.save()
    # ensure Student group
    grp, _ = Group.objects.get_or_create(name='Student')
    grp.user_set.add(user)
    return user


def run():
    user = ensure_user()
    client = Client()
    logged_in = client.login(username=username, password=password)
    print('Logged in:', logged_in)
    resp = client.get('/student/')
    print('Status code:', resp.status_code)
    content = resp.content.decode('utf-8')
    if 'Please log in to view menu.' in content:
        print('ERROR: Sidebar still shows login prompt for authenticated user')
    else:
        print('OK: Sidebar does not show login prompt')
    # show a small snippet
    start = content.find('<aside')
    end = content.find('</aside>')
    if start != -1 and end != -1:
        print(content[start:end+8])

if __name__ == '__main__':
    run()
