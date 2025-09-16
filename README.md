# МОТОРЧИК — автомобильный AI-ассистент

МОТОРЧИК — это FastAPI‑приложение, которое классифицирует пользовательские сообщения (поиск авто, вопросы об устройстве, сравнения, рекомендации, помощь, системные запросы, базовое общение) и обрабатывает их локально, а для диалоговых ответов использует Llama.

## Возможности
- Классификация запросов с точностью 95%+ (v4 роутер на 170 тестах)
- Поиск автомобилей по критериям (марка/модель/цвет/цена/год/привод и т.д.)
- Объяснение автомобильных технологий и систем (ABS, ESP, вариатор, гибрид…)
- Сравнения (бензин vs дизель, автомат vs механика, марки/кузова и др.)
- Персональные рекомендации (для семьи, города, зимы, такси, студента…)
- Базовое общение, системная помощь (что умеет ассистент)
- Фильтрация неавтомобильных тем с вежливым ответом‑отказом

## Архитектура (кратко)
- `app.py` — FastAPI приложение и REST‑эндпоинты
- `enhanced_query_router_v4.py` — основной роутер с высокой точностью
- `enhanced_query_router_v3.py` — роутер с фильтрацией неавтомобильных запросов
- `enhanced_query_router.py`, `enhanced_query_router_v2.py` — предыдущие версии роутера
- `modules/search/auto_search_processor.py` — обработка поисковых запросов по авто
- `modules/credit/loan_calculator.py` — расчёт кредита
- `enhanced_llama_processor.py`, `llama_service.py` — интеграция с Llama
- Тесты/скрипты: `test_v4_extended.py`, `test_v3_filtering.py`, `test_v2_accuracy.py`, и др.

### Структура проекта
```text
├─ app.py
├─ enhanced_query_router.py
├─ enhanced_query_router_v2.py
├─ enhanced_query_router_v3.py
├─ enhanced_query_router_v4.py
├─ enhanced_llama_processor.py
├─ llama_service.py
├─ mistral_service.py              # отключено по умолчанию (без ключа)
├─ modules/
│  ├─ search/auto_search_processor.py
│  └─ credit/loan_calculator.py
├─ tests & scripts
│  ├─ test_v4_extended.py
│  ├─ test_v3_filtering.py
│  ├─ test_v2_accuracy.py
│  └─ extended_test_queries.py
└─ requirements.txt
```

## Требования
- Python 3.11+ (рекомендуется 3.12/3.13)
- pip
- Доступ к Llama (локальный/удалённый), настроенный в `llama_service.py` или через переменные окружения (см. ниже)

## Переменные окружения
Задайте при необходимости:
- `LLAMA_API_BASE` — базовый URL вашего Llama‑сервера, например `http://127.0.0.1:11434`
- `LLAMA_API_KEY` — если требуется ключ для доступа к Llama‑сервису
- `MISTRAL_API_KEY` — опционально, если решите временно включать Mistral (по умолчанию не используется)
- `LOG_LEVEL` — уровень логирования (`INFO`/`DEBUG` и т.д.)

Windows PowerShell:
```powershell
$env:LLAMA_API_BASE = "http://127.0.0.1:11434"
# $env:LLAMA_API_KEY = "<your_key>"
# $env:LOG_LEVEL = "INFO"
```
Linux/macOS:
```bash
export LLAMA_API_BASE="http://127.0.0.1:11434"
# export LLAMA_API_KEY="<your_key>"
# export LOG_LEVEL="INFO"
```

Примечание: интеграция с Mistral отключена по умолчанию. Файл `mistral_service.py` не содержит ключ. При необходимости используйте `MISTRAL_API_KEY` через окружение.

## Установка и запуск

### 1) Клонирование проекта
```bash
# HTTPS
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>.git motorchik
cd motorchik

# Или SSH
# git clone git@github.com:<ORG>/<REPO>.git motorchik
# cd motorchik
```

### 2) Создать виртуальное окружение и активировать
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS (bash/zsh)
# python3 -m venv .venv
# source .venv/bin/activate
```

### 3) Установить зависимости
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Настройки Llama
Отредактируйте `llama_service.py` под ваш источник Llama (локальный сервер, HTTP API и т.п.) или задайте переменные окружения, если сервис это поддерживает. Пример (если используется HTTP‑endpoint):
```bash
# Пример переменных окружения (кастомизируйте под ваш сервис)
# Windows PowerShell
$env:LLAMA_API_BASE="http://127.0.0.1:11434"
# Linux/macOS
# export LLAMA_API_BASE="http://127.0.0.1:11434"
```

### 5) Запуск сервера (локально)
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Сервер будет доступен на `http://127.0.0.1:8000`.

## Эндпоинты

### POST `/api/enhanced-chat-v4`
Основной роутер (высокая точность). Тело запроса:
```json
{
  "message": "Что такое ABS?",
  "user_id": "demo"
}
```
Пример ответа (объяснение/диалог через Llama):
```json
{
  "success": true,
  "type": "automotive_question",
  "query_type": "question",
  "message": "ABS — это антиблокировочная система...",
  "llama_used": true,
  "mistral_used": false
}
```
Пример ответа (неавтомобильный запрос — вежливый отказ):
```json
{
  "success": true,
  "type": "non_automotive",
  "query_type": "rejected",
  "message": "Здравствуйте! Это МОТОРЧИК.\nК сожалению, я специализируюсь только на автомобильных вопросах. Пожалуйста, задайте ваш вопрос, связанный с автомобилями, и я с радостью помогу!",
  "llama_used": false,
  "mistral_used": false,
  "rejected": true
}
```

### POST `/api/enhanced-chat-v3`
Роутер с жёсткой фильтрацией неавтомобильных запросов. Схема запроса/ответа аналогична v4.

## Примеры запросов (curl)
```bash
# Объяснение
curl -X POST http://127.0.0.1:8000/api/enhanced-chat-v4 \
  -H "Content-Type: application/json" \
  -d '{"message":"Что такое ABS?","user_id":"demo"}'

# Рекомендация
curl -X POST http://127.0.0.1:8000/api/enhanced-chat-v4 \
  -H "Content-Type: application/json" \
  -d '{"message":"Порекомендуй авто для семьи","user_id":"demo"}'

# Поиск
curl -X POST http://127.0.0.1:8000/api/enhanced-chat-v4 \
  -H "Content-Type: application/json" \
  -d '{"message":"Покажи машины до 2 млн","user_id":"demo"}'
```

## Тестирование
Запуск расширенного теста классификатора v4 (170 запросов):
```bash
python test_v4_extended.py
```
Фильтрация неавтомобильных запросов (v3):
```bash
python test_v3_filtering.py
```

На некоторых терминалах Windows включите UTF‑8, чтобы избежать ошибок вывода:
```powershell
chcp 65001
```

## Отладка и частые проблемы
- Предупреждения sklearn о несовпадении версий при загрузке pickle — ожидаемы, но рекомендуется привести версии к совместимым.
- Поиск: проверьте `modules/search/auto_search_processor.py` на синтаксис и корректность извлечения сущностей.
- Кредитный калькулятор: убедитесь, что у `LoanCalculator` реализован `calculate_loan` и корректно импортирован в роутер.
- Llama не отвечает: проверьте `LLAMA_API_BASE`/ключ, сетевую доступность и конфиг `llama_service.py`.
- Windows PowerShell: при проблемах с кодировкой используйте `chcp 65001`.

## Публикация в GitHub
Готовый публичный репозиторий: `https://github.com/gorffff41-sys/MotorchikAAA`

Загрузить проект в этот репозиторий:
```bash
# из корня проекта
git init
git add .
git commit -m "Initial import: Motorchik AI assistant"

git branch -M main
git remote add origin https://github.com/gorffff41-sys/MotorchikAAA.git

git push -u origin main
```
Если репозиторий уже инициализирован — замените или обновите `origin`:
```bash
git remote remove origin 2>$null || true
git remote add origin https://github.com/gorffff41-sys/MotorchikAAA.git
git push -u origin main
```

## Лицензия
Укажите условия лицензирования проекта (при необходимости).
