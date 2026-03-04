import os
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, KeyboardButton, InlineQueryResultGif, InlineQueryResultPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, send_file
from dotenv import load_dotenv
import time
import threading
import random
from io import BytesIO
import traceback
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

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

# ========== ВРЕМЕННОЕ ХРАНИЛИЩЕ ==========
temp_images = {}
user_states = {}
pending_wishes = {}  # Для хранения пожеланий, связанных с кнопками

def cleanup_temp_images():
    """Очистка старых файлов каждые 10 минут"""
    while True:
        time.sleep(600)
        now = time.time()
        to_delete = [k for k, (_, ts) in temp_images.items() if now - ts > 900]
        for k in to_delete:
            del temp_images[k]
        
        # Очищаем старые pending_wishes
        to_delete = [k for k, (_, ts) in pending_wishes.items() if now - ts > 900]
        for k in to_delete:
            del pending_wishes[k]
        
        if to_delete:
            print(f"🧹 Очищено {len(to_delete)} старых файлов и пожеланий")

threading.Thread(target=cleanup_temp_images, daemon=True).start()

def generate_unique_id():
    """Генерирует уникальный ID для временных файлов"""
    return f"img_{int(time.time()*1000)}_{random.randint(1000,9999)}"

def generate_callback_id():
    """Генерирует уникальный ID для callback данных"""
    return f"wish_{int(time.time()*1000)}_{random.randint(1000,9999)}"

# ========== РАБОТА С ЛОКАЛЬНЫМИ ГИФКАМИ ==========
def get_random_gif_from_local():
    """Возвращает случайную гифку из локальной папки"""
    print(f"🔥 get_random_gif_from_local: начинаем поиск")
    gifs_folder = "assets/gifs"
    
    try:
        if not os.path.exists(gifs_folder):
            print(f"  ❌ Папка {gifs_folder} не существует")
            return None, None
            
        gif_files = [f for f in os.listdir(gifs_folder) if f.endswith('.gif')]
        print(f"  📁 Найдено .gif файлов: {len(gif_files)}")
        
        if not gif_files:
            print(f"  ❌ В папке {gifs_folder} нет .gif файлов")
            return None, None
            
        selected = random.choice(gif_files)
        gif_path = os.path.join(gifs_folder, selected)
        print(f"  🎲 Выбран файл: {selected}")
        
        with open(gif_path, 'rb') as f:
            gif_data = f.read()
        
        print(f"  📦 Размер файла: {len(gif_data)} байт ({len(gif_data)/1024:.1f} КБ)")
        print(f"  🔍 Первые 6 байт: {gif_data[:6]}")
            
        # Проверяем, что это действительно GIF
        if gif_data.startswith(b'GIF87a') or gif_data.startswith(b'GIF89a'):
            print(f"  ✅ Файл является GIF (сигнатура верна)")
            return gif_data, selected
        else:
            print(f"  ❌ Файл НЕ является GIF (неверная сигнатура)")
            return None, None
            
    except Exception as e:
        print(f"  ❌ Ошибка при чтении гифки: {e}")
        traceback.print_exc()
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
    print(f"🔥 /start от {message.from_user.id}")
    welcome_text = (
        "✨ **Добро пожаловать в DobroPepeBot!** ✨\n\n"
        "Я здесь, чтобы поделиться с тобой теплыми и искренними пожеланиями.\n\n"
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
    """Обработчик кнопки получения пожелания"""
    print(f"🔥 Нажата кнопка 'Получить пожелание' от {message.from_user.id}")
    send_pepe_gif_with_button(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📖 О боте")
def handle_about_button(message):
    """Информация о боте"""
    print(f"🔥 Нажата кнопка 'О боте' от {message.from_user.id}")
    about_text = (
        "🧡 **О боте**\n\n"
        "DobroPepeBot создан, чтобы дарить людям тепло и поддержку.\n"
        "Каждое пожелание — это маленький лучик света в твой день.\n\n"
        "Просто вызови меня в любом чате через @ или нажми кнопку,\n"
        "и я пришлю гифку с кнопкой для получения пожелания.\n\n"
        "С любовью, команда DobroPepe 🤗"
    )
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# ========== ОСНОВНАЯ ЛОГИКА С КНОПКОЙ ==========
def send_pepe_gif_with_button(chat_id):
    """Отправляет гифку с кнопкой для получения пожелания"""
    print(f"🔥 send_pepe_gif_with_button для chat_id: {chat_id}")
    
    try:
        # 1. Получаем случайную гифку
        print(f"  ⏳ Получаем гифку из локальной папки...")
        gif_data, gif_name = get_random_gif_from_local()
        
        if not gif_data:
            print(f"  ❌ Не удалось получить гифку, отправляю только текст")
            wish_text = get_random_wish()
            bot.send_message(chat_id, "✨ " + wish_text)
            return
        
        # 2. Генерируем пожелание и сохраняем его
        wish_text = get_random_wish()
        wish_id = generate_callback_id()
        pending_wishes[wish_id] = (wish_text, time.time())
        print(f"  ✨ Сгенерировано пожелание для кнопки {wish_id}: {wish_text[:30]}...")
        
        # 3. Создаем клавиатуру с кнопкой
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            "🎲 Получить пожелание", 
            callback_data=f"get_wish_{wish_id}"
        )
        markup.add(button)
        
        # 4. Отправляем гифку с кнопкой
        print(f"  ⏳ Отправляем гифку с кнопкой в Telegram...")
        
        gif_message = bot.send_animation(
            chat_id,
            gif_data,
            caption="🎲 Крути кубик и нажми кнопку!",
            reply_markup=markup
        )
        print(f"  ✅ Гифка с кнопкой отправлена, message_id: {gif_message.message_id}")
        
    except Exception as e:
        print(f"❌ Ошибка в send_pepe_gif_with_button: {e}")
        traceback.print_exc()
        bot.send_message(chat_id, "✨ " + get_random_wish())

# ========== ОБРАБОТЧИК НАЖАТИЙ НА КНОПКИ ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработчик нажатий на инлайн-кнопки"""
    print(f"🔥 Callback: {call.data} от {call.from_user.id}")
    
    try:
        if call.data.startswith("get_wish_"):
            wish_id = call.data.replace("get_wish_", "")
            
            if wish_id in pending_wishes:
                wish_text, timestamp = pending_wishes[wish_id]
                print(f"  ✅ Найдено пожелание: {wish_text[:30]}...")
                
                # Создаем картинку с пожеланием
                image_data = create_wish_image(wish_text)
                
                if image_data:
                    image_id = generate_unique_id()
                    temp_images[image_id] = (image_data.getvalue(), time.time())
                    
                    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
                    image_url = f"https://{hostname}/image/{image_id}"
                    
                    # Редактируем сообщение: заменяем гифку на фото с пожеланием
                    bot.edit_message_media(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        media=telebot.types.InputMediaPhoto(
                            media=image_url,
                            caption=wish_text
                        )
                    )
                    
                    # Убираем кнопки
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=None
                    )
                    
                    print(f"  ✅ Сообщение обновлено с пожеланием")
                    
                    # Удаляем использованное пожелание
                    del pending_wishes[wish_id]
                else:
                    # Если не удалось создать картинку
                    bot.edit_message_caption(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        caption=f"✨ {wish_text}"
                    )
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=None
                    )
            else:
                print(f"  ❌ Пожелание {wish_id} не найдено (возможно, устарело)")
                bot.answer_callback_query(
                    call.id,
                    text="😢 Это пожелание уже устарело, попробуй ещё раз!",
                    show_alert=False
                )
        
        # Отвечаем на callback, чтобы убрать "часики" на кнопке
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"❌ Ошибка в handle_callback: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, text="❌ Ошибка, попробуй ещё раз")

# ========== INLINE РЕЖИМ ==========
@bot.inline_handler(lambda query: True)
def inline_handler(inline_query):
    """Обработчик inline запросов"""
    query_text = inline_query.query.strip()
    user_id = inline_query.from_user.id
    
    print(f"\n🔥🔥🔥 INLINE HANDLER ВЫЗВАН 🔥🔥🔥")
    print(f"📨 Запрос: '{query_text}' от user_id: {user_id}")
    print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
    
    results = []
    hostname = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
    
    if query_text == "":
        print(f"  ✅ Пустой запрос - показываем варианты")
        
        # Вариант 1: Гифка с кнопкой (через callback)
        gif_data, gif_name = get_random_gif_from_local()
        
        if gif_data:
            # Сохраняем гифку
            gif_id = generate_unique_id()
            temp_images[gif_id] = (gif_data, time.time())
            gif_url = f"https://{hostname}/image/{gif_id}"
            
            # Генерируем пожелание для кнопки
            wish_text = get_random_wish()
            wish_id = generate_callback_id()
            pending_wishes[wish_id] = (wish_text, time.time())
            
            # Создаём клавиатуру для превью (но в инлайн-результате нельзя передать клавиатуру)
            # Поэтому просто показываем гифку
            result1 = InlineQueryResultGif(
                id=gif_id,
                gif_url=gif_url,
                thumbnail_url=gif_url,
                title="🎲 Гифка с кубиком",
                description="Нажми, чтобы отправить гифку с кнопкой",
                caption="🎲 Нажми кнопку под гифкой, чтобы получить пожелание!"
            )
            results.append(result1)
            print(f"  ✅ InlineQueryResultGif создан")
        
        # Вариант 2: Сразу пожелание (без гифки)
        wish_text = get_random_wish()
        image_data = create_wish_image(wish_text)
        
        if image_data:
            image_id = generate_unique_id()
            temp_images[image_id] = (image_data.getvalue(), time.time())
            image_url = f"https://{hostname}/image/{image_id}"
            
            result2 = InlineQueryResultPhoto(
                id=image_id,
                photo_url=image_url,
                thumbnail_url=image_url,
                title="✨ Сразу пожелание",
                description=wish_text[:50] + "...",
                caption=wish_text
            )
            results.append(result2)
            print(f"  ✅ InlineQueryResultPhoto создан")
        
    elif query_text == "wish":
        # Специальная команда для получения только пожелания
        print(f"  ✅ Команда 'wish' - показываем только пожелание")
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
                description=wish_text[:50] + "...",
                caption=wish_text
            )
            results.append(result)
        else:
            result = InlineQueryResultArticle(
                id=generate_unique_id(),
                title="✨ Пожелание",
                description=wish_text[:50] + "...",
                input_message_content=InputTextMessageContent(
                    message_text=f"✨ {wish_text}"
                )
            )
            results.append(result)
    
    else:
        print(f"  ℹ️ Неизвестный запрос - показываем инструкцию")
        result = InlineQueryResultArticle(
            id=generate_unique_id(),
            title="❓ Как пользоваться",
            description="Отправь пустой запрос или 'wish'",
            input_message_content=InputTextMessageContent(
                message_text="❓ Отправь пустой запрос для гифки или 'wish' для пожелания"
            )
        )
        results.append(result)
    
    # Отправляем результаты
    try:
        if results:
            print(f"  📤 Отправляем {len(results)} результатов в inline...")
            bot.answer_inline_query(inline_query.id, results, cache_time=0, is_personal=True)
            print(f"  ✅ Inline ответ отправлен")
        else:
            print(f"  ⚠️ Нет результатов, отправляем заглушку")
            result = InlineQueryResultArticle(
                id=generate_unique_id(),
                title="🎲 DobroPepeBot",
                description="Нажми, чтобы получить пожелание",
                input_message_content=InputTextMessageContent(
                    message_text="✨ Напиши @DobroPepeBot в любом чате"
                )
            )
            bot.answer_inline_query(inline_query.id, [result], cache_time=0)
    except Exception as e:
        print(f"  ❌ Ошибка ответа на inline: {e}")
        traceback.print_exc()
    
    print(f"🔥🔥🔥 INLINE HANDLER ЗАВЕРШЕН 🔥🔥🔥\n")

# ========== ЭНДПОИНТ ДЛЯ ФАЙЛОВ ==========
@app.route('/image/<image_id>', methods=['GET'])
def serve_image(image_id):
    """Отдает временные картинки и гифки"""
    print(f"🔥 GET /image/{image_id}")
    
    if image_id in temp_images:
        image_data, timestamp = temp_images[image_id]
        age = time.time() - timestamp
        print(f"  ✅ Файл найден, возраст: {age:.1f} сек, размер: {len(image_data)} байт")
        
        # Определяем тип по содержимому
        is_gif = image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a')
        mimetype = 'image/gif' if is_gif else 'image/jpeg'
        
        print(f"  🔍 Сигнатура: {image_data[:6]}")
        print(f"  📤 MIME-тип: {mimetype}")
        
        response = send_file(
            BytesIO(image_data),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'{image_id}.{"gif" if is_gif else "jpg"}'
        )
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        
        print(f"  ✅ Файл отправлен")
        return response
    
    print(f"  ❌ Файл {image_id} не найден")
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
        f'🎲 Пожеланий в ожидании: {len(pending_wishes)}<br>'
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