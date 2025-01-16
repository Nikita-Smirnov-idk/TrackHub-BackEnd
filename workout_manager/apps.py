from django.apps import AppConfig


class WorkoutManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "workout_manager"
    verbose_name = "Управление тренировками"

    def ready(self):
        import workout_manager.signals  # noqa: F401
