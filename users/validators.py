from django.core.exceptions import ValidationError
import re
from PIL import Image



def password_validator(password):
    errors = []

    # Check length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")

    # Check for a digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")

    # Check for spaces (should not contain spaces)
    if re.search(r'\s', password):
        errors.append("Password must not contain spaces.")

    if errors:
        raise ValidationError(errors)

def name_validator(value):
    """Валидатор для проверки имени и фамилии"""
    if not re.match(r'^[A-ZА-ЯЁ][a-zа-яё]+$', value):
        raise ValidationError("Имя и фамилия должны начинаться с заглавной буквы и содержать только буквы.")

def validate_image_size(image):
    # Проверка, что изображение квадратное
    img = Image.open(image)
    if img.width != img.height:
        raise ValidationError("Изображение должно быть квадратным.")
    
    # Проверка размера файла (например, не больше 5 МБ)
    if image.size > 200 * 1024:
        raise ValidationError("Размер файла не должен превышать 200 КБ.")