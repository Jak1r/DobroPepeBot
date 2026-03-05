from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os
from io import BytesIO

print("🔍 ПРОВЕРКА РЕСУРСОВ:")
fonts_dir = "assets/fonts"
backgrounds_dir = "assets/backgrounds"
emojis_dir = "assets/emojis"

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

if os.path.exists(emojis_dir):
    emoji_files = [f for f in os.listdir(emojis_dir) if f.endswith('.png')]
    print(f"✅ ЭМОДЗИ-PNG: {len(emoji_files)}")
    for f in emoji_files:
        print(f"   - {f}")
else:
    print(f"❌ Папка {emojis_dir} не найдена! Создайте её и добавьте sparkles.png")
    os.makedirs(emojis_dir, exist_ok=True)

# Пути к ресурсам
FONTS_DIR = 'assets/fonts'
BACKGROUNDS_DIR = 'assets/backgrounds'
EMOJIS_DIR = 'assets/emojis'

# ⚡ ТОЛЬКО ЖИРНЫЕ ШРИФТЫ ⚡
BOLD_FONTS = [
    os.path.join(FONTS_DIR, 'RussoOne-Regular.ttf'),      # Самый жирный
    os.path.join(FONTS_DIR, 'Charis-Bold.ttf'),           # Тоже жирный
    os.path.join(FONTS_DIR, 'Montserrat-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Nunito-VariableFont_wght.ttf'),
    os.path.join(FONTS_DIR, 'Jost-VariableFont_wght.ttf'),
]

# Путь к PNG блёсток
SPARKLES_PNG = os.path.join(EMOJIS_DIR, 'sparkles.png')

def get_random_bold_font(size):
    """Выбирает случайный жирный шрифт и загружает его"""
    available_fonts = []
    
    for font_path in BOLD_FONTS:
        if os.path.exists(font_path):
            available_fonts.append(font_path)
            print(f"  ✅ Доступен: {os.path.basename(font_path)}")
    
    if not available_fonts:
        print(f"  ⚠️ Нет жирных шрифтов, ищу любые...")
        for f in os.listdir(FONTS_DIR):
            if f.endswith('.ttf'):
                available_fonts.append(os.path.join(FONTS_DIR, f))
    
    if not available_fonts:
        print(f"  ❌ Вообще нет шрифтов!")
        return ImageFont.load_default()
    
    selected = random.choice(available_fonts)
    print(f"  🎲 Выбран шрифт: {os.path.basename(selected)}")
    
    try:
        font = ImageFont.truetype(selected, size)
        
        # Пробуем установить жирное начертание если шрифт вариабельный
        try:
            if 'Variable' in selected or 'Montserrat' in selected or 'Nunito' in selected or 'Jost' in selected:
                font.set_variation_by_name('Bold')
                print(f"  ✅ Установлено жирное начертание")
        except:
            pass
        
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

def draw_text_with_outline(draw, text, font, x, y):
    """Рисует текст с черной обводкой"""
    outline_size = 3
    
    # Обводка
    for dx in range(-outline_size, outline_size + 1):
        for dy in range(-outline_size, outline_size + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill='black')
    
    # Основной текст
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

# Глобальная переменная для фона
bg = None

def create_wish_image(text):
    """Создает изображение с текстом пожелания на фоне"""
    global bg
    
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
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 70))
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Загружаем PNG эмодзи
        emoji_png = None
        if os.path.exists(SPARKLES_PNG):
            try:
                emoji_png = Image.open(SPARKLES_PNG).convert('RGBA')
                print(f"  ✅ Загружен PNG эмодзи: sparkles.png")
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки PNG: {e}")
        
        # 4. Подготавливаем шрифты
        draw = ImageDraw.Draw(bg)
        
        # Начинаем с большого размера шрифта (увеличил до 90)
        font_size = 90
        font = get_random_bold_font(font_size)
        
        # Отступы от краев
        margin = 80
        max_width = width - (margin * 2)
        
        # Разбиваем текст на строки
        lines = wrap_text(text, font, max_width, draw)
        print(f"  📊 Строк: {len(lines)}")
        
        # Если текст не влезает, уменьшаем шрифт
        while len(lines) > 4 and font_size > 40:
            font_size -= 5
            print(f"  ⬇️ Уменьшаю шрифт до {font_size}")
            font = get_random_bold_font(font_size)
            lines = wrap_text(text, font, max_width, draw)
            print(f"  📊 Строк стало: {len(lines)}")
        
        # 5. Рассчитываем позиции для всего блока
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        # Находим самую широкую строку для центрирования блока
        max_line_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width > max_line_width:
                max_line_width = line_width
        
        # Центрируем весь блок текста
        text_block_x = (width - max_line_width) // 2
        
        # 6. Рисуем все строки текста
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            
            # Центрируем конкретную строку
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = text_block_x + (max_line_width - line_width) // 2
            
            draw_text_with_outline(draw, line, font, x, y)
        
        # 7. Добавляем две большие блёстки по бокам всего текста
        if emoji_png:
            # Размер блёсток (большие)
            sparkle_size = 120
            
            # Левая блёстка
            emoji_left = emoji_png.resize((sparkle_size, sparkle_size), Image.Resampling.LANCZOS)
            left_x = text_block_x - sparkle_size - 40  # отступ слева
            left_y = start_y + (total_text_height // 2) - (sparkle_size // 2)
            bg.paste(emoji_left, (int(left_x), int(left_y)), emoji_left)
            
            # Правая блёстка
            emoji_right = emoji_png.resize((sparkle_size, sparkle_size), Image.Resampling.LANCZOS)
            right_x = text_block_x + max_line_width + 40  # отступ справа
            right_y = start_y + (total_text_height // 2) - (sparkle_size // 2)
            bg.paste(emoji_right, (int(right_x), int(right_y)), emoji_right)
            
            print(f"  ✨ Добавлены большие блёстки по бокам")
        
        # 8. Добавляем декоративную рамку
        frame_color = (255, 255, 255, 30)
        frame_width = 3
        
        for i in range(frame_width):
            draw.rectangle(
                [i, i, width - 1 - i, height - 1 - i],
                outline=(*frame_color[:3], frame_color[3] - i*5)
            )
        
        # 9. Сохраняем
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
    test_wish = "Ты справишься со всем, что встретится на пути"
    img = create_wish_image(test_wish)
    if img:
        print("✅ Тест успешен!")
    else:
        print("❌ Тест провален")