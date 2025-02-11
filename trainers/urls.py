from django.urls import path
from trainers.views import (
                         #    TrainerView,
                            WorkHoursGetPutView,
                            ExperienceView,
                            ExperiencesOfTrainerView,
                            ExperienceDetailView,
                            TrainerDetailView,
                            TrainerChangeView,
                            TrainerSearchView,
                            GymCreateView,
                            GymChangeView,
                        )

urlpatterns = [
     # path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
     # path('trainers/', TrainerView.as_view(), name='trainers'),
     path('trainers/', TrainerSearchView.as_view(), name='trainer-search'),
     path('work_hours/<int:trainer_id>/', WorkHoursGetPutView.as_view(),
          name='work_hours_detail'),

     path('experiences/', ExperienceView.as_view(), name='experiences'),
     path('experiences/<int:experience_id>/', ExperienceDetailView.as_view(),
          name='experience_detail'),
     path('experiences_of_trainer/<int:trainer_id>/',
          ExperiencesOfTrainerView.as_view(), name='experiences_of_trainer'),
     path('trainer/<int:trainer_id>/', TrainerDetailView.as_view(), name='trainer_detail'),
     path('trainer/change_data', TrainerChangeView.as_view(), name='trainer_change'),
     path('gym/create', GymCreateView.as_view(), name='create_gym'),
     path('gym/<int:gymId>/', GymChangeView.as_view(), name='change_gym')
]
