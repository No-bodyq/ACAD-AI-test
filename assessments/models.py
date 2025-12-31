from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Exam(models.Model):
    title = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    course = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    MCQ = "mcq"
    TEXT = "text"
    QUESTION_TYPES = [(MCQ, "Multiple Choice"), (TEXT, "Text")]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPES, default=TEXT)
    # For MCQ: store choices as list of dicts: [{"key":"A","text":"..."}, ...]
    choices = models.JSONField(default=list, blank=True)
    # Expected answer: for MCQ a key (e.g., "A"), for TEXT a list of keywords
    expected_answer = models.JSONField(default=None, null=True, blank=True)
    points = models.FloatField(default=1.0)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Q{self.id}: {self.text[:60]}"


class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="submissions")
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded = models.BooleanField(default=False)
    grade = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["student", "exam"]) ]
       
        unique_together = ("student", "exam")

    def __str__(self):
        return f"Submission {self.id} by {self.student} for {self.exam}"


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # For MCQ store the selected key, for TEXT store submitted text
    answer_text = models.TextField(blank=True, null=True)
    selected_choice = models.CharField(max_length=64, blank=True, null=True)
    points_awarded = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("submission", "question")

    def __str__(self):
        return f"Answer to Q{self.question_id} in S{self.submission.id}"
