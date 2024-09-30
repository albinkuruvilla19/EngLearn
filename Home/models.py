from django.contrib.auth.models import User
from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Quiz(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_text = models.TextField()

    def __str__(self):
        return self.question_text


class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text


class UserQuizScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ('user', 'quiz')

    def __str__(self):
        return f'{self.user.username} - {self.quiz.name}: {self.score}'
    
    def is_completed(self):
        return self.score is not None

    def skillup_points(self):
        return self.score * 10


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user.username} - {self.question.question_text}: {self.selected_option.option_text}'


class Lesson(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tip = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class LessonSection(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    content = models.TextField()
    example = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} - {self.lesson.name}"

    class Meta:
        ordering = ['order']


class LessonCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')  # Ensure a user can complete a lesson only once

    def __str__(self):
        return f"{self.user.username} - {self.lesson.name} (Completed)"
    
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_login_date = models.DateField(null=True, blank=True)
    login_streak = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username
    
    def get_login_dates(self):
        # Get all login dates for the user and convert to string format
        return list(self.login_history.values_list('login_date', flat=True).order_by('login_date'))


