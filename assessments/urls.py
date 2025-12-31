from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"submissions", SubmissionViewSet, basename="submission")

urlpatterns = [path("", include(router.urls))]
