from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

try:
    from rest_framework.authtoken.models import Token
except Exception:
    Token = None

User = get_user_model()


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create an auth token automatically when a new user is created."""
    if not created:
        return
    if Token is None:
        return
    Token.objects.get_or_create(user=instance)
