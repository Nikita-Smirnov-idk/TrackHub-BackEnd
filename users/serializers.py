from rest_framework import serializers
from users.models import (
    CustomUser,
    Review,
)
from users.validators import (
    validate_password,
    validate_name,
    validate_image,
)
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(validators=[validate_password], write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            CustomUser._meta.get_field('first_name').name,
            CustomUser._meta.get_field('last_name').name,
            CustomUser._meta.get_field('email').name,
            'password',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.method == 'POST':
            self.fields[CustomUser._meta.get_field('email').name].required = True
            self.fields['password'].required = True
            self.fields['first_name'].required = True

        elif request and request.method == 'PUT':
            for field in self.fields.values():
                field.required = False

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(
                validated_data['password']
            )
        return super().update(instance, validated_data)


class CustomUserGetSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = [
            CustomUser._meta.get_field('id').name,
            CustomUser._meta.get_field('first_name').name,
            CustomUser._meta.get_field('last_name').name,
            CustomUser._meta.get_field('email').name,
            CustomUser._meta.get_field('avatar').name,
            CustomUser._meta.get_field('user_rating').name,
        ]
        read_only_fields = [CustomUser._meta.get_field('id').name]

class CustomUserPreviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = [
            CustomUser._meta.get_field('id').name,
            CustomUser._meta.get_field('first_name').name,
            CustomUser._meta.get_field('last_name').name,
            CustomUser._meta.get_field('avatar').name,
        ]
        read_only_fields = [CustomUser._meta.get_field('id').name]


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
            Review._meta.get_field('id').name,
            "user_id",
            "for_user_id",
            Review._meta.get_field('rating').name,
            Review._meta.get_field('review_text').name,
            Review._meta.get_field('date').name,
        ]
        read_only_fields = [Review._meta.get_field('id').name, Review._meta.get_field('date').name]

    def validate(self, data):
        if self.instance is None:
            try:
                _ = Review.objects.get(
                    user=data['user_id'],
                    for_user=data['for_user_id']
                )
                raise ValidationError("Review already exists.")
            except Review.DoesNotExist:
                pass
        return super().validate(data)
    
    def update(self, instance, validated_data):
        # Удаляем поля, которые нельзя изменять при обновлении
        non_updatable_fields = ['user_id', 'for_user_id']
        for field in non_updatable_fields:
            validated_data.pop(field, None)
        return super().update(instance, validated_data)

class AvatarSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['avatar']