from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS, BasePermission
from django.shortcuts import get_object_or_404

from .models import Exam, Submission, Question, Answer
from .serializers import (
    ExamSerializer,
    SubmissionSerializer,
    SubmissionCreateSerializer,
    QuestionSerializer,
)
from . import grader


class IsAdminOrReadOnly(BasePermission):
    """Allow safe methods for anyone, restrict unsafe methods to admin users."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.prefetch_related("questions").all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrReadOnly]


class IsOwnerOrStaff:
    """Simple permission check helper used in view methods."""

    @staticmethod
    def check(request, obj):
        return request.user.is_staff or obj.student_id == request.user.id


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all().prefetch_related("answers__question")
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(student=user)

    def create(self, request, *args, **kwargs):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam_id = serializer.validated_data["exam"]
        exam = get_object_or_404(Exam, pk=exam_id)

        # create Submission
        submission = Submission.objects.create(student=request.user, exam=exam)

        total_awarded = 0.0
        total_points = 0.0

        # create Answer objects and grade
        for ans in serializer.validated_data["answers"]:
            q = get_object_or_404(Question, pk=ans["question"])
            answer = Answer.objects.create(
                submission=submission,
                question=q,
                answer_text=ans.get("answer_text"),
                selected_choice=ans.get("selected_choice"),
            )
            awarded, points = grader.grade_question(q, answer)
            answer.points_awarded = awarded
            answer.save(update_fields=["points_awarded"])
            total_awarded += awarded
            total_points += points

        # finalize submission
        submission.submitted_at = submission.started_at
        submission.graded = True
        submission.grade = round((total_awarded / total_points) * 100.0, 2) if total_points else 0.0
        submission.save(update_fields=["submitted_at", "graded", "grade"])

        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("exam").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrReadOnly]

