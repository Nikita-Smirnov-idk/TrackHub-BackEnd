from rest_framework.test import APITestCase
from trainers.models import (
    WorkHours,
    Experience,
)
from clients.models import (
    TrainersOfCLient,
)
from django.urls import reverse
from rest_framework import status
from trainers.serializers import (
    WorkHoursSerializer,
    ExperienceSerializer,
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
        self.user.trainer.is_public = True
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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


class ExperienceViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user_1 = self.User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=True,
        )
        self.user_1.trainer.is_public = True
        self.user_1.trainer.save()
        self.user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=False,
        )

        self.experience = Experience.objects.create(
            trainer=self.user_1.trainer,
            position='test',
            company_name='test',
            start_date='2020-01-01',
            end_date='2020-05-01',
        )

        self.experience_url = reverse('experiences')
        self.experience_detail_url = reverse(
            'experience_detail',
            kwargs={'experience_id': self.experience.id}
        )
        self.experiences_of_trainer_url = reverse(
            'experiences_of_trainer',
            kwargs={'trainer_id': self.user_1.trainer.id}
        )

    def test_get_detail_with_valid_data_as_trainer(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            ExperienceSerializer(self.experience).data,
        )

    def test_get_detail_with_valid_data_as_client(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            ExperienceSerializer(self.experience).data,
        )

    def test_get_detail_with_not_public(self):
        self.client.force_authenticate(user=self.user_2)
        self.user_1.trainer.is_public = False
        self.user_1.trainer.save()
        response = self.client.get(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_detail_with_client_of_trainer(self):
        self.trainer_of_client = TrainersOfCLient.objects.create(
            client=self.user_2.client,
            trainer=self.user_1.trainer,
            found_by_link=True,
        )
        self.user_1.trainer.is_public = False
        self.user_1.trainer.save()

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(self.experience_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            ExperienceSerializer(self.experience).data,
        )

    def test_get_detail_non_active(self):
        self.trainer_of_client = TrainersOfCLient.objects.create(
            client=self.user_2.client,
            trainer=self.user_1.trainer,
            found_by_link=True,
        )
        self.user_1.trainer.is_active = False
        self.user_1.trainer.save()
        self.assertFalse(self.user_1.trainer.is_public)

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(self.experience_detail_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_detail_non_existing(self):
        self.user_1.trainer.is_public = True
        self.user_1.trainer.save()

        wrong_experience_detail_url = reverse(
            'experience_detail',
            kwargs={'experience_id': self.experience.id+1000}
        )

        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(wrong_experience_detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_invalid_data_1(self):
        data = {
            'trainer': self.user_1.trainer,
            'position': 'test',
            'company_name': 'test',
            'start_date': '2020-01-01',
            'end_date': '2020-01-01',
        }

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.experience_detail_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invalid_data_2(self):
        data = {
            'position': 'test',
            'company_name': 'test',
            'start_date': '2020-01-01asdasd',
            'end_date': '2020-01-01',
        }

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.experience_detail_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invalid_user(self):
        data = {
            'position': 'test',
            'company_name': 'test',
            'start_date': '2020-01-01asdasd',
            'end_date': '2020-01-01',
        }

        self.client.force_authenticate(user=self.user_2)
        response = self.client.put(self.experience_detail_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_invalid_data_3(self):
        data = {
            'position': 'test_new',
            'company_name': 'test_new',
            'start_date': '2020-04-02',
            'end_date': '2020-03-01',
        }

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.experience_detail_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invalid_data_4(self):
        data = {
            'position': 'test_new',
            'company_name': 'test_new',
            'start_date': '18/01/2025',
            'end_date': '12/01/2025',
        }

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.experience_detail_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_valid_data(self):
        data = {
            'position': 'test_new',
            'company_name': 'test_new',
            'start_date': '2020-02-02',
            'end_date': '2020-03-01',
        }

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(self.experience_detail_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            ExperienceSerializer(
                Experience.objects.get(id=self.experience.id)
            ).data
        )

    def test_delete_unauthenticated(self):
        response = self.client.delete(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_valid_data(self):
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Experience.objects.filter(
            id=self.experience.id).exists()
        )

    def test_delete_wrong_user(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.experience_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_uninauthenticated(self):
        response = self.client.post(self.experience_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_valid_data(self):
        count_old = Experience.objects.count()
        data = {
            'position': 'test',
            'company_name': 'test',
            'start_date': '2020-01-01',
            'end_date': '2020-10-01',
        }
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.experience_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            count_old + 1,
            Experience.objects.count()
        )

    def test_post_invalid_data(self):
        data = {
            'position': 'test',
            'company_name': 'test',
            'start_date': '2020-10-01',
            'end_date': '2020-10-01',
        }
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.experience_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_experiences_of_trainer(self):
        experience_2 = Experience.objects.create(
            trainer=self.user_1.trainer,
            position='test3',
            company_name='test3',
            start_date='2020-01-01',
            end_date='2020-10-01',
        )
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.experiences_of_trainer_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data),
            Experience.objects.filter(trainer=self.user_1.trainer).count()+1
        )
        self.assertEqual(
            response.data[1],
            ExperienceSerializer(self.experience).data
        )
        self.assertEqual(
            response.data[2],
            ExperienceSerializer(experience_2).data
        )
