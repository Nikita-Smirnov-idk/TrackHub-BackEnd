from django.core.exceptions import ValidationError
import re
from PIL import Image


def validate_password(password, min_length=8, require_uppercase=True, require_lowercase=True,
                require_digit=True, require_special=False, disallow_spaces=True):
    errors = []

    # Проверка длины пароля
    if len(password) < min_length:
        errors.append(f"Пароль должен содержать не менее {min_length} символов.")

    # Проверка наличия заглавной буквы
    if require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Пароль должен содержать хотя бы одну заглавную букву.")

    # Проверка наличия строчной буквы
    if require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Пароль должен содержать хотя бы одну строчную букву.")

    # Проверка наличия цифры
    if require_digit and not re.search(r'\d', password):
        errors.append("Пароль должен содержать хотя бы одну цифру.")

    # Проверка наличия специального символа
    if require_special and not re.search(r'[\W_]', password):
        errors.append("Пароль должен содержать хотя бы один специальный символ.")

    # Проверка наличия пробела
    if disallow_spaces and re.search(r'\s', password):
        errors.append("Пароль не должен содержать пробелы.")

    if errors:
        raise ValidationError(errors)
        

def validate_name(value):
    
    if not re.match(r'^[A-Za-zА-ЯЁа-яё]+$', value):
        raise ValidationError("Имя и фамилия должны содержать только буквы.")
        

def validate_image(image, max_size=200 * 1024):
    errors = []

    img = Image.open(image)
    if img.width != img.height:
            errors.append("Изображение должно быть квадратным.")
    
    if image.size > max_size:
            errors.append(f"Размер файла не должен превышать {max_size//1024} КБ.")

    if errors:
        raise ValidationError(errors)