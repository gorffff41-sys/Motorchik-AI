# 🔧 Устранение проблем автоассистента

## 🚨 Частые проблемы и их решения

### 0. Ошибки типизации psutil (pyright)

**Проблема:**
```
Import "psutil" could not be resolved from source
```

**Решение:**
1. Установите psutil:
   ```bash
   python install_psutil.py
   ```

2. Или вручную:
   ```bash
   pip install psutil==5.9.6
   ```

3. Если не работает pip, попробуйте:
   ```bash
   python -m pip install --user psutil==5.9.6
   ```

4. Проверьте установку:
   ```bash
   python -c "import psutil; print(psutil.__version__)"
   ```

**Альтернативное решение:**
Если psutil не нужен для вашей работы, можно временно закомментировать импорты в:
- `monitoring.py` (строка 3)
- `start_system.py` (строка 47)

### 1. Порт уже занят (ошибка 10048)

**Проблема:**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8001)
```

**Решение:**
1. Найдите процесс, занимающий порт:
   ```bash
   netstat -ano | findstr :8001
   ```

2. Завершите процесс:
   ```bash
   taskkill /PID <номер_процесса> /F
   ```

3. Или измените порт в `app.py`:
   ```python
   uvicorn.run(app, host="0.0.0.0", port=8002)
   ```

### 2. Ошибки типизации (pyright)

**Проблема:**
```
Cannot access attribute "cursor" for class "_GeneratorContextManager"
```

**Решение:**
- Используйте правильный контекстный менеджер:
  ```python
  with get_db() as conn:
      cursor = conn.cursor()
      # ... код ...
  ```

### 3. База данных не найдена

**Проблема:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'instance/cars.db'
```

**Решение:**
1. Создайте директорию:
   ```bash
   mkdir instance
   ```

2. Скопируйте базу данных из backup или создайте новую:
   ```python
   from database import init_car_db
   init_car_db()
   ```

### 4. Отсутствуют зависимости

**Проблема:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Решение:**
```bash
pip install -r requirements.txt
```

### 5. Ошибки импорта модулей

**Проблема:**
```
ImportError: cannot import name 'DialogManager'
```

**Решение:**
1. Проверьте структуру файлов
2. Убедитесь, что все модули существуют
3. Запустите проверку системы:
   ```bash
   python check_system.py
   ```

### 6. Проблемы с правами доступа

**Проблема:**
```
PermissionError: [Errno 13] Permission denied
```

**Решение:**
1. Запустите от имени администратора
2. Проверьте права на директории `logs/`, `reports/`, `instance/`
3. Создайте директории вручную:
   ```bash
   mkdir logs reports instance
   ```

### 7. Ошибки SQLite

**Проблема:**
```
sqlite3.OperationalError: no such table
```

**Решение:**
1. Инициализируйте базу данных:
   ```python
   from database import init_car_db, create_dealer_centers_table_if_not_exists
   init_car_db()
   create_dealer_centers_table_if_not_exists()
   ```

### 8. Проблемы с мониторингом

**Проблема:**
```
psutil.AccessDenied: [WinError 5] Access is denied
```

**Решение:**
1. Запустите от имени администратора
2. Или отключите мониторинг системы в `monitoring.py`

### 9. Ошибки сети

**Проблема:**
```
requests.exceptions.ConnectionError
```

**Решение:**
1. Проверьте подключение к интернету
2. Проверьте настройки прокси
3. Временно отключите геолокацию в `database.py`

### 10. Проблемы с веб-интерфейсом

**Проблема:**
- Страница не загружается
- API не отвечает

**Решение:**
1. Проверьте, что сервер запущен:
   ```bash
   python app.py
   ```

2. Проверьте доступность:
   ```bash
   curl http://localhost:8001/health
   ```

3. Проверьте логи в `logs/system.log`

## 🔍 Диагностика

### Скрипт проверки системы
```bash
python check_system.py
```

Этот скрипт проверит:
- ✅ Зависимости
- ✅ Файлы
- ✅ Директории
- ✅ База данных
- ✅ Импорт модулей

### Ручная диагностика

1. **Проверка процессов:**
   ```bash
   tasklist | findstr python
   ```

2. **Проверка портов:**
   ```bash
   netstat -an | findstr :8001
   ```

3. **Проверка файлов:**
   ```bash
   dir *.py
   dir instance\
   ```

4. **Проверка логов:**
   ```bash
   type logs\system.log
   ```

## 🛠️ Восстановление системы

### Полная переустановка
```bash
# 1. Остановите все процессы
taskkill /F /IM python.exe

# 2. Удалите кэш
rmdir /s __pycache__
rmdir /s .pytest_cache

# 3. Переустановите зависимости
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 4. Проверьте систему
python check_system.py

# 5. Запустите
python app.py
```

### Восстановление базы данных
```python
from database import init_car_db, ensure_dealer_centers_filled, add_lat_lon_to_dealer_centers

# Инициализация
init_car_db()

# Заполнение дилерских центров
ensure_dealer_centers_filled()

# Добавление координат
add_lat_lon_to_dealer_centers()
```

## 📞 Получение помощи

### Логи для анализа
- `logs/system.log` - основные логи
- `reports/` - отчеты мониторинга
- Консольный вывод при запуске

### Информация о системе
```bash
python -c "import sys; print(sys.version)"
python -c "import platform; print(platform.platform())"
```

### Проверка окружения
```bash
python check_system.py > system_check.txt
```

## 🎯 Профилактика

### Регулярные проверки
1. Запускайте `python check_system.py` перед каждым запуском
2. Проверяйте логи в `logs/system.log`
3. Мониторьте использование ресурсов

### Резервное копирование
1. Регулярно копируйте `instance/cars.db`
2. Сохраняйте конфигурационные файлы
3. Документируйте изменения

### Обновления
1. Регулярно обновляйте зависимости
2. Проверяйте совместимость версий
3. Тестируйте изменения перед внедрением

---

🔧 **Следуйте этим инструкциям для решения большинства проблем!** 