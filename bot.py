import os
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request, send_file
from dotenv import load_dotenv
import time
import threading
import json
import random
from io import BytesIO
import traceback

# Импортируем наши модули
from wishes import get_random_wish
from image_generator import create_wish_image

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PORT = int(os.getenv('PORT', 8080))

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не задан!")

print("🚀 Запуск DobroPepeBot...")
print("🎲 Бот с добрыми пожеланиями")

# Проверяем шрифты при старте
fonts_dir = "assets/fonts"
if os.path.exists(fonts_dir):
    fonts = os.listdir(fonts_dir)
    print(f"📁 Найдено шрифтов: {len(fonts)}")
    for f in fonts:
        print(f"   - {f}")
else:
    print(f"❌ Папка {fonts_dir} не найдена!")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

# ========== ВРЕМЕННОЕ ХРАНИЛИЩЕ ==========
temp_images = {}
user_states = {}

def cleanup_temp_images():
    """Очистка старых файлов каждые 10 минут"""
    while True:
        time.sleep(600)
        now = time.time()
        to_delete = [k for k, (_, ts) in temp_images.items() if now - ts > 900]
        for k in to_delete:
            del temp_images[k]
        if to_delete:
            print(f"🧹 Очищено {len(to_delete)} старых файлов")

threading.Thread(target=cleanup_temp_images, daemon=True).start()

def generate_unique_id():
    """Генерирует уникальный ID для временных файлов"""
    return f"img_{int(time.time()*1000)}_{random.randint(1000,9999)}"

def get_random_gif():
    """Возвращает случайную гифку из папки assets/gifs/"""
    gifs_folder = "assets/gifs"
    try:
        gif_files = [f for f in os.listdir(gifs_folder) if f.endswith('.gif')]
        if gif_files:
            selected = random.choice(gif_files)
            gif_path = os.path.join(gifs_folder, selected)
            with open(gif_path, 'rb') as f:
                gif_data = f.read()
            print(f"🎬 Выбрана гифка: {selected}, размер: {len(gif_data)/1024:.1f} КБ")
            return gif_data, selected
    except Exception as e:
        print(f"❌ Ошибка при выборе гифки: {e}")
    return None, None

# ========== ФУНКЦИИ ДЛЯ ЛИЧНЫХ СООБЩЕНИЙ ==========
def create_main_keyboard():
    """Создает главную клавиатуру"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🎲 Получить пожелание")
    btn2 = KeyboardButton("📖 О боте")
    markup.add(btn1, btn2)
    return markup

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обрабатывает /start и /help"""
    welcome_text = (
        "✨ **Добро пожаловать в DobroPepeBot!** ✨\n\n"
        "Я здесь, чтобы поделиться с тобой теплыми и искренними пожеланиями.\n\n"
        "📝 **Как пользоваться:**\n"
        "• В **личных сообщениях** нажми кнопку ниже 👇\n"
        "• В **любом чате** просто напиши @DobroPepeBot\n\n"
        "🎲 И я пришлю тебе гифку с крутящимся кубиком, "
        "а затем — пожелание, которое согреет душу.\n\n"
        "Поехали! 🚀"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🎲 Получить пожелание")
def handle_wish_button(message):
    """Обработчик кнопки получения пожелания"""
    send_pepe_wish_sequence(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📖 О боте")
def handle_about_button(message):
    """Информация о боте"""
    about_text = (
        "🧡 **О боте**\n\n"
        "DobroPepeBot создан, чтобы дарить людям тепло и поддержку.\n"
        "Каждое пожелание — это маленький лучик света в твой день.\n\n"
        "Просто вызови меня в любом чате через @ или нажми кнопку,\n"
        "и я поделюсь с тобой чем-то важным.\n\n"
        "С любовью, команда DobroPepe 🤗"
    )
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# ========== ОСНОВНАЯ ЛОГИКА ==========
def send_pepe_wish_sequence(chat_id):
    """Отправляет гифку, а через 12 секунд - пожелание"""
    try:
        # 1. Отправляем гифку
        gif_data, gif_name = get_random_gif()
        
        if gif_data:
            gif_message = bot.send_animation(
                chat_id,
                gif_data,
                caption="🎲 Кручу кубик... (12 секунд)"
            )
        else:
            gif_message = bot.send_message(
                chat_id,
                "🎲 Кручу кубик... (12 секунд)"
            )
        
        # 2. Через 12 секунд отправляем пожелание отдельным сообщением
        def send_wish_later():
            time.sleep(12)
            try:
                wish_text = get_random_wish()
                print(f"✨ Генерирую пожелание: {wish_text[:30]}...")
                
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    image_id = generate_unique_id()
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    
                    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    bot.send_photo(
                        chat_id,
                        image_url,
                        caption=wish_text
                    )
                    print(f"✅ Пожелание отправлено")
                else:
                    bot.send_message(chat_id, f"✨ {wish_text}")
            except Exception as e:
                print(f"❌ Ошибка при отправке пожелания: {e}")
        
        threading.Thread(target=send_wish_later, daemon=True).start()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        bot.send_message(chat_id, "✨ " + get_random_wish())

# ========== INLINE РЕЖИМ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    """Обработчик inline запросов"""
    query_text = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    print(f"📨 Inline запрос от {user_id}: '{query_text}'")
    
    if query_text == "":
        # Для инлайн отправляем гифку
        wish_text = get_random_wish()
        gif_data, gif_name = get_random_gif()
        
        if gif_data:
            # Сохраняем гифку во временное хранилище
            gif_id = generate_unique_id()
            temp_images[gif_id] = (gif_data, time.time())
            
            hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
            gif_url = f"https://{hostname}/image/{gif_id}"
            
            # Убираем description, оставляем только поддерживаемые параметры
            result = telebot.types.InlineQueryResultGif(
                id=gif_id,
                gif_url=gif_url,
                thumbnail_url=gif_url,
                title="🎲 DobroPepe",
                caption="🎲 Кручу кубик... (12 секунд)"
            )
            
            results = [result]
            
            # Запускаем отправку пожелания через 12 секунд
            def send_wish_later():
                time.sleep(12)
                try:
                    image_data = create_wish_image(wish_text)
                    if image_data:
                        image_id = generate_unique_id()
                        temp_images[image_id] = (image_data.getvalue(), time.time())
                        image_url = f"https://{hostname}/image/{image_id}"
                        
                        # Отправляем пожелание в личку пользователю
                        bot.send_photo(
                            user_id,
                            image_url,
                            caption=wish_text
                        )
                        print(f"✅ Пожелание отправлено в личку {user_id}")
                except Exception as e:
                    print(f"❌ Ошибка при отправке пожелания: {e}")
            
            threading.Thread(target=send_wish_later, daemon=True).start()
            
        else:
            # Если нет гифки - показываем фото
            image_data = create_wish_image(wish_text)
            if image_data:
                image_id = generate_unique_id()
                temp_images[image_id] = (image_data.getvalue(), time.time())
                hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                image_url = f"https://{hostname}/image/{image_id}"
                
                result = telebot.types.InlineQueryResultPhoto(
                    id=image_id,
                    photo_url=image_url,
                    thumbnail_url=image_url,
                    title="✨ Пожелание",
                    description=wish_text[:50] + "...",
                    caption=wish_text
                )
                results = [result]
            else:
                result = InlineQueryResultArticle(
                    id=generate_unique_id(),
                    title="✨ Пожелание",
                    description=wish_text[:50] + "...",
                    input_message_content=InputTextMessageContent(
                        message_text=f"✨ {wish_text}"
                    )
                )
                results = [result]
        
        try:
            bot.answer_inline_query(inline_query.id, results, cache_time=0, is_personal=True)
            print(f"✅ Инлайн результат отправлен")
        except Exception as e:
            print(f"❌ Ошибка inline: {e}")
    else:
        help_text = "❓ Просто отправь пустой запрос через @DobroPepeBot"
        result = InlineQueryResultArticle(
            id=generate_unique_id(),
            title="❓ Как пользоваться",
            description="Отправь пустой запрос",
            input_message_content=InputTextMessageContent(
                message_text=help_text
            )
        )
        bot.answer_inline_query(inline_query.id, [result], cache_time=0)

# ========== ЭНДПОИНТ ДЛЯ ФАЙЛОВ ==========
@app.route('/image/<image_id>', methods=['GET'])
def serve_image(image_id):
    """Отдает временные картинки и гифки"""
    if image_id in temp_images:
        image_data, _ = temp_images[image_id]
        
        # Определяем тип по содержимому или ID
        is_gif = image_id.startswith('img_') and len(image_data) > 100  # Простая проверка
        mimetype = 'image/gif' if is_gif else 'image/jpeg'
        
        response = send_file(
            BytesIO(image_data),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'{image_id}.{"gif" if is_gif else "jpg"}'
        )
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
        
    return "File not found", 404

# ========== ВЕБХУК ==========
def setup_webhook():
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not hostname:
        print("🌐 Локальный режим (без вебхука)")
        return

    webhook_path = f"/{TELEGRAM_TOKEN}"
    webhook_url = f"https://{hostname}{webhook_path}"

    try:
        bot.remove_webhook()
        time.sleep(1)
        success = bot.set_webhook(url=webhook_url)
        if success:
            print(f"✅ Webhook установлен: {webhook_url}")
        else:
            print("❌ Ошибка установки webhook")
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
            traceback.print_exc()
            return 'Error', 500
    return 'Bad request', 403

@app.route('/')
def index():
    gifs_count = 0
    try:
        gifs_folder = "assets/gifs"
        if os.path.exists(gifs_folder):
            gifs_count = len([f for f in os.listdir(gifs_folder) if f.endswith('.gif')])
    except:
        pass
    
    return (
        f'✨ DobroPepeBot работает!<br>'
        f'📦 Файлов в памяти: {len(temp_images)}<br>'
        f'🎬 Гифок в папке: {gifs_count}<br>'
        f'🎲 Дарим добрые пожелания!'
    ), 200

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    setup_webhook()
    print(f"🚀 Сервер запущен на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
else:
    setup_webhook()