from django.urls import path
from workout_manager.views import (
                            ExerciseView,
                            ExerciseDetailView,
                            WorkoutExerciseView,
                            WorkoutView,
                            WorkoutDetailView,
                        )

urlpatterns = [
    path(
        'exercises/<int:exercise_id>/',
        ExerciseDetailView.as_view(),
        name='exercise_detail'
    ),
    path(
        'exercises/',
        ExerciseView.as_view(),
        name='exercises'
    ),

    path(
        'workout_exercises/<int:exercise_id>/',
        WorkoutExerciseView.as_view(),
        name='workout_exercises'
    ),

    path(
        'workouts/<int:workout_id>/',
        WorkoutDetailView.as_view(),
        name='workout_detail'
    ),
    path(
        'workouts/',
        WorkoutView.as_view(),
        name='workouts'
    ),
]
