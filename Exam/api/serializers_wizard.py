"""
Enhanced API Serializers for new Question Management Models
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from questions.models_new import Question_DB_New, QuestionPool, ExamTemplate
from questions.question_enhancements import QuestionTag
from course.models import Course


class QuestionTagSerializer(serializers.ModelSerializer):
    """Serializer for question tags."""
    
    class Meta:
        model = QuestionTag
        fields = ['id', 'name']


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Question_DB_New."""
    
    tags = QuestionTagSerializer(many=True, read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.user.username', read_only=True)
    
    class Meta:
        model = Question_DB_New
        fields = [
            'qno', 'question', 'optionA', 'optionB', 'optionC', 'optionD',
            'answer', 'max_marks', 'difficulty', 'tags', 'course', 'course_name',
            'faculty', 'faculty_name', 'created_at'
        ]
        read_only_fields = ['qno', 'created_at']


class QuestionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for question lists."""
    
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = Question_DB_New
        fields = ['qno', 'question', 'max_marks', 'difficulty', 'difficulty_display', 'course']
        read_only_fields = ['qno']


class QuestionPoolSerializer(serializers.ModelSerializer):
    """Serializer for QuestionPool."""
    
    questions = QuestionListSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    
    class Meta:
        model = QuestionPool
        fields = [
            'id', 'name', 'description', 'course', 'course_name',
            'questions', 'question_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_question_count(self, obj):
        return obj.question_count()


class ExamTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template lists."""
    
    course_name = serializers.CharField(source='course.name', read_only=True)
    total_marks = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamTemplate
        fields = [
            'id', 'name', 'course', 'course_name', 'total_marks',
            'question_count', 'created_at'
        ]
    
    def get_total_marks(self, obj):
        return obj.total_marks()
    
    def get_question_count(self, obj):
        return obj.questions.count()


class ExamTemplateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for ExamTemplate."""
    
    questions = QuestionListSerializer(many=True, read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    total_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamTemplate
        fields = [
            'id', 'name', 'description', 'course', 'course_name',
            'questions', 'settings', 'total_marks', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_marks(self, obj):
        return obj.total_marks()


class QuestionSelectionSerializer(serializers.Serializer):
    """Serializer for manual question selection in exam creation."""
    
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of question numbers to add to exam"
    )


class QuestionAutoGenerationSerializer(serializers.Serializer):
    """Serializer for auto-generating questions by difficulty."""
    
    easy_count = serializers.IntegerField(min_value=0, default=0)
    medium_count = serializers.IntegerField(min_value=0, default=0)
    hard_count = serializers.IntegerField(min_value=0, default=0)
    course_id = serializers.IntegerField(required=False)
    tags = serializers.ListField(child=serializers.IntegerField(), required=False)


class QuestionFilterSerializer(serializers.Serializer):
    """Serializer for filtering questions."""
    
    course_id = serializers.IntegerField(required=False)
    difficulty = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        required=False
    )
    tags = serializers.ListField(child=serializers.IntegerField(), required=False)
    search = serializers.CharField(max_length=200, required=False)


class ExamCreationRequestSerializer(serializers.Serializer):
    """Serializer for complete exam creation request."""
    
    name = serializers.CharField(max_length=100)
    course_id = serializers.IntegerField()
    question_ids = serializers.ListField(child=serializers.IntegerField())
    marks_per_question = serializers.IntegerField(min_value=1)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    shuffle_questions = serializers.BooleanField(default=True)
    show_answers = serializers.BooleanField(default=False)
    instructions = serializers.CharField(required=False, allow_blank=True)


class TemplateCloneSerializer(serializers.Serializer):
    """Serializer for cloning exam templates."""
    
    template_id = serializers.IntegerField()
    new_name = serializers.CharField(max_length=200)


class QuestionValidationResponseSerializer(serializers.Serializer):
    """Response serializer for question pool validation."""
    
    is_valid = serializers.BooleanField()
    available_count = serializers.IntegerField()
    required_count = serializers.IntegerField()
    message = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
