# 🔧 Решение проблем с psutil

## 🚨 Проблема

Если вы видите ошибки pyright:
```
Import "psutil" could not be resolved from source
```

Это означает, что пакет `psutil` не установлен в вашей системе.

## 🛠️ Решения

### 1. Автоматическое исправление (рекомендуется)

```bash
python fix_psutil.py
```

Этот скрипт предложит несколько вариантов решения и автоматически применит их.

### 2. Установка psutil

```bash
python install_psutil.py
```

Или вручную:
```bash
pip install psutil==5.9.6
```

### 3. Использование версий без psutil

Если установка psutil не работает, используйте альтернативные версии:

```bash
# Запуск системы без psutil
python start_system_no_psutil.py

# Мониторинг без psutil
python monitoring_no_psutil.py
```

### 4. Комплексная диагностика

```bash
python system_diagnostic.py
```

Этот скрипт проверит всю систему и предложит решения.

## 📋 Что делает psutil

`psutil` используется для:
- Мониторинга CPU и памяти
- Отслеживания производительности системы
- Создания отчетов о состоянии

## 🔄 Альтернативные версии

### monitoring_no_psutil.py
- Базовый мониторинг без системных метрик
- Отслеживание времени работы
- Размер файлов и количество записей
- Генерация отчетов

### start_system_no_psutil.py
- Запуск системы без psutil
- Проверка зависимостей
- Создание директорий
- Запуск компонентов

## 🧪 Проверка решения

После применения любого решения проверьте:

```bash
python check_system.py
```

Или запустите тест:

```bash
python -c "import psutil; print('psutil работает!')"
```

## 📁 Файлы для решения

- `fix_psutil.py` - автоматическое исправление
- `install_psutil.py` - установка psutil
- `install_dependencies.py` - установка всех зависимостей
- `system_diagnostic.py` - комплексная диагностика
- `monitoring_no_psutil.py` - мониторинг без psutil
- `start_system_no_psutil.py` - запуск без psutil

## 🎯 Рекомендуемый порядок действий

1. **Попробуйте автоматическое исправление:**
   ```bash
   python fix_psutil.py
   ```

2. **Если не помогло, установите psutil:**
   ```bash
   python install_psutil.py
   ```

3. **Если установка не работает, используйте версии без psutil:**
   ```bash
   python start_system_no_psutil.py
   ```

4. **Проверьте результат:**
   ```bash
   python check_system.py
   ```

## 🚀 Запуск системы

После решения проблемы запустите:

```bash
# Основное приложение
python app.py

# Или полную систему
python start_system.py
```

## 📞 Поддержка

Если проблемы остаются:
1. Проверьте логи в `logs/system.log`
2. Запустите диагностику: `python system_diagnostic.py`
3. Обратитесь к `TROUBLESHOOTING.md`

---

🎉 **Удачи с автоассистентом!** 🚗 