"""
API Serializers for all models.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from questions.models import Exam_Model, Question_DB
from questions.question_models import Question_DB as Question_Model
from student.models import StudentInfo, Stu_Question, StuExam_DB, StuResults_DB
from faculty.models import FacultyInfo


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class StudentInfoSerializer(serializers.ModelSerializer):
    """Serializer for StudentInfo model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentInfo
        fields = ['id', 'user', 'address', 'stream', 'picture']


class FacultyInfoSerializer(serializers.ModelSerializer):
    """Serializer for FacultyInfo model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = FacultyInfo
        fields = ['id', 'user', 'address', 'subject', 'picture']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question_DB model."""
    
    class Meta:
        model = Question_DB
        fields = [
            'qno', 'question', 'optionA', 'optionB', 'optionC', 'optionD',
            'answer', 'max_marks', 'category', 'difficulty', 'created_at', 'updated_at'
        ]
        read_only_fields = ['qno', 'created_at', 'updated_at']
    
    def validate_answer(self, value):
        """Validate that answer is one of the options."""
        valid_answers = ['A', 'B', 'C', 'D']
        if value.upper() not in valid_answers:
            raise serializers.ValidationError(
                f"Answer must be one of {valid_answers}"
            )
        return value.upper()


class ExamSerializer(serializers.ModelSerializer):
    """Serializer for Exam_Model."""
    
    professor_name = serializers.CharField(source='professor.username', read_only=True)
    question_count = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam_Model
        fields = [
            'id', 'name', 'total_marks', 'question_paper',
            'start_time', 'end_time', 'professor', 'professor_name',
            'question_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_question_count(self, obj):
        """Get total number of questions in exam."""
        return obj.question_paper.questions.count() if obj.question_paper else 0
    
    def get_total_marks(self, obj):
        """Get total marks from question paper."""
        return obj.question_paper.total_marks if obj.question_paper else 0


class StudentExamDetailSerializer(serializers.ModelSerializer):
    """Serializer for student exam details with questions."""
    
    questions = QuestionSerializer(many=True, read_only=True)
    professor_name = serializers.CharField(source='professor.username', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam_Model
        fields = [
            'id', 'name', 'total_marks', 'questions',
            'start_time', 'end_time', 'duration_minutes',
            'professor_name'
        ]
    
    def get_duration_minutes(self, obj):
        """Calculate exam duration in minutes."""
        if obj.start_time and obj.end_time:
            delta = obj.end_time - obj.start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def get_total_marks(self, obj):
        """Get total marks from question paper."""
        return obj.question_paper.total_marks if obj.question_paper else 0


class StudentAnswerSerializer(serializers.ModelSerializer):
    """Serializer for student answers."""
    
    question_text = serializers.CharField(source='question', read_only=True)
    
    class Meta:
        model = Stu_Question
        fields = ['qno', 'question_text', 'choice', 'answer', 'max_marks']
        read_only_fields = ['qno', 'question_text', 'answer', 'max_marks']


class StudentExamSubmissionSerializer(serializers.Serializer):
    """Serializer for exam submission."""
    
    exam_id = serializers.IntegerField()
    answers = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dict of question_text -> selected_option"
    )
    
    def validate_exam_id(self, value):
        """Validate exam exists."""
        try:
            Exam_Model.objects.get(id=value)
        except Exam_Model.DoesNotExist:
            raise serializers.ValidationError("Exam not found")
        return value


class ExamResultSerializer(serializers.ModelSerializer):
    """Serializer for exam results."""
    
    exam_name = serializers.CharField(source='examname', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)
    percentage = serializers.SerializerMethodField()
    questions = StudentAnswerSerializer(many=True, read_only=True)
    total_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = StuExam_DB
        fields = [
            'id', 'exam_name', 'student_name', 'score', 'total_marks',
            'percentage', 'completed', 'questions'
        ]
        read_only_fields = ['id', 'score', 'completed']
    
    def get_percentage(self, obj):
        """Calculate percentage score."""
        if obj.qpaper and obj.qpaper.questions.count() > 0:
            total = sum(q.max_marks for q in obj.qpaper.questions.all())
            return round((obj.score / total * 100), 2) if total > 0 else 0
        return 0
    
    def get_total_marks(self, obj):
        """Get total marks from question paper."""
        return obj.qpaper.total_marks if obj.qpaper else 0


class StudentProgressSerializer(serializers.Serializer):
    """Serializer for student progress statistics."""
    
    total_exams = serializers.IntegerField()
    completed_exams = serializers.IntegerField()
    total_score = serializers.IntegerField()
    average_score = serializers.FloatField()
    completion_percentage = serializers.FloatField()


class ExamAnalyticsSerializer(serializers.Serializer):
    """Serializer for exam analytics."""
    
    exam_name = serializers.CharField()
    total_students = serializers.IntegerField()
    attempted_students = serializers.IntegerField()
    average_score = serializers.FloatField()
    median_score = serializers.FloatField()
    highest_score = serializers.IntegerField()
    lowest_score = serializers.IntegerField()
    pass_percentage = serializers.FloatField()
    question_statistics = serializers.ListField(
        child=serializers.DictField()
    )
