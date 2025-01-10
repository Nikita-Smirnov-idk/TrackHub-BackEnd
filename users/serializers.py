from rest_framework import serializers
from users.models import CustomUser, RatingOfUser, Review
from users.validators import password_validator
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


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
            'is_trainer'
        ]

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


class CustomUserGetSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'is_trainer',
            'user_rating'
        ]


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
