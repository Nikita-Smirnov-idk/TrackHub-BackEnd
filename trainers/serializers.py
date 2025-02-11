# serializers.py в приложении trainer
from rest_framework import serializers
from trainers.models import (Trainer,
                             WeekDay,
                             Break,
                             Holiday,
                             WorkHours,
                             Experience,
                             WholeExperience,
                             Gym,
                             )
from django.conf import settings


class WeekDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeekDay
        fields = ['id', 'name']
        read_only_fields = ['id']


class BreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Break
        fields = ['id', 'name', 'start_time', 'end_time']
        read_only_fields = ['id']


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'name', 'start_date', 'end_date']
        read_only_fields = ['id']


class WorkHoursSerializer(serializers.ModelSerializer):
    trainer_id = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all(),
        source='trainer',
    )

    class Meta:
        model = WorkHours
        fields = ['id', 'trainer_id', 'start_time', 'end_time']
        read_only_fields = ['id', 'trainer_id']


class ExperienceSerializer(serializers.ModelSerializer):
    trainer = serializers.PrimaryKeyRelatedField(
        queryset=Trainer.objects.all()
    )

    class Meta:
        model = Experience
        fields = [
            'id',
            'trainer',
            'company_name',
            'position',
            'description',
            'start_date',
            'end_date'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date >= end_date:
            raise serializers.ValidationError({
                "end_date": "end_date must be later than start_date."
            })

        return super().validate(attrs)


class WholeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholeExperience
        fields = ['id', 'trainer', 'experience']
        read_only_fields = ['id']

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gym
        fields = ['id', 'address', 'latitude', 'longitude']
        read_only_fields = ['id']


class TrainerGetSerializer(serializers.ModelSerializer):
    weekends = serializers.PrimaryKeyRelatedField(
        queryset=WeekDay.objects.all(),
        many=True
    )
    work_hours = serializers.PrimaryKeyRelatedField(
        queryset=WorkHours.objects.all(), allow_null=True
    )
    breaks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Break.objects.all()
    )
    holidays = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Holiday.objects.all()
    )
    whole_experience = WholeExperienceSerializer(read_only=True)
    avatar = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    gyms = GymSerializer(many=True, read_only=True)

    class Meta:
        model = Trainer
        fields = [
            'id',
            'first_name',
            'last_name',
            'user',
            'description',
            'is_public',
            'is_active',
            'is_male',
            'gyms',
            'is_able_to_visit',
            'price_per_minimum_workout_duration',
            'minimum_workout_duration',
            'workout_duration_devided_by_value',
            'weekends',
            'work_hours',
            'breaks',
            'holidays',
            'whole_experience',
            'avatar',
        ]
        read_only_fields = ['id', 'gyms']
    
    def get_avatar(self, obj):
        if obj.user.avatar:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}{obj.user.avatar}"
        return None
    
    def get_first_name(self, obj):
        return obj.user.first_name
    
    def get_last_name(self, obj):
        return obj.user.last_name


class TrainerSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = [
            'id',
            'user',
            'description',
            'is_able_to_visit',
            'is_public',
            'is_active',
            'is_male',
            'price_per_hour',
            'minimum_workout_duration',
            'workout_duration_devided_by_value',
        ]
        read_only_fields = ['id']
    
    def get_avatar(self, obj):
        if obj.user.avatar:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}{obj.user.avatar}"
        return None
