from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io
from django.contrib.auth import get_user_model
import os
from django.conf import settings


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
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, '../static/fonts/pt-sans.narrow-bold.ttf')

    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_path, 150)
    except:
        font = ImageFont.load_default()
    
    text = name[0].upper() if name else "U"
    text_color = (255, 255, 255)  # Белый цвет текста
    
    # Получаем размеры текста с помощью getbbox
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Позиционируем текст по центру
    text_position = ((size[0] - text_width) / 2.15, (size[1] - text_height) / 7)
    draw.text(text_position, text, font=font, fill=text_color)
    
    # Сохраняем изображение в BytesIO
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Сохраняем изображение в поле avatar
    user.avatar.save(f"default_avatar_{id}.png", ContentFile(buffer.getvalue()), save=False)
    user.save()
    buffer.close()