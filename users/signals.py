from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser
from clients.models import Client
from trainers.models import Trainer


@receiver(post_save, sender=CustomUser)
def create_client_for_user(sender, instance, created, **kwargs):
    """
    Signal to create a Client and Trainer instance if the User instance has
    no related Client and Trainer.
    """
    if created:
        Client.objects.get_or_create(user=instance)
        Trainer.objects.get_or_create(
            user=instance,
            is_active=instance.is_trainer,
        )
