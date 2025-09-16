# 🐳 Docker контейнер для MOTORCHIK APP

## 📋 Описание

Этот репозиторий содержит Docker конфигурацию для запуска приложения MOTORCHIK APP в контейнере.

## 🚀 Быстрый старт

### Предварительные требования

- Docker Desktop установлен и запущен
- Docker Compose установлен
- Порты 5000 свободен

### Запуск приложения

#### Вариант 1: Использование PowerShell скрипта (Windows)
```powershell
.\build_and_run.ps1
```

#### Вариант 2: Использование Bash скрипта (Linux/Mac)
```bash
chmod +x build_and_run.sh
./build_and_run.sh
```

#### Вариант 3: Ручной запуск
```bash
# Сборка образа
docker-compose build

# Запуск контейнера
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## 🌐 Доступ к приложению

После успешного запуска приложение будет доступно по адресу:
- **Локально**: http://localhost:5000
- **В сети**: http://[IP-адрес]:5000

## 📊 Управление контейнером

### Просмотр логов
```bash
# Все логи
docker-compose logs motorchik_app

# Логи в реальном времени
docker-compose logs -f motorchik_app

# Последние 100 строк
docker-compose logs --tail=100 motorchik_app
```

### Остановка контейнера
```bash
docker-compose stop motorchik_app
```

### Перезапуск контейнера
```bash
docker-compose restart motorchik_app
```

### Полная остановка и удаление
```bash
docker-compose down
```

### Пересборка образа
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Структура монтирования

Контейнер монтирует следующие директории:

- `./instance` → `/app/instance` (база данных)
- `./logs` → `/app/logs` (логи приложения)
- `./reports` → `/app/reports` (отчеты)
- `./debug_html` → `/app/debug_html` (отладочные файлы)
- `./ml_models` → `/app/ml_models` (ML модели)

## 🔧 Конфигурация

### Переменные окружения

- `PYTHONPATH=/app` - путь к Python модулям
- `PYTHONUNBUFFERED=1` - отключение буферизации Python

### Порты

- **5000** - основной порт приложения

## 🐛 Отладка

### Проверка статуса контейнера
```bash
docker-compose ps
```

### Вход в контейнер
```bash
docker-compose exec motorchik_app bash
```

### Проверка логов
```bash
docker-compose logs motorchik_app
```

### Проверка использования ресурсов
```bash
docker stats motorchik_app
```

## 🧹 Очистка

### Удаление контейнера и образа
```bash
docker-compose down --rmi all
```

### Удаление всех неиспользуемых ресурсов
```bash
docker system prune -a
```

## 📝 Полезные команды

```bash
# Просмотр всех контейнеров
docker ps -a

# Просмотр всех образов
docker images

# Просмотр использования диска
docker system df

# Очистка неиспользуемых ресурсов
docker system prune
```

## 🔄 Обновление приложения

1. Остановите контейнер:
   ```bash
   docker-compose down
   ```

2. Обновите код приложения

3. Пересоберите и запустите:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs motorchik_app`
2. Убедитесь, что порт 5000 свободен
3. Проверьте, что Docker Desktop запущен
4. Попробуйте пересобрать образ: `docker-compose build --no-cache`

---

**МОТОРЧИК** - умный помощник по выбору автомобиля 🚗💙 