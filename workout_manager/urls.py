from django.urls import path
from workout_manager.views import (
    ExercisePublishedView,
    ExercisePersonalView,
    ExerciseSubcribedView,
    ExerciseView,
    ExerciseDetailView,
    ArchivedExerciseView,
    ArchivedExercisesDetailView,

    WorkoutPersonalView,
    WorkoutSubcribedView,
    WorkoutView,
    WorkoutDetailView,
    ArchivedWorkoutView,
    ArchivedWorkoutDetailView,
    WorkoutSubscriptionView,
    WorkoutPublishDetailView,
    WorkoutPublishView,

    WeeklyFitnessPlanPersonalView,
    WeeklyFitnessPlanSubcribedView,
    WeeklyFitnessPlanView,
    WeeklyFitnessPlanDetailView,
    ArchivedWeeklyFitnessPlanView,
    ArchivedWeeklyFitnessPlanDetailView,
    WeeklyFitnessPlanSubscriptionView,
    WeeklyFitnessPlanPublishDetailView,
    WeeklyFitnessPlanPublishView,

    DataForExerciseCreationView,
)

urlpatterns = [
    # Exercises
    path('exercises/', ExerciseView.as_view(), name='exercises'),
    path('exercises/published/', ExercisePublishedView.as_view(), name='exercises_published'),
    path('exercises/personal/', ExercisePersonalView.as_view(), name='exercises_personal'),
    path('exercises/subscribed/', ExerciseSubcribedView.as_view(), name='exercises_subscribed'),
    path('exercises/<int:exercise_id>/', ExerciseDetailView.as_view(), name='exercise_detail'),

    path('exercises/archived/', ArchivedExerciseView.as_view(), name='exercises_archived'),
    path('exercises/archived/<int:exercise_id>/', ArchivedExercisesDetailView.as_view(), name='exercise_archived_detail'), # изменение is_archived на противоположное

    path('exercises/data_for_exercise_creation/', DataForExerciseCreationView.as_view(), name='data_for_exercise_creation'),

    # Workouts
    path('workouts/', WorkoutView.as_view(), name='workouts'),
    path('workouts/personal/', WorkoutPersonalView.as_view(), name='workouts_personal'),
    path('workouts/subscribed/', WorkoutSubcribedView.as_view(), name='workouts_subscribed'),
    path('workouts/<int:workout_id>/', WorkoutDetailView.as_view(), name='workout_detail'),

    path('workouts/archived/', ArchivedWorkoutView.as_view(), name='workouts_archived'),
    path('workouts/archived/<int:workout_id>/', ArchivedWorkoutDetailView.as_view(), name='workout_archived_detail'), # изменение is_archived на противоположное

    path('workouts/subscribtion/<int:workout_id>/', WorkoutSubscriptionView.as_view(), name='workout_subscriptions_detail'),

    path('workouts/publish/', WorkoutPublishView.as_view(), name='workout_publish'),
    path('workouts/publish/<int:workout_id>/', WorkoutPublishDetailView.as_view(), name='workout_publish_detail'),

    # Weekly Fitness Plans
    path('weekly_plans/', WeeklyFitnessPlanView.as_view(), name='weekly_plans'),
    path('weekly_plans/personal/', WeeklyFitnessPlanPersonalView.as_view(), name='weekly_plans_personal'),
    path('weekly_plans/subscribed/', WeeklyFitnessPlanSubcribedView.as_view(), name='weekly_plans_subscribed'),
    path('weekly_plans/<int:plan_id>/', WeeklyFitnessPlanDetailView.as_view(), name='weekly_plan_detail'),

    path('weekly_plans/archived/', ArchivedWeeklyFitnessPlanView.as_view(), name='weekly_plans_archived'),
    path('weekly_plans/archived/<int:plan_id>/', ArchivedWeeklyFitnessPlanDetailView.as_view(), name='weekly_plan_archived_detail'), # изменение is_archived на противоположное

    path('weekly_plans/subscribtion/<int:plan_id>/', WeeklyFitnessPlanSubscriptionView.as_view(), name='weekly_plan_subscriptions_detail'),

    path('weekly_plans/publish/', WeeklyFitnessPlanPublishView.as_view(), name='weekly_plan_publish'),
    path('weekly_plans/publish/<int:plan_id>/', WeeklyFitnessPlanPublishDetailView.as_view(), name='weekly_plan_publish_detail'),
]
