from django.http import QueryDict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import (
                                CustomUserGetSerializer,
                                CustomUserSerializer,
                                ReviewSerializer,
                                CustomUserAvatarSerializer,
                            )
from users.models import Review, CustomUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO


from django.conf import settings
from django.core.mail import send_mail
import jwt
from datetime import datetime, timedelta

class SendVerificationEmailView(APIView):
    """
    Отправка письма для подтверждения email.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = CustomUser.objects.get(email=request.user.email)

        # Создание токена для email
        token_payload = {
            'user_id': user.id,
            'exp': datetime.now() + timedelta(hours=24),
        }
        token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm='HS256')

        # Ссылка для iOS приложения
        confirm_url = f"TrackHub://verify-email?token={token}"

        # Отправка письма
        send_mail(
            subject="Подтверждение регистрации",
            message=f"Подтвердите ваш email:\n\n{confirm_url}\n\nСсылка действительна 24 часа.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        return Response({"message": "На ваш email отправлена ссылка для подтверждения."}, status=status.HTTP_201_CREATED)


class CustomUserRegisterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email и пароль обязательны"}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Пользователь уже существует"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    """
    Подтверждение email через токен (полученный в iOS-приложении).
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response({"error": "Токен обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = get_object_or_404(CustomUser, id=payload['user_id'])

            if user.is_verified:
                return Response({"message": "Email уже подтвержден."}, status=status.HTTP_400_BAD_REQUEST)

            user.is_verified = True
            user.save()
            return Response({"message": "Email успешно подтвержден!"}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({"error": "Срок действия токена истек."}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.DecodeError:
            return Response({"error": "Неверный токен."}, status=status.HTTP_400_BAD_REQUEST)


class AccountDeletionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Проверяем валидность токена
            token = RefreshToken(refresh_token)

            # Проверяем, что токен принадлежит текущему пользователю
            if str(token["user_id"]) != str(user.id):
                return Response(
                    {
                        "error":
                        "This refresh token does not belong" +
                        "to the current user."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                    )

            # Добавляем Refresh Token в чёрный список
            token.blacklist()
        except Exception:
            return Response(
                        {
                            "error":
                            "Invalid refresh token."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                        )

        user.delete()
        return Response({"detail": "Account deleted successfully"},
                        status=204)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"},
                            status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"},
                            status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        raw_email = request.data.get('email')
        email = BaseUserManager.normalize_email(raw_email)

        password = request.data.get('password')

        if any([not email, not password]):
            return Response({'error': 'Invalid credentials'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            email=email, password=password
        )

        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_id': user.id
                }
            )
        else:
            try:
                if get_object_or_404(CustomUser, email=email):
                    return Response({'error': 'Password is incorrect'},
                                    status=status.HTTP_401_UNAUTHORIZED)
            except Exception:
                return Response({'error': 'Not found such account'},
                                status=status.HTTP_404_NOT_FOUND)


class ChangeUserDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data,
                                          context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def get_authenticators(self):
        if self.request.method == 'GET':
            # Disable authentication for GET requests
            return []
        # Default authentication for other methods
        return [JWTAuthentication()]

    def put(self, request, profile_id):
        if not (
            request.user.is_authenticated and request.user.id == profile_id
        ):
            return Response(
                {"detail": "You are not authorized to edit this profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            user = get_object_or_404(CustomUser, pk=profile_id)
        except Exception:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = CustomUserSerializer(user, data=request.data,
                                          context={'request': request},
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, profile_id):
        try:
            user = get_object_or_404(CustomUser, pk=profile_id)
        except Exception:
            return Response({"error": "Profile not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = CustomUserGetSerializer(
            user, context={'request': request}
        )
        if request.user.id == profile_id:
            return Response(serializer.data, status=status.HTTP_200_OK)
        if not user.is_public:
            return Response({"error": "Access denied"},
                            status=status.HTTP_403_FORBIDDEN)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewWithPkView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'get', 'delete']

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def put(self, request, review_id):
        if 'user_id' in request.data:
            return Response(
                {'message': 'You can not have user in ' +
                 'request data. You already have it in url.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        review = get_object_or_404(Review, pk=review_id)

        if review.user != request.user:
            return Response(
                {"detail": "You are not authorized to edit this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Use partial=True for PATCH
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, review_id):
        if review_id:
            review = get_object_or_404(Review, pk=review_id)
            serializer_review = ReviewSerializer(review)
            return Response(serializer_review.data, status=status.HTTP_200_OK)

    def delete(self, request, review_id):
        if request.user.id != int(request.data['user_id']):
            return Response(
                {"detail": "You are not authorized to delete this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        review = get_object_or_404(Review, pk=review_id)
        if review.user != request.user:
            return Response(
                {"detail": "You are not authorized to delete this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        review.delete()
        return Response({'message': 'Review deleted successfully'},
                        status=status.HTTP_204_NO_CONTENT)


class ReviewView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'get']

    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to access GET requests
            return [AllowAny()]
        # Require authentication for other methods
        return [IsAuthenticated()]

    def post(self, request):
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = True
        request.data["user_id"] = request.user.id
        if isinstance(request.data, QueryDict):  # optional
            request.data._mutable = False

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Review created successfully'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        review = Review.objects.filter(for_user=request.data['for_user_id'])
        serializer_review = ReviewSerializer(review, many=True)
        return Response(serializer_review.data, status=status.HTTP_200_OK)


class AvatarView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'delete']

    def get_permissions(self):
        return [IsAuthenticated()]

    def post(self, request, *args, **kwargs):

        user = request.user
        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка размера файла (не более 5 МБ)
        if avatar.size > 200 * 1024:  # 5 МБ в байтах
            return Response({"error": "File size exceeds 200 KB."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Открываем изображение
            image = Image.open(avatar)
            # Удаляем старую аватарку, если она есть
            if user.avatar:
                user.avatar.delete(save=False)
            
            buffer = BytesIO()
            image.save(buffer, format="JPEG")

            # Сохраняем сжатое изображение
            user.avatar.save(avatar.name, ContentFile(buffer.getvalue()), save=False)
            user.save()
            
            return Response({"avatar_url": user.avatar.url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        user = request.user
        # Delete the avatar from S3 if it exists
        if user.avatar:
            user.avatar.delete(save=False)  # Delete the file from S3
            user.avatar = None  # Set the avatar field to None
            user.save()
        
        return Response(status=status.HTTP_200_OK)