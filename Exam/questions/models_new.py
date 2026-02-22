"""
New Question Management Models
Enhanced models for better question management, pooling, and exam templates.
"""

from django.db import models
from django.contrib.auth.models import User
from course.models import Course
from .question_models import Question_DB
from .question_enhancements import QuestionTag


class Question_DB_New(models.Model):
    """
    Enhanced Question model with additional fields for better organization.
    """
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]
    
    professor = models.ForeignKey(
        User, 
        limit_choices_to={'groups__name': "Professor"}, 
        on_delete=models.CASCADE, 
        null=True
    )
    question = models.CharField(max_length=500)
    optionA = models.CharField(max_length=200)
    optionB = models.CharField(max_length=200)
    optionC = models.CharField(max_length=200)
    optionD = models.CharField(max_length=200)
    answer = models.CharField(max_length=200)
    max_marks = models.IntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_questions')
    tags = models.ManyToManyField(QuestionTag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."
    
    @property
    def qno(self):
        return self.id


class QuestionPool(models.Model):
    """
    A pool of questions that can be used for generating exams.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question_DB_New, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def question_count(self):
        return self.questions.count()


class ExamTemplate(models.Model):
    """
    Template for exams with predefined question selection criteria.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question_DB_New, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def total_marks(self):
        return sum(q.max_marks for q in self.questions.all())
