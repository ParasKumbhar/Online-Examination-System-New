"""
API URL Configuration.
Versioned REST API endpoints.
"""

from django.urls import path
from . import views

# API v1 endpoints
app_name = 'api'

urlpatterns = [
    # Exam endpoints
    path('v1/exams/', views.exam_list_create, name='exam-list-create'),
    path('v1/exams/<int:exam_id>/', views.exam_detail, name='exam-detail'),
    path('v1/exams/<int:exam_id>/submit/', views.exam_submit, name='exam-submit'),
    path('v1/exams/<int:exam_id>/results/', views.exam_results, name='exam-results'),
    path('v1/exams/<int:exam_id>/analytics/', views.exam_analytics, name='exam-analytics'),
    
    # Student endpoints
    path('v1/student/progress/', views.student_progress, name='student-progress'),
    
    # Question endpoints
    path('v1/questions/', views.questions_list, name='questions-list'),
    path('v1/questions/create/', views.questions_create, name='questions-create'),
]
