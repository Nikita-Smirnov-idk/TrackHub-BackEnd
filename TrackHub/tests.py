from rest_framework.test import APITestCase
import boto3
import logging
import os
from django.conf import settings


# class StorageS3ConnectionTest(APITestCase):
#     def test_connection_with_s3_storage(self):
        
#         # Авторизация
#         s3 = boto3.client(
#             service_name='s3',
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,  # Замените на ваш ACCESS_KEY
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,  # Замените на ваш SECRET_KEY
#             endpoint_url=settings.AWS_S3_ENDPOINT_URL,
#             verify=False,
#         )
#         print(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)

#         with open("cat.jpg", "rb") as f:
#             s3.upload_fileobj(f, settings.AWS_STORAGE_BUCKET_NAME, 'cat.jpg')

#         # Скачивание объекта
#         get_object_response = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key="cat.jpg")
#         s3.download_file(settings.AWS_STORAGE_BUCKET_NAME,'cat.jpg','my_file.jpg')

