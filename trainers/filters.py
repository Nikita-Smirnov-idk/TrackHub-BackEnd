from django_filters import rest_framework as filters
from trainers.models import Trainer


class TrainerFilter(filters.FilterSet):
    min_price_per_hour = filters.NumberFilter(field_name='price_per_hour', lookup_expr='gte')
    max_price_per_hour = filters.NumberFilter(field_name='price_per_hour', lookup_expr='lte')
    address = filters.CharFilter(field_name='address', lookup_expr='icontains')
    min_experience = filters.NumberFilter(field_name='whole_experience__experience', lookup_expr='gte')

    class Meta:
        model = Trainer
        fields = ['user__name', 'user__surname', ]