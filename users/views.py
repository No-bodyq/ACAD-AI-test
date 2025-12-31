from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .serializers import UserSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow write actions only to staff users, read-only for others."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class UserViewSet(viewsets.ModelViewSet):
    """A simple ViewSet for viewing and editing users."""

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
