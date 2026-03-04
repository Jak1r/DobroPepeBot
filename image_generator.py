from PIL import Image, ImageDraw, ImageFont
import random
import os
from io import BytesIO

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
            if f.endswith('.ttf'):
                available_fonts.append(os.path.join(FONTS_DIR, f))
    
    if not available_fonts:
        print(f"  ❌ Вообще нет шрифтов!")
        return ImageFont.load_default()
    
    # Выбираем случайный шрифт из доступных
    selected = random.choice(available_fonts)
    print(f"  🎲 Выбран шрифт: {os.path.basename(selected)}")
    
    try:
        # Для вариабельных шрифтов пробуем установить жирное начертание
        if 'Montserrat' in selected or 'Nunito' in selected or 'Jost' in selected:
            # Пробуем загрузить с жирным начертанием
            font = ImageFont.truetype(selected, size)
            # Устанавливаем жирность (weight) если поддерживается
            try:
                font.set_variation_by_name('Bold')
                print(f"  ✅ Установлено жирное начертание")
            except:
                print(f"  ⚠️ Не удалось установить жирное начертание")
        else:
            # Обычные шрифты
            font = ImageFont.truetype(selected, size)
        
        return font
    except Exception as e:
        print(f"  ❌ Ошибка загрузки: {e}")
        return ImageFont.load_default()

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
        
        # 2. Затемняем фон
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 80))  # Еще сильнее затемняем
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Подготавливаем текст
        draw = ImageDraw.Draw(bg)
        
        # Пробуем разные размеры шрифта
        font_size = 80
        font = get_random_bold_font(font_size)
        
        # Отступы от краев
        margin = 100
        max_width = width - (margin * 2)
        
        # Разбиваем на строки
        lines = wrap_text(text, font, max_width, draw)
        print(f"  📊 Строк: {len(lines)}")
        
        # Если текст не влезает, уменьшаем шрифт
        while len(lines) > 4 and font_size > 30:
            font_size -= 10
            print(f"  ⬇️ Уменьшаю шрифт до {font_size}")
            font = get_random_bold_font(font_size)
            lines = wrap_text(text, font, max_width, draw)
            print(f"  📊 Строк стало: {len(lines)}")
        
        # 4. Рисуем текст
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        # Тень
        shadow_offset = 5
        shadow_color = (0, 0, 0, 220)
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            # Тень
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     font=font, fill=shadow_color)
        
        # Основной текст (ярко-белый)
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        
        # 5. Сохраняем
        output = BytesIO()
        bg.save(output, format='JPEG', quality=95, optimize=True)
        output.seek(0)
        
        print(f"  ✅ Картинка создана, размер: {len(output.getvalue())} байт")
        return output
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return None