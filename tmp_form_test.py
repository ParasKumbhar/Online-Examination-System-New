import os, sys
from datetime import datetime

# Setup Django env
sys.path.append(r'd:/Paras/College/Final Project/Online-Examination-System/Exam')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examProject.settings')

import django

django.setup()

from django.utils import timezone
from questions.models import ExamForm, Exam_Model
from django.contrib.auth.models import User
from questions.questionpaper_models import Question_Paper

# Prepare dummy objects
user = User(username='dummy')
qp = Question_Paper(id=1, qPaperTitle='Dummy', professor=user)
# original exam stored at 2026-03-09 19:30 local
orig_start = timezone.make_aware(datetime(2026,3,9,19,30))
orig_end = timezone.make_aware(datetime(2026,3,9,20,30))
exam = Exam_Model(pk=1, professor=user, name='Test', question_paper=qp, start_time=orig_start, end_time=orig_end)

# Simulate form submission editing exam to new start/end
post_data = {
    'name': 'Test',
    'question_paper': str(qp.id),
    'start_time': '2026-03-10T20:00',
    'end_time': '2026-03-10T21:00',
}

form = ExamForm(user, post_data, instance=exam)
print('is_valid:', form.is_valid())
print('errors:', form.errors)
if form.is_valid():
    updated = form.save(commit=False)
    print('updated start_time:', updated.start_time)
    print('updated end_time:', updated.end_time)
    # simulate save
    updated.save = lambda *args, **kwargs: print('save called')
    form.save_m2m()

# show cleaned_data for datetime fields
print('cleaned start_time:', form.cleaned_data.get('start_time'))
print('cleaned end_time:', form.cleaned_data.get('end_time'))
