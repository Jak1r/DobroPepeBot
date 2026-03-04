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

# Список доступных шрифтов (будем пробовать по порядку)
FONT_PATHS = [
    os.path.join(FONTS_DIR, 'Impact.ttf'),
    os.path.join(FONTS_DIR, 'Montserrat-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Nunito-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Jost-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'RussoOne-Regular.ttf'),
    os.path.join(FONTS_DIR, 'Charis-Bold.ttf'),
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # системный Linux
]

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
    
    # Если нет фонов, создаем градиентный фон
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

def get_font(size):
    """Пытается загрузить шрифт, если не получается - использует дефолтный"""
    for font_path in FONT_PATHS:
        try:
            if os.path.exists(font_path):
                print(f"  ✅ Пробуем шрифт: {font_path}")
                font = ImageFont.truetype(font_path, size)
                # Проверяем, может ли шрифт отобразить эмодзи
                test_text = "✨"
                bbox = font.getbbox(test_text)
                if bbox[2] - bbox[0] > 0:  # если ширина > 0, значит шрифт работает
                    print(f"  ✅ Шрифт загружен: {font_path}")
                    return font
        except Exception as e:
            print(f"  ⚠️ Ошибка загрузки {font_path}: {e}")
            continue
    
    print("⚠️ Не удалось загрузить шрифт с эмодзи, использую дефолтный")
    return ImageFont.load_default()

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
            print(f"  ✅ Фон загружен: {bg_path}")
        else:
            bg = create_gradient_background(width, height)
            print(f"  ✅ Создан градиентный фон")
        
        # 2. Немного затемняем фон для лучшей читаемости текста
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 60))
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Подготавливаем текст
        draw = ImageDraw.Draw(bg)
        
        # Пробуем разные размеры шрифта
        font_size = 80
        font = get_font(font_size)
        
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
            font = get_font(font_size)
            lines = wrap_text(text, font, max_width, draw)
            print(f"  📊 Строк стало: {len(lines)}")
        
        # 4. Рисуем текст
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        # Тень для текста (для лучшей читаемости)
        shadow_offset = 4
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            # Тень
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     font=font, fill=(0, 0, 0, 200))
        
        # Основной текст (белый)
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            draw.text((x, y), line, font=font, fill='white')
        
        # 5. Сохраняем в BytesIO
        output = BytesIO()
        bg.save(output, format='JPEG', quality=92, optimize=True)
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
    test_wish = "Ты справишься со всем, что встретится на пути ✨"
    img = create_wish_image(test_wish)
    if img:
        print("✅ Тест успешен!")
    else:
        print("❌ Тест провален")