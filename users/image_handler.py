from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import random
import io
from django.contrib.auth import get_user_model
from django.core.files import File

AVATAR_COLORS = [
    "#FF6F61",  # Коралловый
    "#6B5B95",  # Лавандово-фиолетовый
    "#88B04B",  # Зеленый мох
    "#F7CAC9",  # Розовый кварц
    "#92A8D1",  # Нежно-голубой
    "#955251",  # Коричнево-красный
    "#B565A7",  # Пурпурный
    "#009B77",  # Изумрудный
    "#DD4124",  # Ярко-красный
    "#D65076",  # Малиновый
    "#45B8AC",  # Бирюзовый
    "#EFC050",  # Золотисто-желтый
    "#5B5EA6",  # Сине-фиолетовый
    "#9B2335",  # Рубиновый
    "#DFCFBE",  # Бежевый
    "#55B4B0",  # Аквамариновый
]

def generate_default_avatar(id):
    user = get_user_model()
    user = user.objects.get(id=id)
    name = user.first_name
    # Размер изображения
    size = (200, 200)
    
    # Выбираем цвет на основе хэша от id пользователя
    color_index = hash(id) % len(AVATAR_COLORS)
    background_color = AVATAR_COLORS[color_index]
    
    # Преобразуем HEX-цвет в RGB
    background_rgb = tuple(int(background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    # Создаем квадратное изображение
    image = Image.new("RGB", size, background_rgb)
    
    # Рисуем первую букву имени
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 100)  # Используем шрифт Arial
    except IOError:
        font = ImageFont.load_default()  # Используем шрифт по умолчанию, если Arial недоступен
    
    text = name[0].upper() if name else "U"
    text_color = (255, 255, 255)  # Белый цвет текста
    
    # Получаем размеры текста с помощью getbbox
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Позиционируем текст по центру
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(text_position, text, font=font, fill=text_color)
    
    # Сохраняем изображение в BytesIO
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Сохраняем изображение в поле avatar
    user.avatar.save(f"default_avatar_{id}.png", ContentFile(buffer.getvalue()), save=False)
    user.save()
    buffer.close()


# def compress_image(image, max_size_kb):
#         """
#         Сжимает изображение до указанного размера в КБ.
#         """
#         quality = 95
#         while True:
#             buffer = io.BytesIO()
#             image.save(buffer, format="JPEG", quality=quality)
#             size_kb = buffer.tell() / 1024  # Размер в КБ
#             if size_kb <= max_size_kb or quality <= 10:
#                 break
#             quality -= 5
#         return buffer.getvalue()


# def compress_image_to_target_size(image, target_size_kb, max_quality=95, min_quality=5):
#     """
#     Compress an image to a target file size in KB.
    
#     :param input_path: Path to the input image.
#     :param output_path: Path to save the compressed image.
#     :param target_size_kb: Target file size in kilobytes (KB).
#     :param max_quality: Maximum quality to use (0-100).
#     :param min_quality: Minimum quality to use (0-100).
#     """
#     target_size_bytes = target_size_kb * 1024  # Convert KB to bytes
#     buffer = io.BytesIO()
#     image.save(buffer, format="JPEG")

#     # Function to get the size of the image in bytes
#     def get_image_size(img, quality):
#         buffer = io.BytesIO()
#         img.save(buffer, format="JPEG", quality=quality)
#         print(buffer.tell())
#         return buffer.tell()

#     # Binary search to find the optimal quality
#     low, high = min_quality, max_quality
#     while low <= high:
#         mid = (low + high) // 2
#         size = get_image_size(image, mid)

#         if size < target_size_bytes:
#             low = mid + 1  # Increase quality to increase size
#         else:
#             high = mid - 1  # Decrease quality to reduce size

#     # Save the image with the optimal quality
#     optimal_quality = high if high >= min_quality else min_quality

#     buffer = io.BytesIO()
#     image.save(buffer, format="JPEG", quality=optimal_quality)

#     return buffer.getvalue()