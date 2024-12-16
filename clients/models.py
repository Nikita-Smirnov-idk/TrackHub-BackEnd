from django.db import models
from users.models import CustomUser
from trainers.models import Trainer


class Client(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    trainer_of_user = models.ForeignKey('TrainersOfUser',
                                        on_delete=models.CASCADE,
                                        related_name="clients")

    def __str__(self):
        return f"Client: {self.user.name} {self.user.surname}"


# Create your models here.
class TrainersOfUser(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # Флаг "Любимый тренер"
    favourite = models.BooleanField(default=False)
    # Флаг "Найден по ссылке"
    found_by_link = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client.user.name} -> {self.trainer.user.name}"