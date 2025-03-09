import boto3
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def delete_instance_from_s3(file_path):
        """Deletes the old avatar from Yandex Object Storage"""

        if not file_path:
            return

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL
        )
        try:
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                # The file path (including folder) in your bucket
                Key=file_path
            )
        except Exception as e:
            raise ImproperlyConfigured(
                "Error deleting image from Yandex Object Storage:" +
                f" {str(e)}"
            )


def get_instance_path_in_s3(filename):
    path = filename.split('/')[-1]
    path = path.replace("%2F", "/")

    return path