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
from wishes import get_random_wish, get_random_button_phrase, get_random_process_phrase
from image_generator import create_wish_image

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PORT = int(os.getenv('PORT', 8080))

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не задан!")

print("🚀 Запуск DobroPepeBot...")
print("🎲 Бот с добрыми пожеланиями")

# Проверка ресурсов
fonts_dir = "assets/fonts"
gifs_dir = "assets/gifs"
backgrounds_dir = "assets/backgrounds"
emojis_dir = "assets/emojis"

if os.path.exists(fonts_dir):
    fonts = os.listdir(fonts_dir)
    print(f"🔍 ШРИФТОВ: {len(fonts)}")
if os.path.exists(gifs_dir):
    gifs = [f for f in os.listdir(gifs_dir) if f.endswith('.gif')]
    print(f"🎬 ГИФОК: {len(gifs)}")
if os.path.exists(backgrounds_dir):
    bgs = [f for f in os.listdir(backgrounds_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    print(f"🖼️ ФОНОВ: {len(bgs)}")
if os.path.exists(emojis_dir):
    emoji_files = [f for f in os.listdir(emojis_dir) if f.endswith('.png')]
    print(f"✨ ЭМОДЗИ-PNG: {len(emoji_files)}")

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

def generate_unique_id(prefix="img"):
    return f"{prefix}_{int(time.time()*1000)}_{random.randint(1000,9999)}"

def generate_callback_id():
    return f"wish_{int(time.time()*1000)}_{random.randint(1000,9999)}"

# ========== РАБОТА С ЛОКАЛЬНЫМИ ГИФКАМИ ==========
def get_random_gif_from_local():
    """Возвращает случайную гифку из локальной папки"""
    gifs_folder = "assets/gifs"
    
    try:
        if not os.path.exists(gifs_folder):
            print(f"  ❌ Папка {gifs_folder} не существует")
            return None, None
            
        gif_files = [f for f in os.listdir(gifs_folder) if f.endswith('.gif')]
        
        if not gif_files:
            return None, None
            
        selected = random.choice(gif_files)
        gif_path = os.path.join(gifs_folder, selected)
        
        with open(gif_path, 'rb') as f:
            gif_data = f.read()
        
        # Проверяем сигнатуру
        if gif_data.startswith(b'GIF87a') or gif_data.startswith(b'GIF89a'):
            print(f"  ✅ Это GIF")
        else:
            print(f"  ⚠️ Странная сигнатура: {gif_data[:10]}")
        
        return gif_data, selected
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
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
    welcome_text = (
        "✨ **Добро пожаловать в DobroPepeBot!** ✨\n\n"
        "📝 **Как пользоваться:**\n"
        "• В **личных сообщениях** нажми кнопку ниже 👇\n"
        "• В **любом чате** просто напиши @DobroPepeBot\n\n"
        "🎲 Я пришлю гифку, а затем — пожелание, которое согреет душу.\n\n"
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
    about_text = (
        "🧡 **О боте**\n\n"
        "DobroPepeBot создан, чтобы дарить людям тепло и поддержку.\n"
        "Каждое пожелание — это маленький лучик света в твой день.\n\n"
        "С любовью, команда DobroPepe 🤗"
    )
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# ========== ЛИЧКА: ГИФКА → ЧЕРЕЗ 8 СЕК РЕДАКТИРУЕТСЯ ==========
def send_pepe_wish_sequence(chat_id):
    """Отправляет гифку, затем картинку с пожеланием"""
    try:
        print(f"\n🎬 send_pepe_wish_sequence для {chat_id}")
        
        # Получаем случайную фразу для процесса
        process_phrase = get_random_process_phrase()
        print(f"  💬 Фраза процесса: {process_phrase}")
        
        # Получаем случайную гифку
        gif_data, gif_name = get_random_gif_from_local()
        
        if not gif_data:
            print(f"  ❌ Нет гифок, отправляю только пожелание")
            wish_text = get_random_wish()
            bot.send_message(chat_id, f"✨ {wish_text} ✨")
            return
        
        # Проверяем, что это действительно GIF
        if not (gif_data.startswith(b'GIF87a') or gif_data.startswith(b'GIF89a')):
            print(f"  ❌ Файл не является GIF!")
            wish_text = get_random_wish()
            bot.send_message(chat_id, f"✨ {wish_text} ✨")
            return
        
        # Сохраняем гифку во временное хранилище
        gif_id = generate_unique_id("gif")
        temp_images[gif_id] = (gif_data, time.time())
        hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
        gif_url = f"https://{hostname}/image/{gif_id}"
        
        # Отправляем гифку с креативной фразой
        gif_message = bot.send_animation(
            chat_id,
            gif_url,
            caption=process_phrase
        )
        print(f"  ✅ Гифка отправлена, ID: {gif_message.message_id}")
        
        def send_wish_later():
            time.sleep(8)
            try:
                wish_text = get_random_wish()
                print(f"  ✨ Пожелание: {wish_text[:30]}...")
                
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    image_id = generate_unique_id("wish")
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    # Пытаемся отредактировать сообщение
                    try:
                        bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=gif_message.message_id,
                            media=telebot.types.InputMediaPhoto(
                                media=image_url,
                                caption=f"✨ {wish_text} ✨"  # Добавляем блёстки в подпись
                            )
                        )
                        print(f"  ✅ Сообщение отредактировано на фото")
                    except Exception as e:
                        print(f"  ⚠️ Не удалось отредактировать: {e}")
                        # Отправляем новым сообщением
                        bot.send_photo(
                            chat_id,
                            image_url,
                            caption=f"✨ {wish_text} ✨"  # Добавляем блёстки в подпись
                        )
                        print(f"  ✅ Отправлено новое сообщение с фото")
                else:
                    print(f"  ❌ Не удалось создать картинку")
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=gif_message.message_id,
                        text=f"✨ {wish_text} ✨"  # Добавляем блёстки в текст
                    )
            except Exception as e:
                print(f"❌ Ошибка в send_wish_later: {e}")
                traceback.print_exc()
        
        threading.Thread(target=send_wish_later, daemon=True).start()
        
    except Exception as e:
        print(f"❌ Ошибка в send_pepe_wish_sequence: {e}")
        traceback.print_exc()
        wish_text = get_random_wish()
        bot.send_message(chat_id, f"✨ {wish_text} ✨")

# ========== ИНЛАЙН: ГИФКА С КНОПКОЙ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    query_text = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    print(f"\n🔥🔥🔥 INLINE от {user_id}: '{query_text}'")
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
    
    results = []
    
    try:
        if query_text == "":
            # Пустой запрос - показываем гифку с кнопкой
            print(f"  ✅ Пустой запрос, ищем гифку...")
            gif_data, gif_name = get_random_gif_from_local()
            
            if gif_data:
                gif_id = generate_unique_id("gif")
                temp_images[gif_id] = (gif_data, time.time())
                gif_url = f"https://{hostname}/image/{gif_id}"
                
                # Получаем случайную фразу для кнопки
                button_phrase = get_random_button_phrase()
                
                # Создаем клавиатуру с кнопкой
                keyboard = InlineKeyboardMarkup()
                button = InlineKeyboardButton(
                    button_phrase,
                    callback_data=f"wish_{user_id}"
                )
                keyboard.add(button)
                
                # Создаем inline результат с кнопкой
                result = InlineQueryResultGif(
                    id=gif_id,
                    gif_url=gif_url,
                    thumbnail_url=gif_url,
                    title="🎲 DobroPepe - получи пожелание",
                    reply_markup=keyboard,
                    gif_width=320,
                    gif_height=240
                )
                results.append(result)
                print(f"  ✅ GIF результат добавлен с кнопкой: {button_phrase}")
            else:
                print(f"  ❌ Нет гифок, показываем пожелание")
                wish_text = get_random_wish()
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    image_id = generate_unique_id("wish")
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    result = InlineQueryResultPhoto(
                        id=image_id,
                        photo_url=image_url,
                        thumbnail_url=image_url,
                        photo_width=1080,
                        photo_height=720,
                        title="✨ Пожелание",
                        description=wish_text[:50]
                    )
                    results.append(result)
                    print(f"  ✅ Пожелание добавлено")
        
        elif query_text == "wish":
            # Команда wish - показываем пожелание
            print(f"  ✅ Команда wish")
            wish_text = get_random_wish()
            image_data = create_wish_image(wish_text)
            
            if image_data:
                image_id = generate_unique_id("wish")
                temp_images[image_id] = (image_data.getvalue(), time.time())
                image_url = f"https://{hostname}/image/{image_id}"
                
                result = InlineQueryResultPhoto(
                    id=image_id,
                    photo_url=image_url,
                    thumbnail_url=image_url,
                    photo_width=1080,
                    photo_height=720,
                    title="✨ Пожелание",
                    description=wish_text[:50]
                )
                results.append(result)
                print(f"  ✅ Пожелание добавлено")
        
        else:
            # Любой другой запрос - показываем подсказку
            print(f"  ℹ️ Неизвестный запрос, показываем подсказку")
            result = InlineQueryResultArticle(
                id=generate_unique_id("help"),
                title="❓ Как пользоваться",
                description="Отправь пустой запрос, чтобы получить гифку с кнопкой",
                input_message_content=InputTextMessageContent(
                    "❓ Просто отправь пустой запрос @DobroPepeBot\n\n"
                    "Например: @DobroPepeBot и сразу отправь"
                )
            )
            results.append(result)
        
        # Отправляем результаты
        if results:
            try:
                bot.answer_inline_query(
                    inline_query.id, 
                    results, 
                    cache_time=0, 
                    is_personal=True
                )
                print(f"✅ Отправлено {len(results)} результатов")
            except Exception as e:
                print(f"❌ Ошибка при отправке результатов: {e}")
                traceback.print_exc()
        else:
            print(f"⚠️ Нет результатов, отправляю заглушку")
            fallback = InlineQueryResultArticle(
                id=generate_unique_id("empty"),
                title="❌ Нет результатов",
                description="Попробуйте позже",
                input_message_content=InputTextMessageContent(
                    "😢 Не удалось загрузить контент. Попробуйте позже."
                )
            )
            bot.answer_inline_query(inline_query.id, [fallback], cache_time=0)
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА В INLINE: {e}")
        traceback.print_exc()
        
        try:
            error_result = InlineQueryResultArticle(
                id=generate_unique_id("error"),
                title="❌ Ошибка",
                description="Что-то пошло не так",
                input_message_content=InputTextMessageContent(
                    "😢 Произошла ошибка. Попробуйте позже."
                )
            )
            bot.answer_inline_query(inline_query.id, [error_result], cache_time=0)
        except:
            pass

# ========== ОБРАБОТЧИК КОЛБЭКОВ ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    print(f"🔥 Callback: {call.data}")
    print(f"  📱 Тип: {'inline' if call.inline_message_id else 'обычное сообщение'}")
    
    try:
        if call.data.startswith("wish_"):
            user_id = call.data.replace("wish_", "")
            
            # Получаем пожелание
            wish_text = get_random_wish()
            
            # Создаем картинку с пожеланием
            image_data = create_wish_image(wish_text)
            
            if image_data:
                image_id = generate_unique_id("wish")
                temp_images[image_id] = (image_data.getvalue(), time.time())
                
                hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                image_url = f"https://{hostname}/image/{image_id}"
                
                # Проверяем, откуда пришел callback
                if call.inline_message_id:
                    # Это inline режим - редактируем исходное сообщение
                    try:
                        bot.edit_message_media(
                            inline_message_id=call.inline_message_id,
                            media=telebot.types.InputMediaPhoto(
                                media=image_url,
                                caption=f"✨ {wish_text} ✨"  # Добавляем блёстки в подпись
                            )
                        )
                        print(f"  ✅ Inline сообщение отредактировано")
                    except Exception as e:
                        print(f"  ⚠️ Не удалось отредактировать: {e}")
                        # Если не получается отредактировать, отправляем в личку
                        bot.send_photo(
                            call.from_user.id,
                            image_url,
                            caption=f"✨ {wish_text} ✨"  # Добавляем блёстки в подпись
                        )
                else:
                    # Это обычное сообщение в личке
                    bot.send_photo(
                        call.message.chat.id,
                        image_url,
                        caption=f"✨ {wish_text} ✨",  # Добавляем блёстки в подпись
                        reply_to_message_id=call.message.message_id
                    )
                    print(f"  ✅ Пожелание отправлено в личку")
            else:
                # Если не удалось создать картинку
                wish_text_plain = f"✨ {wish_text} ✨"
                if call.inline_message_id:
                    bot.edit_message_text(
                        inline_message_id=call.inline_message_id,
                        text=wish_text_plain
                    )
                else:
                    bot.send_message(
                        call.message.chat.id,
                        wish_text_plain,
                        reply_to_message_id=call.message.message_id
                    )
            
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        print(f"❌ Ошибка в callback: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, text="😢 Ошибка", show_alert=False)

# ========== ЭНДПОИНТ ДЛЯ ФАЙЛОВ ==========
@app.route('/image/<image_id>', methods=['GET', 'HEAD'])
def serve_image(image_id):
    if image_id in temp_images:
        image_data, _ = temp_images[image_id]
        
        # Определяем тип по ID
        is_gif = image_id.startswith('gif')
        mimetype = 'image/gif' if is_gif else 'image/jpeg'
        
        if request.method == 'HEAD':
            response = app.make_response('')
            response.headers['Content-Type'] = mimetype
            response.headers['Content-Length'] = str(len(image_data))
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        response = send_file(
            BytesIO(image_data),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'{image_id}.{"gif" if is_gif else "jpg"}'
        )
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
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
        print(f"❌ Ошибка: {e}")
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