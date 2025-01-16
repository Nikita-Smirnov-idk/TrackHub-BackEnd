from rest_framework.test import APITestCase
from trainers.models import (
    WorkHours,
)
from clients.models import (
    TrainersOfCLient,
)
from django.urls import reverse
from rest_framework import status
from trainers.serializers import (
    WorkHoursSerializer,
)
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
        self.work_hours = WorkHours.objects.get(trainer=self.user.trainer)
        self.work_hours_url = reverse(
            'work_hours_detail',
            kwargs={'trainer_id': self.user.trainer.id}
        )
        self.user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=True,
        )
        self.user_3 = self.User.objects.create_user(
            email='testuser3@example.com',
            password='Securepassword123',
            first_name='testuser3',
            is_trainer=False,
        )
        self.trainer_of_client = TrainersOfCLient.objects.create(
            client=self.user_3.client,
            trainer=self.user.trainer,
            found_by_link=True,
        )
        self.user_3.client.trainers_of_client.add(self.trainer_of_client)

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
        response = self.client.get(self.work_hours_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def test_put_work_hours_dif_users(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'trainer_id': self.user_2.trainer.id,
            'start_time': '12:00:00',
            'end_time': '17:00:00'
        }
        response = self.client.put(self.work_hours_url, data=data)
        self.user_2.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_work_hours_with_followed_by_link(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.get(self.work_hours_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            WorkHoursSerializer(self.work_hours).data
        )
