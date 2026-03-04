from PIL import Image, ImageDraw, ImageFont
import random
import os
from io import BytesIO
import emoji

print("🔍 ПРОВЕРКА РЕСУРСОВ:")
fonts_dir = "assets/fonts"
backgrounds_dir = "assets/backgrounds"

if os.path.exists(fonts_dir):
    fonts = os.listdir(fonts_dir)
    print(f"✅ ШРИФТОВ: {len(fonts)}")
    for f in fonts:
        print(f"   - {f}")
else:
    print(f"❌ Папка {fonts_dir} не найдена!")

if os.path.exists(backgrounds_dir):
    bgs = [f for f in os.listdir(backgrounds_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    print(f"✅ ФОНОВ: {len(bgs)}")
else:
    print(f"❌ Папка {backgrounds_dir} не найдена!")

# Пути к ресурсам
FONTS_DIR = 'assets/fonts'
BACKGROUNDS_DIR = 'assets/backgrounds'

# ⚡ ТОЛЬКО ЖИРНЫЕ ШРИФТЫ ⚡
BOLD_FONTS = [
    os.path.join(FONTS_DIR, 'RussoOne-Regular.ttf'),      # Самый жирный
    os.path.join(FONTS_DIR, 'Charis-Bold.ttf'),           # Тоже жирный
    os.path.join(FONTS_DIR, 'Montserrat-VariableFont_wght.ttf'),  # Будем делать жирным
    os.path.join(FONTS_DIR, 'Nunito-VariableFont_wght.ttf'),      # Тоже вариабельный
    os.path.join(FONTS_DIR, 'Jost-VariableFont_wght.ttf'),        # Тоже вариабельный
]

# 👇 ОБНОВЛЕНО: теперь ищем NotoColorEmoji в папке assets/fonts/
EMOJI_FONT_PATHS = [
    os.path.join(FONTS_DIR, 'NotoColorEmoji.ttf'),        # Локальный файл
    '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',  # Системный (запасной)
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Запасной вариант
]

def get_random_bold_font(size):
    """Выбирает случайный жирный шрифт и загружает его"""
    available_fonts = []
    
    # Проверяем какие жирные шрифты реально есть
    for font_path in BOLD_FONTS:
        if os.path.exists(font_path):
            available_fonts.append(font_path)
            print(f"  ✅ Доступен: {os.path.basename(font_path)}")
    
    if not available_fonts:
        print(f"  ⚠️ Нет жирных шрифтов, ищу любые...")
        # Если нет жирных, ищем любые
        for f in os.listdir(FONTS_DIR):
            if f.endswith('.ttf') and f != 'NotoColorEmoji.ttf':  # Исключаем эмодзи-шрифт
                available_fonts.append(os.path.join(FONTS_DIR, f))
    
    if not available_fonts:
        print(f"  ❌ Вообще нет шрифтов!")
        return ImageFont.load_default()
    
    # Выбираем случайный шрифт из доступных
    selected = random.choice(available_fonts)
    print(f"  🎲 Выбран шрифт: {os.path.basename(selected)}")
    
    try:
        # Для вариабельных шрифтов пробуем установить жирное начертание
        font = ImageFont.truetype(selected, size)
        
        # Пробуем установить жирное начертание если шрифт вариабельный
        try:
            # Проверяем, поддерживает ли шрифт вариации
            if 'Variable' in selected or 'Montserrat' in selected or 'Nunito' in selected or 'Jost' in selected:
                # Пытаемся установить жирность
                font.set_variation_by_name('Bold')
                print(f"  ✅ Установлено жирное начертание")
        except:
            # Если не получилось, просто используем как есть
            pass
        
        return font
    except Exception as e:
        print(f"  ❌ Ошибка загрузки: {e}")
        return ImageFont.load_default()

def get_emoji_font(size):
    """Загружает шрифт для эмодзи (сначала из локальной папки)"""
    for font_path in EMOJI_FONT_PATHS:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
                print(f"  ✅ Загружен эмодзи-шрифт: {os.path.basename(font_path)}")
                return font
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки {font_path}: {e}")
                continue
    
    print(f"  ⚠️ Эмодзи-шрифт не найден, буду использовать жирный шрифт")
    return None

def get_random_background():
    """Выбирает случайный фон из папки backgrounds"""
    try:
        if os.path.exists(BACKGROUNDS_DIR):
            backgrounds = [f for f in os.listdir(BACKGROUNDS_DIR) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if backgrounds:
                selected = random.choice(backgrounds)
                print(f"  🎨 Выбран фон: {selected}")
                return os.path.join(BACKGROUNDS_DIR, selected)
    except Exception as e:
        print(f"⚠️ Ошибка при выборе фона: {e}")
    
    print("  ⚠️ Фонов нет, создаю градиент")
    return None

def create_gradient_background(width, height):
    """Создает градиентный фон, если нет картинок"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Рисуем градиент от светлого к темному
    for i in range(height):
        color_value = int(200 + (55 * i / height))
        draw.line([(0, i), (width, i)], fill=(color_value, color_value, color_value))
    
    return img

def wrap_text(text, font, max_width, draw):
    """Разбивает текст на строки по ширине"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def draw_text_with_emoji(draw, text, font_bold, font_emoji, x_start, y, color=(255, 255, 255)):
    """
    Рисует текст, переключаясь между жирным шрифтом и шрифтом с эмодзи.
    """
    current_x = x_start
    
    # Если нет шрифта для эмодзи, рисуем всё жирным шрифтом
    if not font_emoji:
        draw.text((current_x, y), text, font=font_bold, fill=color)
        return current_x + draw.textbbox((0, 0), text, font=font_bold)[2]
    
    # Разбиваем текст на части: обычный текст и эмодзи
    parts = []
    current_part = ""
    
    i = 0
    while i < len(text):
        char = text[i]
        # Проверяем, является ли символ эмодзи
        if char in emoji.EMOJI_DATA:
            if current_part:
                parts.append(('text', current_part))
                current_part = ""
            parts.append(('emoji', char))
        else:
            current_part += char
        i += 1
    
    if current_part:
        parts.append(('text', current_part))
    
    # Рисуем каждую часть своим шрифтом
    for part_type, part_text in parts:
        font = font_emoji if part_type == 'emoji' else font_bold
        bbox = draw.textbbox((0, 0), part_text, font=font)
        part_width = bbox[2] - bbox[0]
        
        draw.text((current_x, y), part_text, font=font, fill=color)
        current_x += part_width
    
    return current_x

def create_wish_image(text):
    """Создает изображение с текстом пожелания на фоне"""
    try:
        print(f"\n🎨 СОЗДАНИЕ КАРТИНКИ:")
        print(f"  📝 Текст: {text[:50]}...")
        
        width = 1080
        height = 720
        
        # 1. Загружаем или создаем фон
        bg_path = get_random_background()
        if bg_path and os.path.exists(bg_path):
            bg = Image.open(bg_path).convert('RGB')
            bg = bg.resize((width, height), Image.Resampling.LANCZOS)
            print(f"  ✅ Фон загружен")
        else:
            bg = create_gradient_background(width, height)
            print(f"  ✅ Создан градиентный фон")
        
        # 2. Затемняем фон для лучшей читаемости
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 80))
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Подготавливаем шрифты
        draw = ImageDraw.Draw(bg)
        
        # Начинаем с большого размера шрифта
        font_size = 80
        font_bold = get_random_bold_font(font_size)
        font_emoji = get_emoji_font(font_size)
        
        # Отступы от краев
        margin = 100
        max_width = width - (margin * 2)
        
        # Разбиваем текст на строки (используем жирный шрифт для измерения)
        lines = wrap_text(text, font_bold, max_width, draw)
        print(f"  📊 Строк: {len(lines)}")
        
        # Если текст не влезает, уменьшаем шрифт
        while len(lines) > 4 and font_size > 30:
            font_size -= 10
            print(f"  ⬇️ Уменьшаю шрифт до {font_size}")
            font_bold = get_random_bold_font(font_size)
            font_emoji = get_emoji_font(font_size)
            lines = wrap_text(text, font_bold, max_width, draw)
            print(f"  📊 Строк стало: {len(lines)}")
        
        # 4. Рисуем текст построчно с поддержкой эмодзи
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        # Сначала рисуем тень (только для обычного текста, жирным шрифтом)
        shadow_offset = 5
        shadow_color = (0, 0, 0, 220)
        
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            
            # Для тени используем жирный шрифт
            draw.text((margin + shadow_offset, y + shadow_offset), line, 
                     font=font_bold, fill=shadow_color)
        
        # Рисуем основной текст с эмодзи
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            draw_text_with_emoji(draw, line, font_bold, font_emoji, margin, y, color=(255, 255, 255))
        
        # 5. Сохраняем в BytesIO
        output = BytesIO()
        bg.save(output, format='JPEG', quality=95, optimize=True)
        output.seek(0)
        
        print(f"  ✅ Картинка создана, размер: {len(output.getvalue())} байт")
        return output
        
    except Exception as e:
        print(f"❌ ОШИБКА создания изображения: {e}")
        import traceback
        traceback.print_exc()
        return None

# Для теста
if __name__ == "__main__":
    print("\n🎲 ТЕСТ ГЕНЕРАЦИИ:")
    test_wish = "✨ Ты справишься со всем, что встретится на пути ✨"
    img = create_wish_image(test_wish)
    if img:
        print("✅ Тест успешен!")
    else:
        print("❌ Тест провален")