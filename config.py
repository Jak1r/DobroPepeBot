import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Настройки Railway
RAILWAY_PUBLIC_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')
PORT = int(os.getenv('PORT', 8080))

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, 'backgrounds')
GIFS_DIR = os.path.join(ASSETS_DIR, 'gifs')

# Настройки изображений
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 720
FONT_SIZE = 60