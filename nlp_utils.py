"""
Модуль для обработки естественного языка (NLP)
Улучшенная версия с расширенными словарями и более точным анализом
"""

import re
from difflib import get_close_matches
from brand_synonyms import normalize_brand_extended, get_all_brand_variants, CHINESE_MODEL_SYNONYMS
import unicodedata
from typing import Optional

# Расширенные словари для лучшего распознавания
SEARCH_KEYWORDS = [
    'найти', 'поиск', 'искать', 'есть ли', 'покажи', 'найди', 'ищу', 'хочу найти',
    'покажите', 'найдите', 'ищется', 'искал', 'искала', 'искали'
]

PRICE_KEYWORDS = [
    'цена', 'стоимость', 'сколько стоит', 'почём', 'ценник', 'дорого', 'дешево',
    'стоит', 'стоила', 'стоили', 'цену', 'стоимости', 'цене', 'ценой'
]

COMPARISON_KEYWORDS = [
    'сравни', 'сравнение', 'против', 'или', 'vs', 'versus', 'лучше', 'хуже',
    'сравнить', 'сравниваю', 'сравниваешь', 'сравнивает', 'сравнивают'
]

RECOMMENDATION_KEYWORDS = [
    'рекоменд', 'посоветуй', 'что выбрать', 'какой лучше', 'подскажи',
    'совет', 'рекомендация', 'посоветуйте', 'подскажите', 'что посоветуете'
]

VIN_KEYWORDS = [
    'vin', 'вин', 'номер', 'проверить', 'история', 'vin-код', 'вин-код',
    'vin номер', 'вин номер', 'vin код', 'вин код'
]

OVERVIEW_KEYWORDS = [
    'обзор', 'информация', 'расскажи', 'что это', 'описание', 'характеристики',
    'расскажите', 'информацию', 'обзор', 'описание'
]

CONTACT_KEYWORDS = [
    'контакт', 'телефон', 'адрес', 'связаться', 'позвонить', 'связаться',
    'контакты', 'телефонный', 'адрес', 'где находитесь'
]

TEST_DRIVE_KEYWORDS = [
    'тест-драйв', 'прокат', 'попробовать', 'водить', 'тест драйв',
    'прокатиться', 'попробовать машину', 'водить машину'
]

DEALER_CENTER_KEYWORDS = [
    'где купить', 'в каком дц', 'дилерский центр', 'где находится', 'где приобрести',
    'где продается', 'где продаётся', 'где продают', 'где взять', 'где можно купить',
    'какой дилер', 'какой автосалон', 'в каком автосалоне', 'где продают', 'где найти дц', 'где найти дилера'
]

# Расширенный словарь типов топлива
FUEL_TYPES = {
    'бензин': ['бензин', 'бензиновый', 'бензиновая', 'бензиновое', 'бензиновые', 'бензином'],
    'дизель': ['дизель', 'дизельный', 'дизельная', 'дизельное', 'дизельные', 'дизелем'],
    'гибрид': ['гибрид', 'гибридный', 'гибридная', 'гибридное', 'гибридные', 'гибридом'],
    'электро': ['электро', 'электрический', 'электрическая', 'электрическое', 'электрические', 'электро'],
    'газ': ['газ', 'газовый', 'газовая', 'газовое', 'газовые', 'газом', 'газобаллонное']
}

# Расширенный словарь типов кузова
BODY_TYPES = {
    'седан': ['седан', 'седан', 'седаны', 'седана', 'седаном'],
    'хэтчбек': ['хэтчбек', 'хетчбек', 'хэтч', 'хетч', 'хэтчбеки', 'хетчбеки'],
    'универсал': ['универсал', 'комби', 'универсалы', 'комби', 'универсала'],
    'внедорожник': ['внедорожник', 'джип', 'suv', 'кроссовер', 'внедорожники', 'джипы'],
    'купе': ['купе', 'купе', 'купе', 'купе'],
    'кабриолет': ['кабриолет', 'кабриолет', 'кабриолеты', 'кабриолета'],
    'лифтбек': ['лифтбек', 'лифтбеки', 'лифтбека'],
    'пикап': ['пикап', 'пикапы', 'пикапа'],
    'микроавтобус': ['микроавтобус', 'микроавтобусы', 'микроавтобуса', 'минивэн', 'минивэны']
}

# Расширенный словарь состояний автомобиля
CAR_STATES = {
    'new': ['новый', 'новая', 'новое', 'новые', 'без пробега', 'салон', 'с нуля', 'первый владелец'],
    'used': ['б/у', 'бу', 'подержанный', 'подержанная', 'подержанное', 'подержанные', 'с пробегом', 'вторичка', 'вторичный']
}

# Фонетические синонимы для автопроизводителей (расширяем по необходимости)
PHONETIC_SYNONYMS = {
    'хендай': 'Hyundai',
    'бмв': 'BMW',
    'мерседес': 'Mercedes',
    'мерседес-бенц': 'Mercedes-Benz',
    'ауди': 'Audi',
    'тойота': 'Toyota',
    'ниссан': 'Nissan',
    'киа': 'Kia',
    'фольксваген': 'Volkswagen',
    'шкода': 'Skoda',
    'опель': 'Opel',
    'пежо': 'Peugeot',
    'рено': 'Renault',
    'мазда': 'Mazda',
    'хонда': 'Honda',
    'ситроен': 'Citroen',
    'джили': 'Geely',
    'чери': 'Chery',
    'омода': 'Omoda',
    'джейку': 'Jaecoo',
    'эксид': 'Exeed',
    'гели': 'Geely',
    'генесис': 'Genesis',
    'лада': 'Lada',
    'вольво': 'Volvo',
    'ссангйонг': 'SsangYong',
    'лексус': 'Lexus',
    'инфинити': 'Infiniti',
    'мицубиси': 'Mitsubishi',
    'сузуки': 'Suzuki',
    'субару': 'Subaru',
    'тесла': 'Tesla',
    'форд': 'Ford',
    'шевроле': 'Chevrolet',
    'додж': 'Dodge',
    'крайслер': 'Chrysler',
    'кадиллак': 'Cadillac',
    'джип': 'Jeep',
    'хаммер': 'Hummer',
    'бентли': 'Bentley',
    'ягуар': 'Jaguar',
    'ленд ровер': 'Land Rover',
    'роллс ройс': 'Rolls-Royce',
    'феррари': 'Ferrari',
    'ламборгини': 'Lamborghini',
    'макларен': 'McLaren',
    'альфа ромео': 'Alfa Romeo',
    'фиат': 'Fiat',
    'акура': 'Acura',
    'майбах': 'Maybach',
    'мини': 'MINI',
    'смарт': 'Smart',
    'сааб': 'Saab',
    'полестар': 'Polestar',
    'лотус': 'Lotus',
    'астон мартин': 'Aston Martin',
    'коенигсегг': 'Koenigsegg',
    'бугатти': 'Bugatti',
    'пагани': 'Pagani',
}

# --- Стоп-слова, которые не могут быть моделью ---
STOP_WORDS = set([
    'до', 'от', 'за', 'по', 'или', 'и', 'с', 'на', 'в', 'под', 'для', 'к', 'у', 'о', 'об', 'про', 'без', 'при', 'над', 'из', 'под', 'через', 'после', 'перед', 'между',
    'внедорожник', 'внедорожники', 'кроссовер', 'кроссоверы', 'седан', 'седаны', 'универсал', 'универсалы', 'купе', 'кабриолет', 'пикап', 'минивэн', 'лифтбэк', 'хэтчбек', 'хэтчбеки',
    'автомобиль', 'автомобили', 'машина', 'машины', 'руб', 'млн', 'тыс', 'k', 'т'
])

def detect_intent(text):
    """
    Определяет намерение пользователя на основе текста
    Улучшенная версия с более точным распознаванием
    """
    text_lower = text.lower()
    
    # Проверяем каждый тип интента с расширенными ключевыми словами
    if any(keyword in text_lower for keyword in DEALER_CENTER_KEYWORDS):
        return 'dealer_center'
    if any(keyword in text_lower for keyword in SEARCH_KEYWORDS):
        return 'search'
    elif any(keyword in text_lower for keyword in PRICE_KEYWORDS):
        return 'price_query'
    elif any(keyword in text_lower for keyword in COMPARISON_KEYWORDS):
        return 'comparison'
    elif any(keyword in text_lower for keyword in RECOMMENDATION_KEYWORDS):
        return 'recommendation'
    elif any(keyword in text_lower for keyword in VIN_KEYWORDS):
        return 'vin_check'
    elif any(keyword in text_lower for keyword in OVERVIEW_KEYWORDS):
        return 'brand_overview'
    elif any(keyword in text_lower for keyword in CONTACT_KEYWORDS):
        return 'contact'
    elif any(keyword in text_lower for keyword in TEST_DRIVE_KEYWORDS):
        return 'test_drive'

    return 'general'

def extract_entities(text):
    """
    Извлекает сущности из текста
    Улучшенная версия с более точным распознаванием
    """
    entities = {}
    text_lower = text.lower()
    
    # Извлекаем бренд
    brand = extract_brand(text_lower)
    if brand:
        entities['brand'] = brand
    
    # Извлекаем модель
    model = extract_model(text_lower, brand)
    if model:
        entities['model'] = model
    
    # Извлекаем год
    year = extract_year(text_lower)
    if year:
        entities['year'] = year
    
    # Извлекаем ценовой диапазон
    price_range = extract_price_range(text_lower)
    if price_range:
        entities['price_range'] = price_range
    
    # Определяем тип автомобиля
    for state, keywords in CAR_STATES.items():
        if any(keyword in text_lower for keyword in keywords):
            entities['state'] = state
            break
    
    # Определяем тип топлива
    for fuel_type, keywords in FUEL_TYPES.items():
        if any(keyword in text_lower for keyword in keywords):
            entities['fuel_type'] = fuel_type
            break
    
    # Определяем тип кузова
    for body_type, keywords in BODY_TYPES.items():
        if any(keyword in text_lower for keyword in keywords):
            entities['body_type'] = body_type
            break
    
    return entities

def extract_brand(text):
    """
    Извлекает бренд автомобиля из текста
    Улучшенная версия с поддержкой падежных вариаций и составных названий
    """
    # Используем улучшенную систему распознавания брендов
    from brand_synonyms import normalize_brand_extended, BRAND_SYNONYMS
    
    # Специальная обработка для составных брендов
    compound_brands = {
        'tesla model': 'Tesla',
        'mercedes benz': 'Mercedes-Benz',
        'mercedes-benz': 'Mercedes-Benz',
        'land rover': 'Land Rover',
        'rolls royce': 'Rolls-Royce',
        'rolls-royce': 'Rolls-Royce',
        'aston martin': 'Aston Martin',
        'alfa romeo': 'Alfa Romeo',
        'lynk & co': 'Lynk & Co',
        'li auto': 'Li Auto'
    }
    
    # Проверяем составные бренды
    for compound, canonical in compound_brands.items():
        if compound in text:
            return canonical
    
    # Используем улучшенную функцию нормализации с падежными вариациями
    normalized_brand = normalize_brand_extended(text)
    if normalized_brand and normalized_brand != text.title():
        return normalized_brand
    
    # Проверяем словарь синонимов брендов (включая падежные вариации)
    words = text.lower().split()
    for word in words:
        if word in BRAND_SYNONYMS:
            return BRAND_SYNONYMS[word]
    
    # Fallback: получаем все бренды из базы данных
    all_brands = list(get_all_brand_variants())
    
    # Ищем точные совпадения среди всех брендов
    for brand in all_brands:
        if brand.lower() in text:
            return normalize_brand_extended(brand)
    
    # Ищем составные названия брендов (2-3 слова)
    words = text.split()

    # Проверяем биграммы (2 слова)
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        normalized = normalize_brand_extended(bigram)
        if normalized and normalized != bigram.title():
            return normalized
    
    # Проверяем триграммы (3 слова)
    for i in range(len(words) - 2):
        trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
        normalized = normalize_brand_extended(trigram)
        if normalized and normalized != trigram.title():
            return normalized
    
    # Ищем отдельные слова
    for word in words:
        if len(word) > 2:  # Игнорируем короткие слова
            normalized = normalize_brand_extended(word)
            if normalized and normalized != word.title():
                return normalized

    return None

def extract_model(text, brand=None):
    """
    Извлекает модель автомобиля из текста
    Улучшенная версия с поддержкой китайских моделей
    """
    # Сначала проверяем словарь синонимов моделей
    from brand_synonyms import MODEL_SYNONYMS
    for synonym, canonical in MODEL_SYNONYMS.items():
        if synonym in text:
            return canonical
    # Специальная обработка для популярных моделей
    popular_models = {
        'tesla model 3': 'Model 3',
        'tesla model s': 'Model S',
        'tesla model x': 'Model X',
        'tesla model y': 'Model Y',
        'bmw x5': 'X5',
        'bmw x3': 'X3',
        'bmw x1': 'X1',
        'bmw x7': 'X7',
        'mercedes c': 'C-Class',
        'mercedes e': 'E-Class',
        'mercedes s': 'S-Class',
        'audi a4': 'A4',
        'audi a6': 'A6',
        'audi q5': 'Q5',
        'audi q7': 'Q7',
        'kia sportage': 'Sportage',
        'kia sorento': 'Sorento',
        'hyundai creta': 'Creta',
        'hyundai tucson': 'Tucson',
        'toyota camry': 'Camry',
        'toyota corolla': 'Corolla',
        'honda accord': 'Accord',
        'honda civic': 'Civic'
    }
    # Проверяем популярные модели
    for model_pattern, canonical in popular_models.items():
        if model_pattern in text:
            return canonical
    # --- ДОРАБОТКА: если после бренда есть слово, считаем его моделью ---
    if brand:
        brand_pattern = re.escape(brand.lower())
        after_brand = re.split(brand_pattern, text, 1)
        if len(after_brand) > 1:
            model_text = after_brand[1].strip()
            # Берем первое слово после бренда
            model_match = re.match(r'^([a-zа-я0-9\-]+)', model_text)
            if model_match:
                candidate = model_match.group(1).title()
                # Проверяем, что это не бренд и не стоп-слово
                if not normalize_brand_extended(candidate.lower()) and candidate.lower() not in STOP_WORDS:
                    return candidate
    # Ищем модели в тексте по паттернам
    model_patterns = [
        r'модель\s+([a-zа-я0-9\-]+)',
        r'([a-zа-я0-9\-]+)\s+модель',
        r'([a-zа-я0-9\-]{3,})\s+(?:автомобиль|машина)',
        r'([a-zа-я0-9\-]{2,})\s+(?:седан|хэтчбек|универсал|внедорожник|купе)',
        r'([a-zа-я0-9\-]{2,})\s+(?:202\d|201\d|200\d)'
    ]
    for pattern in model_patterns:
        match = re.search(pattern, text)
        if match:
            model = match.group(1).title()
            # Проверяем, что это не бренд
            if not normalize_brand_extended(model.lower()):
                return model
    return None

def extract_year(text):
    """
    Извлекает год выпуска из текста
    Улучшенная версия с поддержкой относительных дат
    """
    # Ищем год в формате YYYY
    year_match = re.search(r'(20\d{2}|19\d{2})', text)
    if year_match:
        year = int(year_match.group(1))
        if 1900 <= year <= 2030:
            return year
    
    # Ищем относительные годы
    current_year = 2025
    relative_years = {
        'прошлый год': current_year - 1,
        'позапрошлый год': current_year - 2,
        'этот год': current_year,
        'новый': current_year,
        'старый': current_year - 5,
        'пятилетний': current_year - 5,
        'десятилетний': current_year - 10
    }
    
    for keyword, year in relative_years.items():
        if keyword in text:
            return year
    
    return None

def transliterate(text):
    """
    Примитивная транслитерация кириллицы в латиницу и наоборот для сопоставления брендов
    """
    # Создаем правильную таблицу транслитерации
    cyrillic = 'абвгдеёжзийклмнопрстуфхцчшщьыъэюя'
    latin = 'abvgdeejzijklmnoprstufkhtcshshch_y_eua'
    
    # Проверяем, что длины равны
    if len(cyrillic) != len(latin):
        # Если длины не равны, обрезаем до минимальной
        min_len = min(len(cyrillic), len(latin))
        cyrillic = cyrillic[:min_len]
        latin = latin[:min_len]
    
    table = str.maketrans(cyrillic, latin)
    table_rev = str.maketrans(latin, cyrillic)
    
    # Транслитерируем в обе стороны и возвращаем оба варианта
    return [text.translate(table), text.translate(table_rev)]

def find_similar_words(word, word_list, threshold=0.6):
    """
    Находит похожие слова в списке, учитывая фонетические синонимы и транслитерацию
    """
    import difflib
    word_lower = word.lower()
    # 1. Поиск по словарю фонетических синонимов
    if word_lower in PHONETIC_SYNONYMS:
        canonical = PHONETIC_SYNONYMS[word_lower]
        for w in word_list:
            if w.lower() == canonical.lower():
                return [w]
    # 2. Поиск по get_close_matches
    word_variants = [word_lower] + transliterate(word_lower)
    word_list_lower = [w.lower() for w in word_list]
    word_list_variants = word_list_lower[:]
    for w in word_list_lower:
        word_list_variants += transliterate(w)
    result = set()
    for wv in word_variants:
        matches = difflib.get_close_matches(wv, word_list_variants, n=3, cutoff=threshold)
        for m in matches:
            for idx, orig in enumerate(word_list_lower):
                if m == orig or m in transliterate(orig):
                    result.add(word_list[idx])
    return list(result)

def extract_price_range(text):
    """
    Извлекает ценовой диапазон из текста
    Улучшенная версия с поддержкой различных форматов
    """
    patterns = [
        (r"от\s*([\d.,]+)\s*тыс\s*до\s*([\d.,]+)\s*млн", lambda x, y: (float(x.replace(',', '.'))*1000, float(y.replace(',', '.'))*1000000)),
        (r"от\s*([\d.,]+)\s*тыс\s*до\s*([\d.,]+)\s*тыс", lambda x, y: (float(x.replace(',', '.'))*1000, float(y.replace(',', '.'))*1000)),
        (r"от\s*([\d.,]+)\s*млн\s*до\s*([\d.,]+)\s*млн", lambda x, y: (float(x.replace(',', '.'))*1000000, float(y.replace(',', '.'))*1000000)),
        (r"от\s*([\d.,]+)\s*до\s*([\d.,]+)", lambda x, y: (float(x.replace(',', '.')), float(y.replace(',', '.')))),
        (r"до\s*([\d.,]+)\s*млн", lambda x: (0, float(x.replace(',', '.')) * 1000000)),
        (r"до\s*([\d.,]+)\s*тыс", lambda x: (0, float(x.replace(',', '.')) * 1000)),
        (r"от\s*([\d.,]+)\s*млн", lambda x: (float(x.replace(',', '.')) * 1000000, float('inf'))),
        (r"от\s*([\d.,]+)\s*тыс", lambda x: (float(x.replace(',', '.')) * 1000, float('inf'))),
        (r"([\d.,]+)\s*-\s*([\d.,]+)\s*млн", lambda x, y: (float(x.replace(',', '.'))*1000000, float(y.replace(',', '.'))*1000000)),
        (r"([\d.,]+)\s*-\s*([\d.,]+)\s*тыс", lambda x, y: (float(x.replace(',', '.'))*1000, float(y.replace(',', '.'))*1000)),
        (r"([\d.,]+)\s*-\s*([\d.,]+)", lambda x, y: (float(x.replace(',', '.')), float(y.replace(',', '.')))),
        (r"стоимость\s*до\s*([\d.,]+)", lambda x: (0, float(x.replace(',', '.')))),
        (r"цена\s*до\s*([\d.,]+)", lambda x: (0, float(x.replace(',', '.'))))
    ]
    for pattern, converter in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            try:
                return converter(*groups)
            except:
                continue
    return None

def get_all_brand_variants():
    """
    Получает все варианты брендов
    """
    try:
        from brand_synonyms import get_all_brand_variants as get_brands
        return get_brands()
    except:
        # Fallback на базовые бренды
        return ["Kia", "Hyundai", "Toyota", "BMW", "Audi", "Lada", "Chery", "Omoda", "Jaecoo", "Mercedes-Benz", "Tesla"]

def get_first_deep(val):
    if isinstance(val, (list, tuple)):
        return get_first_deep(val[0]) if val else None
    return val

def normalize_brand_extended(brand_input) -> Optional[str]:
    brand_input = get_first_deep(brand_input)
    if not brand_input:
        return None
    brand_input_lower = brand_input.lower().strip()
    # ... остальной код ...

def normalize_text(text):
    text = get_first_deep(text)
    if not text:
        return ''
    words = str(text).split()
    normalized = []
    for word in words:
        normalized_word = normalize_brand_extended(word.lower())
        if normalized_word and normalized_word != word.title():
            normalized.append(normalized_word)
        else:
            normalized.append(word)
    return ' '.join(normalized)

def analyze_query(user_message):
    """
    Анализирует пользовательский запрос и извлекает интенты и сущности
    Возвращает: (intent, entities, need_clarification, clarification_questions)
    """
    message_lower = user_message.lower()
    
    # Определяем интент
    intent = detect_intent(user_message)
    
    # Извлекаем сущности
    entities = extract_entities(message_lower)
    
    # Определяем, нужны ли уточнения
    need_clarification = False
    clarification_questions = []
    
    # Если запрос о цене конкретной модели, уточнения не нужны
    if intent == 'price_query' and entities.get('brand') and entities.get('model'):
        need_clarification = False
    # Если запрос о цене без указания модели, но с брендом
    elif intent == 'price_query' and entities.get('brand') and not entities.get('model'):
        need_clarification = True
        clarification_questions.append("Какую модель вас интересует?")
    # Если запрос о цене без бренда
    elif intent == 'price_query' and not entities.get('brand'):
        need_clarification = True
        clarification_questions.append("Какой бренд автомобиля вас интересует?")
        clarification_questions.append("Какой ценовой диапазон вас интересует?")
    
    # Если поиск конкретной модели, уточнения не нужны
    elif intent == 'search' and entities.get('brand') and entities.get('model'):
        need_clarification = False
    # Если поиск по бренду без модели
    elif intent == 'search' and entities.get('brand') and not entities.get('model'):
        need_clarification = False  # Поиск по бренду допустим
    # Если поиск без бренда
    elif intent == 'search' and not entities.get('brand'):
        need_clarification = True
        clarification_questions.append("Какой бренд автомобиля вас интересует?")
    
    # Если рекомендация без указания бренда
    elif intent == 'recommendation' and not entities.get('brand'):
        need_clarification = True
        clarification_questions.append("Какой бренд автомобиля вас интересует?")
        clarification_questions.append("Вас интересуют новые или подержанные автомобили?")
    
    # Если общий запрос о покупке без бренда
    elif any(word in message_lower for word in ['купить', 'выбрать', 'найти', 'ищу']) and not entities.get('brand'):
        need_clarification = True
        clarification_questions.append("Какой бренд автомобиля вас интересует?")
        clarification_questions.append("Вас интересуют новые или подержанные автомобили?")
    
    return intent, entities, need_clarification, clarification_questions

def extract_car_features(text):
    """
    Извлекает дополнительные характеристики автомобиля
    """
    features = {}
    text_lower = text.lower()
    
    # Цвет
    colors = ['белый', 'черный', 'красный', 'синий', 'зеленый', 'серый', 'серебристый', 'золотой']
    for color in colors:
        if color in text_lower:
            features['color'] = color
            break
    
    # Пробег
    mileage_match = re.search(r'(\d+)\s*(?:тыс|км|километров)', text_lower)
    if mileage_match:
        features['mileage'] = int(mileage_match.group(1)) * 1000
    
    # Мощность
    power_match = re.search(r'(\d+)\s*(?:л\.с|лс|лошадиных)', text_lower)
    if power_match:
        features['power'] = int(power_match.group(1))
    
    # Объем двигателя — ищем только если нет "лс" рядом
    engine_patterns = [
        r'(\d+\.?\d*)\s*(?:л|литра)(?!\s*с)',
        r'объем\s*(?:двигателя|двигатель)\s*(\d+\.?\d*)\s*(?:л|литра)',
        r'(\d+\.?\d*)\s*л\.(?!с)'
    ]
    for pattern in engine_patterns:
        engine_match = re.search(pattern, text_lower)
        if engine_match:
            try:
                features['engine_volume'] = float(engine_match.group(1))
                break
            except ValueError:
                continue
    
    return features 