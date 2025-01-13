from django.urls import path
from trainers.views import (
                            TrainerView,
                            WorkHoursGetPutView,
                            ExerciseView,
                            ExerciseDetailView,
                            WorkoutExerciseView,
                            WorkoutView,
                            WorkoutDetailView,
                        )

urlpatterns = [
     path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
     path('trainers/', TrainerView.as_view(), name='trainers'),

     path('work_hours/<int:trainer_id>/', WorkHoursGetPutView.as_view(),
          name='work_hours_detail'),

     path('exercises/<int:exercise_id>/', ExerciseDetailView.as_view(),
          name='exercise_detail'),
     path('exercises/', ExerciseView.as_view(),
          name='exercises'),

     path('workout_exercises/<int:exercise_id>/',
          WorkoutExerciseView.as_view(),
          name='workout_exercises'),

     path('workouts/<int:workout_id>/', WorkoutDetailView.as_view(),
          name='workout_detail'),
     path('workouts/', WorkoutView.as_view(),
          name='workouts'),
]