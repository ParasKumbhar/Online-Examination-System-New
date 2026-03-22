"""
API URL Configuration.
Versioned REST API endpoints.
"""

from django.urls import path
from . import views

# API v1 endpoints
app_name = 'api'

urlpatterns = [
    # Auth endpoints
    path('v1/auth/login/', views.api_login, name='api-login'),
    path('v1/auth/otp/request/', views.otp_request, name='otp-request'),
    path('v1/auth/otp/verify/', views.otp_verify, name='otp-verify'),
    path('v1/auth/audits/', views.login_audits, name='login-audits'),
    
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

    # Anti-Cheating endpoints
    path('v1/exams/<int:exam_id>/focus-loss/', views.record_focus_loss, name='record-focus-loss'),
    path('v1/exams/<int:exam_id>/fullscreen-exit/', views.record_fullscreen_exit, name='fullscreen-exit'),
    path('v1/exams/<int:exam_id>/focus-status/', views.get_focus_status, name='focus-status'),
    path('v1/exams/<int:exam_id>/validate-timestamp/', views.validate_submission_timestamp, name='validate-timestamp'),

    # Exam Assignment endpoints
    path('v1/exams/<int:exam_id>/assignments/', views.manage_exam_assignments, name='manage-assignments'),

    # Question search and management
    path('v1/questions/search/', views.search_questions, name='search-questions'),
    path('v1/questions/export-csv/', views.export_questions_csv, name='export-csv'),
    path('v1/questions/import-csv/', views.import_questions_csv, name='import-csv'),
]
