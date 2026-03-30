"""
API Views using Django REST Framework.
Implements RESTful endpoints for all modules.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib import auth
from django.db.models import Q, Avg, Max, Min, Count
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import logging


from questions.models import Exam_Model
from questions.question_models import Question_DB
from student.models import StudentInfo, StuExam_DB, StuResults_DB, Stu_Question
from faculty.models import FacultyInfo
from .serializers import (
    UserSerializer, StudentInfoSerializer, FacultyInfoSerializer,
    QuestionSerializer, ExamSerializer, StudentExamDetailSerializer,
    ExamResultSerializer, StudentProgressSerializer, ExamAnalyticsSerializer,
    StudentExamSubmissionSerializer
)
from .serializers_security import (
    LoginSerializer, OTPRequestSerializer, OTPVerifySerializer,
    LoginAuditSerializer, JWTSerializer
)
from core.two_factor_auth import OTPGenerator, TwoFactorAuth
from core.two_factor_auth import TwoFactorAuth
from core.models import LoginAudit, AuditLog


logger = logging.getLogger('app')


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsStudent(permissions.BasePermission):
    """Permission to check if user is student."""
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Student').exists()


class IsFaculty(permissions.BasePermission):
    """Permission to check if user is faculty."""
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Professor').exists()


class IsAdmin(permissions.BasePermission):
    """Permission to check if user is admin."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ==================== EXAM ENDPOINTS ====================

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def exam_list_create(request):
    """
    List exams or create new exam.
    GET: List exams available to user (respects exam assignments)
    POST: Create new exam (Faculty only)
    """

    if request.method == 'GET':
        from questions.exam_assignment_models import ExamAssignment

        # Cache key for user's exams
        cache_key = f'exams_list_{request.user.id}'
        exams = cache.get(cache_key)

        if not exams:
            if request.user.groups.filter(name='Professor').exists():
                # Professors see their own exams
                exams = Exam_Model.objects.filter(professor=request.user)
            else:
                # Students see only assigned exams
                all_exams = Exam_Model.objects.all()
                exams = [exam for exam in all_exams if ExamAssignment.is_exam_assigned_to_student(exam, request.user)]

            # Cache for 5 minutes
            cache.set(cache_key, exams, 300)

        serializer = ExamSerializer(exams, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.groups.filter(name='Professor').exists():
            return Response(
                {'error': 'Only faculty can create exams'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(professor=request.user)
            logger.info(f'Exam created: {serializer.data["name"]} by {request.user}')
            
            # Invalidate cache
            cache.delete(f'exams_list_{request.user.id}')
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def exam_detail(request, exam_id):
    """
    Retrieve, update, or delete an exam.
    """
    
    try:
        exam = Exam_Model.objects.get(id=exam_id)
    except Exam_Model.DoesNotExist:
        return Response(
            {'error': 'Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions
    if request.method in ['PUT', 'DELETE']:
        if exam.professor != request.user:
            return Response(
                {'error': 'You can only modify your own exams'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    if request.method == 'GET':
        # For students, show exam details with questions
        if request.user.groups.filter(name='Student').exists():
            serializer = StudentExamDetailSerializer(exam)
        else:
            serializer = ExamSerializer(exam)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ExamSerializer(exam, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f'Exam updated: {exam.name}')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        from student.models import StuExam_DB
        StuExam_DB.objects.filter(examname=exam.name, qpaper=exam.question_paper).delete()
        exam.is_active = False
        exam.save()
        logger.info(f'Exam deactivated and student records reset: {exam.name}')
        cache.delete(f'exams_list_{request.user.id}')
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def exam_submit(request, exam_id):
    """
    Submit exam answers.
    
    Request body:
    {
        "answers": {
            "question_text_1": "A",
            "question_text_2": "B",
            ...
        }
    }
    """
    
    try:
        exam = Exam_Model.objects.get(id=exam_id)
    except Exam_Model.DoesNotExist:
        return Response(
            {'error': 'Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if student already submitted
    if StuExam_DB.objects.filter(
        examname=exam.name,
        student=request.user,
        completed=1
    ).exists():
        return Response(
            {'error': 'You have already submitted this exam'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate exam timing
    now = datetime.now()
    if now < exam.start_time:
        return Response(
            {'error': 'Exam has not started yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if now > exam.end_time:
        return Response(
            {'error': 'Exam time has expired'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get total marks from question paper
    total_marks = exam.question_paper.total_marks if exam.question_paper else 0
    
    # Process submission
    answers = request.data.get('answers', {})
    student = request.user
    
    try:
        # Create or update exam submission
        stu_exam, created = StuExam_DB.objects.get_or_create(
            examname=exam.name,
            student=student,
            qpaper=exam.question_paper
        )
        
        # Calculate score
        score = 0
        for question in exam.question_paper.questions.all():
            provided_answer = answers.get(question.question, 'E')
            
            if provided_answer.upper() == question.answer.upper():
                score += question.max_marks
        
        # Save submission
        stu_exam.score = score
        stu_exam.completed = 1
        stu_exam.save()
        
        # Add to results
        results, _ = StuResults_DB.objects.get_or_create(student=student)
        results.exams.add(stu_exam)
        
        logger.info(f'Exam submitted: {exam.name} by {student} with score {score}')
        
        return Response({
            'success': True,
            'message': 'Exam submitted successfully',
            'score': score,
            'total_marks': total_marks,
            'percentage': round((score / total_marks * 100), 2) if total_marks > 0 else 0
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error submitting exam: {str(e)}')
        return Response(
            {'error': 'Failed to submit exam'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== RESULTS ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def exam_results(request, exam_id):
    """
    Get results for a specific exam.
    Students see their own results, Faculty see all students' results.
    """
    
    try:
        exam = Exam_Model.objects.get(id=exam_id)
    except Exam_Model.DoesNotExist:
        return Response(
            {'error': 'Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get results
    results = StuExam_DB.objects.filter(examname=exam.name, completed=1)
    
    # Filter for students (only their results)
    if request.user.groups.filter(name='Student').exists():
        results = results.filter(student=request.user)
    elif request.user.groups.filter(name='Professor').exists():
        # Faculty only sees their own exams' results
        results = results.filter(student__in=exam.question_paper.professor.user_set.all())
    
    serializer = ExamResultSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def student_progress(request):
    """
    Get student's progress statistics.
    """
    
    # Try to get from cache
    cache_key = f'student_progress_{request.user.id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    # Get stats
    total_exams = Exam_Model.objects.count()
    student_exams = StuExam_DB.objects.filter(student=request.user)
    completed_exams = student_exams.filter(completed=1).count()
    total_score = student_exams.aggregate(Sum=0)['Sum'] or 0
    
    if completed_exams > 0:
        average_score = total_score / completed_exams
    else:
        average_score = 0
    
    completion_percentage = (completed_exams / total_exams * 100) if total_exams > 0 else 0
    
    data = {
        'total_exams': total_exams,
        'completed_exams': completed_exams,
        'total_score': total_score,
        'average_score': round(average_score, 2),
        'completion_percentage': round(completion_percentage, 2),
    }
    
    # Cache for 10 minutes
    cache.set(cache_key, data, 600)
    
    serializer = StudentProgressSerializer(data)
    return Response(serializer.data)


# ==================== ANALYTICS ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def exam_analytics(request, exam_id):
    """
    Get detailed analytics for an exam.
    Only faculty can access.
    """
    
    try:
        exam = Exam_Model.objects.get(id=exam_id, professor=request.user)
    except Exam_Model.DoesNotExist:
        return Response(
            {'error': 'Exam not found or access denied'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Try cache
    cache_key = f'exam_analytics_{exam_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    # Get all submissions
    submissions = StuExam_DB.objects.filter(examname=exam.name, completed=1)
    
    if not submissions.exists():
        return Response({'error': 'No submissions yet'})
    
    # Get total marks from question paper
    total_marks = exam.question_paper.total_marks if exam.question_paper else 0
    
    # Calculate statistics
    scores = list(submissions.values_list('score', flat=True))
    
    data = {
        'exam_name': exam.name,
        'total_students': User.objects.filter(groups__name='Student').count(),
        'attempted_students': submissions.count(),
        'average_score': round(sum(scores) / len(scores), 2),
        'median_score': sorted(scores)[len(scores) // 2],
        'highest_score': max(scores),
        'lowest_score': min(scores),
        'pass_percentage': round(
            sum(1 for s in scores if s >= total_marks * 0.5) / len(scores) * 100,
            2
        ) if total_marks > 0 else 0,
        'question_statistics': []
    }
    
    # Question-wise analysis
    for question in exam.question_paper.questions.all():
        correct_count = Stu_Question.objects.filter(
            question=question.question,
            choice__iexact=question.answer
        ).count()
        
        data['question_statistics'].append({
            'question': question.question[:50],
            'correct_answers': correct_count,
            'accuracy_percentage': round(correct_count / submissions.count() * 100, 2)
        })
    
    # Cache for 30 minutes
    cache.set(cache_key, data, 1800)
    
    serializer = ExamAnalyticsSerializer(data)
    return Response(serializer.data)


# ==================== QUESTION ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def questions_list(request):
    """
    List all questions created by faculty.
    """
    
    cache_key = f'faculty_questions_{request.user.id}'
    questions = cache.get(cache_key)
    
    if not questions:
        questions = Question_DB.objects.filter(professor=request.user)
        cache.set(cache_key, questions, 600)
    
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(questions, request)
    if page is not None:
        serializer = QuestionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def questions_create(request):
    """
    Create a new question.
    """
    
    serializer = QuestionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(professor=request.user)
        logger.info(f'Question created by {request.user}')
        
        # Invalidate cache
        cache.delete(f'faculty_questions_{request.user.id}')
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== AUTHENTICATION & 2FA ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Step 1: Validate credentials and initiate 2FA.
    POST /api/v1/auth/login/
    
    Request:
    {
        "username": "user@example.com or username",
        "password": "password"
    }
    
    Response (Success):
    {
        "requires_2fa": true,
        "session_id": "unique-session-id",
        "message": "Credentials verified. OTP sent to your email.",
        "email": "user@example.com"
    }
    
    CRITICAL: User MUST verify OTP before accessing dashboard.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create audit log for successful credential verification
        audit = LoginAudit.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=request.data.get('device_fingerprint', ''),
            success=True,
            suspicious=False,
        )
        
        # Create OTP session (Email OTP ONLY)
        session_result = TwoFactorAuth.create_otp_session(
            user_email=user.email,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=request.data.get('device_fingerprint', ''),
        )
        
        if not session_result['success']:
            return Response({
                'error': session_result['message'],
                'success': False,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        session_id = session_result['session_id']
        
        # Send OTP email
        email_result = TwoFactorAuth.send_email_otp(
            session_id=session_id,
            user_email=user.email,
            user_name=user.get_full_name() or user.username,
        )
        
        if not email_result['success']:
            return Response({
                'error': 'Failed to send OTP email. Please try again.',
                'success': False,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f'OTP session created for user {user.username} from IP {ip_address}')
        
        return Response({
            'requires_2fa': True,
            'session_id': session_id,
            'message': 'Credentials verified. OTP sent to your email.',
            'email': user.email,
            'expires_in_minutes': session_result.get('expires_in_minutes', 3),
            'otp': session_result.get('otp'),  # Only for DEBUG mode
        }, status=status.HTTP_202_ACCEPTED)
    
    # Log failed attempt
    ip_address = get_client_ip(request)
    AuditLog.objects.create(
        user=None,
        action='LOGIN_FAILED',
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        success=False,
        details={'error': 'Invalid credentials'},
    )
    
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_request(request):
    """
    Step 2a: Request Resend OTP.
    POST /api/v1/auth/otp/request/
    
    Allows user to resend OTP if not received, with rate limiting.
    
    Request:
    {
        "session_id": "unique-session-id"
    }
    
    Response (Success):
    {
        "success": true,
        "message": "OTP resent to your email",
        "expires_in_minutes": 3,
        "otp": "123456" (DEBUG only)
    }
    
    Rate Limiting: 1 resend per 30 seconds
    """
    
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({
            'error': 'session_id required',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from core.models import OTPSession
        
        session = OTPSession.objects.get(session_id=session_id, is_active=True)
        user_email = session.user_email
        
        # Resend OTP with rate limiting
        result = TwoFactorAuth.resend_otp(session_id, user_email)
        
        # Audit log
        AuditLog.objects.create(
            user=session.user,
            action='OTP_RESEND',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=result['success'],
            details={'session_id': session_id, 'resend_count': session.resend_count + 1}
        )
        
        if result['success']:
            return Response({
                'success': True,
                'message': result['message'],
                'expires_in_minutes': result.get('expires_in_minutes', 3),
                'otp': result.get('otp'),  # DEBUG only
                'resend_count': result.get('resend_count', 1)
            }, status=status.HTTP_200_OK)
        
        # Rate limit or other error
        return Response({
            'success': False,
            'error': result['message'],
            'seconds_remaining': result.get('seconds_remaining'),
        }, status=status.HTTP_429_TOO_MANY_REQUESTS if 'wait' in result['message'].lower() else status.HTTP_400_BAD_REQUEST)
    
    except OTPSession.DoesNotExist:
        return Response({
            'error': 'Session not found. Please login again.',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error in otp_request: {str(e)}')
        return Response({
            'error': 'OTP resend failed',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_verify(request):
    """
    Step 2b: Verify OTP and Issue JWT Tokens.
    POST /api/v1/auth/otp/verify/
    
    CRITICAL: This is the ONLY way to get JWT tokens after login.
    Dashboard access is impossible without this step.
    
    Request:
    {
        "session_id": "unique-session-id",
        "otp": "123456"
    }
    
    Response (Success):
    {
        "success": true,
        "message": "OTP verified successfully",
        "access": "jwt-access-token",
        "refresh": "jwt-refresh-token",
        "user": {
            "id": 1,
            "username": "student1",
            "email": "student@example.com"
        }
    }
    
    Response (Invalid):
    {
        "error": "Invalid OTP. 4 attempts remaining.",
        "attempts_remaining": 4
    }
    
    Security Features:
    - Validates session exists and is active
    - Checks OTP expiry
    - Enforces retry limit (5 attempts max)
    - Rejects reused/expired OTPs
    - Clears OTP from cache after verification
    - Links OTP verification to specific login attempt
    """
    
    session_id = request.data.get('session_id')
    otp = request.data.get('otp')
    
    if not session_id or not otp:
        return Response({
            'error': 'session_id and otp required',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from core.models import OTPSession
        
        # Verify OTP
        ip_address = get_client_ip(request)
        result = TwoFactorAuth.verify_otp(session_id, otp, ip_address)
        
        if not result['valid']:
            # Log failed attempt
            AuditLog.objects.create(
                user=None,
                action='OTP_VERIFY_FAILED',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=False,
                details={
                    'session_id': session_id,
                    'reason': result.get('reason', 'UNKNOWN'),
                    'attempts_remaining': result.get('attempts_remaining'),
                }
            )
            
            return Response({
                'error': result['message'],
                'reason': result.get('reason'),
                'attempts_remaining': result.get('attempts_remaining'),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP verified successfully
        user = result['user']
        session = result['session']
        
        # Log successful verification
        AuditLog.objects.create(
            user=user,
            action='OTP_VERIFIED',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True,
            details={'session_id': session_id}
        )
        
        # Establish Django session (allows browser navigation without JWT headers)
        auth.login(request, user)
        
        # Generate JWT tokens (ONLY after OTP verification)
        refresh = JWTSerializer.get_token(user)
        
        logger.info(f'2FA successful for user {user.username} from IP {ip_address}')
        
        return Response({
            'success': True,
            'message': 'OTP verified successfully. Logging in...',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'groups': [g.name for g in user.groups.all()],
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f'Error verifying OTP: {str(e)}', exc_info=True)
        return Response({
            'error': 'OTP verification failed',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def login_audits(request):
    """
    List recent login audits.
    GET /api/v1/auth/audits/
    """
    audits = LoginAudit.objects.all()[:100]  # Last 100
    serializer = LoginAuditSerializer(audits, many=True)
    return Response(serializer.data)


# ==================== ANTI-CHEATING ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def record_focus_loss(request, exam_id):
    """
    Record a focus loss event (tab switch, window blur, etc.)

    Request body:
    {
        "event_type": "TAB_SWITCH" | "WINDOW_BLUR" | "VISIBILITY",
        "browser_timestamp": "2026-03-10T10:30:45.123Z"
    }
    """

    try:
        from questions.anticheating_models import ExamFocusLog, FocusLossEvent

        exam = Exam_Model.objects.get(id=exam_id)

        # Check if exam is still active
        now = timezone.now()
        if now > exam.end_time:
            return Response(
                {'error': 'Exam has ended', 'action': 'submit_immediately'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create focus log
        focus_log, created = ExamFocusLog.objects.get_or_create(
            student=request.user,
            exam=exam
        )

        # Record the event
        event_type = request.data.get('event_type', 'TAB_SWITCH')
        browser_timestamp = request.data.get('browser_timestamp')

        FocusLossEvent.objects.create(
            student=request.user,
            exam=exam,
            event_type=event_type,
            browser_timestamp=browser_timestamp,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # Update focus loss count
        focus_log.record_focus_loss()

        # Update related exam session
        from questions.anticheating_models import ExamSession
        exam_session = ExamSession.objects.filter(student=request.user, exam=exam).first()
        if exam_session:
            exam_session.record_tab_switch()

        # Send immediate alert email when count increases
        try:
            send_mail(
                subject=f"[Security Alert] {exam.name}: Tab switches detected ({focus_log.focus_loss_count})",
                message=(
                    f"Student: {request.user.get_full_name() or request.user.username}\n"
                    f"Exam: {exam.name}\n"
                    f"Tab switches: {focus_log.focus_loss_count}\n"
                    f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[exam.professor.email],
                fail_silently=True
            )
        except Exception as email_err:
            logger.error(f"Cheating alert email failed: {email_err}")

        response_data = {
            'success': True,
            'focus_loss_count': focus_log.focus_loss_count,
            'max_allowed': focus_log.max_focus_losses,
            'exceeded': focus_log.exceeded_max_losses()
        }

        # Show warnings after each switch
        if focus_log.focus_loss_count > 0:
            response_data['warning'] = f'Warning: You have switched tabs {focus_log.focus_loss_count} time(s). Maximum allowed: {focus_log.max_focus_losses}. (Faculty will be notified at >=5)'

        # At the threshold (5): fire alert & auto-submit
        if focus_log.focus_loss_count >= focus_log.max_focus_losses:
            response_data['action'] = 'submit_immediately'
            response_data['summary'] = 'Threshold reached: exam auto-submitting.'

            if focus_log.focus_loss_count == focus_log.max_focus_losses:
                try:
                    send_mail(
                        subject=f"[Cheating Alert] {exam.name}: {request.user.username} switched tabs {focus_log.focus_loss_count} times",
                        message=(
                            f"Student: {request.user.get_full_name() or request.user.username}\n"
                            f"Exam: {exam.name}\n"
                            f"Tab switches: {focus_log.focus_loss_count}\n"
                            f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[exam.professor.email],
                        fail_silently=True
                    )
                except Exception as email_err:
                    logger.error(f"Cheating alert email failed: {email_err}")

            # Auto-submit on suspicion
            session = ExamSession.objects.filter(student=request.user, exam=exam).first()
            if session and not session.is_submitted:
                session.mark_submitted()
                stu, _ = StuExam_DB.objects.get_or_create(
                    student=request.user,
                    examname=exam.name,
                    qpaper=exam.question_paper,
                    defaults={'completed':1,'score':0}
                )
                stu.completed = 1
                stu.score = stu.score or 0
                stu.save()
                results = StuResults_DB.objects.get_or_create(student=request.user)[0]
                results.exams.add(stu)

        logger.warning(
            f'Focus loss recorded: {request.user.username} in exam {exam.name} '
            f'(count: {focus_log.focus_loss_count}, type: {event_type})'
        )

        return Response(response_data, status=status.HTTP_200_OK)

    except Exam_Model.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error recording focus loss: {str(e)}')
        return Response({'error': 'Failed to record focus loss'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def record_fullscreen_exit(request, exam_id):
    """Record fullscreen exit event and log suspicious activity."""
    try:
        exam = Exam_Model.objects.get(id=exam_id)
        now = timezone.now()
        if now > exam.end_time:
            return Response({'error': 'Exam has ended', 'action': 'submit_immediately'}, status=status.HTTP_400_BAD_REQUEST)

        from questions.anticheating_models import ExamSession, ExamSecurityAlert

        session = ExamSession.objects.filter(student=request.user, exam=exam).first()
        if not session:
            session = ExamSession.objects.create(
                student=request.user,
                exam=exam,
                duration_seconds=int((exam.end_time - exam.start_time).total_seconds()),
                ends_at=exam.end_time,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        session.record_fullscreen_exit()

        send_mail(
            subject=f"[Security Alert] {exam.name}: Fullscreen exit #{session.fullscreen_exit_count}",
            message=(
                f"Student: {request.user.get_full_name() or request.user.username}\n"
                f"Exam: {exam.name}\n"
                f"Fullscreen exits: {session.fullscreen_exit_count}\n"
                f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[exam.professor.email],
            fail_silently=True
        )

        response = {
            'success': True,
            'fullscreen_exit_count': session.fullscreen_exit_count,
            'exceeded': session.fullscreen_exit_count >= 3
        }

        if session.fullscreen_exit_count >= 3:
            response['action'] = 'review_or_autosubmit'
            ExamSecurityAlert.objects.create(
                student=request.user,
                exam=exam,
                alert_type='FULLSCREEN_EXIT',
                level='WARNING',
                message='Repeated fullscreen exits detected.'
            )

        return Response(response, status=status.HTTP_200_OK)

    except Exam_Model.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error recording fullscreen exit: {str(e)}')
        return Response({'error': 'Failed to record fullscreen exit'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def get_focus_status(request, exam_id):
    """
    Get current focus loss status for student during exam
    """

    try:
        from questions.anticheating_models import ExamFocusLog

        exam = Exam_Model.objects.get(id=exam_id)

        focus_log = ExamFocusLog.objects.filter(
            student=request.user,
            exam=exam
        ).first()

        if not focus_log:
            return Response({
                'focus_loss_count': 0,
                'max_allowed': 3,
                'exceeded': False
            })

        return Response({
            'focus_loss_count': focus_log.focus_loss_count,
            'max_allowed': focus_log.max_focus_losses,
            'exceeded': focus_log.exceeded_max_losses(),
            'reason': focus_log.reason if focus_log.is_suspicious else None
        })

    except Exam_Model.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error getting focus status: {str(e)}')
        return Response({'error': 'Failed to get focus status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def validate_submission_timestamp(request, exam_id):
    """
    Validate that submission timestamp is legitimate (prevents timer manipulation)

    Request body:
    {
        "submission_time_client": "2026-03-10T10:35:45.123Z"
    }
    """

    try:
        from questions.anticheating_models import ServerTimestampValidator

        exam = Exam_Model.objects.get(id=exam_id)
        submission_time = request.data.get('submission_time_client')

        if not submission_time:
            return Response(
                {'error': 'submission_time_client is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_valid, message = ServerTimestampValidator.validate_submission_time(
            request.user,
            exam,
            submission_time
        )

        return Response({
            'valid': is_valid,
            'message': message
        }, status=status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST)

    except Exam_Model.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Error validating timestamp: {str(e)}')
        return Response({'error': 'Validation error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==================== EXAM ASSIGNMENT ENDPOINTS ====================

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def manage_exam_assignments(request, exam_id):
    """
    Manage exam assignments for a specific exam.
    GET: List all assignments for exam
    POST: Create new assignment
    DELETE: Remove assignment
    """

    try:
        from questions.exam_assignment_models import ExamAssignment

        exam = Exam_Model.objects.get(id=exam_id, professor=request.user)

        if request.method == 'GET':
            assignments = ExamAssignment.objects.filter(exam=exam, is_active=True)
            data = []
            for assignment in assignments:
                data.append({
                    'id': assignment.id,
                    'exam': assignment.exam.name,
                    'type': assignment.assignment_type,
                    'student': assignment.student.username if assignment.student else None,
                    'batch': assignment.batch_name,
                    'created_at': assignment.created_at.isoformat()
                })
            return Response(data)

        elif request.method == 'POST':
            assignment_type = request.data.get('assignment_type', 'public')
            student_id = request.data.get('student_id')
            batch_name = request.data.get('batch_name')

            if assignment_type == 'individual' and not student_id:
                return Response(
                    {'error': 'student_id is required for individual assignments'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if assignment_type == 'batch' and not batch_name:
                return Response(
                    {'error': 'batch_name is required for batch assignments'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                student = User.objects.get(id=student_id) if student_id else None
            except User.DoesNotExist:
                return Response(
                    {'error': 'Student not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            assignment = ExamAssignment.objects.create(
                exam=exam,
                assignment_type=assignment_type,
                student=student,
                batch_name=batch_name or ''
            )

            logger.info(f"Exam assignment created: {exam.name} - {assignment_type}")

            return Response({
                'id': assignment.id,
                'message': f'Assignment created successfully ({assignment_type})'
            }, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            assignment_id = request.data.get('assignment_id')
            if not assignment_id:
                return Response(
                    {'error': 'assignment_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                assignment = ExamAssignment.objects.get(id=assignment_id, exam=exam)
                assignment.deactivate()
                logger.info(f"Exam assignment deactivated: {exam.name}")
                return Response({'message': 'Assignment deactivated successfully'})
            except ExamAssignment.DoesNotExist:
                return Response(
                    {'error': 'Assignment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    except Exam_Model.DoesNotExist:
        return Response(
            {'error': 'Exam not found or access denied'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error managing exam assignments: {str(e)}')
        return Response(
            {'error': 'Failed to manage assignments'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== QUESTION SEARCH & MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def search_questions(request):
    """
    Search questions by text, difficulty, or other criteria.

    Query parameters:
    - q: Search text (searches in question text and options)
    - difficulty: Filter by difficulty (easy, medium, hard)
    - min_marks: Minimum marks
    - max_marks: Maximum marks
    """

    try:
        from django.db.models import Q

        search_query = request.query_params.get('q', '')
        difficulty = request.query_params.get('difficulty', '')
        min_marks = request.query_params.get('min_marks')
        max_marks = request.query_params.get('max_marks')

        # Base query: only professor's questions
        questions = Question_DB.objects.filter(professor=request.user)

        # Text search
        if search_query:
            questions = questions.filter(
                Q(question__icontains=search_query) |
                Q(optionA__icontains=search_query) |
                Q(optionB__icontains=search_query) |
                Q(optionC__icontains=search_query) |
                Q(optionD__icontains=search_query)
            )

        # Difficulty filter
        if difficulty in ['easy', 'medium', 'hard']:
            questions = questions.filter(difficulty=difficulty)

        # Marks filter
        if min_marks:
            try:
                questions = questions.filter(max_marks__gte=int(min_marks))
            except ValueError:
                pass

        if max_marks:
            try:
                questions = questions.filter(max_marks__lte=int(max_marks))
            except ValueError:
                pass

        serializer = QuestionSerializer(questions, many=True)
        return Response({
            'count': questions.count(),
            'results': serializer.data
        })

    except Exception as e:
        logger.error(f'Error searching questions: {str(e)}')
        return Response({'error': 'Search failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def export_questions_csv(request):
    """
    Export all professor's questions to CSV file.

    Returns: CSV file download
    """

    try:
        from questions.enhanced_question_models import QuestionCSVImporter
        from django.http import HttpResponse

        success, result = QuestionCSVImporter.export_to_csv(request.user)

        if not success:
            return Response({'error': 'Export failed: ' + result}, status=status.HTTP_400_BAD_REQUEST)

        # Return CSV file
        with open(result, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{result}"'
            return response

    except Exception as e:
        logger.error(f'Error exporting questions: {str(e)}')
        return Response({'error': 'Export failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsFaculty])
def import_questions_csv(request):
    """
    Import questions from CSV upload.

    CSV format:
    Question Text,Option A,Option B,Option C,Option D,Correct Answer,Max Marks,Difficulty

    Example:
    What is 2+2?,3,4,5,6,B,1,easy
    """

    try:
        from questions.enhanced_question_models import QuestionCSVImporter
        import io

        if 'file' not in request.FILES:
            return Response({'error': 'CSV file is required'}, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES['file']

        # Validate file is CSV
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV file'}, status=status.HTTP_400_BAD_REQUEST)

        # Read CSV
        csv_data = io.TextIOWrapper(csv_file.file, encoding='utf-8')
        imported_count, errors = QuestionCSVImporter.import_from_csv(request.user, csv_data)

        return Response({
            'imported': imported_count,
            'errors': errors,
            'error_count': len(errors),
            'success': len(errors) == 0
        })

    except Exception as e:
        logger.error(f'Error importing questions: {str(e)}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
