"""
Enhanced Question Model with categories, difficulty, and versioning.
Migration to add these fields to existing Question_DB model.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class QuestionCategory(models.Model):
    """Category for organizing questions."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Question Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class QuestionDifficulty(models.TextChoices):
    """Difficulty levels for questions."""
    EASY = 'EASY', 'Easy'
    MEDIUM = 'MEDIUM', 'Medium'
    HARD = 'HARD', 'Hard'


class QuestionBloomsLevel(models.TextChoices):
    """Bloom's Taxonomy levels."""
    REMEMBER = 'REMEMBER', 'Remember'
    UNDERSTAND = 'UNDERSTAND', 'Understand'
    APPLY = 'APPLY', 'Apply'
    ANALYZE = 'ANALYZE', 'Analyze'
    EVALUATE = 'EVALUATE', 'Evaluate'
    CREATE = 'CREATE', 'Create'


class QuestionTag(models.Model):
    """Tags for questions."""
    
    name = models.CharField(max_length=50)
    
    class Meta:
        unique_together = ['name']
    
    def __str__(self):
        return self.name


class QuestionVersion(models.Model):
    """Tracks versions of questions for revision history."""
    
    question = models.OneToOneField('questions.Question_DB', on_delete=models.CASCADE, related_name='version')
    version_number = models.IntegerField(default=1)
    question_text = models.CharField(max_length=100)
    optionA = models.CharField(max_length=100)
    optionB = models.CharField(max_length=100)
    optionC = models.CharField(max_length=100)
    optionD = models.CharField(max_length=100)
    answer = models.CharField(max_length=200)
    max_marks = models.IntegerField(default=1)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateTimeField(auto_now_add=True)
    change_description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-modified_at']
    
    def __str__(self):
        return f"Question {self.question.qno} - v{self.version_number}"


class QuestionStatistics(models.Model):
    """Statistics for questions."""
    
    question = models.OneToOneField('questions.Question_DB', on_delete=models.CASCADE, related_name='statistics')
    total_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    difficulty_index = models.FloatField(default=0.5)  # 0-1, lower = harder
    discrimination_index = models.FloatField(default=0.0)  # How well it distinguishes
    last_used_in_exam = models.DateTimeField(null=True, blank=True)
    
    @property
    def effectiveness_score(self):
        """Calculate how effective this question is."""
        if self.total_attempts == 0:
            return 0
        return self.difficulty_index * abs(self.discrimination_index)
    
    class Meta:
        verbose_name_plural = "Question Statistics"
    
    def __str__(self):
        return f"Stats for Q{self.question.qno}"


# Fields to add to Question_DB (via migration):
# - category = ForeignKey(QuestionCategory)
# - difficulty = CharField(choices=QuestionDifficulty)
# - blooms_level = CharField(choices=QuestionBloomsLevel)
# - tags = ManyToManyField(QuestionTag)
# - created_at = DateTimeField(auto_now_add=True)
# - updated_at = DateTimeField(auto_now=True)
# - is_active = BooleanField(default=True)
# - explanation = TextField(blank=True) - for learning
# - reference_material = CharField(max_length=255, blank=True)
