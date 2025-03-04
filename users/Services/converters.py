import os


def avatar_to_representation(avatar):
    if not avatar:
        return None
    url = os.getenv("AWS_S3_GET_IMAGE_DOMAIN")
    return f"{url}{avatar.split('/')[-1]}"