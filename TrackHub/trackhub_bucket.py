from storages.backends.s3boto3 import S3Boto3Storage
import os
from TrackHub.settings import AWS_STORAGE_BUCKET_NAME


class TrackHubMediaStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = 'media'

    def url(self, name):
        """Generate a URL representation for stored files."""
        domain = os.getenv("AWS_S3_CUSTOM_DOMAIN")
        name = name.replace("/", "%2F")

        return f"https://{domain}/{self.location}%2F{name}"


class TrackHubStaticStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = 'static'