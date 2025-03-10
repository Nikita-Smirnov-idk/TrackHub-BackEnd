import os
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.conf import settings
from workout_manager.models import UserWorkoutManagerLimitation

@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if sender.name == 'users':
        User = get_user_model()
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'sc@example.com')
        password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'asdASDASD123')
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name="admin",
            )
            print("Superuser created.")
        else:
            print("Superuser already exists.")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_workout_manager_limitation(sender, instance, created, **kwargs):
    if created:
        UserWorkoutManagerLimitation.objects.create(user=instance)

