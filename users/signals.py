import os

from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if sender.name == 'users':
        User = get_user_model()
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'sc@example.com')
        password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'asdASDASD123')
        print(email, password)
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password,
            )
            print("Superuser created.")
        else:
            print("Superuser already exists.")