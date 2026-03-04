from PIL import Image, ImageDraw, ImageFont
import random
import os
from io import BytesIO

# ... (остальной код остается таким же)

def create_wish_image(text):
    try:
        width = 1080
        height = 720
        
        # 1. Загружаем или создаем фон
        bg_path = get_random_background()
        if bg_path and os.path.exists(bg_path):
            bg = Image.open(bg_path).convert('RGB')
            bg = bg.resize((width, height), Image.Resampling.LANCZOS)
        else:
            bg = create_gradient_background(width, height)
        
        # 2. Немного затемняем фон
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 60))  # Увеличил затемнение
        bg.paste(overlay, (0, 0), overlay)
        
        # 3. Подготавливаем текст
        draw = ImageDraw.Draw(bg)
        
        # Пробуем разные размеры шрифта
        font_size = 80
        font = get_font(font_size)
        
        # Отступы от краев
        margin = 100  # Увеличил отступы
        max_width = width - (margin * 2)
        
        # Разбиваем на строки
        lines = wrap_text(text, font, max_width, draw)
        
        # Если текст не влезает, уменьшаем шрифт
        while len(lines) > 4 and font_size > 30:  # Уменьшил макс строк до 4
            font_size -= 10
            font = get_font(font_size)
            lines = wrap_text(text, font, max_width, draw)
        
        # 4. Рисуем текст
        line_height = font_size + 15
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        # Тень
        shadow_offset = 4
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            draw.text((x + shadow_offset, y + shadow_offset), line, 
                     font=font, fill=(0, 0, 0, 200))
        
        # Основной текст
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            draw.text((x, y), line, font=font, fill='white')
        
        # 5. Сохраняем
        output = BytesIO()
        bg.save(output, format='JPEG', quality=92)
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None