from rest_framework import serializers
from users.models import (
    CustomUser,
    Review,
)
from users.validators import (
    validate_password,
    validate_name,
)
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from users.Services import converters


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(validators=[validate_password], write_only=True)
    first_name = serializers.CharField(validators=[validate_name], required=False)
    last_name = serializers.CharField(validators=[validate_name], required=False)

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            CustomUser._meta.get_field('email').get_attname(),
            'password',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.method == 'POST':
            self.fields[CustomUser._meta.get_field('email').get_attname()].required = True
            self.fields['password'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True

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
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            CustomUser._meta.get_field('id').get_attname(),
            CustomUser._meta.get_field('first_name').get_attname(),
            CustomUser._meta.get_field('last_name').get_attname(),
            CustomUser._meta.get_field('email').get_attname(),
            CustomUser._meta.get_field('user_rating').get_attname(),
            'avatar',
        ]
        read_only_fields = [CustomUser._meta.get_field('id').get_attname()]
    
    def get_avatar(self, obj):
        return converters.avatar_to_representation(obj.avatar.url)


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
            Review._meta.get_field('id').get_attname(),
            "user_id",
            "for_user_id",
            Review._meta.get_field('rating').get_attname(),
            Review._meta.get_field('review_text').get_attname(),
            Review._meta.get_field('date').get_attname(),
        ]
        read_only_fields = [Review._meta.get_field('id').get_attname(), Review._meta.get_field('date').get_attname()]

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
