from django.db import models
from users.models import CustomUser
from trainers.models import Trainer


class Client(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='client'
    )
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Client: {self.user.first_name} {self.user.last_name}"


class TrainersOfCLient(models.Model):
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name="trainers_of_client"
    )
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE,
                                related_name="clients_of_trainer")
    # Флаг "Любимый тренер"
    favourite = models.BooleanField(default=False)
    # Флаг "Найден по ссылке"
    found_by_link = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.client.user.first_name} ->" +
            f" {self.trainer.user.first_name}"
        )


class WorkoutSession(models.Model):
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        related_name='workout_sessions'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='workout_sessions'
    )
    start = models.DateTimeField()
    duration = models.DurationField()
