# serializers.py в приложении trainer
from rest_framework import serializers
from trainers.models import (Trainer,
                             Exercise,
                             Workout,
                             WeekDay,
                             Break,
                             Holiday,
                             WorkoutExercise,
                             WorkHours,
                             Experience,
                             WholeExperience,
                             TrainerWeekend,
                             ExerciseCategory,
                             )
from users.models import CustomUser
from django.core.exceptions import ValidationError


class MuscleGroupCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = ['id', 'name']


class ExerciseSerializer(serializers.ModelSerializer):
    shared_with = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CustomUser.objects.all()
    )  # IDs пользователей, с которыми делимся

    class Meta:
        model = Exercise
        fields = ['id',
                  'name',
                  'description',
                  'category',
                  'is_public',
                  'shared_with',
                  ]
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        shared_with_data = validated_data.pop('shared_with', [])
        exercise = Exercise.objects.create(created_by=user, **validated_data)

        exercise.shared_with.set(shared_with_data)

        return exercise

    def update(self, instance, validated_data):
        # Извлекаем новые данные для shared_with
        shared_with_data = validated_data.pop('shared_with', [])

        # Обновляем все остальные поля, используя
        # super() для обработки их обновления
        instance = super().update(instance, validated_data)

        # Обновляем поле shared_with: только добавляем новых пользователей
        current_shared_with = set(instance.shared_with.all())
        new_shared_with = set(shared_with_data)

        # Находим пользователей, которых нужно добавить
        # (не удаляем существующих)
        users_to_add = new_shared_with - current_shared_with
        if users_to_add:
            instance.shared_with.add(*users_to_add)

        return instance


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(required=True)

    class Meta:
        model = WorkoutExercise
        fields = ['id',
                  'workout',
                  'exercise',
                  'sets',
                  'reps',
                  'rest_time',
                  'shared_with'
                  ]
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        shared_with_data = validated_data.pop('shared_with', [])
        workoutexercise = WorkoutExercise.objects.create(created_by=user,
                                                         **validated_data)

        workoutexercise.shared_with.set(shared_with_data)

        return workoutexercise

    def update(self, instance, validated_data):
        # Извлекаем новые данные для shared_with
        shared_with_data = validated_data.pop('shared_with', [])

        # Обновляем все остальные поля, используя super()
        # для обработки их обновления
        instance = super().update(instance, validated_data)

        # Обновляем поле shared_with: только добавляем новых пользователей
        current_shared_with = set(instance.shared_with.all())
        new_shared_with = set(shared_with_data)

        # Находим пользователей, которых нужно добавить
        # (не удаляем существующих)
        users_to_add = new_shared_with - current_shared_with
        if users_to_add:
            instance.shared_with.add(*users_to_add)

        return instance


# Пример для тренировки
class WorkoutSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)
    shared_with = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CustomUser.objects.all()
    )  # IDs пользователей, с которыми делимся

    class Meta:
        model = Workout
        fields = [
            'id',
            'name',
            'workout_exercises',
            'shared_with',
        ]
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        workout_exercises_data = validated_data.pop('workout_exercises', [])
        shared_with_data = validated_data.pop('shared_with', [])
        workout = Workout.objects.create(created_by=user, **validated_data)

        # Создаем или получаем упражнения и добавляем их в тренировку
        for exercise_data in workout_exercises_data:
            workout_exercise, _ = Exercise.objects.get_or_create(
                **exercise_data
            )
            workout.exercises.add(workout_exercise)

        workout.shared_with.set(shared_with_data)

        return workout

    def update(self, instance, validated_data):
        # Извлечение данных для обновления
        # None, если данные не переданы
        exercises_data = validated_data.pop('exercises', None)
        shared_with_data = validated_data.pop('shared_with', None)

        # Обновляем простые поля модели
        instance = super().update(instance, validated_data)

        # Обновляем поле exercises, если данные были переданы
        if exercises_data is not None:  # Только если передано
            instance.exercises.clear()  # Удаляем старые связи
            for exercise_data in exercises_data:
                exercise, _ = Exercise.objects.get_or_create(**exercise_data)
                instance.exercises.add(exercise)

        # Обновляем поле shared_with: только добавляем новых пользователей
        current_shared_with = set(instance.shared_with.all())
        new_shared_with = set(shared_with_data)

        # Находим пользователей, которых нужно добавить
        # (не удаляем существующих)
        users_to_add = new_shared_with - current_shared_with
        if users_to_add:
            instance.shared_with.add(*users_to_add)

        return instance


class WeekDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekDay
        fields = ['id', 'name']


class BreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Break
        fields = ['id', 'name', 'start_time', 'end_time']


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'name', 'start_date', 'end_date']


class WorkHoursSerializer(serializers.ModelSerializer):
    trainer = serializers.PrimaryKeyRelatedField(queryset=Trainer.objects.all())

    class Meta:
        model = WorkHours
        fields = ['id', 'trainer', 'start_time', 'end_time']

    def validate(self, data):
        if 'trainer' in data and WorkHours.objects.filter(trainer=data['trainer']).exists():
            raise serializers.ValidationError("Workhours already exists.")
        return super().validate(data)


class TrainerWeekendSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerWeekend
        fields = ['id', 'weekday_ids', 'trainer']

    def update(self, instance, validated_data):
        weekday_ids = validated_data.pop('weekday_ids', [])
        instance.trainer = validated_data.get('trainer', instance.trainer)

        # Очистка существующих связанных записей
        instance.weekday.clear()

        # Добавляем новые записи
        for weekday_id in weekday_ids:
            weekday = WeekDay.objects.get(id=weekday_id)
            instance.weekday.add(weekday)

        instance.save()
        return instance

    def create(self, validated_data):
        weekday_ids = validated_data.pop('weekday_ids', [])
        trainer = validated_data.get('trainer')

        # Создание нового объекта TrainerWeekend
        trainer_weekend = TrainerWeekend.objects.create(trainer=trainer)

        # Добавление связей ManyToMany
        for weekday_id in weekday_ids:
            weekday = WeekDay.objects.get(id=weekday_id)
            trainer_weekend.weekday.add(weekday)

        return trainer_weekend


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            'id',
            'trainer',
            'user',
            'company_name',
            'position',
            'description',
            'start_date',
            'end_date'
        ]


class WholeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeExperience
        fields = ['id', 'trainer', 'experience']


class TrainerGetSerializer(serializers.ModelSerializer):
    weekends = TrainerWeekendSerializer(many=True, read_only=True)
    work_hours = serializers.PrimaryKeyRelatedField(
        queryset=WorkHours.objects.all(), allow_null=True
    )
    breaks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Break.objects.all()
    )
    holidays = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Holiday.objects.all()
    )
    whole_experience = WholeExperienceSerializer(read_only=True)

    class Meta:
        model = Trainer
        fields = [
            'id',
            'user',
            'description',
            'address',
            'is_public',
            'is_active',
            'is_male',
            'price_per_hour',
            'minimum_workout_duration',
            'workout_duration_devided_by_value',
            'weekends',
            'work_hours',
            'breaks',
            'holidays',
            'whole_experience',
        ]


class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = [
            'id',
            'user',
            'description',
            'address',
            'is_public',
            'is_active',
            'is_male',
            'price_per_hour',
            'minimum_workout_duration',
            'workout_duration_devided_by_value',
        ]
