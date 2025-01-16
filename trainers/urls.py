from django.urls import path
from trainers.views import (
                            TrainerView,
                            WorkHoursGetPutView,
                        )

urlpatterns = [
     path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
     path('trainers/', TrainerView.as_view(), name='trainers'),

     path('work_hours/<int:trainer_id>/', WorkHoursGetPutView.as_view(),
          name='work_hours_detail'),
]
