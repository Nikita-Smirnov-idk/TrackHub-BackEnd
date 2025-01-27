from rest_framework.test import APITestCase
import boto3
from TrackHub.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_ENDPOINT_URL,
    AWS_STORAGE_BUCKET_NAME,
    )
import logging
import os


class YandexStorageConnectionTes(APITestCase):
    def test_connection_with_yandex_storage(self):
        s3 = boto3.client(
            's3',
            endpoint_url='https://storage.yandexcloud.net',
        )

        # Создать новый бакет
        s3.create_bucket(Bucket='track-hub-12312312123123123')

        # Загрузить объекты в бакет

        ## Из строки
        s3.put_object(Bucket='track-hub-12312312123123123', Key='object_name', Body='TEST')