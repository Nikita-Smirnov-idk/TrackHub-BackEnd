from django.core.exceptions import ValidationError


def validate_video_size(value, max_size_mb = 50):
    max_size_bytes = max_size_mb * 1024 * 1024  # Перевод в байты
    
    if value.size > max_size_bytes:
        raise ValidationError(f"Файл слишком большой! Максимальный размер: {max_size_mb}MB.")
    

def validate_instructions(value):
    """Validates the number of steps and the length of each step."""
    max_steps = 10  # Ограничение на количество шагов
    max_length_per_step = 200  # Максимальная длина одной строки

    if not isinstance(value, list):
        raise ValidationError("Инструкции должны быть списком.")

    if len(value) > max_steps:
        raise ValidationError(f"Слишком много шагов, всего может быть: {max_steps}.")

    for step in value:
        if not isinstance(step, str):
            raise ValidationError("Каждый шаг должен быть строкой.")
        if len(step) > max_length_per_step:
            raise ValidationError(f"Каждый шаг не должен превышать {max_length_per_step} символов.")