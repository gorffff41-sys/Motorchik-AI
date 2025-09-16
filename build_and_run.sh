#!/bin/bash

echo "🚀 Сборка и запуск контейнера motorchik_app..."

# Остановка существующего контейнера если он запущен
echo "🛑 Остановка существующего контейнера..."
docker-compose down

# Удаление старого образа если он существует
echo "🗑️ Удаление старого образа..."
docker rmi motorchik_app:latest 2>/dev/null || true

# Сборка нового образа
echo "🔨 Сборка нового образа..."
docker-compose build --no-cache

# Запуск контейнера
echo "▶️ Запуск контейнера..."
docker-compose up -d

# Проверка статуса
echo "📊 Проверка статуса контейнера..."
docker-compose ps

echo "✅ Контейнер motorchik_app запущен на порту 5000"
echo "🌐 Приложение доступно по адресу: http://localhost:5000"
echo ""
echo "📋 Полезные команды:"
echo "  docker-compose logs -f motorchik_app  # Просмотр логов"
echo "  docker-compose stop motorchik_app     # Остановка"
echo "  docker-compose restart motorchik_app  # Перезапуск" 