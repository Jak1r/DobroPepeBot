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

def add_soft_glow(draw, text, font, x, y, color=(255, 255, 255)):
    """Добавляет мягкое свечение вокруг текста"""
    glow_steps = [3, 5, 7]  # радиусы свечения
    glow_opacity = [100, 60, 30]  # прозрачность для каждого радиуса
    
    for radius, opacity in zip(glow_steps, glow_opacity):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    glow_color = (*color, opacity)
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_color)

def draw_text_with_emoji_and_outline(draw, text, font, emoji_png, x, y, outline=True, glow=False):
    """
    Рисует текст по центру с обводкой и эмодзи.
    outline=True - добавляет черную обводку [citation:2][citation:5]
    glow=False - добавляет мягкое свечение (опционально)
    """
    current_x = x
    
    # Разбиваем текст по ✨
    parts = text.split('✨')
    
    for i, part in enumerate(parts):
        # Рисуем обычный текст
        if part:
            # Сначала обводка (если нужно)
            if outline:
                outline_size = 3
                for dx in range(-outline_size, outline_size + 1):
                    for dy in range(-outline_size, outline_size + 1):
                        if dx != 0 or dy != 0:  # пропускаем центр
                            draw.text((current_x + dx, y + dy), part, font=font, fill='black')
            
            # Потом свечение (если нужно)
            if glow:
                add_soft_glow(draw, part, font, current_x, y)
            
            # Основной текст
            draw.text((current_x, y), part, font=font, fill=(255, 255, 255))
            
            bbox = draw.textbbox((0, 0), part, font=font)
            current_x += bbox[2] - bbox[0]
        
        # Вставляем эмодзи
        if i < len(parts) - 1:
            if emoji_png:
                # Рассчитываем размер эмодзи
                emoji_height = int(font.size * 1.3)
                emoji_width = emoji_height
                
                # Ресайзим PNG
                emoji_resized = emoji_png.resize((emoji_width, emoji_height), Image.Resampling.LANCZOS)
                
                # Вставляем PNG на картинку (немного смещаем по вертикали)
                emoji_y = y - 8
                bg.paste(emoji_resized, (int(current_x), int(emoji_y)), emoji_resized)
                
                current_x += emoji_width + 8
            else:
                # Если нет PNG, рисуем *
                draw.text((current_x, y), '*', font=font, fill=(255, 255, 255))
                bbox = draw.textbbox((0, 0), '*', font=font)
                current_x += bbox[2] - bbox[0]
    
    return current_x

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
        
        # 2. Затемняем фон (чуть сильнее для контраста с обводкой)
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 80))
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Загружаем PNG эмодзи если есть
        emoji_png = None
        if os.path.exists(SPARKLES_PNG):
            try:
                emoji_png = Image.open(SPARKLES_PNG).convert('RGBA')
                print(f"  ✅ Загружен PNG эмодзи: sparkles.png")
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки PNG: {e}")
        
        # 4. Подготавливаем шрифты
        draw = ImageDraw.Draw(bg)
        
        # Начинаем с большого размера шрифта
        font_size = 80
        font = get_random_bold_font(font_size)
        
        # Отступы от краев
        margin = 100
        max_width = width - (margin * 2)
        
        # Разбиваем текст на строки
        lines = wrap_text(text, font, max_width, draw)
        print(f"  📊 Строк: {len(lines)}")
        
        # Если текст не влезает, уменьшаем шрифт
        while len(lines) > 4 and font_size > 30:
            font_size -= 10
            print(f"  ⬇️ Уменьшаю шрифт до {font_size}")
            font = get_random_bold_font(font_size)
            lines = wrap_text(text, font, max_width, draw)
            print(f"  📊 Строк стало: {len(lines)}")
        
        # 5. Рисуем текст построчно по центру
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            
            # Рассчитываем ширину строки для центрирования
            temp_x = margin
            parts = line.split('✨')
            line_width = 0
            
            for j, part in enumerate(parts):
                if part:
                    bbox = draw.textbbox((0, 0), part, font=font)
                    line_width += bbox[2] - bbox[0]
                if j < len(parts) - 1:
                    line_width += font_size + 8  # ширина эмодзи + отступ
            
            # Вычисляем x для центрирования
            x = (width - line_width) // 2
            
            # Рисуем строку по центру с обводкой (без свечения для чистоты)
            draw_text_with_emoji_and_outline(draw, line, font, emoji_png, x, y, outline=True, glow=False)
        
        # 6. Добавляем декоративную рамку (опционально)
        frame_color = (255, 255, 255, 40)
        frame_width = 4
        
        # Внешняя рамка
        for i in range(frame_width):
            draw.rectangle(
                [i, i, width - 1 - i, height - 1 - i],
                outline=(*frame_color[:3], frame_color[3] - i*10)
            )
        
        # 7. Сохраняем
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