import django_filters
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from .models import Trainer, CategoryOfTrainers

class TrainerFilter(django_filters.FilterSet):
    # Distance filter (latitude and longitude)
    latitude = django_filters.NumberFilter(method='filter_by_distance')
    longitude = django_filters.NumberFilter(method='filter_by_distance')

    # Price filter
    min_price = django_filters.NumberFilter(field_name='price_per_minimum_workout_duration', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price_per_minimum_workout_duration', lookup_expr='lte')

    # Gender filter
    is_male = django_filters.BooleanFilter(field_name='is_male')

    # Categories filter
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name='trainer_categories__name',
        to_field_name='name',
        queryset=CategoryOfTrainers.objects.all()
    )

    class Meta:
        model = Trainer
        fields = ['latitude', 'longitude', 'min_price', 'max_price', 'is_male', 'categories']

    def filter_by_distance(self, queryset, name, value):
        # Get latitude and longitude from request
        latitude = self.data.get('latitude')
        longitude = self.data.get('longitude')

        if latitude and longitude:
            # Create a Point object from the user's location
            user_location = Point(float(longitude), float(latitude), srid=4326)

            # Filter trainers within a certain distance (e.g., 50 km)
            max_distance = Distance(km=50)  # Adjust the distance as needed
            queryset = queryset.filter(
                user__location__distance_lte=(user_location, max_distance)
            )

        return queryset