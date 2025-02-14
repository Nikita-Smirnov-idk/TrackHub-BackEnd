from rest_framework import serializers
from users.models import (
    CustomUser,
    Review,
)
from users.validators import password_validator
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.conf import settings


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'password',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        request_method = self.context.get('request').method

        if request_method == 'POST':
            required_fields = ['email', 'password']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(
                        {field: f"{field} is required for creation."}
                    )
            password_validator(data['password'])


        return super().validate(data)

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(
                validated_data['password']
            )
        return super().update(instance, validated_data)


class CustomUserAvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(use_url=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'avatar']
        read_only_fields = ['id']


class CustomUserGetSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'user_rating',
            'avatar',
        ]
        read_only_fields = ['id']
    
    def get_avatar(self, obj):
        if obj.avatar:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}{obj.avatar}"
        return None  


# class RatingOfUserSerializer(serializers.ModelSerializer):
#     user = serializers.PrimaryKeyRelatedField(
#         queryset=CustomUser.objects.all()
#     )

#     class Meta:
#         model = RatingOfUser
#         fields = ['user', 'rating', 'is_rating_active']

#     def validate(self, data):
#         if 'user' in data and RatingOfUser.objects.filter(
#             trainer=data['user']
#         ).exists():
#             raise serializers.ValidationError("RatingOfUser already exists.")
#         return super().validate(data)


class ReviewSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='user',
    )
    for_user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='for_user',
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "user_id",
            "for_user_id",
            "rating",
            "review_text",
            "date"
        ]
        read_only_fields = ["id", "date"]

    def validate(self, data):
        if self.instance is None:
            try:
                _ = Review.objects.get(
                    user=data['user'],
                    for_user=data['for_user']
                )
                raise ValidationError("Review already exists.")
            except Review.DoesNotExist:
                pass
        return super().validate(data)
