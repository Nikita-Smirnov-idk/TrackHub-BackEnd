from rest_framework import serializers
from workout_manager.models import (
    ExerciseCategory,
    Exercise,
    Workout,
    WorkoutExercise,
    GymEquipment,
    WeeklyFitnessPlan,
    WeeklyFitnessPlanWorkout,
)
from users.models import CustomUser
from users.serializers import CustomUserPreviewSerializer
from rest_framework.exceptions import ValidationError
from workout_manager.validators import validate_instructions


class GymEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymEquipment
        fields = '__all__'
        read_only_fields = [GymEquipment._meta.get_field('id').name]


class ExerciseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = [
            ExerciseCategory._meta.get_field('id').name,
            ExerciseCategory._meta.get_field('name').name,
        ]
        read_only_fields = [ExerciseCategory._meta.get_field('id').name]


class ExerciseSerializer(serializers.ModelSerializer):
    original = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        required=False,
    )

    gym_equipment = serializers.PrimaryKeyRelatedField(
        queryset=GymEquipment.objects.all(),
        many=True,
    )

    category = serializers.PrimaryKeyRelatedField(
        queryset=ExerciseCategory.objects.all(),
        many=True,
    )

    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
    )
    instructions = serializers.ListField(
        child=serializers.CharField(),
        validators=[validate_instructions],
        required=True
    )

    class Meta:
        model = Exercise
        fields = [
            Exercise._meta.get_field('id').name,
            Exercise._meta.get_field('name').name,
            Exercise._meta.get_field('description').name,
            Exercise._meta.get_field('changed_at').name,

            Exercise._meta.get_field('is_measured_in_reps').name,
            Exercise._meta.get_field('is_public').name,
            Exercise._meta.get_field('is_published').name,
            Exercise._meta.get_field('is_archived').name,

            'instructions',
            'original',
            'gym_equipment',
            'category',
            'created_by',
        ]
        read_only_fields = [
            Exercise._meta.get_field('id').name,
            Exercise._meta.get_field('changed_at').name,
            Exercise._meta.get_field('is_public').name,
            Exercise._meta.get_field('is_published').name,
            Exercise._meta.get_field('is_archived').name,

            'created_by',
            'original',
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['gym_equipment'] = GymEquipmentSerializer(instance.gym_equipment, many=True).data
        data['category'] = ExerciseCategorySerializer(instance.category, many=True).data
        data['created_by'] = CustomUserPreviewSerializer(instance.created_by).data
        data['original'] = instance.original.id if instance.original else ""
        return data
    
    def validate(self, data):
        """Custom validation for unique_together constraint."""
        user = self.context['request'].user

        if not self.instance:
            # Get user-specific limit from UserProfile
            user_limit = user.workout_manager_limitation.exercise_limitation

            # Check if user exceeded the limit
            exercise_count = Exercise.objects.filter(created_by=user).count()
            if exercise_count >= user_limit:
                raise ValidationError({
                    "non_field_errors": [f"You can create a maximum of {user_limit} exercises."]
                })


        # Check if an identical Exercise already exists

        if Exercise.objects.filter(id=data.get("original")).exists():
            original = Exercise.objects.get(id=data.get("original"))

            existing_exercise = Exercise.objects.filter(
                name=data.get("name"),
                description=data.get("description"),
                preview=data.get("preview"),
                video=data.get("video"),
                created_by=user,
                original=original,
            ).exists()

            if existing_exercise:
                raise serializers.ValidationError({
                    "non_field_errors": ["An exercise with these exact details already exists."]
                })
        
        if self.instance and self.instance.is_published:
            # Check if there are any subscribers to the exercise
            if Exercise.objects.filter(original=self.instance).exists():
                raise serializers.ValidationError("Cannot update a published exercise with subscribers.")

        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        required=True,
    )
    workout = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
        required=False,
    )

    class Meta:
        model = WorkoutExercise
        fields = [
            WorkoutExercise._meta.get_field('id').name,
            WorkoutExercise._meta.get_field('sets').name,
            WorkoutExercise._meta.get_field('value').name,
            WorkoutExercise._meta.get_field('rest_time_after_set').name,

            'workout',
            'exercise',
        ]
        read_only_fields = [WorkoutExercise._meta.get_field('id').name]

    def validate(self, attrs):
        if self.instance:
            workout_exercise_id = self.instance.id
            if not WorkoutExercise.objects.filter(
                id=workout_exercise_id
            ).exists():
                raise ValidationError("Workout exercise does not exist.")
            workout_exercise = WorkoutExercise.objects.get(
                id=workout_exercise_id
            )
            if self.attrs.get('workout', None) != workout_exercise.workout.id:
                raise ValidationError("Workout does not match.")
            if (
                self.attrs.get('exercise', None) !=
                workout_exercise.exercise.id
            ):
                raise ValidationError("Exercise does not match.")

        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['exercise'] = ExerciseSerializer(instance.exercise).data
        return data


class WorkoutSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)

    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False
    )

    original = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
        required=False
    )


    class Meta:
        model = Workout
        fields = [
            Workout._meta.get_field('id').name,
            Workout._meta.get_field('name').name,
            Workout._meta.get_field('changed_at').name,
            Workout._meta.get_field('description').name,

            Workout._meta.get_field('is_public').name,
            Workout._meta.get_field('is_published').name,
            Workout._meta.get_field('is_archived').name,
            
            'created_by',
            'workout_exercises',
            'original',
        ]
        read_only_fields = [
            Workout._meta.get_field('id').name,
            Workout._meta.get_field('changed_at').name,
            Workout._meta.get_field('is_public').name,
            Workout._meta.get_field('is_published').name,
            Workout._meta.get_field('is_archived').name,

            'created_by',
            'original',
        ]

    def validate(self, attrs):

        user = self.context['request'].user

        if not self.instance:
            # Get user-specific limit from UserProfile
            user_limit = user.workout_manager_limitation.workout_limitation

            # Check if user exceeded the limit
            workout_count = Workout.objects.filter(created_by=user).count()
            if workout_count >= user_limit:
                raise ValidationError({
                    "non_field_errors": [f"You can create a maximum of {user_limit} workouts."]
                })

        if self.instance and self.instance.is_published:
            # Check if there are any subscribers to the exercise
            if Workout.objects.filter(original=self.instance).exists():
                raise serializers.ValidationError("Cannot update a published workout with subscribers.")
            
        return super().validate(attrs)

    def create(self, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', [])

        # Создаем Workout
        workout = Workout.objects.create(**validated_data)

        for we_data in workout_exercises_data:
            exercise = we_data.pop('exercise')

            # Создаем WorkoutExercise
            WorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise,
                **we_data
            )

        return workout

    def update(self, instance, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', [])

        # Обновляем Workout
        super().update(instance, validated_data)

        if workout_exercises_data:
            # Удаляем старые WorkoutExercise
            instance.exercises.all().delete()

            for we_data in workout_exercises_data:
                exercise = we_data.get('exercise')

                # Создаем WorkoutExercise
                WorkoutExercise.objects.create(
                    workout=instance,
                    exercise=exercise,
                    **we_data
                )

        return instance
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workout_exercises'] = WorkoutExerciseSerializer(instance.workout_exercises, many=True).data
        data['created_by'] = CustomUserPreviewSerializer(instance.created_by).data
        data['original'] = instance.original.id if instance.original else ""
        return data
    

class WeeklyFitnessPlanWorkoutSerializer(serializers.ModelSerializer):
    workout = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
    )
    weekly_fitness_plan = serializers.PrimaryKeyRelatedField(
        queryset=WeeklyFitnessPlan.objects.all(),
        required=False
    )
    

    class Meta:
        model = WeeklyFitnessPlanWorkout
        fields = [
            WeeklyFitnessPlanWorkout._meta.get_field('id').name,
            WeeklyFitnessPlanWorkout._meta.get_field('workout').name,
            WeeklyFitnessPlanWorkout._meta.get_field('week_day').name,
            WeeklyFitnessPlanWorkout._meta.get_field('weekly_fitness_plan').name,
            
        ]
        read_only_fields = [
            WeeklyFitnessPlanWorkout._meta.get_field('id').name,
        ]
    

class WeeklyFitnessPlanSerializer(serializers.ModelSerializer):
    workouts = WeeklyFitnessPlanWorkoutSerializer(many=True, required=False, source="weekly_fitness_plan_workouts")

    original = serializers.PrimaryKeyRelatedField(
        queryset=WeeklyFitnessPlan.objects.all(),
        required=False
    )

    created_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False
    )

    class Meta:
        model = WeeklyFitnessPlan
        fields = [
            WeeklyFitnessPlan._meta.get_field('id').name,
            WeeklyFitnessPlan._meta.get_field('name').name,
            WeeklyFitnessPlan._meta.get_field('changed_at').name,
            WeeklyFitnessPlan._meta.get_field('description').name,

            WeeklyFitnessPlan._meta.get_field('is_public').name,
            WeeklyFitnessPlan._meta.get_field('is_published').name,
            WeeklyFitnessPlan._meta.get_field('is_archived').name,
            
            'workouts',
            'created_by',
            'original',
        ]
        read_only_fields = [
            WeeklyFitnessPlan._meta.get_field('id').name,
            WeeklyFitnessPlan._meta.get_field('changed_at').name,
            WeeklyFitnessPlan._meta.get_field('is_public').name,
            WeeklyFitnessPlan._meta.get_field('is_published').name,
            WeeklyFitnessPlan._meta.get_field('is_archived').name,

            'created_by',
            'original',
        ]


    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['workouts'] = WeeklyFitnessPlanWorkoutSerializer(instance.weekly_fitness_plan_workouts, many=True).data
        data['created_by'] = CustomUserPreviewSerializer(instance.created_by).data
        data['original'] = instance.original.id if instance.original else ""
        return data
    

    def validate(self, attrs):

        user = self.context['request'].user

        if not self.instance:
            # Get user-specific limit from UserProfile
            user_limit = user.workout_manager_limitation.plans_limitation

            # Check if user exceeded the limit
            plans_count = WeeklyFitnessPlan.objects.filter(created_by=user).count()
            if plans_count >= user_limit:
                raise ValidationError({
                    "non_field_errors": [f"You can create a maximum of {user_limit} plans."]
                })

        if self.instance and self.instance.is_published:
            # Check if there are any subscribers to the exercise
            if WeeklyFitnessPlan.objects.filter(original=self.instance).exists():
                raise serializers.ValidationError("Cannot update a published weekly plan with subscribers.")
            
        return super().validate(attrs)


    def create(self, validated_data):
        plan_workouts_data = validated_data.pop('workouts', [])

        plan = WeeklyFitnessPlan.objects.create(**validated_data)

        for pw_data in plan_workouts_data:
            workout_id = pw_data.get('workout').id

            workout = Workout.objects.filter(id=workout_id).first()
            if not workout_id:
                raise serializers.ValidationError({
                    'plan_workouts':
                    f'workout with id {workout_id} does not exist.'
                })

            WeeklyFitnessPlanWorkout.objects.create(
                weekly_fitness_plan=plan,
                workout=workout,
                **pw_data
            )

        return workout

    def update(self, instance, validated_data):
        plan_workouts_data = validated_data.pop('workouts', [])

        # Обновляем Workout
        super().update(instance, validated_data)

        if plan_workouts_data:
            # Удаляем старые WorkoutExercise
            instance.workouts.all().delete()

            for pw_data in plan_workouts_data:
                workout_id = pw_data.get('workout').id

                # Проверяем существование Exercise
                workout = Workout.objects.filter(id=workout_id).first()
                if not workout:
                    raise serializers.ValidationError({
                        'workout_exercises':
                        f'Exercise with id {workout_id} does not exist.'
                    })

                # Создаем WorkoutExercise
                WeeklyFitnessPlanWorkout.objects.create(
                    weekly_fitness_plan=instance,
                    workout=workout,
                    **pw_data
                )

        return instance