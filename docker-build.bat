@echo off
echo ========================================
echo Сборка Docker образа MOTORCHI_APP
echo ========================================

echo.
echo Остановка существующих контейнеров...
docker-compose down

echo.
echo Удаление старых образов...
docker rmi motorchi_app:latest 2>nul

echo.
echo Сборка нового образа...
docker-compose build --no-cache

echo.
echo Сборка завершена!
echo Для запуска используйте: docker-compose up
echo Для запуска в фоне: docker-compose up -d
echo.
pause 