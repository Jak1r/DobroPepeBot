import json
import random
import os

# База пожеланий (только как запасной вариант)
FALLBACK_WISHES = [
    "Ты справишься со всем, что встретится на пути",
    "В тебе больше сил, чем ты думаешь",
    "Каждый день — новый шанс стать счастливее",
    "Ты важен и нужен именно таким, какой ты есть",
    "Пусть сегодня случится что-то хорошее",
    # ... остальные
]

# Пары фраз (кнопка → процесс)
PHRASE_PAIRS = [
    ("🔮 Спросить у судьбы", "🔮 Спрашиваю у судьбы..."),
    ("✨ Открыть послание", "✨ Открываю тайное послание..."),
    ("🌟 Забрать добро", "🌟 Собираю добро..."),
    ("🎯 Испытать удачу", "🎯 Испытываю удачу..."),
    ("💫 Получить ответ", "💫 Ищу ответ..."),
    ("⭐ Взять с собой", "⭐ Упаковываю тепло..."),
    ("🌈 Поймать момент", "🌈 Ловлю момент..."),
    ("🪄 Создать чудо", "🪄 Творю чудо..."),
    ("🎁 Распаковать", "🎁 Распаковываю..."),
    ("☀️ Впустить свет", "☀️ Впускаю свет..."),
    ("🌙 Услышать тишину", "🌙 Слушаю тишину..."),
    ("⚡ Зарядиться", "⚡ Заряжаюсь..."),
    ("💎 Найти сокровище", "💎 Ищу сокровище..."),
    ("🎨 Создать настроение", "🎨 Создаю настроение..."),
    ("🌺 Принять тепло", "🌺 Принимаю тепло..."),
    ("🍀 Поймать удачу", "🍀 Ловлю удачу..."),
    ("🕯️ Зажечь свечу", "🕯️ Зажигаю свечу..."),
    ("🎐 Поймать ветер", "🎐 Ловлю ветер..."),
    ("💌 Прочитать письмо", "💌 Читаю письмо..."),
    ("🌀 Войти в поток", "🌀 Вхожу в поток...")
]

# Кэш для загруженных пожеланий
_wishes_cache = None

def load_wishes_from_file():
    """Загружает пожелания из JSON файла"""
    global _wishes_cache
    
    # Если уже загружали, возвращаем кэш
    if _wishes_cache is not None:
        print(f"📦 Используются кэшированные пожелания ({len(_wishes_cache)} шт)")
        return _wishes_cache
    
    try:
        if os.path.exists('wishes.json'):
            print(f"📁 Найден файл wishes.json, загружаю...")
            with open('wishes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Может быть список или словарь с ключом 'wishes'
                if isinstance(data, list):
                    _wishes_cache = data
                    print(f"✅ Загружено {len(data)} пожеланий из JSON (список)")
                    return data
                elif isinstance(data, dict) and 'wishes' in data:
                    _wishes_cache = data['wishes']
                    print(f"✅ Загружено {len(data['wishes'])} пожеланий из JSON (словарь)")
                    return data['wishes']
                else:
                    print(f"⚠️ Неизвестный формат JSON, использую запасные")
        else:
            print(f"📁 Файл wishes.json не найден")
            
    except Exception as e:
        print(f"⚠️ Ошибка загрузки wishes.json: {e}")
    
    # Если ничего не получилось, используем запасные
    print(f"📝 Использую запасные пожелания ({len(FALLBACK_WISHES)} шт)")
    return FALLBACK_WISHES

def get_random_wish():
    """Возвращает случайное пожелание из wishes.json"""
    wishes = load_wishes_from_file()
    return random.choice(wishes)

def get_random_phrase_pair():
    """Возвращает пару фраз (кнопка, процесс)"""
    return random.choice(PHRASE_PAIRS)

def get_random_button_phrase():
    """Возвращает случайную фразу для кнопки"""
    return random.choice(PHRASE_PAIRS)[0]

def get_random_process_phrase():
    """Возвращает случайную фразу для процесса"""
    return random.choice(PHRASE_PAIRS)[1]

# Для теста
if __name__ == "__main__":
    print("🎲 ТЕСТ ЗАГРУЗКИ:")
    wishes = load_wishes_from_file()
    print(f"📊 Всего пожеланий: {len(wishes)}")
    print(f"📝 Первые 3:")
    for i, w in enumerate(wishes[:3]):
        print(f"  {i+1}. {w[:50]}...")
    
    print(f"\n🎯 ТЕСТ ФРАЗ:")
    print(f"Случайная кнопка: {get_random_button_phrase()}")
    print(f"Случайный процесс: {get_random_process_phrase()}")