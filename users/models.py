from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import EmailValidator
from TrackHub import settings
from users.validators import (
    password_validator,
    validate_image_size,
)
from django.contrib.postgres.indexes import GinIndex
import boto3
from django.core.exceptions import ImproperlyConfigured
from TrackHub.trackhub_bucket import TrackHubMediaStorage


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    """

    def create_user(
        self,
        email,
        password=None,
        is_trainer=False,
        **extra_fields
    ):
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)
        unique_identifier = f"{email}:{is_trainer}"

        user = self.model(
            email=email,
            unique_identifier=unique_identifier,
            is_trainer=is_trainer,
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            # Отмечаем, что пароль нельзя использовать
            user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    """
    email = models.EmailField(validators=[EmailValidator()])
    password = models.CharField(max_length=128,
                                validators=[password_validator])
    avatar = models.ImageField(
        null=True,
        blank=True,
        validators=[validate_image_size],
        storage=TrackHubMediaStorage()
    )

    unique_identifier = models.CharField(max_length=512, unique=True)
    username = None

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_public = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_trainer = models.BooleanField(default=False)  # Custom field
    timezone = models.CharField(max_length=50, default='UTC')

    objects = CustomUserManager()

    USERNAME_FIELD = 'unique_identifier'
    REQUIRED_FIELDS = ['email']

    class Meta:
        indexes = [
            GinIndex(
                fields=['first_name'],
            ),
            GinIndex(
                fields=['last_name'],
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'is_trainer'],
                name='unique_email_is_trainer',
            )
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Check if we are updating an existing user
        if self.pk:
            # Get the current instance
            old_instance = CustomUser.objects.get(pk=self.pk)

            # Check if the avatar has changed and delete the
            # old one from Yandex Storage
            if old_instance.avatar and old_instance.avatar != self.avatar:
                # Delete the old avatar from Yandex Storage
                old_avatar_path = old_instance.avatar.name
                self.delete_old_image_from_yandex_storage(old_avatar_path)

        # Save the new avatar

        if not self.unique_identifier:
            self.unique_identifier = f"{self.email}:{self.is_trainer}"

        # Сохраняем объект User
        super().save(*args, **kwargs)

        # Проверяем, есть ли связанные объекты (чтобы избежать дублирования)
        if not hasattr(self, 'user_rating'):
            RatingOfUser.objects.create(user=self)

    def delete_old_image_from_yandex_storage(self, file_path):
        """Deletes the old avatar from Yandex Object Storage"""
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
                "Error deleting old avatar from Yandex Object Storage:" +
                f" {str(e)}"
            )

    def set_password(self, raw_password):
        # Validate the password
        password_validator(raw_password)

        # Call the base method to hash the password
        super().set_password(raw_password)


class RatingOfUser(models.Model):
    user = models.OneToOneField(CustomUser,
                                on_delete=models.CASCADE,
                                related_name="user_rating")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    is_rating_active = models.BooleanField(default=False)

    def update_rating(self):
        reviews = Review.objects.filter(user=self.user)
        if reviews.exists():
            self.rating = sum(
                [review.rating for review in reviews]
                ) / len(reviews)
            self.is_rating_active = True
            self.save()
        else:
            self.is_rating_active = False
            self.save()


class Review(models.Model):
    user = models.ForeignKey(CustomUser,
                             on_delete=models.CASCADE,
                             related_name='reviews')
    review_text = models.TextField(blank=True)
    # Рейтинг от 0 до 5
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(6)])
    date = models.DateTimeField(auto_now_add=True)
    for_user = models.ForeignKey(CustomUser,
                                 on_delete=models.CASCADE,
                                 related_name='received_reviews')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'for_user'], name='unique_user_for_user'
            )
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Сохраняем запись
        if hasattr(self.for_user, 'user_rating'):
            self.user.user_rating.update_rating()  # Обновляем стаж

    def delete(self, *args, **kwargs):
        user = self.user
        super().delete(*args, **kwargs)  # Удаляем запись
        if hasattr(user, 'user_rating'):
            user.user_rating.update_rating()  # Обновляем стаж

    def __str__(self):
        return f"Review for {self.for_user.first_name}" + \
               f" by {self.user.first_name}"
