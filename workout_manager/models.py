from django.db import models
from users.models import CustomUser
from django.core.validators import MaxValueValidator, MinValueValidator
from users.validators import validate_image
from workout_manager.validators import (
    validate_video_size,
    validate_instructions,
)
from TrackHub.trackhub_bucket import TrackHubMediaStorage
from django.core.exceptions import ValidationError
from users.Services.delete_instances_from_s3 import delete_instance_from_s3
from workout_manager.Services import created_at_service


class UserWorkoutManagerLimitation(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='workout_manager_limitation')

    workout_limitation=models.PositiveIntegerField(default=50)
    exercise_limitation=models.PositiveIntegerField(default=100)
    plans_limitation=models.PositiveIntegerField(default=25)


class GymEquipment(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(
        validators=[
            validate_image
        ],
        storage=TrackHubMediaStorage(),
        upload_to="gym_equipment/",
    )


class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True, null=True)
    instructions = models.JSONField(default=list, validators=[validate_instructions])

    category = models.ManyToManyField(
        'ExerciseCategory',
        related_name='exercises',
    )
    gym_equipment = models.ManyToManyField(
        GymEquipment,
        related_name='exercises',
    )
    preview = models.ImageField(
        validators=[
            validate_image
        ],
        storage=TrackHubMediaStorage(),
        upload_to="exercises/previews/",
        null=True,
        blank=True,
    )
    video = models.FileField(
        upload_to='exercises/videos/',
        validators=[
            validate_video_size,
        ],
        null=True,
        blank=True,
    )

    is_measured_in_reps = models.BooleanField(default=True)

    is_public = models.BooleanField(default=False)

    is_published = models.BooleanField(default=False)

    original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    is_archived = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="created_exercises",
        null=True,
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "description", "preview", "video", "created_by", "original")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Exercise.objects.filter(pk=self.pk).first()

            if old_instance:
                if old_instance.preview != self.preview:
                    preview_used_elsewhere = Exercise.objects.filter(preview=old_instance.preview).exclude(pk=self.pk).exists()
                    
                    if not preview_used_elsewhere and old_instance.preview:
                        delete_instance_from_s3(old_instance.preview)
                
                if old_instance.video != self.video:
                    video_used_elsewhere = Exercise.objects.filter(video=old_instance.video).exclude(pk=self.pk).exists()
                    
                    if not video_used_elsewhere and old_instance.video:
                        delete_instance_from_s3(old_instance.video)
            
            created_at_service.update_changed_at(self, old_instance)
    
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        """Check if the preview is used elsewhere before deleting it when deleting this record."""

        if self.preview != self.preview:
            preview_used_elsewhere = Exercise.objects.filter(preview=self.preview).exclude(pk=self.pk).exists()
            
            if not preview_used_elsewhere and self.preview:
                delete_instance_from_s3(self.preview)
        
        if self.video != self.video:
            video_used_elsewhere = Exercise.objects.filter(video=self.video).exclude(pk=self.pk).exists()
            
            if not video_used_elsewhere and self.video:
                delete_instance_from_s3(self.video)

        return super().delete(*args, **kwargs)


    def clone_for_user(self, user):
        """Создаёт копию упражнения для нового пользователя"""
        cloned_exercise = Exercise.objects.create(
            name=self.name,
            description=self.description,
            instructions=self.instructions,
            category=self.category,
            gym_equipment=self.gym_equipment,
            preview=self.preview,
            video=self.video,

            is_measured_in_reps=self.is_measured_in_reps,

            original=self,
            created_by=user,
        )

        return cloned_exercise
        


class Workout(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True, null=True)
    exercises = models.ManyToManyField(Exercise, through='WorkoutExercise')

    is_published = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    is_archived = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="created_workouts",
        null=True,
    )

    changed_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):

        return f"{self.name}"
    
    def clean(self):
        """Limit the number of exercises in a workout."""
        MAX_EXERCISES = 30
        if self.exercises.count() > MAX_EXERCISES:
            raise ValidationError(f"A workout cannot have more than {MAX_EXERCISES} exercises.")

    def save(self, *args, **kwargs):

        if self.pk:
            old_instance = Exercise.objects.filter(pk=self.pk).first()

            created_at_service.update_changed_at(self, old_instance)

        super().save(*args, **kwargs)

    
    def clone_for_user(self, user):
        """Создаёт копию тренировки для нового пользователя"""

        cloned_workout = Workout.objects.create(
            name = self.name,
            description = self.description,

            original = self,
            created_by=user
        )

        original_workout_exercises = WorkoutExercise.objects.filter(workout=self).select_related('exercise')

        workout_exercises = []

        for original_we in original_workout_exercises:
            cloned_exercise = original_we.exercise.clone_for_user(user)

            workout_exercises.append(
                WorkoutExercise(
                    workout=cloned_workout,
                    exercise=cloned_exercise,
                    sets=original_we.sets,
                    value=original_we.value,
                    rest_time_after_set=original_we.rest_time_after_set,
                )
            )

        # Bulk create all WorkoutExercise instances
        WorkoutExercise.objects.bulk_create(workout_exercises)

        return cloned_workout
    

    def __str__(self):
        return f"{self.name}"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout,
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                related_name="workout_exercises",
                                )
    
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="workout_exercises")
    value = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(3600),
            MinValueValidator(1)
        ]
    )
    sets = models.PositiveIntegerField(
        default=1,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(1)
        ]
    )
    rest_time_after_set = models.PositiveIntegerField(
        default=60,
        validators=[
            MaxValueValidator(3600),
            MinValueValidator(1)
        ]
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']  # Ensure exercises are always retrieved in order
        unique_together = ('workout', 'order')  # Prevent duplicate orders


    def __str__(self):
        return (f"exercise is {self.exercise.name} with " +
                f"{self.sets} sets and {self.reps} reps")
    
    def save(self, *args, **kwargs):
        """Automatically assign the next order if not set."""
        if not self.order:
            last_order = WorkoutExercise.objects.filter(workout=self.workout).count()
            print(last_order + 1)
            self.order = last_order + 1  # Assign the next order
        super().save(*args, **kwargs)


class ExerciseCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class WeeklyFitnessPlanWorkout(models.Model):
    WEEK_DAYS = [
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    ]

    weekly_fitness_plan = models.ForeignKey('WeeklyFitnessPlan', on_delete=models.CASCADE, related_name="weekly_fitness_plan_workouts")
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="weekly_fitness_plan_workouts")
    week_day = models.PositiveIntegerField(choices=WEEK_DAYS)

    class Meta:
        ordering = ["week_day"]
    
    def __str__(self):
        return f"{self.weekly_fitness_plan.name}"


class WeeklyFitnessPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True, null=True)
    workouts = models.ManyToManyField(Workout, through=WeeklyFitnessPlanWorkout)

    is_published = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    is_archived = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name="created_weekly_fitness_plans",
        null=True,
    )

    changed_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):

        if self.pk:
            old_instance = WeeklyFitnessPlan.objects.filter(pk=self.pk).first()

            created_at_service.update_changed_at(self, old_instance)

        super().save(*args, **kwargs)


    def clone_for_user(self, user):
        """Создаёт копию тренировки для нового пользователя"""

        cloned_plan = WeeklyFitnessPlan.objects.create(
            name = self.name,
            description = self.description,

            original = self,
            created_by=user
        )

        original_plan_workouts = WeeklyFitnessPlanWorkout.objects.filter(weekly_fitness_plan=self).select_related('workout')

        plan_workouts = []

        for original_pw in original_plan_workouts:
            cloned_workout = original_pw.workout.clone_for_user(user)

            plan_workouts.append(
                WeeklyFitnessPlanWorkout(
                    weekly_fitness_plan=cloned_plan,
                    wokrout=cloned_workout,
                    week_day=original_pw.week_day,
                )
            )

        # Bulk create all WorkoutExercise instances
        WeeklyFitnessPlanWorkout.objects.bulk_create(plan_workouts)

        return cloned_plan

