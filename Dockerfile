FROM python:3.9-slim

WORKDIR /app
COPY . /app

# Устанавливаем системные зависимости для OpenCV (без GUI), FFmpeg и работы с графикой
RUN apt-get update && apt-get install -y \
    build-essential \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Пробрасываем порт для FastAPI/WebSocket сервера
EXPOSE 8000

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]