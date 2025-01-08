from rest_framework import serializers
from users.models import CustomUser, RatingOfUser, Review
from users.validators import password_validator


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
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    for_user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Review
        fields = "__all__"
        extra_kwargs = {
            'rating': {'required': True},
            'user': {'required': True},
            'for_user': {'required': True},
        }
