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
from concurrent.futures import ThreadPoolExecutor  # Оптимизация 6

from wishes import get_random_wish, get_random_button_phrase, get_random_process_phrase
from image_generator import create_wish_image

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PORT = int(os.getenv('PORT', 8080))

# Оптимизация 5: время хранения файлов 5 минут вместо 15
TEMP_FILE_TTL = 300  # секунд

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не задан!")

print("🚀 Запуск DobroPepeBot (оптимизированная версия)")
print("🎲 Бот с добрыми пожеланиями")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

# ========== ПУЛ ПОТОКОВ ==========
executor = ThreadPoolExecutor(max_workers=2)  # Оптимизация 6

temp_images = {}
pending_wishes = {}

def cleanup_temp_images():
    while True:
        time.sleep(600)  # раз в 10 минут
        now = time.time()
        to_delete = [k for k, (_, ts) in temp_images.items() if now - ts > TEMP_FILE_TTL]
        for k in to_delete:
            del temp_images[k]
        to_delete = [k for k, (_, ts) in pending_wishes.items() if now - ts > TEMP_FILE_TTL]
        for k in to_delete:
            del pending_wishes[k]
        if to_delete:
            print(f"🧹 Очищено {len(to_delete)} старых файлов")

threading.Thread(target=cleanup_temp_images, daemon=True).start()

def generate_unique_id(prefix="img"):
    return f"{prefix}_{int(time.time()*1000)}_{random.randint(1000,9999)}"

def get_random_gif_from_local():
    gifs_folder = "assets/gifs"
    try:
        if not os.path.exists(gifs_folder):
            return None, None
        gif_files = [f for f in os.listdir(gifs_folder) if f.endswith('.gif')]
        if not gif_files:
            return None, None
        selected = random.choice(gif_files)
        gif_path = os.path.join(gifs_folder, selected)
        with open(gif_path, 'rb') as f:
            gif_data = f.read()
        return gif_data, selected
    except Exception as e:
        print(f"  ❌ Ошибка загрузки гифки: {e}")
        return None, None

def create_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("🎲 Получить пожелание")
    btn2 = KeyboardButton("📖 О боте")
    markup.add(btn1, btn2)
    return markup

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
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎲 Получить пожелание")
def handle_wish_button(message):
    send_pepe_wish_sequence(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📖 О боте")
def handle_about_button(message):
    about_text = "🧡 **О боте**\n\nDobroPepeBot создан, чтобы дарить людям тепло и поддержку."
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

def send_pepe_wish_sequence(chat_id):
    try:
        process_phrase = get_random_process_phrase()
        gif_data, gif_name = get_random_gif_from_local()
        if not gif_data:
            wish = get_random_wish()
            bot.send_message(chat_id, f"✨ {wish} ✨")
            return

        gif_id = generate_unique_id("gif")
        temp_images[gif_id] = (gif_data, time.time())
        hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
        gif_url = f"https://{hostname}/image/{gif_id}"

        gif_message = bot.send_animation(chat_id, gif_url, caption=process_phrase)

        def send_wish_later():
            time.sleep(8)
            try:
                wish_text = get_random_wish()
                image_data = create_wish_image(wish_text)
                if image_data:
                    image_id = generate_unique_id("wish")
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    image_url = f"https://{hostname}/image/{image_id}"
                    try:
                        bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=gif_message.message_id,
                            media=telebot.types.InputMediaPhoto(media=image_url, caption=f"✨ {wish_text} ✨")
                        )
                    except:
                        bot.send_photo(chat_id, image_url, caption=f"✨ {wish_text} ✨")
                else:
                    bot.edit_message_text(chat_id=chat_id, message_id=gif_message.message_id, text=f"✨ {wish_text} ✨")
            except Exception as e:
                print(f"❌ Ошибка в send_wish_later: {e}")

        executor.submit(send_wish_later)  # Оптимизация 6: используем пул потоков

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        wish = get_random_wish()
        bot.send_message(chat_id, f"✨ {wish} ✨")

@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    query_text = inline_query.query.strip()
    user_id = inline_query.from_user.id
    print(f"\n🔥 INLINE от {user_id}: '{query_text}'")
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
    results = []

    try:
        if query_text == "":
            gif_data, _ = get_random_gif_from_local()
            if gif_data:
                gif_id = generate_unique_id("gif")
                temp_images[gif_id] = (gif_data, time.time())
                gif_url = f"https://{hostname}/image/{gif_id}"
                button_phrase = get_random_button_phrase()
                keyboard = InlineKeyboardMarkup()
                button = InlineKeyboardButton(button_phrase, callback_data=f"wish_{user_id}")
                keyboard.add(button)
                result = InlineQueryResultGif(
                    id=gif_id,
                    gif_url=gif_url,
                    thumbnail_url=gif_url,
                    title="🎲 DobroPepe",
                    reply_markup=keyboard,
                    gif_width=320,
                    gif_height=240
                )
                results.append(result)
            else:
                wish = get_random_wish()
                image_data = create_wish_image(wish)
                if image_data:
                    img_id = generate_unique_id("wish")
                    temp_images[img_id] = (image_data.getvalue(), time.time())
                    img_url = f"https://{hostname}/image/{img_id}"
                    result = InlineQueryResultPhoto(
                        id=img_id,
                        photo_url=img_url,
                        thumbnail_url=img_url,
                        title="✨ Пожелание",
                        description=wish[:50]
                    )
                    results.append(result)
        else:
            # подсказка
            result = InlineQueryResultArticle(
                id=generate_unique_id("help"),
                title="❓ Как пользоваться",
                description="Отправь пустой запрос",
                input_message_content=InputTextMessageContent("❓ Отправь пустой запрос @DobroPepeBot")
            )
            results.append(result)

        if results:
            bot.answer_inline_query(inline_query.id, results, cache_time=0, is_personal=True)
    except Exception as e:
        print(f"❌ Ошибка inline: {e}")
        traceback.print_exc()

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith("wish_"):
        user_id = call.data.replace("wish_", "")
        wish_text = get_random_wish()
        image_data = create_wish_image(wish_text)
        hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
        if image_data:
            img_id = generate_unique_id("wish")
            temp_images[img_id] = (image_data.getvalue(), time.time())
            img_url = f"https://{hostname}/image/{img_id}"
            if call.inline_message_id:
                try:
                    bot.edit_message_media(
                        inline_message_id=call.inline_message_id,
                        media=telebot.types.InputMediaPhoto(media=img_url, caption=f"✨ {wish_text} ✨")
                    )
                except:
                    bot.send_photo(call.from_user.id, img_url, caption=f"✨ {wish_text} ✨")
            else:
                bot.send_photo(call.message.chat.id, img_url, caption=f"✨ {wish_text} ✨")
        else:
            txt = f"✨ {wish_text} ✨"
            if call.inline_message_id:
                bot.edit_message_text(inline_message_id=call.inline_message_id, text=txt)
            else:
                bot.send_message(call.message.chat.id, txt)
        bot.answer_callback_query(call.id)

@app.route('/image/<image_id>', methods=['GET', 'HEAD'])
def serve_image(image_id):
    if image_id in temp_images:
        data, _ = temp_images[image_id]
        is_gif = image_id.startswith('gif')
        mimetype = 'image/gif' if is_gif else 'image/jpeg'
        if request.method == 'HEAD':
            resp = app.make_response('')
            resp.headers['Content-Type'] = mimetype
            resp.headers['Content-Length'] = str(len(data))
            return resp
        return send_file(BytesIO(data), mimetype=mimetype, download_name=f'{image_id}.{"gif" if is_gif else "jpg"}')
    return "Not found", 404

def setup_webhook():
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not hostname:
        return
    webhook_url = f"https://{hostname}/{TELEGRAM_TOKEN}"
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode())
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad', 403

@app.route('/')
def index():
    return '✨ DobroPepeBot работает!', 200

if __name__ == '__main__':
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT, debug=False)