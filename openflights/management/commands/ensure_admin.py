from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the Django admin (superuser) using settings.ADMIN_USERNAME/ADMIN_PASSWORD."

    def handle(self, *args, **options):
        username = getattr(settings, "ADMIN_USERNAME", None)
        password = getattr(settings, "ADMIN_PASSWORD", None)

        if not username or not password:
            self.stdout.write(self.style.ERROR(
                "ADMIN_USERNAME / ADMIN_PASSWORD not set in settings.py"
            ))
            return

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "email": "",
            },
        )

        # Ensure permissions (in case user existed but wasn't staff/superuser)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated superuser '{username}' (password + flags refreshed)"))