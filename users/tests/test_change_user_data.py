from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse



class UserChangeDataTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='Testuserone',
        )
        self.url = reverse("account")

    def test_put_authenticated_user_with_valid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url,
                                   data={'first_name': 'Artaman',
                                         },)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'],
                         self.user_model.objects.
                         get(email=self.user.email).first_name)

    def test_put_unauthenticated_user_with_valid_data(self):
        response = self.client.put(self.url,
                                   data={'first_name': 'Artaman',
                                         },)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(self.user_model.objects.
                         get(email=self.user.email).first_name, 'Artaman')

    def test_put_authenticated_user_with_more_valid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url,
                                   data={'email': 'testuser2@example.com',
                                         'first_name': 'Testuser',
                                         'last_name': 'Artamanov',
                                         },)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'],
                         self.user_model.objects.
                         get(email=response.data['email']).last_name)
        self.assertEqual(response.data['first_name'],
                         self.user_model.objects.
                         get(email=response.data['email']).first_name)
        self.assertEqual(response.data['email'],
                         self.user_model.objects.
                         get(email=response.data['email']).email)