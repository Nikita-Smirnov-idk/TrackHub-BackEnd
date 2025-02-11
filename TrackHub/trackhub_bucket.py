from storages.backends.s3boto3 import S3Boto3Storage

from TrackHub.settings import AWS_STORAGE_BUCKET_NAME


class TrackHubMediaStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = 'media'


class TrackHubStaticStorage(S3Boto3Storage):
    bucket_name = AWS_STORAGE_BUCKET_NAME
    location = 'static'