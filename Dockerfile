FROM python:3.11-slim

# Устанавливаем необходимые пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Создаем папки
RUN mkdir -p /app/assets/fonts
RUN mkdir -p /app/assets/backgrounds
RUN mkdir -p /app/assets/gifs

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Убеждаемся, что шрифты на месте
RUN ls -la /app/assets/fonts/ && echo "Шрифты скопированы"

# Создаем временную папку для изображений
RUN mkdir -p /tmp/pepe_bot

CMD ["python", "bot.py"]