from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        BaseUserManager,
                                        PermissionsMixin)


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Отмечаем, что пароль нельзя использовать
            user.set_unusable_password()
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
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_trainer = models.BooleanField(default=False)  # Custom field

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


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
        return f"Review for {self.for_user.name} by {self.user.name}"