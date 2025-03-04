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
            'email',
            'password',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.method == 'POST':
            self.fields['email'].required = True
            self.fields['password'].required = True

        elif request and request.method == 'PUT':
            for field in self.fields.values():
                field.required = False

    def create(self, validated_data):
        if CustomUser.objects.filter(email=validated_data["email"]).exists():
            raise serializers.ValidationError({"email": "Такой пользователь уже существует"})
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
            'id',
            'first_name',
            'last_name',
            'email',
            'user_rating',
            'avatar',
        ]
        read_only_fields = ['id']
    
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
    
    def update(self, instance, validated_data):
        # Удаляем поля, которые нельзя изменять при обновлении
        non_updatable_fields = ['user_id', 'for_user_id']
        for field in non_updatable_fields:
            validated_data.pop(field, None)
        return super().update(instance, validated_data)
