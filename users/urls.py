from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import path
from users.views import (
                            CustomUserRegisterView,
                            AccountDeletionView,
                            LogoutView,
                            ReviewView,
                            ReviewWithPkView,
                            LoginView,
                            ProfileView,
                            ChangeUserDataView,
                        )

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
         name='account_deletion'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', LoginView.as_view(), name='login'),
    path(
        'change_user_data/',
        ChangeUserDataView.as_view(),
        name='change_user_data/'
    ),
    path('reviews/', ReviewView.as_view(), name='review'),
    path(
        'reviews/<int:review_id>/',
        ReviewWithPkView.as_view(),
        name='review_detail'
    ),
    path('profile/<int:profile_id>/', ProfileView.as_view(), name='profile'),
]
