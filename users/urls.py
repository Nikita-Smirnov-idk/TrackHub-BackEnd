from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import path
from users.views import (
                            AccountWithPkView,
                            AccountView,
                            LogoutView,
                            ReviewView,
                            ReviewWithPkView,
                            LoginView,
                            AvatarView,
                            EmailView,
                        )

urlpatterns = [
    # Токены
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Аккаунты
    path('account/', AccountView.as_view(), name='account'),
    path('account/<int:account_id>/', AccountWithPkView.as_view(), name='account_detail'),
    path('avatar/', AvatarView.as_view(), name='avatar'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', LoginView.as_view(), name='login'),

    # Emails
    path('email/', EmailView.as_view(), name='email'),

    # Reviews
    path('reviews/', ReviewView.as_view(), name='review'),
    path('reviews/<int:review_id>/', ReviewWithPkView.as_view(), name='review_detail'),
]
