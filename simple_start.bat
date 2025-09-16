@echo off
chcp 65001 >nul
title Автоассистент - Упрощенный запуск

echo.
echo ========================================
echo    🚗 Автоассистент - Упрощенный запуск
echo ========================================
echo.

echo 🔍 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден в PATH
    echo 📝 Убедитесь, что Python установлен и добавлен в PATH
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

echo 🚀 Запуск упрощенной версии...
python simple_start.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска
    echo 📝 Проверьте логи выше для диагностики
    pause
) 
 
 
 
 
 