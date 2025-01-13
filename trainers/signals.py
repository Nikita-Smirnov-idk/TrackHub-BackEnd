from django.db.models.signals import post_migrate
from django.dispatch import receiver
from trainers.models import WeekDay, ExerciseCategory
from trainers.apps import TrainersConfig


@receiver(post_migrate)
def create_days_of_week(sender, **kwargs):
    # Проверяем, чтобы сигнал срабатывал только для нашего приложения
    if sender.name == TrainersConfig.name:
        days = [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]
        for day in days:
            WeekDay.objects.get_or_create(name=day)


@receiver(post_migrate)
def create_exercise_categories(sender, **kwargs):
    # Проверяем, чтобы сигнал срабатывал только для нашего приложения
    if sender.name == TrainersConfig.name:
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
