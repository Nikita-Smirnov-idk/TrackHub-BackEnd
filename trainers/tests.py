from rest_framework.test import APITestCase
from users.models import CustomUser
from trainers.models import Trainer, WorkHours
from django.urls import reverse
from rest_framework import status
from trainers.serializers import WorkHoursSerializer
from django.contrib.auth import get_user_model


class WorkHoursViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=True,
        )
        self.work_hours = WorkHours.objects.create(
            trainer=self.user.trainer,
            start_time='10:00:00',
            end_time='18:00:00'
        )
        self.work_hours_url = reverse(
            'work_hours_detail',
            kwargs={'trainer_id': self.user.trainer.id}
        )
        self.work_hours_url_create = reverse(
            'work_hours_create'
        )
        self.user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=True,
        )

    def test_get_work_hours_authenticated_trainer(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.work_hours_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            WorkHoursSerializer(self.work_hours).data
        )

    def test_get_work_hours_unauthenticated_with_public(self):
        trainer = self.User.objects.get(
            email='testuser@example.com').trainer
        trainer.is_public = True
        trainer.save()
        response = self.client.get(self.work_hours_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            WorkHoursSerializer(self.work_hours).data
        )

    def test_get_work_hours_unauthenticated_without_public(self):
        self.user.client.is_public = True

        response = self.client.get(self.work_hours_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_work_hours_with_url_for_post(self):
        trainer = self.User.objects.get(
            email='testuser@example.com').trainer
        trainer.is_public = True
        trainer.save()
        response = self.client.get(self.work_hours_url_create)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_invalid_data_1(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'trainer': self.user.trainer.id,
            'start_time': 'asdda',
            'end_time': '18:00:00'
        }
        response = self.client.post(self.work_hours_url_create, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_data_2(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'trainer': self.user.trainer.id,
            'start_time': '10ф:00:00',
            'end_time': '18:00:00'
        }
        response = self.client.post(self.work_hours_url_create, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_valid_data_2(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'trainer': self.user.trainer.id,
            'start_time': '10:00:00',
            'end_time': '18:00:00'
        }
        response = self.client.post(self.work_hours_url_create, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_valid_data(self):
        self.client.force_authenticate(user=self.user_2)
        data = {
            'trainer': self.user_2.trainer.id,
            'start_time': '11:00:00',
            'end_time': '18:00:00'
        }
        response = self.client.post(self.work_hours_url_create, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            WorkHoursSerializer(WorkHours.objects.get(trainer=self.user_2.trainer)).data
        )

    def test_put_work_hours(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'start_time': '12:00:00',
            'end_time': '17:00:00'
        }
        response = self.client.put(self.work_hours_url, data=data)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            WorkHoursSerializer(self.user.trainer.workhours).data,
        )
