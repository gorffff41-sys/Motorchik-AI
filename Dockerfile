# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Rust для компиляции некоторых пакетов
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директории для логов и данных
RUN mkdir -p logs instance reports debug_html

# Устанавливаем права на файлы
RUN chmod +x *.py

# Открываем порт 5000
EXPOSE 5000

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда для запуска приложения
CMD ["python", "app.py"]

# Метаданные образа
LABEL maintainer="МОТОРЧИК Team"
LABEL description="Умный помощник по выбору автомобиля МОТОРЧИК"
LABEL version="2.0.0"
LABEL name="MOTORCHI_APP"

# Создание директории для ML моделей если её нет
RUN mkdir -p ml_models

# Альтернативная команда для FastAPI/Uvicorn (раскомментировать при необходимости)
# CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--reload"] 