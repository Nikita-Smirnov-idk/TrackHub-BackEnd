from django.db import models
from users.models import CustomUser
from django.core.validators import MaxValueValidator, MinValueValidator


class UserFitnessProgram(models.Model):
    workout_limitation=models.PositiveIntegerField(default=100)
    exercise_limitation=models.PositiveIntegerField(default=200)
    plans_limitation=models.PositiveIntegerField(default=50)


class GymEquippment(models.Model):
    Exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='gym_equipment')

    name = models.CharField(max_length=255)
    


class Exercise(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=250, blank=True, null=True)
    # Категория упражнения
    category = models.ForeignKey('ExerciseCategory',
                                 on_delete=models.CASCADE,
                                 related_name='exercises')
    gym_equipment = models.ForeignKey(
        GymEquippment,
        on_delete=models.models.CASCADE,
        null=True, 
        elated_name='exercises'
    )

    # Упражнение доступно для всех
    is_public = models.BooleanField(default=False)

    shared_with = models.ManyToManyField(CustomUser,
                                         related_name='shared_exercises',
                                         blank=True)  # С кем поделились
    
    reps_measured = models.BooleanField(default=True)

    value = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(3600),
            MinValueValidator(1)
        ]
    )

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if (
            self.created_by is None and
            self.shared_with.count() == 0 and
            not self.is_public
        ):
            self.delete()


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
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    rest_between_workout_exercises = models.PositiveIntegerField(default=0)

    def __str__(self):

        return f"{self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for exercise in self.exercises.all():
            for user in self.shared_with.all():
                if not exercise.shared_with.filter(id=user.id).exists():
                    exercise.shared_with.add(user)
            if self.created_by and exercise.created_by != self.created_by:
                exercise.shared_with.add(self.created_by)

        for workout_exercise in self.workout_exercises.filter(workout=self):
            for user in self.shared_with.all():
                if not workout_exercise.available_for.filter(
                    id=user.id
                ).exists():
                    workout_exercise.available_for.add(user)


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout,
                                on_delete=models.SET_NULL,
                                null=True,  # Поле может быть пустым
                                # Разрешаем не указывать значение в форме
                                blank=True,
                                # Для обратной связи
                                related_name="workout_exercises",
                                )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(1)
        ]
    )  # Количество подходов
    reps = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(1)
        ]
    ) # Количество повторений
    # Время отдыха между подходами (в секундах)
    rest_time = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(3600),
            MinValueValidator(1)
        ]
    )

    equipment_value = 

    available_for = models.ManyToManyField(
        CustomUser,
        related_name='available_workout_exercises',
        blank=True
    )  # Кому доступно

    def __str__(self):
        return (f"exercise is {self.exercise.name} with " +
                f"{self.sets} sets and {self.reps} reps")


class ExerciseCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
