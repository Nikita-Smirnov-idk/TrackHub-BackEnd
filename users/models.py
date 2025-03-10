from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager,
                                        PermissionsMixin)
from django.core.validators import EmailValidator
from TrackHub import settings
from users.validators import (
    validate_image,
    validate_password,
    validate_name,
)
import boto3
from django.core.exceptions import ImproperlyConfigured
from TrackHub.trackhub_bucket import TrackHubMediaStorage
from users.Services.image_handler import generate_default_avatar
from users.Services.delete_instances_from_s3 import delete_instance_from_s3


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    """

    def create_user(
        self,
        email,
        password=None,
        **extra_fields
    ):
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)


        user = self.model(
            email=email,
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
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.
    """
    email = models.EmailField(validators=[EmailValidator()], unique=True, db_index=True)
    password = models.CharField(max_length=128,
                                validators=[validate_password])
    avatar = models.ImageField(
        null=True,
        blank=True,
        validators=[validate_image],
        storage=TrackHubMediaStorage(),
        upload_to="avatars/"
    )

    first_name = models.CharField(max_length=150, validators=[validate_name])
    last_name = models.CharField(max_length=150, blank=True, validators=[validate_name])

    is_public = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    timezone = models.CharField(max_length=50, default='UTC')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

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
                delete_instance_from_s3(old_avatar_path)
            
            if old_instance.email != self.email:
                self.is_verified = False
            
            if old_instance.first_name != self.first_name:
                generate_default_avatar(self.id)

        if self.first_name:
            self.first_name = self.first_name.lower().capitalize()
        if self.last_name:
            self.last_name = self.last_name.lower().capitalize()

        # Сохраняем объект User
        super().save(*args, **kwargs)

        # Проверяем, есть ли связанные объекты (чтобы избежать дублирования)
        if not hasattr(self, 'user_rating'):
            RatingOfUser.objects.create(user=self)

        if not self.avatar:
            generate_default_avatar(self.id)

        
    def delete(self, *args, **kwargs):
        delete_instance_from_s3(self.avatar)

        self.created_exercises.filter(is_published=False).delete()
        self.created_exercises.filter(is_published=True).update(author=None)

        self.created_workouts.filter(is_published=False).delete()
        self.created_workouts.filter(is_published=True).update(author=None)

        self.created_weekly_fitness_plans.filter(is_published=False).delete()
        self.created_weekly_fitness_plans.filter(is_published=True).update(author=None)

        return super().delete(*args, **kwargs)
    

    def set_password(self, raw_password):
        # Validate the password
        validate_password(raw_password)

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
    review_text = models.CharField(max_length=1024, null=True, blank=True)
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
