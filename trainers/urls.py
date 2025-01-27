from django.urls import path
from trainers.views import (
                         #    TrainerView,
                            WorkHoursGetPutView,
                            ExperienceView,
                            ExperiencesOfTrainerView,
                            ExperienceDetailView
                        )

urlpatterns = [
     # path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
     # path('trainers/', TrainerView.as_view(), name='trainers'),

     path('work_hours/<int:trainer_id>/', WorkHoursGetPutView.as_view(),
          name='work_hours_detail'),

     path('experiences/', ExperienceView.as_view(), name='experiences'),
     path('experiences/<int:experience_id>/', ExperienceDetailView.as_view(),
          name='experience_detail'),
     path('experiences_of_trainer/<int:trainer_id>/',
          ExperiencesOfTrainerView.as_view(), name='experiences_of_trainer'),
]
