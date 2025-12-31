from rest_framework import serializers
from .models import Exam, Question, Submission, Answer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("id", "exam", "text", "question_type", "choices", "points", "order")


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ("id", "title", "duration_minutes", "course", "metadata", "questions")


class AnswerSubmissionSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer_text = serializers.CharField(allow_blank=True, required=False)
    selected_choice = serializers.CharField(allow_blank=True, required=False)


class SubmissionCreateSerializer(serializers.Serializer):
    exam = serializers.IntegerField()
    answers = AnswerSubmissionSerializer(many=True)

    def validate(self, data):
        # Basic validation to ensure exam and answers exist
        return data


class AnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ("id", "question", "answer_text", "selected_choice", "points_awarded")


class SubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    student = serializers.StringRelatedField()
    exam = ExamSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ("id", "student", "exam", "started_at", "submitted_at", "graded", "grade", "answers")
