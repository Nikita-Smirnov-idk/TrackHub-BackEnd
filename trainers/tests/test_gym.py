# tests.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from trainers.models import Trainer, Gym

User = get_user_model()

class GymAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='Ванек',
            last_name="Васильев",
            is_trainer=True,
        )
        self.trainer = self.user.trainer
        self.client = APIClient()
        # Force authentication using the test user
        self.client.force_authenticate(user=self.user)

    def test_create_gym_success(self):
        """
        Test that an authenticated trainer can create a gym using the POST endpoint.
        The trainer field is not provided by the client but set from request.user.trainer.
        """
        url = reverse('create_gym')
        data = {
            "address": "123 Main Street",
            "latitude": "40.712776",
            "longitude": "-74.005974"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Ensure that the response contains a gym_id
        self.assertIn('gym_id', response.data)
        gym = Gym.objects.get(id=response.data['gym_id'])
        self.assertEqual(gym.trainer, self.trainer)

    def test_create_gym_invalid(self):
        """
        Test that invalid data (e.g. missing required fields) returns a 400 response.
        """
        url = reverse('create_gym')
        data = {}  # Missing required fields like address, latitude, longitude
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_gym_success(self):
        """
        Test that a trainer can update his own gym.
        """
        # First, create a gym for this trainer
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=self.trainer
        )
        url = reverse('change_gym', kwargs={'gymId': gym.id})
        data = {"address": "456 New Street"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gym.refresh_from_db()
        self.assertEqual(gym.address, "456 New Street")

    def test_update_gym_unauthorized(self):
        """
        Test that a trainer cannot update a gym owned by another trainer.
        """
        # Create another user and trainer
        other_user = User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='Василий',
            last_name="Петров",
            is_trainer=True,
        )
        # Create a gym for the other trainer
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=other_user.trainer
        )
        gym.refresh_from_db()
        url = reverse('change_gym', kwargs={'gymId': gym.id})
        data = {"address": "456 New Street"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_gym_success(self):
        """
        Test that a trainer can delete his own gym.
        """
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=self.trainer
        )
        url = reverse('change_gym', kwargs={'gymId': gym.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure the gym is deleted
        with self.assertRaises(Gym.DoesNotExist):
            Gym.objects.get(id=gym.id)

    def test_delete_gym_unauthorized(self):
        """
        Test that a trainer cannot delete a gym owned by another trainer.
        """
        other_user = User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='Василий',
            last_name="Петров",
            is_trainer=True,
        )
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=other_user.trainer
        )
        url = reverse('change_gym', kwargs={'gymId': gym.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_different_ids(self):
        """
        Test that a trainer cannot delete a gym owned by another trainer.
        """
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=self.user.trainer
        )
        data = {
            "id": gym.id+1000,
            "address": "123 Main Street",
            "latitude": "40.712776",
            "longitude": "-74.005974"
        }
        gymId = gym.id
        url = reverse('change_gym', kwargs={'gymId': gymId})
        response = self.client.put(url, data, format='json')
        gym.refresh_from_db()
        self.assertEqual(gymId, gym.id)
