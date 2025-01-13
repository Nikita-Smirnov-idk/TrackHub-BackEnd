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
                             ExerciseCategory,
                             )
from users.models import CustomUser
from django.core.exceptions import ValidationError


class MuscleGroupCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = ['id', 'name']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    shared_with = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.all(),
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=ExerciseCategory.objects.all(),
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
    )

    class Meta:
        model = Exercise
        fields = ['id',
                  'name',
                  'description',
                  'category',
                  'is_public',
                  'shared_with',
                  'created_by',
                  'created_at',
                  ]
        read_only_fields = ['id', 'created_at']

    def update(self, instance, validated_data):
        shared_with_data = validated_data.pop('shared_with', [])
        shared_with_data_previous = [
            shared.id for shared in instance.shared_with.all()
        ]
        new_shared_with = shared_with_data_previous
        for shared_user_id in shared_with_data:
            if shared_user_id not in shared_with_data_previous:
                new_shared_with.append(shared_user_id)
        validated_data['shared_with'] = new_shared_with
        return super().update(instance, validated_data)


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
    )
    workout = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
    )
    available_for = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.all(),
    )

    class Meta:
        model = WorkoutExercise
        fields = ['id',
                  'workout',
                  'exercise',
                  'sets',
                  'reps',
                  'rest_time',
                  'available_for',
                  ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if self.instance:
            workout_exercise_id = self.instance.id
            if not WorkoutExercise.objects.filter(id=workout_exercise_id).exists():
                raise ValidationError("Workout exercise does not exist.")
            workout_exercise = WorkoutExercise.objects.get(id=workout_exercise_id)
            if self.attrs.get('workout', None) != workout_exercise.workout.id:
                raise ValidationError("Workout does not match.")
            if self.attrs.get('exercise', None) != workout_exercise.exercise.id:
                raise ValidationError("Exercise does not match.")

        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['exercise'] = ExerciseSerializer(instance.exercise).data
        return data


class WorkoutSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)

    shared_with = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.all(),
    )

    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
    )

    class Meta:
        model = Workout
        fields = [
            'id',
            'created_by',
            'shared_with',
            'name',
            'workout_exercises',
            'is_public',
            'rest_between_workout_exercises',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', [])

        # Создаем Workout
        workout = Workout.objects.create(**validated_data)

        for we_data in workout_exercises_data:
            exercise_id = we_data.get('exercise')

            # Проверяем существование Exercise
            exercise = Exercise.objects.filter(id=exercise_id).first()
            if not exercise:
                raise serializers.ValidationError({
                    'workout_exercises':
                    f'Exercise with id {exercise_id} does not exist.'
                })

            # Создаем WorkoutExercise
            WorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise,
                **we_data
            )

        return workout

    def update(self, instance, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', None)

        # Обновляем Workout
        super().update(instance, validated_data)

        if workout_exercises_data:
            # Удаляем старые WorkoutExercise
            instance.workout_exercises.all().delete()

            for we_data in workout_exercises_data:
                exercise_id = we_data.get('exercise')

                # Проверяем существование Exercise
                exercise = Exercise.objects.filter(id=exercise_id).first()
                if not exercise:
                    raise serializers.ValidationError({
                        'workout_exercises': f'Exercise with id {exercise_id} does not exist.'
                    })

                # Создаем WorkoutExercise
                WorkoutExercise.objects.create(
                    workout=instance,
                    exercise=exercise,
                    **we_data
                )

        return instance


class WeekDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekDay
        fields = ['id', 'name']
        read_only_fields = ['id']


class BreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Break
        fields = ['id', 'name', 'start_time', 'end_time']
        read_only_fields = ['id']


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'name', 'start_date', 'end_date']
        read_only_fields = ['id']


class WorkHoursSerializer(serializers.ModelSerializer):
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all(),
        source='trainer',
    )

    class Meta:
        model = WorkHours
        fields = ['id', 'trainer_id', 'start_time', 'end_time']
        read_only_fields = ['id', 'trainer_id']


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
        read_only_fields = ['id']


class WholeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeExperience
        fields = ['id', 'trainer', 'experience']
        read_only_fields = ['id']


class TrainerGetSerializer(serializers.ModelSerializer):
    weekends = serializers.PrimaryKeyRelatedField(
        queryset=WeekDay.objects.all(),
        many=True
    )
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
        read_only_fields = ['id']


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
        read_only_fields = ['id']
