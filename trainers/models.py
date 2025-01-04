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


class TrainerCategory(models.Model):
    trainer = models.ForeignKey('Trainer', on_delete=models.CASCADE)
    category = models.ForeignKey(CategoryOfTrainers, on_delete=models.CASCADE)

    class Meta:
        # Гарантируем, что один тренер не может быть в одной категории
        # несколько раз
        unique_together = ('trainer', 'category')

    def __str__(self):
        return f"{self.trainer.user.name} - {self.category.name}"


class Trainer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='trainer')
    description = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)  # Адрес зала
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_male = models.BooleanField(default=True)
    price_per_hour = models.PositiveIntegerField(default=0)
    minimum_workout_duration = models.PositiveIntegerField(default=60)
    workout_duration_devided_by_value = models.PositiveIntegerField(
        default=30
    )
    weekends = models.ManyToManyField('Weekday', through='TrainerWeekend',
                                      blank=True,)
    breaks = models.ManyToManyField('Break',
                                    blank=True,)
    holidays = models.ManyToManyField('Holiday',
                                      blank=True,)
    trainer_categories = models.ManyToManyField(CategoryOfTrainers,
                                                through='TrainerCategory')

    class Meta:
        indexes = [
            GinIndex(
                fields=['description'],
            )
        ]

    def __str__(self):
        return f"Trainer: {self.user.name} " + \
            f"{self.user.surname} ({self.address})"

    def save(self, *args, **kwargs):
        # Сохраняем объект Trainer
        super().save(*args, **kwargs)

        # Проверяем, есть ли связанные объекты (чтобы избежать дублирования)
        if not hasattr(self, 'whole_experience'):
            WholeExperience.objects.create(trainer=self)


class Exercise(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=250, blank=True, null=True)
    # Категория упражнения
    muscle_group_category = models.ForeignKey('MuscleGroupCategory',
                                              on_delete=models.CASCADE)
    # Упражнение доступно для всех
    is_public = models.BooleanField(default=True)

    shared_with = models.ManyToManyField(CustomUser,
                                         related_name='shared_exercises',
                                         blank=True)  # С кем поделились
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,  # Если пользователь удален, оставляем NULL
        null=True,  # Поле может быть пустым
        blank=True,  # Разрешаем не указывать значение в форме
        related_name="created_exercises"  # Для обратной связи
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Workout(models.Model):
    created_by = models.ForeignKey(CustomUser,
                                   on_delete=models.SET_NULL,
                                   null=True,  # Поле может быть пустым
                                   # Разрешаем не указывать значение в форме
                                   blank=True,
                                   # Для обратной связи
                                   related_name="created_workouts",
                                   )
    shared_with = models.ManyToManyField(CustomUser,
                                         related_name='shared_workouts',
                                         blank=True)  # С кем поделились
    name = models.CharField(max_length=100)
    exercises = models.ManyToManyField(Exercise, through='WorkoutExercise')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"Workout for {self.user.name}"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout,
                                on_delete=models.SET_NULL,
                                null=True,  # Поле может быть пустым
                                # Разрешаем не указывать значение в форме
                                blank=True,
                                # Для обратной связи
                                related_name="workout_exercises",
                                )
    shared_with = models.ManyToManyField(
        CustomUser,
        related_name='shared_workout_exercises',
        blank=True  # С кем поделились
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField()  # Количество подходов
    reps = models.PositiveIntegerField()  # Количество повторений
    # Время отдыха между подходами (в секундах)
    rest_time = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser,
                                   on_delete=models.SET_NULL,
                                   null=True,  # Поле может быть пустым
                                   # Разрешаем не указывать значение в форме
                                   blank=True,
                                   # Для обратной связи
                                   related_name="created_workout_exercises",
                                   )

    def __str__(self):
        return f"{self.exercise.name} in {self.workout.user.name}'s workout"


class WeekDay(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Пн, Вт, Ср, Чт, Пт, Сб, Вс

    def __str__(self):
        return self.name


class MuscleGroupCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TrainerWeekend(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    weekday = models.ForeignKey(WeekDay, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.trainer} has weekend on {self.weekday.name}"


class Break(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Break from {self.start} to {self.end}"


class WorkHours(models.Model):
    trainer = models.OneToOneField('Trainer', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"Work hours: {self.start} - {self.end}"


class Holiday(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

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
