# 🔍 Подробный анализ обработки через LLAMA

## 📋 Общая архитектура обработки запросов

### 1. **Маршрутизация запросов**
Система использует `SmartQueryRouter` для классификации запросов:

```python
# smart_query_router.py
class SmartQueryRouter:
    def is_car_related(self, query: str) -> bool:
        # Проверяет ключевые слова автомобильной тематики
        car_keywords = ['машина', 'автомобиль', 'bmw', 'mercedes', 'найди', 'покажи', ...]
        return any(keyword in query.lower() for keyword in car_keywords)
```

**Результат маршрутизации:**
- **Автомобильные запросы** → `UniversalQueryProcessor`
- **Общие запросы** → `generate_general_response()` с промтом "Моторчик"

---

## 🚗 Обработка автомобильных запросов

### 2. **Локальная обработка (приоритет)**

```python
# modules/classifiers/query_processor.py
def process(self, query: str, entities: dict, user_id: str = 'default'):
    # 1. Извлечение сущностей через NER
    auto_entities = self.ner_intent.extract_entities(query)
    entities = {**auto_entities, **entities}
    
    # 2. Классификация интента
    intent = self.ner_intent.classify_intent(query)
    
    # 3. Локальный поиск через SearchModule
    local_result = self.search.process(query, entities, context)
    
    # 4. Если найдены результаты - возвращаем без LLAMA
    if local_result.get('cars') and len(local_result['cars']) > 0:
        local_result['message'] = 'Результат найден локально (без LLAMA).'
        return local_result
```

**Данные для локального поиска:**
- **Сущности из NER**: brand, model, color, price, year, city, body_type
- **Синонимы**: расширенные словари для брендов, цветов, городов
- **Фильтры**: SQL-запросы с LIKE, нормализацией

---

## 🤖 Обработка через LLAMA

### 3. **Когда используется LLAMA**

LLAMA вызывается только если:
1. Локальный поиск не дал результатов
2. Запрос требует сложной обработки
3. Нужна генерация текстового ответа

### 4. **Процесс обработки через LLAMA**

#### **Шаг 1: Построение промта для фильтров**

```python
filter_prompt = (
    "Пользователь задал вопрос: '" + query + "'. "
    "В базе данных автомобиля есть следующие поля: "
    "mark: марка автомобиля (например, BMW, Toyota); "
    "model: модель автомобиля (например, X5, Camry); "
    "manufacture_year: год выпуска; "
    "price: цена в рублях; "
    "city: город продажи; "
    "color: цвет кузова; "
    "body_type: тип кузова (седан, кроссовер и т.д.); "
    "gear_box_type: тип коробки передач (автомат, механика и т.д.); "
    "driving_gear_type: тип привода (передний, задний, полный); "
    "engine_vol: объём двигателя; "
    "power: мощность двигателя; "
    "fuel_type: тип топлива; "
    "dealer_center: дилерский центр; "
    "option_description: опции автомобиля (например, люк, панорамная крыша, кабриолет). "
    "Используй только эти поля. Если речь о люке, панорамной крыше или кабриолете — используй поле option_description со значением ['люк', 'панорамная крыша', 'открывающаяся крыша']. Не используй поля, которых нет в списке. "
    "Сформируй фильтры для поиска в базе данных автомобилей. Верни только JSON, например: "
    '{"body_type": "кроссовер", "option_description": ["люк", "панорамная крыша"]}. '
    "Если фильтры не извлечены — верни пустой JSON {}."
)
```

#### **Шаг 2: Вызов LLAMA для генерации фильтров**

```python
# llama_service.py
def generate_with_llama(prompt: str, context: Optional[Dict] = None) -> str:
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "stream": False
    }
    
    # Retry логика с несколькими URL
    for url in LLAMA_URLS:  # ["http://127.0.0.1:11434/api/generate", "http://localhost:11434/api/generate"]
        for attempt in range(RETRY_ATTEMPTS):  # 3 попытки
            try:
                response = requests.post(url, json=payload, timeout=90)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Извините, не удалось обработать запрос...")
            except Exception as e:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))  # Экспоненциальная задержка
```

#### **Шаг 3: Парсинг ответа LLAMA**

```python
try:
    llama_filters = generate_with_llama(filter_prompt)
    filters = json.loads(llama_filters.strip().split('```')[-1] if '```' in llama_filters else llama_filters)
except Exception:
    filters = {}
```

#### **Шаг 4: Пост-обработка фильтров**

```python
# Коррекция нестандартных фильтров
if isinstance(filters, dict):
    for key in list(filters.keys()):
        if key.lower() in ["open_roof", "roof_type", "roof_open"] or (
            isinstance(filters[key], str) and "открыт" in filters[key].lower()
        ):
            filters["option_description"] = ['люк', 'панорамная крыша', 'открывающаяся крыша']
            del filters[key]

# Маппинг полей
mapping = {
    'brand': 'brand', 'mark': 'brand', 'model': 'model', 'body_type': 'body_type',
    'year_from': 'year_from', 'year_to': 'year_to', 'price_from': 'price_from', 'price_to': 'price_to',
    'fuel_type': 'fuel_type', 'transmission': 'transmission', 'gear_box_type': 'transmission',
    'drive_type': 'drive_type', 'city': 'city', 'option': 'option_description', 'options': 'option_description'
}
```

#### **Шаг 5: Поиск в базе данных**

```python
# Ограничиваем выборку для LLAMA
cars = search_all_cars(**search_kwargs, limit=50)

# Передаем LLAMA только 5 машин
cars_str = '\n'.join([
    f"{c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')} {c.get('body_type','')} {c.get('price','')} {c.get('city','')}"
    for c in cars[:5]
])
```

#### **Шаг 6: Генерация финального ответа**

```python
prompt = (
    "Пользователь задал вопрос: '" + query + "'. Вот список машин из базы данных по найденным фильтрам:\n"
    f"{cars_str}\n"
    "Ответь только на русском языке и только по этим данным. "
    "Если ни одна не подходит — скажи, что ничего не найдено. "
    "Сформируй понятный ответ для пользователя."
)

final_response = generate_with_llama(prompt)
```

---

## 💬 Обработка общих запросов

### 5. **Промт "Моторчик"**

```python
# llama_service.py
MOTORCHIK_PROMPT = """
Ты - Моторчик, умный автомобильный ассистент, созданный для помощи пользователям в вопросах, связанных с автомобилями, покупкой, продажей, обслуживанием и всем, что касается автомобильной тематики.

## Твоя роль и возможности:

### 🚗 Основная специализация:
- Помощь в выборе автомобилей
- Сравнение характеристик машин
- Консультации по покупке и продаже
- Информация об обслуживании и ремонте
- Рекомендации по безопасности на дороге
- Советы по экономии топлива
- Помощь с документами и страховкой

### 💡 Дополнительные возможности:
- Общие вопросы и поддержка
- Объяснение технических терминов
- Советы по уходу за автомобилем
- Информация о новых технологиях в автоиндустрии
- Помощь с планированием поездок

## Стиль общения:
- Дружелюбный и профессиональный
- Полезный и информативный
- Терпеливый в объяснениях
- Поощряющий вопросы и уточнения
- Всегда готов помочь

## Правила взаимодействия:
- Всегда представляйся как Моторчик
- Предлагай конкретную помощь
- Задавай уточняющие вопросы
- Предоставляй практические советы
- Ссылайся на свою специализацию
"""
```

### 6. **Fallback ответы**

```python
fallback_responses = {
    "привет": "Привет! Я Моторчик, твой автомобильный ассистент. Готов помочь с любыми вопросами по автомобилям - от выбора машины до советов по обслуживанию. Что тебя интересует?",
    "кто ты": "Я Моторчик - специализированный ИИ-ассистент для автомобильной тематики. Моя главная задача - помогать людям с вопросами, связанными с автомобилями...",
    "что ты умеешь": "Как автомобильный ассистент, я умею многое! Могу помочь найти идеальный автомобиль под твои потребности и бюджет...",
    "как дела": "Спасибо, у меня все отлично! Готов помогать с автомобильными вопросами..."
}
```

---

## 📊 Данные, используемые в LLAMA

### 7. **Структура данных базы**

**Основные поля:**
- `mark` - марка автомобиля (BMW, Toyota, Mercedes)
- `model` - модель автомобиля (X5, Camry, GLE)
- `manufacture_year` - год выпуска
- `price` - цена в рублях
- `city` - город продажи
- `color` - цвет кузова
- `body_type` - тип кузова (седан, кроссовер, SUV)
- `gear_box_type` - тип коробки передач
- `driving_gear_type` - тип привода
- `engine_vol` - объём двигателя
- `power` - мощность двигателя
- `fuel_type` - тип топлива
- `dealer_center` - дилерский центр
- `option_description` - опции автомобиля

### 8. **Синонимы и нормализация**

**Цвета:**
```python
COLOR_SYNONYMS = {
    'красный': ['красный', 'Красный', 'red', 'Red', 'огненно-красный', 'fire red', ...],
    'синий': ['синий', 'Синий', 'blue', 'Blue', 'голубой', 'Голубой', 'navy blue', ...],
    # ... другие цвета
}
```

**Города:**
```python
CITY_SYNONYMS = {
    "Ростов-на-Дону": ['ростов-на-дону', 'ростов', 'ростове', 'rostov', 'rostov-on-don', ...],
    "Воронеж": ['воронеж', 'воронеже', 'voronezh', 'voroneje', ...],
    "Краснодар": ['краснодар', 'краснодаре', 'krasnodar', 'krasnodare', ...]
}
```

**Бренды:**
```python
BRAND_SYNONYMS = {
    "BMW": ['bmw', 'бмв', 'BMW', 'БМВ'],
    "Mercedes": ['mercedes', 'мерседес', 'mercedes-benz', 'мерседес-бенц'],
    "Lada": ['lada', 'лада', 'ваз', 'ВАЗ']
}
```

---

## 🔧 Технические детали

### 9. **Конфигурация LLAMA**

```python
# llama_service.py
LLAMA_URLS = [
    "http://127.0.0.1:11434/api/generate",
    "http://localhost:11434/api/generate"
]
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 2  # seconds

payload = {
    "model": "llama3:8b",
    "prompt": prompt,
    "stream": False
}
```

### 10. **Обработка ошибок**

```python
def generate_with_llama(prompt: str, context: Optional[Dict] = None) -> str:
    last_error = None
    for url in LLAMA_URLS:
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = requests.post(url, json=payload, timeout=90)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Извините, не удалось обработать запрос...")
                else:
                    last_error = f"Ошибка Llama API: {response.status_code} ({url})"
            except Exception as e:
                last_error = f"{e} ({url})"
            time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
    
    # Fallback: возвращаем пользовательское сообщение
    return "Извините, не удалось обработать запрос. Попробуйте уточнить параметры..."
```

### 11. **Пост-обработка ответов**

```python
def postprocess_llama_response(text):
    """Заменяет коды опций вида `optXXXX` на их описания из базы."""
    import re
    from database import get_all_options
    options = get_all_options()
    code2desc = {o['code']: o['description'] for o in options if o['code']}
    def repl(match):
        code = match.group(1)
        desc = code2desc.get(code)
        return f"`{desc}`" if desc else f"`{code}`"
    return re.sub(r'`(opt\d{4,})`', repl, text)
```

---

## 📈 Статистика использования

### 12. **Приоритеты обработки**

1. **Локальная обработка** (приоритет)
   - NER извлечение сущностей
   - Поиск в базе данных
   - Возврат результатов без LLAMA

2. **LLAMA обработка** (fallback)
   - Генерация фильтров
   - Поиск с фильтрами
   - Генерация текстового ответа

3. **Общие запросы**
   - Промт "Моторчик"
   - Fallback ответы

### 13. **Ограничения и оптимизации**

- **Лимит машин для LLAMA**: 50 для поиска, 5 для промта
- **Таймаут**: 90 секунд на запрос
- **Retry логика**: 3 попытки с экспоненциальной задержкой
- **Fallback URLs**: 2 адреса для отказоустойчивости

---

## 🎯 Итоговая схема обработки

```
Пользовательский запрос
         ↓
SmartQueryRouter (классификация)
         ↓
┌─────────────────┬─────────────────┐
│ Автомобильный   │ Общий запрос    │
│ запрос          │                 │
└─────────────────┴─────────────────┘
         ↓                    ↓
UniversalQueryProcessor    generate_general_response()
         ↓                    ↓
1. NER извлечение           MOTORCHIK_PROMPT
2. Локальный поиск          ↓
3. Если нет результатов →   LLAMA (llama3:8b)
   LLAMA обработка          ↓
         ↓              Fallback ответы
Результат с машинами
```

Эта архитектура обеспечивает:
- **Быструю обработку** через локальные модули
- **Гибкость** через LLAMA для сложных запросов
- **Отказоустойчивость** через fallback механизмы
- **Качество ответов** через специализированные промты 