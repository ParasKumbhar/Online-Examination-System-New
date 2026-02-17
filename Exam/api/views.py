"""
API Views using Django REST Framework.
Implements RESTful endpoints for all modules.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Max, Min, Count
from django.core.cache import cache
from datetime import datetime, timedelta
import logging

from questions.models import Exam_Model, Question_DB
from student.models import StudentInfo, StuExam_DB, StuResults_DB, Stu_Question
from faculty.models import FacultyInfo
from .serializers import (
    UserSerializer, StudentInfoSerializer, FacultyInfoSerializer,
    QuestionSerializer, ExamSerializer, StudentExamDetailSerializer,
    ExamResultSerializer, StudentProgressSerializer, ExamAnalyticsSerializer,
    StudentExamSubmissionSerializer
)

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
    GET: List exams available to user
    POST: Create new exam (Faculty only)
    """
    
    if request.method == 'GET':
        # Cache key for user's exams
        cache_key = f'exams_list_{request.user.id}'
        exams = cache.get(cache_key)
        
        if not exams:
            if request.user.groups.filter(name='Professor').exists():
                exams = Exam_Model.objects.filter(professor=request.user)
            else:
                exams = Exam_Model.objects.all()
            
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
        exam.delete()
        logger.info(f'Exam deleted: {exam.name}')
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
            'total_marks': exam.total_marks,
            'percentage': round((score / exam.total_marks * 100), 2)
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
            sum(1 for s in scores if s >= exam.total_marks * 0.5) / len(scores) * 100,
            2
        ),
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
