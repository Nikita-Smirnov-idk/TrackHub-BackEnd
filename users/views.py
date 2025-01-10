from django.http import QueryDict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import (
                                CustomUserGetSerializer,
                                CustomUserSerializer,
                                ReviewSerializer,
                            )
from users.models import Review, CustomUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import BaseUserManager


class CustomUserRegisterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data,
                                          context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        user = authenticate(email=email,
                            password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh),
                             'access': str(refresh.access_token)})
        else:
            try:
                if get_object_or_404(CustomUser, email=email):
                    return Response({'error': 'Password is incorrect'},
                                    status=status.HTTP_401_UNAUTHORIZED)
            except Exception:
                return Response({'error': 'Not found such account'},
                                status=status.HTTP_404_NOT_FOUND)


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
        if not (request.user.is_authenticated and request.user.id == profile_id):
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
        if not user.is_public:
            return Response({"error": "Access denied"},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = CustomUserGetSerializer(user, context={'request': request})
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
