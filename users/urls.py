from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import path
from users.views import CustomUserRegisterView, AccountDeletionView, LogoutView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Эндпоинт для получения токена
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Эндпоинт для обновления токена
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Эндпоинт для проверки токена
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("register/", CustomUserRegisterView.as_view(), name="register"),
    path('delete-account/',
         AccountDeletionView.as_view(),
         name='account-deletion'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', obtain_auth_token, name='login'),
]
