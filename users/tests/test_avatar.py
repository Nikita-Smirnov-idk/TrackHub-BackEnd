from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
import os
import boto3
from botocore.exceptions import NoCredentialsError
from django.test import TestCase


class AvatarUploadAPITestCase(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser1',
            is_trainer=False,
        )
        self.client.force_authenticate(user=self.user)

        self.url = reverse('avatar')

        dummy_image_path = os.path.join(
            'users', 'tests', 'media', 'avatar_test.png'
        )
        with open(dummy_image_path, 'rb') as image_file:
            self.test_image = SimpleUploadedFile(
                name='avatar.png',
                content=image_file.read(),
                content_type='image/png'
            )

    @patch('storages.backends.s3boto3.S3Boto3Storage._save')
    def test_upload_avatar_invalid_file(self, mock_save):
        """
        Test uploading a non-image file as an avatar.
        """
        invalid_file = SimpleUploadedFile(
            'not_an_image.txt',
            b'This is not an image.',
            content_type='text/plain'
        )

        response = self.client.post(
            self.url, {'avatar': invalid_file}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)

    @patch('storages.backends.s3boto3.S3Boto3Storage._save')
    def test_upload_avatar_too_large(self, mock_save):
        """
        Test uploading an image file that exceeds the size limit.
        """
        large_image = SimpleUploadedFile(
            'large_avatar.jpg',
            b'a' * (300 * 1024),
            content_type='image/jpeg'
        )

        response = self.client.post(
            self.url, {'avatar': large_image}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_avatar_unauthenticated(self):
        """
        Test that unauthenticated users cannot upload an avatar.
        """
        self.client.logout()

        response = self.client.post(
            self.url, {'avatar': self.test_image}, format='multipart'
        )

        self.assertEqual(response.status_code, 401)


class YandexStorageIntegrationTestCase(APITestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='testuser1@example.com',
            password='Securepassword123',
            first_name='testuser1',
            is_trainer=False,
        )
        self.url = reverse('avatar')
        # Initialize the Yandex S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://storage.yandexcloud.net',
            aws_access_key_id='YOUR_ACCESS_KEY',
            aws_secret_access_key='YOUR_SECRET_KEY'
        )
        self.bucket_name = 'your-bucket-name'
        self.dummy_image_path = os.path.join(
            'users', 'tests', 'media', 'avatar_test.png'
        )
        with open(self.dummy_image_path, 'rb') as image_file:
            self.file = SimpleUploadedFile(
                name='avatar.png',
                content=image_file.read(),
                content_type='image/png'
            )

    def test_file_upload_to_yandex_storage(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url, {'avatar': self.file}, format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        # After saving, get the file key (or path) from your model
        self.user.refresh_from_db()
        file_key = self.user.avatar.name

        # Try to fetch the file from Yandex Object Storage
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=file_key
            )
            self.assertEqual(
                response['ResponseMetadata']['HTTPStatusCode'], 200
            )  # File exists
        except NoCredentialsError:
            self.fail("Credentials missing for Yandex Object Storage")
