from workout_manager.models import Exercise, Workout, WeeklyFitnessPlan

def publish_workout(workout_id) -> None:
    # Fetch the workout with exercises
    workout = Workout.objects.prefetch_related('exercises').get(id=workout_id)

    # Bulk update exercises instead of saving them one by one
    exercises = list(workout.exercises.all())
    for exercise in exercises:
        exercise.is_published = True
    Workout.exercises.model.objects.bulk_update(exercises, ['is_published'])

    # Update workout
    workout.is_published = True
    workout.save(update_fields=['is_published'])


def publish_plan(plan_id) -> None:
    # Fetch plan with workouts and exercises efficiently
    plan = WeeklyFitnessPlan.objects.prefetch_related('workouts', 'workouts__exercises').get(id=plan_id)

    # Publish all workouts
    workouts = list(plan.workouts.all())
    for workout in workouts:
        publish_workout(workout.id)

    # Update plan
    plan.is_published = True
    plan.save(update_fields=['is_published'])
