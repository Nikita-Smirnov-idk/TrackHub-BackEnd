from workout_manager.models import (
    Exercise,
    Workout,
    WeeklyFitnessPlan,
)
from users.models import CustomUser


def get_workout_originality_values(workout_id, user_id):
    workout = Workout.objects.filter(id=workout_id).prefetch_related('exercises').first()

    count_all = 1
    count_not_original = 1 if workout.original else 0

    for exercise in workout.exercises.all():
        count_all += 1
        if exercise.original:
            count_not_original += 1
    
    return count_all, count_not_original


def get_plan_originality_values(plan_id, user_id):
    plan = WeeklyFitnessPlan.objects.filter(id=plan_id).prefetch_related('workouts').first()

    count_all = 1
    count_not_original = 1 if plan.original else 0

    for workout in plan.workouts.all():
        workout_count_all, workout_count_not_original = get_workout_originality_values(workout.id, user_id)

        count_all += workout_count_all
        count_not_original += workout_count_not_original

        count_all += 1
        if workout.original:
            count_not_original += 1
    
    return count_all, count_not_original

def get_originality(count_all, count_not_original):
    percentage = (count_not_original / count_all) * 100

    return True if percentage < 80 else False

