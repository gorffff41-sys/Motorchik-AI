# 🐳 Контейнер xuy

Контейнер для запуска FastAPI приложения "Автоассистент" на порту 5000.

## 📋 Требования

- Docker
- Docker Compose

## 🚀 Быстрый запуск

### Windows (PowerShell)
```powershell
.\run_xuy.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x run_xuy.sh
./run_xuy.sh
```

### Ручной запуск
```bash
# Сборка и запуск
docker-compose up --build -d

# Проверка статуса
docker ps
```

## 🌐 Доступ к приложению

После успешного запуска приложение будет доступно по адресам:

- **Основное приложение**: http://localhost:5000
- **API документация**: http://localhost:5000/docs
- **Альтернативная документация**: http://localhost:5000/redoc

## 📋 Управление контейнером

### Просмотр логов
```bash
docker-compose logs -f xuy
```

### Остановка контейнера
```bash
docker-compose down
```

### Перезапуск
```bash
docker-compose restart xuy
```

### Пересборка и запуск
```bash
docker-compose up --build -d
```

### Удаление контейнера и образов
```bash
docker-compose down --rmi all --volumes
```

## 📁 Структура проекта

```
.
├── Dockerfile              # Конфигурация Docker образа
├── docker-compose.yml      # Конфигурация Docker Compose
├── .dockerignore          # Исключения для Docker
├── requirements.txt        # Python зависимости
├── app.py                 # Основное приложение
├── run_xuy.sh            # Скрипт запуска (Linux/Mac)
├── run_xuy.ps1           # Скрипт запуска (Windows)
└── README_DOCKER.md      # Этот файл
```

## 🔧 Конфигурация

### Порты
- **5000**: Основной порт приложения

### Тома (Volumes)
- `./instance` → `/app/instance` - База данных
- `./logs` → `/app/logs` - Логи приложения
- `./static` → `/app/static` - Статические файлы
- `./avatar` → `/app/avatar` - Аватары пользователей
- `./ml_models` → `/app/ml_models` - ML модели

### Переменные окружения
- `PYTHONPATH=/app` - Путь к Python модулям
- `PYTHONUNBUFFERED=1` - Небуферизованный вывод Python

## 🐛 Устранение неполадок

### Контейнер не запускается
1. Проверьте логи: `docker-compose logs xuy`
2. Убедитесь, что порт 5000 свободен
3. Проверьте наличие всех файлов

### Ошибки зависимостей
1. Пересоберите образ: `docker-compose build --no-cache`
2. Проверьте файл requirements.txt

### Проблемы с базой данных
1. Проверьте права доступа к папке instance
2. Убедитесь, что файл базы данных существует

## 📊 Мониторинг

### Статус контейнера
```bash
docker ps
```

### Использование ресурсов
```bash
docker stats xuy
```

### Логи в реальном времени
```bash
docker-compose logs -f xuy
```

## 🔄 Обновление

Для обновления приложения:

1. Остановите контейнер: `docker-compose down`
2. Обновите код
3. Пересоберите и запустите: `docker-compose up --build -d`

## 📝 Примечания

- Контейнер автоматически перезапускается при сбоях
- Все данные сохраняются в томах
- Логи доступны в папке `./logs` 