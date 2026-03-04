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

# Устанавливаем шрифты
RUN wget -O /app/assets/fonts/Impact.ttf "https://github.com/mat/best/raw/master/fonts/impact/impact.ttf"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем временную папку для изображений
RUN mkdir -p /tmp/pepe_bot

CMD ["python", "bot.py"]