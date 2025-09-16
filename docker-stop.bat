@echo off
echo ========================================
echo Остановка Docker контейнера MOTORCHI_APP
echo ========================================

echo.
echo Остановка контейнера...
docker-compose down

echo.
echo Контейнер остановлен!
pause 