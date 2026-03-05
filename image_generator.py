from PIL import Image, ImageDraw, ImageFont
import random
import os
from io import BytesIO
from functools import lru_cache

# ========== ГЛОБАЛЬНЫЕ КЭШИ ==========
_font_cache = {}          # {(font_path, size): font_object}
_emoji_size_cache = {}     # {size: resized_emoji_image}
_text_width_cache = {}     # {(text, font_path, size): width}

# ========== КОНФИГУРАЦИЯ ==========
IMAGE_WIDTH = 800          # Оптимизация 8: уменьшили с 1080 до 800
IMAGE_HEIGHT = 600
JPEG_QUALITY = 85          # Оптимизация 2: уменьшили качество
FONT_SIZE_START = 80       # начальный размер шрифта (подбирается)
FONT_SIZE_MIN = 36
FONT_SIZE_STEP = 4
MAX_LINES = 4
MARGIN = 60                 # уменьшили отступы для нового разрешения

print("🔍 ПРОВЕРКА РЕСУРСОВ:")
fonts_dir = "assets/fonts"
backgrounds_dir = "assets/backgrounds"
emojis_dir = "assets/emojis"

if os.path.exists(fonts_dir):
    fonts = os.listdir(fonts_dir)
    print(f"✅ ШРИФТОВ: {len(fonts)}")
else:
    print(f"❌ Папка {fonts_dir} не найдена!")

if os.path.exists(backgrounds_dir):
    bgs = [f for f in os.listdir(backgrounds_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"✅ ФОНОВ: {len(bgs)}")
else:
    print(f"❌ Папка {backgrounds_dir} не найдена!")

if os.path.exists(emojis_dir):
    emoji_files = [f for f in os.listdir(emojis_dir) if f.endswith('.png')]
    print(f"✅ ЭМОДЗИ-PNG: {len(emoji_files)}")
else:
    print(f"❌ Папка {emojis_dir} не найдена! Создайте её и добавьте sparkles.png")
    os.makedirs(emojis_dir, exist_ok=True)

# Пути к ресурсам
FONTS_DIR = 'assets/fonts'
BACKGROUNDS_DIR = 'assets/backgrounds'
EMOJIS_DIR = 'assets/emojis'

BOLD_FONTS = [
    os.path.join(FONTS_DIR, 'RussoOne-Regular.ttf'),
    os.path.join(FONTS_DIR, 'Charis-Bold.ttf'),
    os.path.join(FONTS_DIR, 'Montserrat-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Nunito-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Jost-VariableFont_wght.ttf'),
]

SPARKLES_PNG = os.path.join(EMOJIS_DIR, 'sparkles.png')

def get_cached_font(font_path, size):
    """Оптимизация 1: кэширование шрифтов по (путь, размер)"""
    key = (font_path, size)
    if key not in _font_cache:
        try:
            font = ImageFont.truetype(font_path, size)
            # Для вариабельных шрифтов пробуем установить жирное начертание
            if 'Variable' in font_path or 'Montserrat' in font_path or 'Nunito' in font_path or 'Jost' in font_path:
                try:
                    font.set_variation_by_name('Bold')
                except:
                    pass
            _font_cache[key] = font
        except Exception as e:
            print(f"⚠️ Ошибка загрузки шрифта {font_path}: {e}")
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

def get_random_bold_font(size):
    """Выбирает случайный жирный шрифт и загружает через кэш"""
    available_fonts = [p for p in BOLD_FONTS if os.path.exists(p)]
    if not available_fonts:
        print("  ⚠️ Нет жирных шрифтов, используется дефолтный")
        return ImageFont.load_default()
    selected = random.choice(available_fonts)
    return get_cached_font(selected, size)

def get_cached_emoji(size):
    """Оптимизация 3: кэширование ресайза PNG эмодзи по размеру"""
    if not os.path.exists(SPARKLES_PNG):
        return None
    if size not in _emoji_size_cache:
        try:
            emoji = Image.open(SPARKLES_PNG).convert('RGBA')
            _emoji_size_cache[size] = emoji.resize((size, size), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки эмодзи: {e}")
            return None
    return _emoji_size_cache[size]

def get_cached_text_width(text, font, font_path, size):
    """Оптимизация 7: кэширование ширины текста"""
    key = (text, font_path, size)
    if key not in _text_width_cache:
        # Создаем временный draw объект для измерения
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        _text_width_cache[key] = bbox[2] - bbox[0]
    return _text_width_cache[key]

def get_random_background():
    """Выбирает случайный фон"""
    if os.path.exists(BACKGROUNDS_DIR):
        backgrounds = [f for f in os.listdir(BACKGROUNDS_DIR) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if backgrounds:
            selected = random.choice(backgrounds)
            return os.path.join(BACKGROUNDS_DIR, selected)
    return None

def create_gradient_background(width, height):
    """Создает градиентный фон"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        val = int(200 + (55 * i / height))
        draw.line([(0, i), (width, i)], fill=(val, val, val))
    return img

def wrap_text(text, font, max_width, draw, font_path, size):
    """Разбивает текст на строки с использованием кэша ширины"""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        w = get_cached_text_width(test_line, font, font_path, size)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def draw_text_with_outline(draw, text, font, x, y, font_path, size):
    """Рисует текст с черной обводкой"""
    outline_size = 3
    for dx in range(-outline_size, outline_size + 1):
        for dy in range(-outline_size, outline_size + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill='black')
    draw.text((x, y), text, font=font, fill='white')

def add_sparkles(draw, bg, emoji_png, width, height, text_block_x, text_block_y, text_width, text_height):
    """Умное размещение блёсток (2 по бокам или 4 по углам)"""
    sparkle_size = 80  # для 800x600
    corner_margin = 20
    left_x = text_block_x - sparkle_size - 30
    right_x = text_block_x + text_width + 30

    if left_x < corner_margin or right_x > width - corner_margin:
        # в углы
        corner_size = 70
        emoji_corner = get_cached_emoji(corner_size)
        if emoji_corner:
            corners = [
                (corner_margin, corner_margin),
                (width - corner_size - corner_margin, corner_margin),
                (corner_margin, height - corner_size - corner_margin),
                (width - corner_size - corner_margin, height - corner_size - corner_margin)
            ]
            for x, y in corners:
                bg.paste(emoji_corner, (int(x), int(y)), emoji_corner)
    else:
        emoji_side = get_cached_emoji(sparkle_size)
        if emoji_side:
            sparkle_y = text_block_y + (text_height // 2) - (sparkle_size // 2)
            bg.paste(emoji_side, (int(left_x), int(sparkle_y)), emoji_side)
            bg.paste(emoji_side, (int(right_x), int(sparkle_y)), emoji_side)

def create_wish_image(text):
    """Создает изображение с текстом пожелания (оптимизированная версия)"""
    try:
        print(f"\n🎨 СОЗДАНИЕ КАРТИНКИ (оптимизировано):")
        width, height = IMAGE_WIDTH, IMAGE_HEIGHT

        # 1. Фон
        bg_path = get_random_background()
        if bg_path:
            bg = Image.open(bg_path).convert('RGB')
            bg = bg.resize((width, height), Image.Resampling.LANCZOS)
        else:
            bg = create_gradient_background(width, height)

        # Затемнение
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 70))
        bg.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(bg)

        # 2. Подбор шрифта
        font_size = FONT_SIZE_START
        font = get_random_bold_font(font_size)
        font_path = None
        # Найдем путь текущего шрифта (для кэша)
        for p in BOLD_FONTS:
            if os.path.exists(p) and os.path.basename(p) in str(font):
                font_path = p
                break
        if not font_path:
            font_path = BOLD_FONTS[0] if BOLD_FONTS else "default"

        # 3. Разбивка текста
        max_width = width - MARGIN * 2
        lines = wrap_text(text, font, max_width, draw, font_path, font_size)

        # Уменьшаем шрифт если слишком много строк
        while len(lines) > MAX_LINES and font_size > FONT_SIZE_MIN:
            font_size -= FONT_SIZE_STEP
            font = get_random_bold_font(font_size)
            # обновим font_path
            for p in BOLD_FONTS:
                if os.path.exists(p) and os.path.basename(p) in str(font):
                    font_path = p
                    break
            lines = wrap_text(text, font, max_width, draw, font_path, font_size)

        # 4. Позиционирование
        line_height = font_size + 12
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2

        # Находим самую широкую строку
        max_line_width = 0
        for line in lines:
            w = get_cached_text_width(line, font, font_path, font_size)
            if w > max_line_width:
                max_line_width = w
        text_block_x = (width - max_line_width) // 2

        # 5. Рисуем текст
        for i, line in enumerate(lines):
            y = start_y + i * line_height
            line_width = get_cached_text_width(line, font, font_path, font_size)
            x = text_block_x + (max_line_width - line_width) // 2
            draw_text_with_outline(draw, line, font, x, y, font_path, font_size)

        # 6. Блёстки
        emoji_png = get_cached_emoji(100)  # любой размер, для проверки наличия
        if emoji_png:
            add_sparkles(draw, bg, emoji_png, width, height,
                        text_block_x, start_y, max_line_width, total_text_height)

        # 7. Рамка (чёрная)
        frame_color = (0, 0, 0, 40)
        for i in range(3):
            draw.rectangle([i, i, width-1-i, height-1-i], outline=frame_color[:3])

        # 8. Сохранение
        output = BytesIO()
        bg.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        output.seek(0)
        print(f"  ✅ Картинка создана, размер: {len(output.getvalue())} байт")
        return output

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return None