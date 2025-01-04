from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import path
from trainers.views import (
                            TrainerView,
                        )

urlpatterns = [
    path('trainers/', TrainerView.as_view(), name='trainers'),
    path('trainers/<int:pk>/', TrainerView.as_view(), name='trainer_detail'),
]
