from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from trainers.models import Trainer, Gym
from django.urls import reverse
from django.test import TestCase, override_settings
import tempfile

User = get_user_model()


@override_settings(MEDIA_ROOT='media/')
class TrainerSearchTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='Ванек',
            last_name="Васильев",
            is_trainer=True,
        )
        self.user2 = User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='Василий',
            last_name="Петров",
            is_trainer=True,
        )
        self.user3 = User.objects.create_user(
            email='testuser3@example.com',
            password='Securepassword123',
            first_name='Иван',
            last_name="Кожевников",
            is_trainer=True,
        )
        self.user4 = User.objects.create_user(
            email='testuser4@example.com',
            password='Securepassword123',
            first_name='Даниил',
            last_name="Кожевняк",
            is_trainer=True,
        )
        self.user5 = User.objects.create_user(
            email='testuser5@example.com',
            password='Securepassword123',
            first_name='Андранник',
            last_name="Торосян",
            is_trainer=True,
        )
        gym = Gym.objects.create(
            address="123 Main Street",
            latitude="40.712776",
            longitude="-74.005974",
            trainer=self.user5.trainer
        )
        self.trainer = Trainer.objects.get(user=self.user5)
        self.trainer.description = "фыв боибилдингвыа фывф"
        self.trainer.save()

        self.url = reverse('trainer-search')

    def test_search_by_first_name(self):
        response = self.client.get(self.url, {'search': 'кожевник'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertIn(self.user3.first_name, str(response.data))
        self.assertIn(self.user4.first_name, str(response.data))
    

    def test_search_by_muliple_words(self):
        response = self.client.get(self.url, {'search': 'кожевник ВАСИЬЛев'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
        self.assertIn(self.user1.first_name, str(response.data))
        self.assertIn(self.user2.first_name, str(response.data))
        self.assertIn(self.user3.first_name, str(response.data))
        self.assertIn(self.user4.first_name, str(response.data))

    def test_search_by_discription(self):
        response = self.client.get(self.url, {'search': 'бодибилдинг'})
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn(self.user5.first_name, str(response.data))
    
