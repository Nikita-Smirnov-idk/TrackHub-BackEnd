from django.db import models
from django.contrib.postgres.indexes import GinIndex
from datetime import date
from decimal import Decimal
from users.models import CustomUser
import trainers


class CategoryOfTrainers(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Название категории
    description = models.TextField(blank=True, null=True)  # Описание категории

    def __str__(self):
        return self.name


class Trainer(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='trainer'
    )
    description = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)  # Адрес зала
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_male = models.BooleanField(default=True)
    price_per_minimum_workout_duration = models.PositiveIntegerField(default=0)
    minimum_workout_duration = models.PositiveIntegerField(default=60)
    workout_duration_devided_by_value = models.PositiveIntegerField(
        default=30
    )
    weekends = models.ManyToManyField('Weekday', blank=True)
    breaks = models.ManyToManyField('Break',
                                    blank=True,)
    holidays = models.ManyToManyField('Holiday',
                                      blank=True,)
    trainer_categories = models.ManyToManyField('CategoryOfTrainers',
                                                blank=True)

    class Meta:
        indexes = [
            GinIndex(
                fields=['description'],
            )
        ]

    def __str__(self):
        return f"Trainer: {self.user.first_name} " + \
            f"{self.user.last_name} ({self.address})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = Trainer.objects.get(pk=self.pk)
            if previous.is_active != self.is_active and not self.is_active:
                self.is_public = False

        # Сохраняем объект Trainer
        super().save(*args, **kwargs)

        # Проверяем, есть ли связанные объекты (чтобы избежать дублирования)
        if not hasattr(self, 'whole_experience'):
            WholeExperience.objects.create(trainer=self)

        if not WorkHours.objects.filter(trainer=self).exists():
            WorkHours.objects.create(
                trainer=self,
                start_time='10:00:00',
                end_time='18:00:00'
            )


class WeekDay(models.Model):
    # Пн, Вт, Ср, Чт, Пт, Сб, Вс
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Break(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Break from {self.start} to {self.end}"


class WorkHours(models.Model):
    trainer = models.OneToOneField('Trainer',
                                   on_delete=models.CASCADE,
                                   related_name='workhours')
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Work hours: {self.start_time} - {self.end_time}"


class Holiday(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):

        return f"Holiday from {self.start_date} to {self.end_date}"


class Experience(models.Model):
    trainer = models.ForeignKey('Trainer',
                                on_delete=models.CASCADE,
                                related_name='experiences')  # Связь с тренером
    company_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.company_name} - {self.position}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Сохраняем запись
        if hasattr(self.trainer, 'whole_experience'):
            self.trainer.whole_experience.update_experience()  # Обновляем стаж

    def delete(self, *args, **kwargs):
        trainer = self.trainer
        super().delete(*args, **kwargs)  # Удаляем запись
        if hasattr(trainer, 'whole_experience'):
            trainer.whole_experience.update_experience()  # Обновляем стаж


class WholeExperience(models.Model):
    trainer = models.OneToOneField(Trainer,
                                   on_delete=models.CASCADE,
                                   related_name='whole_experience')
    experience = models.DecimalField(max_digits=5,
                                     decimal_places=1,
                                     default=0.0)  # Стаж в годах

    def update_experience(self):
        """
        Пересчитывает общий стаж тренера на основе его записей опыта работы
        и сохраняет результат в поле experience.
        """
        if not trainers.is_installed('Trainer') or not trainers.get_model(
            'Trainer',
            'Experience'
             ):
            self.experience = 0.0
            self.save()
            return

        experiences = Experience.objects.filter(trainer=self.trainer)
        total_days = 0

        for exp in experiences:
            start = exp.start_date
            # Если дата окончания не указана, берем текущую дату
            end = exp.end_date or date.today()
            total_days += (end - start).days

        # Преобразуем дни в годы и округляем в меньшую сторону до
        # одного знака после запятой
        total_years = Decimal(total_days / 365.25).quantize(Decimal('0.1'))
        self.experience = total_years
        self.save()  # Сохраняем изменения в базе данных

    def __str__(self):
        return f"Whole experience: {self.experience} years"
