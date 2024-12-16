from django.db import models
from datetime import date
from decimal import Decimal
from users.models import CustomUser


class Trainer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=255)  # Адрес зала
    weekends = models.ManyToManyField('Weekday', through='TrainerWeekend')
    breaks = models.ManyToManyField('Break')
    work_hours = models.OneToOneField('WorkHours', on_delete=models.CASCADE)
    holidays = models.ManyToManyField('Holiday')

    def __str__(self):
        return f"Trainer: {self.user.name} " + \
            f"{self.user.surname} ({self.address})"


class Exercise(models.Model):
    name = models.CharField(max_length=255)
    # Категория упражнения
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    # Упражнение доступно для всех
    is_public = models.BooleanField(default=True)

    users = models.ManyToManyField(CustomUser,
                                   related_name='exercises',
                                   through='UserExercise')

    def __str__(self):
        return self.name


class UserExercise(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.name} -> {self.exercise.name}"


class Workout(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    exercises = models.ManyToManyField(Exercise, through='WorkoutExercise')

    def __str__(self):
        return f"Workout for {self.user.name}"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()  # Количество подходов
    reps = models.PositiveIntegerField()  # Количество повторений
    # Время отдыха между подходами (в секундах)
    rest_time = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.exercise.name} in {self.workout.user.name}'s workout"


class Weekday(models.Model):
    name = models.CharField(max_length=50)  # Пн, Вт, Ср, Чт, Пт, Сб, Вс

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TrainerWeekend(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    weekday = models.ForeignKey(Weekday, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.trainer} has weekend on {self.weekday.name}"


class Break(models.Model):
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return f"Break from {self.start} to {self.end}"


class WorkHours(models.Model):
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return f"Work hours: {self.start} - {self.end}"


class Holiday(models.Model):
    start = models.DateField()
    end = models.DateField()

    def __str__(self):

        return f"Holiday from {self.start} to {self.end}"


class Experience(models.Model):
    trainer = models.ForeignKey('Trainer',
                                on_delete=models.CASCADE,
                                related_name='experiences')  # Связь с тренером
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
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