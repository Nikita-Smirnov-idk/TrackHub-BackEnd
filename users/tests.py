from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse


class UserCreationTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_create_user(self):
        user = self.User.objects.create_user(
            email='testuser@example.com',
            password='securepassword123',
            username='testuser',
            is_trainer=False,
        )
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('securepassword123'))
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_trainer)

    def test_create_superuser(self):
        superuser = self.User.objects.create_superuser(
            email='admin@example.com',
            password='secureadmin123',
            username='admin'
        )
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email=None,
                password='securepassword123',
                username='testuser'
            )

    def test_create_superuser_missing_permissions(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_superuser(
                email='admin@example.com',
                password='secureadmin123',
                username='admin',
                is_staff=False,
                is_superuser=False
            )

    def test_unique_email(self):
        self.User.objects.create_user(
            email='unique@example.com',
            password='password123',
            username='uniqueuser'
        )
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                email='unique@example.com',
                password='password123',
                username='anotheruser'
            )


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='securepassword123',
            username='testuser',
            is_trainer=False,
        )

        # Эндпоинты для работы с JWT
        self.token_obtain_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")

    def test_obtain_tokens(self):
        """Проверка получения токенов (Access и Refresh)"""
        response = self.client.post(self.token_obtain_url, {
            'email': 'testuser@example.com',
            'password': 'securepassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_is_authorized_endpoint_without_token(self):
        """Проверка доступа к защищённому ресурсу без токена"""
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_is_authorized_endpoint_with_invalid_token(self):
        """Проверка доступа к защищённому ресурсу с невалидным токеном"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """Проверка обновления Access Token с помощью Refresh Token"""
        # Получаем токены
        response = self.client.post(self.token_obtain_url, {
            'email': 'testuser@example.com',
            'password': 'securepassword123'
        })
        refresh_token = response.data['refresh']
        # Отправляем запрос на обновление Access Token
        refresh_response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_logout_blacklist_refresh_token(self):
        """Проверка добавления Refresh Token в чёрный список при logout"""
        # Получаем токены
        response = self.client.post(self.token_obtain_url, {
            'email': 'testuser@example.com',
            'password': 'securepassword123'
        })
        access_token = response.data['access']
        refresh_token = response.data['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        # Logout (добавляем Refresh Token в чёрный список)
        logout_response = self.client.post(self.logout_url, {
            'refresh': refresh_token
        })

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Проверяем, что токен теперь не работает
        refresh_response = self.client.post(self.token_refresh_url, {
            'refresh': refresh_token
        })

        self.assertEqual(refresh_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', refresh_response.data)
        self.assertEqual(refresh_response.data['detail'],
                         'Token is blacklisted')
