from django.core.exceptions import ValidationError


def validate_video_size(value, max_size_mb = 50):
    max_size_bytes = max_size_mb * 1024 * 1024  # Перевод в байты
    
    if value.size > max_size_bytes:
        raise ValidationError(f"Файл слишком большой! Максимальный размер: {max_size_mb}MB.")


def validate_instructions(value):
    """
    Custom validator to check:
    1. Maximum line length
    2. Maximum number of rows (lines)
    """
    max_line_length = 200  # Max length of each line
    max_rows = 10  # Max number of rows allowed

    if not isinstance(value, list):
        raise ValidationError("Инструкции должны быть списком.")

    # Check the number of rows
    if len(value) > max_rows:
        raise ValidationError(f"Слишком много шагов, всего может быть: {max_rows}.")

    # Check length of each line
    for line in value:
        if len(line) > max_line_length:
            raise ValidationError(f"Каждый шаг не должен превышать {max_line_length} символов.")

    return value