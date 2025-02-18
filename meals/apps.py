from django.apps import AppConfig
import os

class MealsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meals'

    def ready(self):
        # Import inside the ready() method to avoid import issues.
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = os.environ.get("SUPERUSER_USERNAME", "admin")
        email = os.environ.get("SUPERUSER_EMAIL", "admin@example.com")
        password = os.environ.get("SUPERUSER_PASSWORD", "adminpass")

        if not User.objects.filter(username=username).exists():
            try:
                User.objects.create_superuser(username=username, email=email, password=password)
                print("Superuser created automatically.")
            except Exception as e:
                print("Error creating superuser:", e)
