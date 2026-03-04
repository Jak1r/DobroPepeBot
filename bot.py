import os
import telebot
from telebot.types import InlineQueryResultGif, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, send_file
from dotenv import load_dotenv
import time
import threading
import random
from io import BytesIO
import traceback
import sys
from datetime import datetime

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

# Проверка шрифтов
fonts_dir = "assets/fonts"
if os.path.exists(fonts_dir):
    fonts = os.listdir(fonts_dir)
    print(f"🔍 ПРОВЕРКА ШРИФТОВ:")
    print(f"✅ Найдено шрифтов: {len(fonts)}")
    for f in fonts:
        print(f"   - {f}")
else:
    print(f"❌ Папка {fonts_dir} не найдена!")

# Проверка гифок
gifs_dir = "assets/gifs"
if os.path.exists(gifs_dir):
    gifs = [f for f in os.listdir(gifs_dir) if f.endswith('.gif')]
    print(f"🎬 Найдено гифок: {len(gifs)}")
    for g in gifs[:5]:  # Покажем первые 5
        print(f"   - {g}")
else:
    print(f"❌ Папка {gifs_dir} не найдена!")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

# ========== ВРЕМЕННОЕ ХРАНИЛИЩЕ ==========
temp_images = {}
pending_wishes = {}

def cleanup_temp_images():
    while True:
        time.sleep(600)
        now = time.time()
        to_delete = [k for k, (_, ts) in temp_images.items() if now - ts > 900]
        for k in to_delete:
            del temp_images[k]
        
        to_delete = [k for k, (_, ts) in pending_wishes.items() if now - ts > 900]
        for k in to_delete:
            del pending_wishes[k]
        
        if to_delete:
            print(f"🧹 Очищено {len(to_delete)} старых файлов")

threading.Thread(target=cleanup_temp_images, daemon=True).start()

def generate_unique_id():
    return f"img_{int(time.time()*1000)}_{random.randint(1000,9999)}"

def generate_callback_id():
    return f"wish_{int(time.time()*1000)}_{random.randint(1000,9999)}"

# ========== РАБОТА С ЛОКАЛЬНЫМИ ГИФКАМИ ==========
def get_random_gif_from_local():
    """Возвращает случайную гифку из локальной папки"""
    gifs_folder = "assets/gifs"
    
    try:
        print(f"  🔍 Поиск гифок в {gifs_folder}")
        if not os.path.exists(gifs_folder):
            print(f"  ❌ Папка {gifs_folder} не существует")
            return None, None
            
        gif_files = [f for f in os.listdir(gifs_folder) if f.endswith('.gif')]
        print(f"  📁 Найдено .gif файлов: {len(gif_files)}")
        
        if not gif_files:
            print(f"  ❌ Нет .gif файлов")
            return None, None
            
        selected = random.choice(gif_files)
        gif_path = os.path.join(gifs_folder, selected)
        print(f"  🎲 Выбран: {selected}")
        
        with open(gif_path, 'rb') as f:
            gif_data = f.read()
        
        print(f"  📦 Размер: {len(gif_data)} байт")
        print(f"  🔍 Сигнатура: {gif_data[:6]}")
            
        if gif_data.startswith(b'GIF87a') or gif_data.startswith(b'GIF89a'):
            print(f"  ✅ Это GIF")
            return gif_data, selected
        else:
            print(f"  ❌ Не GIF")
            return None, None
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        traceback.print_exc()
        return None, None

# ========== ФУНКЦИИ ДЛЯ ЛИЧНЫХ СООБЩЕНИЙ ==========
def create_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🎲 Получить пожелание")
    btn2 = KeyboardButton("📖 О боте")
    markup.add(btn1, btn2)
    return markup

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    print(f"🔥 /start от {message.from_user.id}")
    welcome_text = (
        "✨ **Добро пожаловать в DobroPepeBot!** ✨\n\n"
        "📝 **Как пользоваться:**\n"
        "• В **личных сообщениях** нажми кнопку ниже 👇\n"
        "• В **любом чате** просто напиши @DobroPepeBot\n\n"
        "🎲 Я пришлю гифку с кубиком, а под ней будет кнопка "
        "— нажми её, чтобы получить пожелание!\n\n"
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
    print(f"🔥 Кнопка 'Получить пожелание' от {message.from_user.id}")
    send_pepe_wish_sequence(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📖 О боте")
def handle_about_button(message):
    about_text = "🧡 **О боте**\n\nDobroPepeBot создан, чтобы дарить людям тепло и поддержку."
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# ========== ЛИЧКА: ГИФКА → ЧЕРЕЗ 12 СЕК РЕДАКТИРУЕТСЯ ==========
def send_pepe_wish_sequence(chat_id):
    print(f"🔥 send_pepe_wish_sequence для {chat_id}")
    
    try:
        gif_data, gif_name = get_random_gif_from_local()
        
        if not gif_data:
            print(f"  ❌ Нет гифки, отправляю текст")
            bot.send_message(chat_id, "✨ " + get_random_wish())
            return
        
        print(f"  ⏳ Отправляю гифку...")
        gif_message = bot.send_animation(
            chat_id,
            gif_data,
            caption="🎲 Кручу кубик... (12 секунд)"
        )
        print(f"  ✅ Гифка отправлена, ID: {gif_message.message_id}")
        
        def send_wish_later():
            print(f"  ⏰ Прошло 12 секунд")
            time.sleep(12)
            try:
                wish_text = get_random_wish()
                print(f"  ✨ Пожелание: {wish_text[:30]}...")
                
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    print(f"  ✅ Картинка создана")
                    image_id = generate_unique_id()
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    
                    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    print(f"  ⏳ Редактирую сообщение...")
                    bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=gif_message.message_id,
                        media=telebot.types.InputMediaPhoto(
                            media=image_url,
                            caption=wish_text
                        )
                    )
                    print(f"  ✅ Сообщение отредактировано")
                else:
                    print(f"  ❌ Не создалась картинка")
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=gif_message.message_id,
                        text=f"✨ {wish_text}"
                    )
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                traceback.print_exc()
        
        threading.Thread(target=send_wish_later, daemon=True).start()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        bot.send_message(chat_id, "✨ " + get_random_wish())

# ========== ИНЛАЙН: ГИФКА С КНОПКОЙ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    query_text = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    print(f"\n🔥🔥🔥 INLINE от {user_id}: '{query_text}'")
    
    results = []
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
    
    try:
        if query_text == "":
            print(f"  ✅ Пустой запрос")
            
            gif_data, gif_name = get_random_gif_from_local()
            
            if gif_data:
                print(f"  ✅ Гифка получена")
                gif_id = generate_unique_id()
                temp_images[gif_id] = (gif_data, time.time())
                gif_url = f"https://{hostname}/image/{gif_id}"
                
                print(f"  🔗 URL: {gif_url}")
                
                result = InlineQueryResultGif(
                    id=gif_id,
                    gif_url=gif_url,
                    thumbnail_url=gif_url,
                    title="🎲 DobroPepe"
                )
                results.append(result)
                print(f"  ✅ Результат добавлен")
            else:
                print(f"  ❌ Нет гифки")
                
        elif query_text == "wish":
            print(f"  ✅ Команда wish")
            wish_text = get_random_wish()
            image_data = create_wish_image(wish_text)
            
            if image_data:
                image_id = generate_unique_id()
                temp_images[image_id] = (image_data.getvalue(), time.time())
                image_url = f"https://{hostname}/image/{image_id}"
                
                result = InlineQueryResultPhoto(
                    id=image_id,
                    photo_url=image_url,
                    thumbnail_url=image_url,
                    title="✨ Пожелание",
                    description=wish_text[:50] + "..."
                )
                results.append(result)
        
        # Отправляем результаты
        if results:
            print(f"  📤 Отправляю {len(results)} результатов")
            bot.answer_inline_query(inline_query.id, results, cache_time=0, is_personal=True)
            print(f"  ✅ Готово")
        else:
            print(f"  ⚠️ Нет результатов, отправляю заглушку")
            result = InlineQueryResultArticle(
                id=generate_unique_id(),
                title="🎲 DobroPepeBot",
                description="Отправь пустой запрос",
                input_message_content=InputTextMessageContent(
                    message_text="❓ Отправь пустой запрос"
                )
            )
            bot.answer_inline_query(inline_query.id, [result], cache_time=0)
            
    except Exception as e:
        print(f"❌ ОШИБКА В INLINE: {e}")
        traceback.print_exc()

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    print(f"🔥 Сообщение от {message.from_user.id}")
    if message.animation:
        print(f"  ✅ Это гифка, добавляю кнопку")
        wish_text = get_random_wish()
        wish_id = generate_callback_id()
        pending_wishes[wish_id] = (wish_text, time.time())
        
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            "🎲 Получить пожелание", 
            callback_data=f"wish_{wish_id}"
        )
        markup.add(button)
        
        try:
            bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption="🎲 Нажми кнопку!",
                reply_markup=markup
            )
            print(f"  ✅ Кнопка добавлена")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    print(f"🔥 Callback: {call.data}")
    
    try:
        if call.data.startswith("wish_"):
            wish_id = call.data.replace("wish_", "")
            
            if wish_id in pending_wishes:
                wish_text, _ = pending_wishes[wish_id]
                print(f"  ✅ Найдено пожелание: {wish_text[:30]}...")
                
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    image_id = generate_unique_id()
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    
                    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=wish_text
                    )
                    print(f"  ✅ Пожелание отправлено")
                    
                    del pending_wishes[wish_id]
                else:
                    bot.send_message(
                        call.message.chat.id,
                        f"✨ {wish_text}"
                    )
            else:
                print(f"  ❌ Пожелание не найдено")
                bot.answer_callback_query(
                    call.id,
                    text="😢 Устарело",
                    show_alert=False
                )
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
    
    bot.answer_callback_query(call.id)

# ========== ЭНДПОИНТ ДЛЯ ФАЙЛОВ ==========
@app.route('/image/<image_id>', methods=['GET'])
def serve_image(image_id):
    print(f"🔥 GET /image/{image_id}")
    
    try:
        if image_id in temp_images:
            image_data, _ = temp_images[image_id]
            
            is_gif = image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a')
            mimetype = 'image/gif' if is_gif else 'image/jpeg'
            
            print(f"  ✅ Отдаю файл, тип: {mimetype}")
            
            response = send_file(
                BytesIO(image_data),
                mimetype=mimetype,
                as_attachment=False,
                download_name=f'{image_id}.{"gif" if is_gif else "jpg"}'
            )
            
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return "File not found", 404

# ========== ВЕБХУК ==========
def setup_webhook():
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not hostname:
        print("🌐 Локальный режим")
        return

    webhook_path = f"/{TELEGRAM_TOKEN}"
    webhook_url = f"https://{hostname}{webhook_path}"

    try:
        bot.remove_webhook()
        time.sleep(1)
        success = bot.set_webhook(url=webhook_url)
        if success:
            print(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
    except Exception as e:
        print(f"❌ Ошибка вебхука: {e}")
        traceback.print_exc()
        return 'Error', 500
    
    return 'Bad request', 403

@app.route('/')
def index():
    return '✨ DobroPepeBot работает!', 200

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    setup_webhook()
    print(f"🚀 Сервер на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
else:
    setup_webhook()