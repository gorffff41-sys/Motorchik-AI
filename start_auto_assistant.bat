@echo off
chcp 65001 >nul
title Автоассистент - Запуск системы

echo.
echo ========================================
echo    🚗 Автоассистент - Запуск системы
echo ========================================
echo.

echo 🔍 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден в PATH
    echo 📝 Убедитесь, что Python установлен и добавлен в PATH
    echo 📝 Или используйте: py --version
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

echo 🚀 Запуск автоассистента...
echo 📍 Веб-интерфейс: http://localhost:8001
echo 📍 API документация: http://localhost:8001/docs
echo 📍 Админ-панель: http://localhost:8001/static/dashboard.html
echo.
echo ⏹️  Для остановки нажмите Ctrl+C
echo.

python start_windows.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска системы
    echo 📝 Проверьте логи выше для диагностики
    pause
) 
 
 
 
 
 