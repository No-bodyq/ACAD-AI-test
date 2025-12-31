from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    
    def ready(self):
        # Import signal handlers to ensure they are registered
        try:
            import users.signals  # noqa: F401
        except Exception:
            pass
 