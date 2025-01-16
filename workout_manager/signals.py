from django.db.models.signals import post_migrate
from workout_manager.apps import WorkoutManagerConfig
from workout_manager.models import ExerciseCategory
from django.dispatch import receiver


@receiver(post_migrate)
def create_exercise_categories(sender, **kwargs):
    # Проверяем, чтобы сигнал срабатывал только для нашего приложения
    if sender.name == WorkoutManagerConfig.name:
        categories = [
            "Растяжка",
            "Кардио",
            "Грудь",
            "Спина",
            "Руки",
            "Ноги",
            "Плечи",
            "Пресс",
            "Плечи",
        ]
        for category in categories:
            ExerciseCategory.objects.get_or_create(name=category)
