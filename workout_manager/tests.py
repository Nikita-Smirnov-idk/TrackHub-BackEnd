from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from workout_manager.models import (
    Exercise,
    ExerciseCategory,
    Workout,
    WorkoutExercise,
)
from workout_manager.serializers import (
    ExerciseSerializer,
)
from users.models import CustomUser


class ExerciseViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=True,
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
            is_trainer=True,
        )
        self.exercise_url = reverse('exercises')
        self.detail_exercise_url = 'exercise_detail'
        self.exercise_1 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test1',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_2 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test2',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_1.shared_with.add(self.user_2)

    def test_get_exercises(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.exercise_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_shared_exercises(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(self.exercise_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], self.exercise_1.name)

    def test_get_public_exercises(self):
        Exercise.objects.create(
            is_public=True,
            created_by=None,
            name='test3',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.exercise_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_non_authenticated(self):
        Exercise.objects.create(
            is_public=True,
            created_by=None,
            name='test4',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )
        response = self.client.get(self.exercise_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_detail_exercise(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, ExerciseSerializer(self.exercise_1).data
        )

    def test_get_detail_unauthorized(self):
        response = self.client.get(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_detail_shared(self):
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, ExerciseSerializer(self.exercise_1).data
        )

    def test_post_unauthenticated(self):
        data = {
            'name': 'test3',
            'description': 'test',
            'category': ExerciseCategory.objects.get(name='Растяжка').id,
            'is_public': True,  # changed on backend
        }
        response = self.client.post(self.exercise_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_valid_data(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': ExerciseCategory.objects.get(name='Растяжка').id,
            'is_public': True,  # changed on backend
        }
        response = self.client.post(self.exercise_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Exercise.objects.filter(name='test3').count(),
            1
        )

    def test_post_valid_data_2(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': ExerciseCategory.objects.get(name='Растяжка').id,
            'is_public': True,  # changed on backend
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id,  # changed on backend
            'shared_with': [
                CustomUser.objects.get(
                    email='testuser2@example.com'
                ).id,
            ]
        }
        response = self.client.post(self.exercise_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Exercise.objects.filter(name='test3').count(),
            1
        )
        self.assertEqual(
            Exercise.objects.filter(name='test3').first().created_by,
            CustomUser.objects.get(email='testuser@example.com')
        )
        self.assertEqual(
            Exercise.objects.filter(name='test3').first().shared_with.first(),
            CustomUser.objects.get(email='testuser2@example.com')
        )

    def test_post_invalid_data(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': 50,
            'is_public': True,
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id  # changed on backend
        }
        response = self.client.post(self.exercise_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_with_automatically_changed_to_valid_data(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': 4,
            'is_public': True,
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id,  # changed on backend
            'extra_field': 'extra'
        }
        response = self.client.put(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            ExerciseSerializer(
                Exercise.objects.filter(name='test3').first()
            ).data
        )

    def test_put_invalid_data(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': 40,
            'is_public': True,
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id  # changed on backend
        }
        response = self.client.put(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_unauthenticated(self):
        data = {
            'name': 'test3',
            'description': 'test',
            'category': 4,
            'is_public': True,
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id,  # changed on backend
            'extra_field': 'extra'
        }
        response = self.client.put(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
            data=data,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unauthenticated(self):
        response = self.client.delete(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_not_shared_with(self):
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test2').first().id
                }
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_by_creator(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Exercise.objects.get(name='test1').created_by,
            None
        )
        self.assertNotEqual(
            Exercise.objects.get(name='test1').shared_with.first(),
            None
        )

    def test_post_deleted_exercise_without_shared_with_and_created_by(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'test3',
            'description': 'test',
            'category': ExerciseCategory.objects.get(name='Растяжка').id,
            'is_public': True,  # changed on backend
            'created_by': CustomUser.objects.get(
                email='testuser2@example.com'
            ).id,  # changed on backend
            'shared_with': [],
        }
        response1 = self.client.post(self.exercise_url, data=data)
        response2 = self.client.delete(
            reverse(
                self.detail_exercise_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test3').first().id
                }
            ),
            data=data
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Exercise.objects.filter(name='test3').count(),
            0
        )


class WorkoutExerciseViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=False,
        )
        self.user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=False,
        )
        self.workout_url = 'workout_exercises'

        self.exercise_1 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test1',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_2 = Exercise.objects.create(
            is_public=False,
            created_by=self.user_2,
            name='test2',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.workout_exercise_1_1 = WorkoutExercise.objects.create(
            exercise=self.exercise_1,
            workout=None,
            sets=2,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_1_1.available_for.add(self.user)

        self.workout_exercise_1_2 = WorkoutExercise.objects.create(
            exercise=self.exercise_1,
            workout=None,
            sets=3,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_1_2.available_for.add(self.user, self.user_2)

        self.workout_exercise_2_1 = WorkoutExercise.objects.create(
            exercise=self.exercise_2,
            workout=None,
            sets=4,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_2_1.available_for.add(self.user)

    def test_get_unauthenticated(self):
        response = self.client.get(
            reverse(
                self.workout_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_authenticated_not_duplicated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                self.workout_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for workout_exercise in response.data:
            self.assertEqual(workout_exercise['exercise']['name'], 'test1')

    def test_get_authenticated_duplicated(self):
        workout_exercise_1_3 = WorkoutExercise.objects.create(
            exercise=self.exercise_1,
            workout=None,
            sets=2,
            reps=12,
            rest_time=60,
        )
        workout_exercise_1_3.available_for.add(self.user)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                self.workout_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            WorkoutExercise.objects.filter(exercise=self.exercise_1).count(), 3
        )
        self.assertEqual(len(response.data), 2)
        for workout_exercise in response.data:
            self.assertEqual(workout_exercise['exercise']['name'], 'test1')

    def test_delete_unauthenticated(self):
        response = self.client.delete(
            reverse(
                self.workout_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete(self):
        self.client.force_authenticate(user=self.user)
        for workout_exercise in WorkoutExercise.objects.filter(
            exercise=self.exercise_1
        ):
            self.assertTrue(
                workout_exercise.available_for.filter(id=self.user.id).exists()
            )
        response = self.client.delete(
            reverse(
                self.workout_url,
                kwargs={
                    'exercise_id':
                    Exercise.objects.filter(name='test1').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for workout_exercise in WorkoutExercise.objects.filter(
            exercise=self.exercise_1
        ):
            self.assertFalse(
                workout_exercise.available_for.filter(id=self.user.id).exists()
            )


class WorkoutViewTests(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
            is_trainer=False,
        )
        self.user_2 = self.User.objects.create_user(
            email='testuser2@example.com',
            password='Securepassword123',
            first_name='testuser2',
            is_trainer=False,
        )
        self.workout_url = reverse('workouts')
        self.detail_workout_url = 'workout_detail'

        self.workout = Workout.objects.create(
            name="test_workout",
            created_by=self.user,
        )

        self.exercise_1 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test1',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_2 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test2',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_1 = Exercise.objects.create(
            is_public=False,
            created_by=self.user,
            name='test1',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.exercise_2 = Exercise.objects.create(
            is_public=False,
            created_by=self.user_2,
            name='test2',
            description='test',
            category=ExerciseCategory.objects.get(name='Растяжка'),
        )

        self.workout_exercise_1_1 = WorkoutExercise.objects.create(
            exercise=self.exercise_1,
            workout=self.workout,
            sets=2,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_1_1.available_for.add(self.user)

        self.workout_exercise_1_2 = WorkoutExercise.objects.create(
            exercise=self.exercise_1,
            workout=None,
            sets=3,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_1_2.available_for.add(self.user)

        self.workout_exercise_2_1 = WorkoutExercise.objects.create(
            exercise=self.exercise_2,
            workout=self.workout,
            sets=4,
            reps=12,
            rest_time=60,
        )
        self.workout_exercise_2_1.available_for.add(self.user)

    def test_get_unauthenticated(self):
        response = self.client.get(
            reverse(
                self.detail_workout_url,
                kwargs={
                    'workout_id':
                    Workout.objects.filter(name='test_workout').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse(
                self.detail_workout_url,
                kwargs={
                    'workout_id':
                    Workout.objects.filter(name='test_workout').first().id
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
