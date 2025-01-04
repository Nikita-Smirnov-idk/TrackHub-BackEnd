from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
                                                             BlacklistedToken,
                                                            )


class UserCreationTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_create_user(self):
        user = self.User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=False,
        )
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('Securepassword123'))
        self.assertEqual(user.first_name, 'testuser')
        self.assertFalse(user.is_trainer)
        self.assertIsNotNone(user.user_rating)

    def test_create_superuser(self):
        superuser = self.User.objects.create_superuser(
            email='admin@example.com',
            password='Secureadmin123',
            first_name='admin'
        )
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email=None,
                password='Securepassword123',
                first_name='testuser'
            )

    def test_create_superuser_missing_permissions(self):
        with self.assertRaises(ValueError):
            self.User.objects.create_superuser(
                email='admin@example.com',
                password='Secureadmin123',
                first_name='admin',
                is_staff=False,
                is_superuser=False
            )

    def test_unique_email(self):
        self.User.objects.create_user(
            email='unique@example.com',
            password='Password123',
            first_name='uniqueuser'
        )
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                email='unique@example.com',
                password='Password123',
                first_name='anotheruser'
            )

    def test_create_user_with_wrong_password_form(self):
        with self.assertRaises(ValidationError):
            self.User.objects.create_user(
                email='testuser@example.com',
                password='secur',
                first_name='testuser',
                is_trainer=False,
            )

    def test_create_user_with_wrong_email_form(self):
        with self.assertRaises(ValidationError):
            self.User.objects.create_user(
                email='example.com',
                password='Password123',
                first_name='testuser',
                is_trainer=False,
            )


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=False,
        )

        # Эндпоинты для работы с JWT
        self.token_obtain_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
        self.deletion_url = reverse("account_deletion")

    def test_obtain_tokens(self):
        """Проверка получения токенов (Access и Refresh)"""
        response = self.client.post(self.token_obtain_url, {
            'email': 'testuser@example.com',
            'password': 'Securepassword123'
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
            'password': 'Securepassword123'
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
            'password': 'Securepassword123'
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


class AccountDeletionViewTests(APITestCase):
    def setUp(self):
        """
        Подготовка данных для тестов:
        - Создаем тестового пользователя.
        - Генерируем для него токены (Access и Refresh).
        """
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=False,
        )
        self.client.force_authenticate(user=self.user)

        # Генерируем Refresh Token и Access Token
        self.refresh_token = str(RefreshToken.for_user(self.user))
        self.access_token = str(RefreshToken(self.refresh_token).access_token)
        self.deletion_url = reverse("account_deletion")
        self.logout_url = reverse("logout")
        self.token_refresh_url = reverse("token_refresh")

    def test_account_deletion_and_token_blacklist(self):
        """
        Тестирует удаление аккаунта и добавление токена в черный список.
        """
        # Отправляем запрос на удаление аккаунта
        response = self.client.delete(self.deletion_url,
                                      data={"refresh": self.refresh_token})

        # Проверяем, что пользователь был успешно удален
        self.assertEqual(response.status_code, 204)
        self.assertFalse(get_user_model().objects.
                         filter(email="testuser@example.com").exists())

        # Проверяем, что токен был добавлен в черный список
        blacklisted_tokens = BlacklistedToken.objects.filter(
                token__token=self.refresh_token
            )
        self.assertEqual(blacklisted_tokens.count(), 1)

    def test_invalid_refresh_token(self):
        """
        Проверяет, что попытка удаления аккаунта с некорректным
        Refresh Token выдает ошибку.
        """
        invalid_refresh = "invalid_token"

        # Отправляем запрос с некорректным токеном
        response = self.client.delete(self.deletion_url,
                                      data={"refresh": invalid_refresh})

        # Проверяем, что вернулась ошибка
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_account_deletion_without_refresh_token(self):
        """
        Проверяет, что удаление аккаунта без передачи Refresh Token
        все равно успешно удаляет пользователя.
        """
        response = self.client.delete(self.deletion_url)

        # Проверяем, что пользователь был удален
        self.assertEqual(response.status_code, 400)


class RegisterViewTests(APITestCase):
    def setUp(self):
        """
        Подготовка данных для тестов:
        - Создаем тестового пользователя.
        - Генерируем для него токены (Access и Refresh).
        """
        self.valid_data = {
            'email': 'testuser@example.com',
            'password': 'Securepassword123',
            'first_name': 'testuser',
            'is_trainer': False,
        }

        self.invalid_password_data = {
            'email': 'testuser@example.com',
            'password': 'secur',
            'first_name': 'testuser',
            'is_trainer': False,
        }

        self.invalid_email_data = {
            'email': '@example.com',
            'password': 'Securepassword123',
            'first_name': 'testuser',
            'is_trainer': False,
        }

        self.register_url = reverse("register")

    def test_account_register_with_valid_data(self):
        """
        Тестирует удаление аккаунта и добавление токена в черный список.
        """
        # Отправляем запрос на удаление аккаунта
        response = self.client.post(self.register_url,
                                    self.valid_data)

        # Проверяем, что пользователь был успешно удален
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(get_user_model().objects.
                             get(email=self.valid_data['email']))

    def test_account_register_with_invalid_password_data(self):
        """
        Тестирует удаление аккаунта и добавление токена в черный список.
        """
        # Отправляем запрос на удаление аккаунта
        response = self.client.post(self.register_url,
                                    self.invalid_password_data)

        # Проверяем, что пользователь был успешно удален
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().
            objects.
            filter(email=self.invalid_password_data['email']).exists()
        )

    def test_account_register_with_invalid_email_data(self):
        """
        Тестирует удаление аккаунта и добавление токена в черный список.
        """
        # Отправляем запрос на удаление аккаунта
        response = self.client.post(self.register_url,
                                    self.invalid_email_data)

        # Проверяем, что пользователь был успешно удален
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().
            objects.
            filter(email=self.invalid_email_data['email']).exists()
        )


class LoginTests(APITestCase):
    # Adjust the endpoint path as per your project
    login_url = reverse("login")

    def setUp(self):
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com",
            password="Testpassword123"
        )
        self.valid_credentials = {
            "email": "testuser@example.com",
            "password": "Testpassword123",
        }
        self.invalid_credentials = {
            "email": "testuser@example.com",
            "password": "wrongpassword",
        }

    def test_login_with_valid_credentials(self):
        """
        Test that a user can log in with valid credentials.
        """
        response = self.client.post(self.login_url, self.valid_credentials)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming token is returned on successful login
        self.assertIn("refresh", response.data)

    def test_login_with_invalid_credentials(self):
        """
        Test that login fails with invalid credentials.
        """
        response = self.client.post(self.login_url, self.invalid_credentials)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertIn("error", response.data)

    def test_login_with_all_missing_fields(self):
        """
        Test that login fails if required fields are missing.
        """
        response = self.client.post(self.login_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_existing_email_and_missing_password_fields(self):
        """
        Test that login fails if required fields are missing.
        """
        response = self.client.post(self.login_url,
                                    {"email": "testuser@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_nonexisting_email_and_missing_password_fields(self):
        """
        Test that login fails if required fields are missing.
        """
        response = self.client.post(self.login_url,
                                    {"email": "tesasdtuser@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_nonexistent_user(self):
        """
        Test that login fails for a non-existent user.
        """
        response = self.client.post(self.login_url, {
            "email": "nonexistent@example.com",
            "password": "Password123",
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_with_case_insensitive_email(self):
        """
        Test that login works with case-insensitive email.
        """
        response = self.client.post(self.login_url, {
            "email": "testuser@Example.com",  # Same email but different casing
            "password": "Testpassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)


class ReviewCreationTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.create_url = reverse("review")

    def test_create_user(self):
        user_1 = self.User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser1',
            is_trainer=False,
        )
        user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=False,
        )

        review = user_1.reviews.create(for_user=user_2,
                                       rating=5,
                                       review_text='Great trainer!')
        self.assertEqual(review.for_user, user_2)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Great trainer!')
        self.assertIsNotNone(review.date)


class ReviewTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model()
        self.create_url = reverse("review")
        self.detail_review_url = "review_detail"
        self.user_1 = self.user.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser1',
            is_trainer=False,
        )
        self.user_2 = self.user.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=False,
        )
        self.client.force_authenticate(user=self.user_2)

    def test_create_user_with_invalid_data(self):
        response = self.client.post(self.create_url,
                                    data={'for_user': self.user_1,
                                          'review_text': 'Great trainer!',
                                          'user': self.user_2},)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_review(self):
        review = self.user_2.reviews.create(for_user=self.user_1,
                                            rating=5,
                                            review_text='Great trainer!')
        review2 = {
            'id': review.id,
            'rating': 2,
        }
        response = self.client.put(reverse(self.detail_review_url,
                                           args=[review.id]),
                                   data=review2,)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(review2['rating'],
                         self.user_2.reviews.get(id=review.id).rating)


class ProfileTestCase(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.profile_url = "profile"
        self.user = self.user_model.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser1',
            is_trainer=False,
        )

    def test_put_authenticated_user_with_valid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(reverse(self.profile_url,
                                           args=[self.user.pk]),
                                   data={'is_trainer': True,
                                         },)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_trainer'],
                         self.user_model.objects.
                         get(email=self.user.email).is_trainer)

    def test_put_unauthenticated_user_with_valid_data(self):
        response = self.client.put(reverse(self.profile_url,
                                           args=[self.user.pk]),
                                   data={'is_trainer': True,
                                         },)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.user_model.objects.
                         get(email=self.user.email).is_trainer, False)

    def test_put_authenticated_user_with_more_valid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(reverse(self.profile_url,
                                           args=[self.user.pk]),
                                   data={'email': 'testuser2@example.com',
                                         'first_name': 'testuser2',
                                         'is_trainer': True,
                                         },)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_trainer'],
                         self.user_model.objects.
                         get(email=response.data['email']).is_trainer)
        self.assertEqual(response.data['first_name'],
                         self.user_model.objects.
                         get(email=response.data['email']).first_name)
        self.assertEqual(response.data['email'],
                         self.user_model.objects.
                         get(email=response.data['email']).email)

    def test_get_authenticated_user_with_public(self):
        user3 = self.user_model.objects.create_user(
            email='testuser3@example.com',
            password='Securepassword123',
            first_name='testuser3',
            is_trainer=False,
            is_public=True,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(self.profile_url,
                                           args=[user3.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'],
                         'testuser3@example.com')
        self.assertEqual(response.data['first_name'],
                         'testuser3')

    def test_get_not_authenticated_user_without_public(self):
        user3 = self.user_model.objects.create_user(
            email='testuser3@example.com',
            password='Securepassword123',
            first_name='testuser3',
            is_trainer=False,
            is_public=False,
        )
        response = self.client.get(reverse(self.profile_url,
                                   args=[user3.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
