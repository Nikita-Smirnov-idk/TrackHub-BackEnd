from django.db.models.signals import post_migrate
from workout_manager.apps import WorkoutManagerConfig
from workout_manager.models import ExerciseCategory, GymEquipment
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


@receiver(post_migrate)
def create_gym_equipment(sender, **kwargs):
    # Проверяем, чтобы сигнал срабатывал только для нашего приложения
    if sender.name == WorkoutManagerConfig.name:
        gym_equipment = [
            ["Беговая дорожка","run.png"],
            ["Велотренажёр","bike.png"],
            ["Эллиптический тренажёр","eleptic.png"],
            ["Степпер","stepper.png"],
            ["Гребной тренажёр","rowing.png"],
            ["Машина Смита","smith_machine.png"],
            ["Кроссовер","crossover.png"],
            ["Жим ногами","leg_press.png"],
            ["Наклонная скамья","angle_bench.png"],
            ["Горизонтальная скамья","horizontal_bench.png"],
            ["Гиперэкстензия","hyperextension.png"],
            ["Турник-пресс-брусья","bar.png"],
            ["Штанги и грифы","barbell.png"],
            ["Гантели","dumbbells.png"],
            ["Гири","kettlebell.png"],
            ["Эспандер","hand_grip.png"],
            ["Резиновые петли","rubber.png"],
            ["Фитбол","fitball.png"],
            ["Коврик для йоги","mat.png"],
            ["Медицинские мячи","balls.png"],
            ["TRX","trx.png"],
            ["Плиометрические тумбы​","box.png"],
            ["Сани", "sled.png"],
            ["Мина", "landmine.png"],
            ["Собственный вес", "personal_weight.png"],
        ]
        for equipment in gym_equipment:
            image_path = '/gym_equipment/' + equipment[1]
            GymEquipment.objects.get_or_create(name=equipment[0], image=image_path)
