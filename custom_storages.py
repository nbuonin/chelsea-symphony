from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.STATICFILES_BUCKET


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.MEDIAFILES_BUCKET
