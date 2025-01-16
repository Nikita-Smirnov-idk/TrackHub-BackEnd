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
        if not instance.is_trainer:
            Client.objects.get_or_create(
                is_active=(not instance.is_trainer),
                user=instance,
            )
        if instance.is_trainer:
            Trainer.objects.get_or_create(
                user=instance,
                is_active=instance.is_trainer,
            )
