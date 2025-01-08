from django.urls import path
from trainers.views import (
                            TrainerView,
                            WorkHoursPostView,
                            WorkHoursGetPutView,
                            TrainerWeekendSerializer,
                        )

urlpatterns = [
    path('trainers/', TrainerView.as_view(), name='trainers'),
    path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
    path('work_hours/', WorkHoursPostView.as_view(),
         name='work_hours_create'),
    path('work_hours/<int:trainer_id>/', WorkHoursGetPutView.as_view(),
         name='work_hours_detail'),
    path('trainer_weekend/<int:trainer_id>/', TrainerWeekendSerializer.as_view(), name='trainer_weekend_detail'),
]
