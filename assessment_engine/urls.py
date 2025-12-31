"""
URL configuration for assessment_engine project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

# Import viewsets to register on a single root router (avoids DRF converter re-registration)
from users.views import UserViewSet
from assessments.views import ExamViewSet, SubmissionViewSet, QuestionViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"submissions", SubmissionViewSet, basename="submission")
router.register(r"questions", QuestionViewSet, basename="question")

urlpatterns = [
    path("admin/", admin.site.urls),
    # API routes
    path("api/", include(router.urls)),
    # OpenAPI schema (basic)
    path("openapi/", get_schema_view(title="Acad AI Mini Assessment API"), name="openapi-schema"),
    path(
        "docs/",
        TemplateView.as_view(
            template_name="drf_docs.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]
