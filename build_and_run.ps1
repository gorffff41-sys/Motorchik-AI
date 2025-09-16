# PowerShell скрипт для сборки и запуска контейнера motorchik_app

Write-Host "🚀 Сборка и запуск контейнера motorchik_app..." -ForegroundColor Green

# Остановка существующего контейнера если он запущен
Write-Host "🛑 Остановка существующего контейнера..." -ForegroundColor Yellow
docker-compose down

# Удаление старого образа если он существует
Write-Host "🗑️ Удаление старого образа..." -ForegroundColor Yellow
docker rmi motorchik_app:latest 2>$null

# Сборка нового образа
Write-Host "🔨 Сборка нового образа..." -ForegroundColor Cyan
docker-compose build --no-cache

# Запуск контейнера
Write-Host "▶️ Запуск контейнера..." -ForegroundColor Green
docker-compose up -d

# Проверка статуса
Write-Host "📊 Проверка статуса контейнера..." -ForegroundColor Magenta
docker-compose ps

Write-Host "✅ Контейнер motorchik_app запущен на порту 5000" -ForegroundColor Green
Write-Host "🌐 Приложение доступно по адресу: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Полезные команды:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f motorchik_app  # Просмотр логов" -ForegroundColor White
Write-Host "  docker-compose stop motorchik_app     # Остановка" -ForegroundColor White
Write-Host "  docker-compose restart motorchik_app  # Перезапуск" -ForegroundColor White 