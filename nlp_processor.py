from brand_synonyms import (
    BRAND_SYNONYMS, CHINESE_MODEL_SYNONYMS, OTECHESTVENNYE,
    normalize_brand_extended, get_all_brand_variants, find_similar_brands
)
from difflib import get_close_matches
import re
import requests
import json
import sqlite3
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import Counter, defaultdict
import os
import logging
from datetime import datetime, timedelta
import random
from database import execute_query

# Graceful fallback для ML библиотек
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, classification_report
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("ML библиотеки недоступны. Используется rule-based подход.")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ключевые слова для новых/б/у авто
NEW_CAR_KEYWORDS = ['новый', 'новая', 'новое', 'новые', 'свежий', 'свежая', 'свежее', 'свежие']
USED_CAR_KEYWORDS = ['подержанный', 'подержанная', 'подержанное', 'подержанные', 'б/у', 'б у', 'бывший в употреблении', 'использованный', 'использованная', 'использованное', 'использованные']

# Ключевые слова для интентов
INTENT_KEYWORDS = {
    'search': ['найти', 'искать', 'показать', 'найди', 'ищу', 'хочу', 'нужен', 'нужна', 'нужно', 'нужны'],
    'loan': ['кредит', 'рассчитать', 'платеж', 'взнос', 'рассрочка', 'финансирование'],
    'test_drive': ['тест-драйв', 'тест драйв', 'прокатиться', 'попробовать', 'записаться'],
    'trade_in': ['trade-in', 'trade in', 'обмен', 'оценить', 'сдать', 'поменять'],
    'dealer_center': ['дилер', 'дилерский', 'центр', 'где купить', 'адрес', 'телефон'],
    'compare': ['сравнить', 'сравнение', 'что лучше', 'разница', 'отличия'],
    'recommendations': ['рекомендации', 'посоветуйте', 'что посоветуете', 'совет'],
    'discounts': ['скидка', 'акция', 'специальное предложение', 'выгодно', 'дешевле'],
    'warranty': ['гарантия', 'гарантийный', 'сервис', 'обслуживание'],
    'ownership_cost': ['стоимость владения', 'расходы', 'содержание', 'эксплуатация']
}

def get_first_deep(val):
    if isinstance(val, (list, tuple)):
        return get_first_deep(val[0]) if val else None
    return val

# --- Расширенная нормализация бренда ---
def normalize_brand_nlp(brand):
    """
    Нормализует название бренда, используя расширенную систему словарей.
    """
    if not brand:
        return None
    
    # Используем новую функцию нормализации
    return normalize_brand_extended(brand)

# --- Нормализация моделей китайских брендов ---
def normalize_chinese_model(model, brand=None):
    """
    Нормализует название модели, особенно для китайских брендов.
    """
    if not model:
        return None
    model_lower = model.strip().lower()
    
    # Сначала ищем в словаре синонимов моделей
    if model_lower in CHINESE_MODEL_SYNONYMS:
        return CHINESE_MODEL_SYNONYMS[model_lower]
        
    # Пытаемся найти близкое совпадение
    possible_matches = get_close_matches(model_lower, CHINESE_MODEL_SYNONYMS.keys(), n=1, cutoff=0.85)
    if possible_matches:
        return CHINESE_MODEL_SYNONYMS[possible_matches[0]]

    return model.title()

# --- Анализ запроса с LLM ---
def analyze_query(user_message):
    """
    Анализирует пользовательский запрос и извлекает интенты и сущности.
    Возвращает: (intent, entities, need_clarification, clarification_questions)
    """
    message_lower = user_message.lower()
    
    # Определяем интент
    intent = 'general'
    
    # Ключевые слова для определения интентов
    if any(word in message_lower for word in ['цена', 'стоимость', 'сколько стоит', 'почём', 'ценник']):
        intent = 'price_query'
    elif any(word in message_lower for word in ['сравни', 'сравнение', 'против', 'или', 'vs', 'versus']):
        intent = 'comparison'
    elif any(word in message_lower for word in ['рекоменд', 'посоветуй', 'что выбрать']):
        intent = 'recommendation'
    elif any(word in message_lower for word in ['vin', 'вин', 'номер']):
        intent = 'vin_check'
    elif any(word in message_lower for word in ['обзор', 'информация', 'расскажи', 'что это']):
        intent = 'brand_overview'
    elif any(word in message_lower for word in INTENT_KEYWORDS['search']):
        intent = 'search'
    elif re.search(r'\d+\s*(пассажир|мест|человек|чел)', message_lower):
        intent = 'search'
    
    # Извлекаем сущности
    entities = extract_entities_from_text(message_lower)
    
    # Fallback: если есть бренд или модель, но intent не определён — выставить intent 'search'
    if intent == 'general' and (entities.get('brand') or entities.get('model')):
        intent = 'search'
    # Если есть только пассажиры — тоже intent search
    if intent == 'general' and entities.get('passengers'):
        intent = 'search'
    
    # Определяем, нужны ли уточнения
    need_clarification = False
    clarification_questions = []
    
    # Если не найден бренд, но есть другие признаки автомобиля
    if not entities.get('brand') and any(word in message_lower for word in ['автомобиль', 'машина', 'авто', 'купить', 'выбрать']):
        need_clarification = True
        clarification_questions.append("Какой бренд автомобиля вас интересует?")
    
    # Если не найден год, но есть упоминание о возрасте
    if not entities.get('year') and any(word in message_lower for word in ['новый', 'старый', 'год', 'возраст']):
        need_clarification = True
        clarification_questions.append("Какой год выпуска вас интересует?")
    
    # Если не указан тип (новый/б/у)
    if not entities.get('state') and any(word in message_lower for word in ['автомобиль', 'машина', 'авто']):
        need_clarification = True
        clarification_questions.append("Вас интересуют новые или подержанные автомобили?")
    
    return intent, entities, need_clarification, clarification_questions

def extract_entities_from_text(text):
    """
    Извлекает сущности (бренд, модель, год и т.д.) из текста.
    Исправлено: цвета извлекаются строго и не попадают в модель.
    """
    import re
    entities = {}
    text_lower = text.lower()
    # Очищаем текст от пунктуации для поиска цветов
    text_clean = re.sub(r'[.,!?;:]', ' ', text_lower)
    print(f"[DEBUG] extract_entities_from_text: '{text}' (очищено: '{text_clean}')")

    # --- 1. Извлекаем все цвета и удаляем их из текста ---
    color_forms = {
        'красный': [
            'красный', 'красного', 'красному', 'красным', 'красном', 'красные', 'красных', 'красными',
            'красная', 'красной', 'красную', 'красною', 'красное', 'красным', 'красными',
            'red', 'бордовый', 'малиновый', 'темно-красный', 'алый', 'алого', 'алому', 'алым', 'алом', 'алая', 'алой', 'алую', 'алое', 'алые', 'алых', 'алыми'
        ],
        'синий': [
            'синий', 'синего', 'синему', 'синим', 'синем', 'синие', 'синих', 'синими',
            'синяя', 'синей', 'синюю', 'синее', 'blue', 'голубой', 'голубого', 'голубому', 'голубым', 'голубом', 'голубые', 'голубых', 'голубыми', 'голубая', 'голубой', 'голубую', 'голубое', 'бирюзовый', 'бирюзовая', 'бирюзовое', 'бирюзовые', 'темно-синий', 'темно-синяя', 'темно-синие'
        ],
        'белый': [
            'белый', 'белого', 'белому', 'белым', 'белом', 'белые', 'белых', 'белыми',
            'белая', 'белой', 'белую', 'белою', 'белое', 'white', 'айвори', 'ivory', 'молочный', 'молочная', 'молочное', 'молочные', 'перламутровый', 'перламутровая', 'перламутровое', 'перламутровые'
        ],
        'черный': [
            'черный', 'черного', 'черному', 'черным', 'черном', 'черные', 'черных', 'черными',
            'черная', 'черной', 'черную', 'черною', 'черное', 'black', 'графитовый', 'графитовая', 'графитовое', 'графитовые', 'антрацит', 'антрацитовый', 'антрацитовая', 'антрацитовое', 'антрацитовые'
        ],
        'серый': [
            'серый', 'серого', 'серому', 'серым', 'сером', 'серые', 'серых', 'серыми',
            'серая', 'серой', 'серую', 'серое', 'серые', 'серых', 'серыми', 'gray', 'серебристый', 'серебристая', 'серебристое', 'серебристые', 'металлик', 'металлический', 'металлическая', 'металлическое', 'металлические'
        ],
        'бежевый': [
            'бежевый', 'бежевого', 'бежевому', 'бежевым', 'бежевом', 'бежевые', 'бежевых', 'бежевыми',
            'бежевая', 'бежевой', 'бежевую', 'бежевою', 'бежевое', 'beige', 'песочный', 'песочного', 'песочному', 'песочным', 'песочном', 'песочные', 'песочных', 'песочными', 'песочная', 'песочной', 'песочную', 'песочною', 'песочное'
        ],
        # ... остальные цвета ...
    }

    found_colors = []
    for color, forms in color_forms.items():
        for form in forms:
            # Ищем строго по границам слова, без учёта регистра
            if re.search(r'\b' + re.escape(form) + r'\b', text_clean, re.IGNORECASE):
                found_colors.append(color)
                print(f"[DEBUG] Найден цвет: '{form}' -> '{color}' в тексте '{text_clean}'")
    print(f"[DEBUG] Найдены цвета: {found_colors}")

    # Удаляем дубликаты, сохраняем порядок
    found_colors = list(dict.fromkeys(found_colors))
    entities['colors'] = found_colors
    # Если найдено несколько цветов — передаём весь список, иначе одну строку
    if not found_colors:
        entities['color'] = None
    else:
        entities['color'] = found_colors if len(found_colors) > 1 else found_colors[0]
    print(f"[DEBUG] Найдены цвета: {found_colors}")
    print(f"[DEBUG] Текст для поиска модели после удаления цветов: '{text_clean}'")

    # --- 2. Извлекаем бренд ---
    brand = extract_brand_from_text(text)
    if brand:
        entities['brand'] = brand
        print(f"[DEBUG] Found brand: {brand}")
    
    # --- 3. Извлекаем модель по очищенному тексту ---
    model = extract_model_from_text(text_clean, brand)
    passenger_words = {'пассажир', 'пассажиров', 'мест', 'место', 'человек', 'чел', 'человека', 'человеку', 'человеком', 'человеке'}
    model_stopwords = {
        'машина', 'машину', 'машины', 'машиной', 'машине', 'машинами', 'машинам', 'машинах',
        'автомобиль', 'автомобиля', 'автомобилю', 'автомобилем', 'автомобиле', 'автомобили', 'автомобилями', 'автомобилях',
        'car', 'cars', 'auto', 'autos', 'авто'
    }
    if model and model.lower() not in passenger_words and model.lower() not in model_stopwords:
        entities['model'] = model
        print(f"[DEBUG] Found model: {model}")
    elif model and model.lower() in model_stopwords:
        print(f"[DEBUG] Model '{model}' is a stopword (ignored as model). Not adding to entities.")
    
    # --- 4. Остальная логика (год, привод, кузов, пассажиры, цена и т.д.) ---
    # ... существующий код ...
    # (оставить без изменений, кроме использования text_clean там, где это логично)

    # --- 5. Возврат ---
    print(f"[DEBUG] Final entities: {entities}")
    return entities

def extract_brand_from_text(text: str) -> Optional[str]:
    """Извлекает бренд автомобиля из текста с поддержкой падежных вариаций"""
    if not text:
        return None
            
    text_lower = text.lower()
    print(f"[DEBUG] extract_brand_from_text: '{text}'")
    
    # Слова, которые НЕ являются брендами
    exclude_words = {
        'внедорожники', 'внедорожник', 'кроссовер', 'кроссоверы',
        'седан', 'седаны', 'хэтчбек', 'хэтчбеки', 'универсал', 'универсалы',
        'купе', 'кабриолет', 'пикап', 'минивэн', 'лифтбэк',
        'передний', 'задний', 'полный', 'полным', 'привод', 'привода',
        'до', 'от', 'млн', 'тыс', 'руб', 'k', 'т',
        'с', 'и', 'или', 'для', 'под', 'на', 'в', 'по', 'за', 'от', 'до',
        'автомобили', 'автомобиль', 'машины', 'машина', 'авто', 'автомобилей',
        'макс', 'про', 'плюс', 'элит', 'люкс', 'спорт', 'комфорт',
        'быстрый', 'быстрая', 'быстрое', 'быстрые', 'динамичный', 'динамичная', 'динамичное', 'динамичные'
    }
    
    print(f"[DEBUG] exclude_words: {exclude_words}")
    
    # Используем улучшенную систему распознавания брендов с падежными вариациями
    from brand_synonyms import normalize_brand_extended, BRAND_SYNONYMS
    
    # Явная нормализация для Mercedes
    mercedes_variants = {'mercedes', 'мерседес', 'mercedes-benz', 'мерседес-бенц', 'мерс'}
    words = text_lower.split()
    for word in words:
        if word in mercedes_variants:
            print(f"[DEBUG] Явная нормализация: найден Mercedes вариант '{word}' -> 'Mercedes-Benz'")
            return 'Mercedes-Benz'
    
    # Проверяем словарь синонимов брендов (включая падежные вариации)
    for word in words:
        if word in BRAND_SYNONYMS:
            brand = BRAND_SYNONYMS[word]
            print(f"[DEBUG] Found brand from synonyms: {brand} (word: {word})")
            return brand
    
    # Используем улучшенную функцию нормализации
    normalized_brand = normalize_brand_extended(text)
    if normalized_brand and normalized_brand != text.title():
        print(f"[DEBUG] Found brand using enhanced normalization: {normalized_brand}")
        return normalized_brand
    
    # Fallback: получаем все бренды из базы данных
    from database import get_all_brands_cached
    brands = get_all_brands_cached()
    
    # Ищем бренд в тексте
    for brand in brands:
        brand_lower = brand.lower()
        
        # Проверяем, не является ли слово исключенным
        if brand_lower in exclude_words:
            print(f"[DEBUG] Brand '{brand}' excluded as it's in exclude_words")
            continue
            
        # Проверяем различные варианты написания бренда
        brand_variants = [
            brand_lower,
            brand_lower.replace('-', ' '),
            brand_lower.replace(' ', ''),
            brand_lower.replace('ё', 'е'),
            brand_lower.replace('е', 'ё')
        ]
        
        for variant in brand_variants:
            if variant in text_lower:
                print(f"[DEBUG] Found brand: {brand} (variant: {variant})")
                return brand
    
    print(f"[DEBUG] No brand found in text")
    return None

def extract_model_from_text(text, brand=None):
    """
    Извлекает модель из текста (после бренда или как второе слово).
    Теперь исключает попадание в model любых слов, которые являются цветами, кузовами, характеристиками, служебными словами, а также любых слов, не являющихся реальными моделями из базы.
    """
    import re
    # Стоп-слова, которые не могут быть моделью
    stop_words = {
        'до', 'от', 'за', 'по', 'или', 'и', 'с', 'на', 'в', 'под', 'для', 'к', 'у', 'о', 'об', 'про', 'без', 'при', 'над', 'из', 'под', 'через', 'после', 'перед', 'между',
        'внедорожник', 'внедорожники', 'кроссовер', 'кроссоверы', 'седан', 'седаны', 'универсал', 'универсалы', 'купе', 'кабриолет', 'пикап', 'минивэн', 'лифтбэк', 'хэтчбек', 'хэтчбеки',
        'автомобиль', 'автомобили', 'машина', 'машины', 'руб', 'млн', 'тыс', 'k', 'т',
        'быстрый', 'быстрая', 'быстрое', 'быстрые', 'динамичный', 'динамичная', 'динамичное', 'динамичные',
        'цвет', 'цвета', 'цветом', 'цвету', 'цвете', 'цветах', 'цветами',
        'новый', 'новая', 'новое', 'новые', 'нового', 'новому', 'новым', 'новом', 'новую',
        'б/у', 'бу', 'подержанный', 'подержанная', 'подержанное', 'подержанные',
        'год', 'года', 'лет', 'году', 'годы', 'г.',
        'марка', 'марки', 'маркой', 'марку', 'марке',
        'модель', 'модели', 'моделью', 'моделями', 'моделях',
        'комплектация', 'комплектации', 'комплектацией', 'комплектацию', 'комплектациях',
        'привод', 'привода', 'приводом', 'приводу', 'приводах',
        'коробка', 'коробки', 'коробкой', 'коробку', 'коробке', 'коробках',
        'трансмиссия', 'трансмиссии', 'трансмиссией', 'трансмиссию', 'трансмиссиях',
        'двигатель', 'двигателя', 'двигателем', 'двигателю', 'двигателях',
        'кузов', 'кузова', 'кузовом', 'кузову', 'кузовах',
        'топливо', 'топлива', 'топливом', 'топливу', 'топливах',
        'опция', 'опции', 'опцией', 'опцию', 'опциях',
        'пассажир', 'пассажиров', 'мест', 'место', 'человек', 'чел', 'человека', 'человеку', 'человеком', 'человеке',
    }
    # Цвета, которые не могут быть моделью (все формы)
    color_forms = set([
        'красный', 'красного', 'красному', 'красным', 'красном', 'красные', 'красных', 'красными',
        'красная', 'красной', 'красную', 'красною', 'красное', 'красным', 'красными',
        'red', 'бордовый', 'малиновый', 'темно-красный', 'алый', 'алого', 'алому', 'алым', 'алом', 'алая', 'алой', 'алую', 'алое', 'алыми', 'алых',
        'синий', 'синего', 'синему', 'синим', 'синем', 'синие', 'синих', 'синими',
        'синяя', 'синей', 'синюю', 'синюю', 'синее', 'синим', 'синими',
        'blue', 'голубой', 'голубого', 'голубому', 'голубым', 'голубом', 'голубые', 'голубых', 'голубыми', 'голубая', 'голубой', 'голубую', 'голубое', 'голубыми',
        'бирюзовый', 'бирюзового', 'бирюзовому', 'бирюзовым', 'бирюзовом', 'бирюзовые', 'бирюзовых', 'бирюзовыми', 'бирюзовая', 'бирюзовой', 'бирюзовую', 'бирюзовое', 'бирюзовыми',
        'темно-синий', 'темно-синего', 'темно-синему', 'темно-синим', 'темно-синем', 'темно-синие', 'темно-синих', 'темно-синими', 'темно-синяя', 'темно-синей', 'темно-синюю', 'темно-синее', 'темно-синими',
        'белый', 'белого', 'белому', 'белым', 'белом', 'белые', 'белых', 'белыми',
        'белая', 'белой', 'белую', 'белою', 'белое', 'белым', 'белыми',
        'white', 'перламутровый', 'перламутрового', 'перламутровому', 'перламутровым', 'перламутровом', 'перламутровые', 'перламутровых', 'перламутровыми', 'перламутровая', 'перламутровой', 'перламутровую', 'перламутровое', 'перламутровыми',
        'черный', 'черного', 'черному', 'черным', 'черном', 'черные', 'черных', 'черными',
        'черная', 'черной', 'черную', 'черною', 'черное', 'черным', 'черными',
        'black',
        'зеленый', 'зеленого', 'зеленому', 'зеленым', 'зеленом', 'зеленые', 'зеленых', 'зелеными',
        'зеленая', 'зеленой', 'зеленую', 'зеленую', 'зеленое', 'зеленым', 'зелеными',
        'green', 'мятный', 'мятного', 'мятному', 'мятным', 'мятном', 'мятные', 'мятных', 'мятными', 'мятная', 'мятной', 'мятную', 'мятное', 'мятными',
        'оливковый', 'оливкового', 'оливковому', 'оливковым', 'оливковом', 'оливковые', 'оливковых', 'оливковыми', 'оливковая', 'оливковой', 'оливковую', 'оливковое', 'оливковыми',
        'темно-зеленый', 'темно-зеленого', 'темно-зеленому', 'темно-зеленым', 'темно-зеленом', 'темно-зеленые', 'темно-зеленых', 'темно-зелеными', 'темно-зеленая', 'темно-зеленой', 'темно-зеленую', 'темно-зеленое', 'темно-зелеными',
        'желтый', 'желтого', 'желтому', 'желтым', 'желтом', 'желтые', 'желтых', 'желтыми',
        'желтая', 'желтой', 'желтую', 'желтою', 'желтое', 'желтым', 'желтыми',
        'yellow', 'янтарный', 'янтарного', 'янтарному', 'янтарным', 'янтарном', 'янтарные', 'янтарных', 'янтарными', 'янтарная', 'янтарной', 'янтарную', 'янтарное', 'янтарными',
        'серый', 'серого', 'серому', 'серым', 'сером', 'серые', 'серых', 'серыми',
        'серая', 'серой', 'серую', 'серою', 'серое', 'серым', 'серыми',
        'gray', 'grey', 'темно-серый', 'темно-серого', 'темно-серому', 'темно-серым', 'темно-сером', 'темно-серые', 'темно-серых', 'темно-серыми', 'темно-серая', 'темно-серой', 'темно-серую', 'темно-серое', 'темно-серыми',
        'серебристый', 'серебристого', 'серебристому', 'серебристым', 'серебристом', 'серебристые', 'серебристых', 'серебристыми',
        'серебристая', 'серебристой', 'серебристую', 'серебристое', 'серебристыми',
        'silver',
        'оранжевый', 'оранжевого', 'оранжевому', 'оранжевым', 'оранжевом', 'оранжевые', 'оранжевых', 'оранжевыми',
        'оранжевая', 'оранжевой', 'оранжевую', 'оранжевое', 'оранжевыми',
        'orange',
        'фиолетовый', 'фиолетового', 'фиолетовому', 'фиолетовым', 'фиолетовом', 'фиолетовые', 'фиолетовых', 'фиолетовыми',
        'фиолетовая', 'фиолетовой', 'фиолетовую', 'фиолетовое', 'фиолетовыми',
        'purple', 'пурпурный', 'пурпурного', 'пурпурному', 'пурпурным', 'пурпурном', 'пурпурные', 'пурпурных', 'пурпурными', 'пурпурная', 'пурпурной', 'пурпурную', 'пурпурное', 'пурпурными',
        'сливовый', 'сливового', 'сливовому', 'сливовым', 'сливовом', 'сливовые', 'сливовых', 'сливовыми', 'сливовая', 'сливовой', 'сливовую', 'сливовое', 'сливовыми',
        'темно-фиолетовый', 'темно-фиолетового', 'темно-фиолетовому', 'темно-фиолетовым', 'темно-фиолетовом', 'темно-фиолетовые', 'темно-фиолетовых', 'темно-фиолетовыми', 'темно-фиолетовая', 'темно-фиолетовой', 'темно-фиолетовую', 'темно-фиолетовое', 'темно-фиолетовыми',
        'коричневый', 'коричневого', 'коричневому', 'коричневым', 'коричневом', 'коричневые', 'коричневых', 'коричневыми',
        'коричневая', 'коричневой', 'коричневую', 'коричневое', 'коричневыми',
        'шоколадный', 'шоколадного', 'шоколадному', 'шоколадным', 'шоколадном', 'шоколадные', 'шоколадных', 'шоколадными', 'шоколадная', 'шоколадной', 'шоколадную', 'шоколадное', 'шоколадными',
        'темно-коричневый', 'темно-коричневого', 'темно-коричневому', 'темно-коричневым', 'темно-коричневом', 'темно-коричневые', 'темно-коричневых', 'темно-коричневыми', 'темно-коричневая', 'темно-коричневой', 'темно-коричневую', 'темно-коричневое', 'темно-коричневыми',
        'розовый', 'розового', 'розовому', 'розовым', 'розовом', 'розовые', 'розовых', 'розовыми',
        'розовая', 'розовой', 'розовую', 'розовое', 'розовыми',
        'золотой', 'золотого', 'золотому', 'золотым', 'золотом', 'золотые', 'золотых', 'золотыми',
        'золотая', 'золотой', 'золотую', 'золотое', 'золотыми',
        'бежевый', 'бежевого', 'бежевому', 'бежевым', 'бежевом', 'бежевые', 'бежевых', 'бежевыми',
        'бежевая', 'бежевой', 'бежевую', 'бежевою', 'бежевое', 'бежевым', 'бежевыми',
        'песочный', 'песочного', 'песочному', 'песочным', 'песочном', 'песочные', 'песочных', 'песочными',
        'beige', 'beige-colored',
    ])
    # Кузова, которые не могут быть моделью
    body_types = {
        'седан', 'седаны', 'хэтчбек', 'хэтчбеки', 'универсал', 'универсалы', 'внедорожник', 'внедорожники', 'купе', 'кабриолет', 'кроссовер', 'кроссоверы', 'пикап', 'минивэн', 'лифтбэк',
        'sedan', 'hatchback', 'wagon', 'suv', 'coupe', 'cabrio', 'crossover', 'pickup', 'minivan', 'liftback'
    }
    # Получаем все реальные модели из базы (если бренд известен)
    real_models = set()
    try:
        from database import get_all_models_cached
        if brand:
            real_models = set([m.lower() for m in get_all_models_cached(brand)])
        else:
            # Если бренд не известен, берём все модели
            real_models = set([m.lower() for m in get_all_models_cached(None)])
    except Exception as e:
        pass
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # Проверяем словарь синонимов моделей (включая составные названия)
    from brand_synonyms import MODEL_SYNONYMS
    sorted_synonyms = sorted(MODEL_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)
    for synonym, canonical in sorted_synonyms:
        if synonym in text_lower:
            print(f"[DEBUG] Found model from synonyms: {canonical} (synonym: {synonym})")
            return canonical
    
    # Проверяем составные названия моделей (например, "тиго макс 7 про")
    compound_patterns = [
        r'тиго\s+макс\s+(\d+)\s+про',
        r'тигго\s+макс\s+(\d+)\s+про',
        r'тиго\s+(\d+)\s+про\s+макс',
        r'тигго\s+(\d+)\s+про\s+макс',
        r'тиго\s+макс\s+(\d+)',
        r'тигго\s+макс\s+(\d+)',
        r'тиго\s+макс\s+(\d+)\s+про\s*$',
        r'тигго\s+макс\s+(\d+)\s+про\s*$',
        r'тиго\s+макс\s+(\d+)\s+про\s+макс',
        r'тигго\s+макс\s+(\d+)\s+про\s+макс',
    ]
    for pattern in compound_patterns:
        match = re.search(pattern, text_lower)
        if match:
            number = match.group(1)
            model_name = f"Tiggo {number} Pro Max"
            print(f"[DEBUG] Found compound model: {model_name}")
            return model_name
    
    # Проверяем паттерны типа "тиго 7 про", "тигго 7 про"
    simple_patterns = [
        r'тиго\s+(\d+)\s+про',
        r'тигго\s+(\d+)\s+про',
        r'тиго\s+(\d+)',
        r'тигго\s+(\d+)',
    ]
    general_tiggo_pattern = r'тиго.*?(\d+).*?(?:про|макс)'
    general_tiggo_match = re.search(general_tiggo_pattern, text_lower)
    if general_tiggo_match:
        number = general_tiggo_match.group(1)
        has_max = 'макс' in text_lower
        has_pro = 'про' in text_lower
        if has_max and has_pro:
            model_name = f"Tiggo {number} Pro Max"
        elif has_pro:
            model_name = f"Tiggo {number} Pro"
        else:
            model_name = f"Tiggo {number}"
        print(f"[DEBUG] Found general Tiggo pattern: {model_name}")
        return model_name
    for pattern in simple_patterns:
        match = re.search(pattern, text_lower)
        if match:
            number = match.group(1)
            model_name = f"Tiggo {number} Pro"
            print(f"[DEBUG] Found simple model: {model_name}")
            return model_name
    
    # Если указан бренд, ищем модель после него
    if brand:
        brand_pattern = re.escape(brand.lower())
        after_brand = re.split(brand_pattern, text_lower, 1)
        if len(after_brand) > 1:
            model_text = after_brand[1].strip()
            model_match = re.search(r'^([a-zа-я0-9\-]+(?:\s+[a-zа-я0-9\-]+)*)', model_text)
            if model_match:
                candidate = model_match.group(1).title()
                # Проверяем, что это не стоп-слово, не цвет, не кузов, не число, не короткое слово и есть в базе моделей
                if (candidate.lower() not in stop_words and
                    candidate.lower() not in color_forms and
                    candidate.lower() not in body_types and
                    not candidate.isdigit() and
                    len(candidate) > 1 and
                    (not real_models or candidate.lower() in real_models)):
                    print(f"[DEBUG] Found model after brand: {candidate}")
                    return candidate
    
    # Если второе слово — возможная модель
    if len(words) > 1:
        candidate = words[1].title()
        if (candidate.lower() not in stop_words and
            candidate.lower() not in color_forms and
            candidate.lower() not in body_types and
            not candidate.isdigit() and
            len(candidate) > 1 and
            (not real_models or candidate.lower() in real_models)):
            print(f"[DEBUG] Found model as second word: {candidate}")
            return candidate
    
    print(f"[DEBUG] No model found in text")
    return None

def normalize_text(text):
    words = text.lower().split()
    normalized = []
    for word in words:
        if word in BRAND_SYNONYMS:
            normalized.append(BRAND_SYNONYMS[word])
        else:
            normalized.append(word)
    return ' '.join(normalized)

def extract_feature_value(text, feature_word):
    # Пример: "с подогревом руля" -> value = "подогрев руля"
    m = re.search(rf"{feature_word}\s*([а-яa-z0-9\- ]+)", text.lower())
    if m:
        return m.group(1).strip()
    return None

def extract_car_entities(text):
    """
    Извлекает сущности автомобилей из текста.
    Алиас для extract_entities_from_text для совместимости.
    """
    return extract_entities_from_text(text) 

def call_llama3(prompt, context=None):
    """Вызывает Llama3 API с проверкой доступности адресов"""
    urls = [
        "http://localhost:11434/api/generate",
        "http://localhost:11888/api/generate",
        "http://localhost:11777/api/generate",
        "http://127.0.0.1:11434/api/generate",
        "http://127.0.0.1:11888/api/generate",
        "http://127.0.0.1:11777/api/generate"
    ]
    
    for url in urls:
        try:
            payload = {
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            }
            if context:
                payload["context"] = context
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Ошибка: пустой ответ от Llama")
        except Exception as e:
            # Просто пробуем следующий url
            pass
    raise Exception("Не удалось подключиться к Llama API ни по одному из адресов")

class NLPProcessor:
    """Расширенный NLP процессор с ML и rule-based подходами"""
    
    def __init__(self, models_dir: str = "ml_models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        
        # Инициализация ML моделей
        self.intent_classifier = None
        self.sentiment_classifier = None
        self.car_clusterer = None
        self.vectorizer = None
        self.scaler = None
        
        # Кеши для быстрого доступа к справочникам
        self._brands_cache: List[str] = []
        self._models_cache: Dict[str, List[str]] = {}
        self._cities_cache: List[str] = []
        self._dealers_cache: List[str] = []
        self._fuel_types_cache: List[str] = []
        self._body_types_cache: List[str] = []
        self._transmissions_cache: List[str] = []
        self._drive_types_cache: List[str] = []
        
        # Расширенные rule-based паттерны
        self.intent_patterns = {
            'search': [
                r'\b(найти|искать|поиск|показать|выбрать|подобрать)\b',
                r'\b(авто|машина|автомобиль|car)\b',
                r'\b(бмв|bmw|мерседес|mercedes|ауди|audi)\b',
                r'\b(цена|стоимость|бюджет)\b',
                r'\b(год|модель|поколение)\b',
                r'\b(цвет|кузов|тип)\b',
                r'\b(мощность|двигатель|топливо)\b',
                r'\b(комплектация|опции|пакет)\b'
            ],
            'compare': [
                r'\b(сравнить|сравнение|сопоставить|против)\b',
                r'\b(что лучше|какая разница|отличия)\b',
                r'\b(или|либо|между)\b'
            ],
            'recommendations': [
                r'\b(рекомендовать|совет|посоветовать|подсказать)\b',
                r'\b(что выбрать|какую взять|лучший вариант)\b',
                r'\b(для|подходит|идеально)\b'
            ],
            'credit': [
                r'\b(кредит|рассрочка|финансирование|лизинг)\b',
                r'\b(платеж|взнос|процент|ставка)\b',
                r'\b(одобрение|заявка|документы)\b'
            ],
            'test_drive': [
                r'\b(тест|драйв|пробная поездка|прокат)\b',
                r'\b(записаться|забронировать|время)\b',
                r'\b(водительские права|паспорт)\b'
            ],
            'dealer': [
                r'\b(дилер|салон|центр|адрес|контакты)\b',
                r'\b(где купить|ближайший|работает)\b',
                r'\b(телефон|email|сайт)\b'
            ],
            'promotions': [
                r'\b(акция|скидка|спецпредложение|бонус)\b',
                r'\b(выгодно|экономия|льгота)\b',
                r'\b(ограниченно|время|условия)\b'
            ],
            'warranty': [
                r'\b(гарантия|сервис|обслуживание|ремонт)\b',
                r'\b(срок|условия|покрытие)\b',
                r'\b(бесплатно|замена|части)\b'
            ],
            'cost_of_ownership': [
                r'\b(расходы|содержание|эксплуатация)\b',
                r'\b(топливо|страховка|налоги|ремонт)\b',
                r'\b(экономичность|выгодность)\b'
            ],
            'trade_in': [
                r'\b(трейд|обмен|сдать|старая машина)\b',
                r'\b(оценка|стоимость|условия)\b',
                r'\b(доплата|разница)\b'
            ],
            'vin_check': [
                r'\b(вин|vin|номер|проверить)\b',
                r'\b(история|пробег|аварии|ремонты)\b',
                r'\b(чистый|залогированный)\b'
            ],
            'review': [
                r'\b(отзыв|обзор|мнение|рейтинг)\b',
                r'\b(плюсы|минусы|достоинства|недостатки)\b',
                r'\b(рекомендация|совет)\b'
            ],
            'greeting': [
                r'\b(привет|здравствуй|добрый|день)\b',
                r'\b(помощь|помоги|нужна помощь)\b'
            ],
            'farewell': [
                r'\b(пока|до свидания|спасибо|благодарю)\b',
                r'\b(все|хватит|закончить)\b'
            ]
        }
        
        # Паттерны для извлечения сущностей
        self.entity_patterns = {
            'brand': [
                r'\b(bmw|бмв|mercedes|мерседес|audi|ауди|volkswagen|фольксваген)\b',
                r'\b(toyota|тойота|honda|хонда|nissan|ниссан)\b',
                r'\b(lexus|лексус|infiniti|инфинити|acura|акура)\b'
            ],
            'model': [
                r'\b(x\d|m\d|i\d|z\d|1\d{3}|2\d{3}|3\d{3}|4\d{3}|5\d{3}|6\d{3}|7\d{3}|8\d{3})\b',
                r'\b(c-class|e-class|s-class|a-class|g-class|glc|gle|gls)\b',
                r'\b(a\d|q\d|rs\d|tt|r\d)\b'
            ],
            'year': [
                r'\b(20\d{2}|19\d{2})\b',
                r'\b(новый|старый|последний|текущий)\b'
            ],
            'price': [
                r'\b(\d+)\s*(тыс|т|k|млн|м)\s*(руб|долл|евро)?\b',
                r'\b(до|от|в пределах)\s*(\d+)\b'
            ],
            'color': [
                r'\b(белый|черный|красный|синий|зеленый|желтый|серый|серебристый)\b',
                r'\b(white|black|red|blue|green|yellow|gray|silver)\b'
            ],
            'fuel_type': [
                r'\b(бензин|дизель|гибрид|электро|газ)\b',
                r'\b(petrol|diesel|hybrid|electric|gas)\b'
            ],
            'transmission': [
                r'\b(автомат|механика|робот|вариатор)\b',
                r'\b(automatic|manual|robot|cvt)\b'
            ],
            'body_type': [
                r'\b(седан|хэтчбек|универсал|внедорожник|купе|кабриолет|кроссовер|пикап|минивэн|лифтбэк)\b',
                r'\b(sedan|hatchback|wagon|suv|coupe|cabrio|crossover|pickup|minivan|liftback)\b'
            ],
            'driving_gear_type': [
                r'\b(полный привод|передний привод|задний привод|полный|передний|задний)\b',
                r'\b(all[- ]?wheel|front[- ]?wheel|rear[- ]?wheel|awd|fwd|rwd)\b'
            ]
        }
        
        # Многошаговые сценарии
        self.dialogue_scenarios = {
            'search': {
                'steps': ['brand', 'model', 'year', 'price', 'features'],
                'current_step': 0,
                'collected_info': {}
            },
            'compare': {
                'steps': ['first_car', 'second_car', 'criteria'],
                'current_step': 0,
                'collected_info': {}
            },
            'credit': {
                'steps': ['income', 'down_payment', 'term', 'car_choice'],
                'current_step': 0,
                'collected_info': {}
            }
        }
        
        # История пользователей
        self.user_history = defaultdict(list)
        
        # Персонализация
        self.user_preferences = defaultdict(dict)
        
        # Инициализация ML моделей только если доступно
        if ML_AVAILABLE:
            self._initialize_ml_safely()
        else:
            logger.info("ML библиотеки недоступны. Используется rule-based подход.")
    
    def _initialize_ml_safely(self):
        """Безопасная инициализация ML компонентов с fallback"""
        try:
            if not ML_AVAILABLE:
                logger.info("ML библиотеки недоступны. Используется rule-based подход.")
                self.ml_available = False
                return
            
            # Проверяем наличие файлов моделей
            model_files = [
                'vectorizer.pkl',
                'intent_classifier.pkl', 
                'sentiment_classifier.pkl',
                'car_clusterer.pkl',
                'scaler.pkl'
            ]
            
            missing_files = []
            for file in model_files:
                if not os.path.exists(os.path.join(self.models_dir, file)):
                    missing_files.append(file)
            
            if missing_files:
                logger.warning(f"Отсутствуют файлы моделей: {missing_files}")
                logger.info("Используется rule-based подход.")
                self.ml_available = False
                return
            
            # Пытаемся загрузить модели
            self._load_models()
            
            # Проверяем, что модели загружены корректно
            if all([self.vectorizer, self.intent_classifier, self.sentiment_classifier]):
                self.ml_available = True
                logger.info("ML модели успешно загружены.")
            else:
                logger.warning("Не все ML модели загружены корректно. Используется rule-based подход.")
                self.ml_available = False
            
        except Exception as e:
            logger.error(f"Ошибка инициализации ML: {e}")
            logger.info("Используется rule-based подход.")
            self.ml_available = False
    
    def _load_models(self):
        """Загрузка сохраненных ML моделей с улучшенной обработкой ошибок"""
        if not ML_AVAILABLE:
            return
            
        try:
            model_files = {
                'intent_classifier': 'intent_classifier.pkl',
                'sentiment_classifier': 'sentiment_classifier.pkl',
                'car_clusterer': 'car_clusterer.pkl',
                'vectorizer': 'vectorizer.pkl',
                'scaler': 'scaler.pkl'
            }
            
            for attr, filename in model_files.items():
                filepath = os.path.join(self.models_dir, filename)
                if os.path.exists(filepath):
                    try:
                        model = joblib.load(filepath)
                        setattr(self, attr, model)
                        logger.info(f"Загружена модель: {filename}")
                    except Exception as e:
                        logger.error(f"Ошибка загрузки модели {filename}: {e}")
                        # Удаляем поврежденный файл
                        try:
                            os.remove(filepath)
                            logger.info(f"Удален поврежденный файл: {filename}")
                        except:
                            pass
                        setattr(self, attr, None)
                    
        except Exception as e:
            logger.error(f"Общая ошибка загрузки моделей: {e}")
    
    def _initialize_ml(self):
        """Инициализация ML моделей"""
        if not ML_AVAILABLE:
            return
            
        try:
            # Расширенные обучающие данные
            training_data = self._get_extended_training_data()
            
            # Векторизация
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 3),
                stop_words='english',
                min_df=2
            )
            
            # Подготовка данных
            texts = [item['text'] for item in training_data]
            intents = [item['intent'] for item in training_data]
            sentiments = [item['sentiment'] for item in training_data]
            
            # Векторизация текстов
            X = self.vectorizer.fit_transform(texts)
            
            # Классификатор интентов (ансамбль)
            self.intent_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.intent_classifier.fit(X, intents)
            
            # Классификатор тональности
            self.sentiment_classifier = SVC(kernel='rbf', probability=True)
            self.sentiment_classifier.fit(X, sentiments)
            
            # Кластеризация автомобилей
            self.car_clusterer = KMeans(n_clusters=8, random_state=42)
            
            # Скалер для числовых признаков
            self.scaler = StandardScaler()
            
            # Сохранение моделей
            self._save_models()
            
            logger.info("ML модели успешно инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации ML: {e}")
            # Сбрасываем модели в None при ошибке
            self.intent_classifier = None
            self.sentiment_classifier = None
            self.car_clusterer = None
            self.vectorizer = None
            self.scaler = None
    
    def _get_extended_training_data(self) -> List[Dict]:
        """Расширенные обучающие данные"""
        return [
            # Поиск
            {'text': 'найти бмв x5', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'ищу автомобиль до 2 млн', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'показать машины 2023 года', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'подобрать авто для семьи', 'intent': 'search', 'sentiment': 'positive'},
            {'text': 'нужна машина с автоматом', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'ищу дизельный внедорожник', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'bmw x3 2022 года', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'мерседес c-class белый', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'ауди а4 с полным приводом', 'intent': 'search', 'sentiment': 'neutral'},
            {'text': 'машина до 1.5 млн рублей', 'intent': 'search', 'sentiment': 'neutral'},
            
            # Сравнение
            {'text': 'сравнить бмв x5 и мерседес gle', 'intent': 'compare', 'sentiment': 'neutral'},
            {'text': 'что лучше x3 или q5', 'intent': 'compare', 'sentiment': 'neutral'},
            {'text': 'сопоставить характеристики', 'intent': 'compare', 'sentiment': 'neutral'},
            {'text': 'разница между моделями', 'intent': 'compare', 'sentiment': 'neutral'},
            {'text': 'против x5 vs gle', 'intent': 'compare', 'sentiment': 'neutral'},
            
            # Рекомендации
            {'text': 'посоветуйте автомобиль', 'intent': 'recommendations', 'sentiment': 'positive'},
            {'text': 'что выбрать для города', 'intent': 'recommendations', 'sentiment': 'neutral'},
            {'text': 'рекомендуйте семейный авто', 'intent': 'recommendations', 'sentiment': 'positive'},
            {'text': 'подскажите лучший вариант', 'intent': 'recommendations', 'sentiment': 'positive'},
            {'text': 'какую машину взять', 'intent': 'recommendations', 'sentiment': 'neutral'},
            
            # Кредит
            {'text': 'оформить кредит на авто', 'intent': 'credit', 'sentiment': 'neutral'},
            {'text': 'рассрочка без первоначального взноса', 'intent': 'credit', 'sentiment': 'positive'},
            {'text': 'финансирование под 0%', 'intent': 'credit', 'sentiment': 'positive'},
            {'text': 'лизинг для ип', 'intent': 'credit', 'sentiment': 'neutral'},
            {'text': 'кредит на 5 лет', 'intent': 'credit', 'sentiment': 'neutral'},
            
            # Тест-драйв
            {'text': 'записаться на тест драйв', 'intent': 'test_drive', 'sentiment': 'positive'},
            {'text': 'прокат автомобиля на день', 'intent': 'test_drive', 'sentiment': 'neutral'},
            {'text': 'пробная поездка бмв', 'intent': 'test_drive', 'sentiment': 'positive'},
            {'text': 'тест машины в выходные', 'intent': 'test_drive', 'sentiment': 'positive'},
            
            # Дилер
            {'text': 'адрес дилерского центра', 'intent': 'dealer', 'sentiment': 'neutral'},
            {'text': 'где купить бмв в москве', 'intent': 'dealer', 'sentiment': 'neutral'},
            {'text': 'контакты салона', 'intent': 'dealer', 'sentiment': 'neutral'},
            {'text': 'ближайший дилер', 'intent': 'dealer', 'sentiment': 'neutral'},
            {'text': 'телефон автосалона', 'intent': 'dealer', 'sentiment': 'neutral'},
            
            # Акции
            {'text': 'акции и спецпредложения', 'intent': 'promotions', 'sentiment': 'positive'},
            {'text': 'скидки на новые авто', 'intent': 'promotions', 'sentiment': 'positive'},
            {'text': 'бонусы при покупке', 'intent': 'promotions', 'sentiment': 'positive'},
            {'text': 'выгодные предложения', 'intent': 'promotions', 'sentiment': 'positive'},
            
            # Гарантия
            {'text': 'гарантия на автомобиль', 'intent': 'warranty', 'sentiment': 'neutral'},
            {'text': 'сервисное обслуживание', 'intent': 'warranty', 'sentiment': 'neutral'},
            {'text': 'ремонт по гарантии', 'intent': 'warranty', 'sentiment': 'neutral'},
            {'text': 'срок гарантии', 'intent': 'warranty', 'sentiment': 'neutral'},
            
            # Стоимость владения
            {'text': 'расходы на содержание', 'intent': 'cost_of_ownership', 'sentiment': 'neutral'},
            {'text': 'стоимость эксплуатации', 'intent': 'cost_of_ownership', 'sentiment': 'neutral'},
            {'text': 'расход топлива', 'intent': 'cost_of_ownership', 'sentiment': 'neutral'},
            {'text': 'страховка и налоги', 'intent': 'cost_of_ownership', 'sentiment': 'neutral'},
            
            # Trade-in
            {'text': 'сдать старую машину', 'intent': 'trade_in', 'sentiment': 'neutral'},
            {'text': 'оценка автомобиля', 'intent': 'trade_in', 'sentiment': 'neutral'},
            {'text': 'обмен на новый', 'intent': 'trade_in', 'sentiment': 'positive'},
            {'text': 'трейд ин программа', 'intent': 'trade_in', 'sentiment': 'neutral'},
            
            # VIN проверка
            {'text': 'проверить вин номер', 'intent': 'vin_check', 'sentiment': 'neutral'},
            {'text': 'история автомобиля', 'intent': 'vin_check', 'sentiment': 'neutral'},
            {'text': 'пробег по вин', 'intent': 'vin_check', 'sentiment': 'neutral'},
            {'text': 'аварии в истории', 'intent': 'vin_check', 'sentiment': 'negative'},
            
            # Обзоры
            {'text': 'отзывы о бмв x5', 'intent': 'review', 'sentiment': 'neutral'},
            {'text': 'обзор автомобиля', 'intent': 'review', 'sentiment': 'neutral'},
            {'text': 'мнения владельцев', 'intent': 'review', 'sentiment': 'neutral'},
            {'text': 'рейтинг машин', 'intent': 'review', 'sentiment': 'neutral'},
            
            # Приветствие
            {'text': 'привет', 'intent': 'greeting', 'sentiment': 'positive'},
            {'text': 'здравствуйте', 'intent': 'greeting', 'sentiment': 'positive'},
            {'text': 'добрый день', 'intent': 'greeting', 'sentiment': 'positive'},
            {'text': 'помогите мне', 'intent': 'greeting', 'sentiment': 'neutral'},
            
            # Прощание
            {'text': 'спасибо', 'intent': 'farewell', 'sentiment': 'positive'},
            {'text': 'до свидания', 'intent': 'farewell', 'sentiment': 'positive'},
            {'text': 'пока', 'intent': 'farewell', 'sentiment': 'positive'},
            {'text': 'все понятно', 'intent': 'farewell', 'sentiment': 'positive'}
        ]
    
    def _save_models(self):
        """Сохранение ML моделей с проверкой на существование"""
        if not ML_AVAILABLE:
            return
            
        try:
            models_to_save = {
                'intent_classifier': self.intent_classifier,
                'sentiment_classifier': self.sentiment_classifier,
                'car_clusterer': self.car_clusterer,
                'vectorizer': self.vectorizer,
                'scaler': self.scaler
            }
            
            saved_count = 0
            for name, model in models_to_save.items():
                if model is not None:
                    filepath = os.path.join(self.models_dir, f"{name}.pkl")
                    
                    # Проверяем, существует ли файл и не поврежден ли он
                    if os.path.exists(filepath):
                        try:
                            # Пробуем загрузить существующий файл для проверки
                            existing_model = joblib.load(filepath)
                            if existing_model is not None:
                                logger.info(f"Модель {name} уже существует и корректна, пропускаем сохранение")
                                continue
                        except:
                            # Если файл поврежден, удаляем его
                            try:
                                os.remove(filepath)
                                logger.info(f"Удален поврежденный файл модели: {name}")
                            except:
                                pass
                    
                    # Сохраняем модель
                    joblib.dump(model, filepath)
                    logger.info(f"Сохранена модель: {name}")
                    saved_count += 1
            
            if saved_count > 0:
                logger.info(f"✅ Успешно сохранено {saved_count} моделей")
            else:
                logger.info("ℹ️ Все модели уже существуют и корректны")
                    
        except Exception as e:
            logger.error(f"Ошибка сохранения моделей: {e}")
    
    def process_query(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """Обработка запроса с ML и rule-based подходами"""
        text = text.lower().strip()
        
        # Сохранение в историю
        self.user_history[user_id].append({
            'text': text,
            'timestamp': datetime.now(),
            'intent': None,
            'entities': {},
            'sentiment': None
        })
        
        # ML предсказание (только если доступно)
        ml_result = None
        if ML_AVAILABLE and self.ml_available:
            try:
                ml_result = self._ml_predict(text)
            except Exception as e:
                logger.warning(f"ML предсказание не удалось: {e}")
        
        # Rule-based анализ
        rule_result = self._rule_based_analysis(text)
        
        # Объединение результатов
        result = self._combine_results(ml_result, rule_result, text)
        
        # Извлечение сущностей
        entities = extract_entities_from_text(text)
        result['entities'] = entities
        
        # --- ДОРАБОТКА: если есть хотя бы один фильтр, intent = 'search' ---
        filter_keys = [
            'body_type', 'driving_gear_type', 'price_from', 'price_to',
            'fuel_type', 'year', 'transmission', 'city'
        ]
        if result['intent'] != 'search' and any(entities.get(k) for k in filter_keys):
            result['intent'] = 'search'
            result['confidence'] = 1.0
            result['method'] = 'forced_by_filters'
        
        # --- ДОРАБОТКА: если есть бренд и запрос содержит "расскажи", "объясни", то intent = 'dealer' ---
        if entities.get('brand') and any(word in text for word in ['расскажи', 'объясни', 'что', 'как', 'почему']):
            result['intent'] = 'dealer'
            result['confidence'] = 0.9
            result['method'] = 'brand_info_request'
        
        # Анализ тональности
        sentiment = self._analyze_sentiment(text)
        result['sentiment'] = sentiment
        
        # Обновление истории
        if self.user_history[user_id]:
            self.user_history[user_id][-1].update({
                'intent': result['intent'],
                'entities': entities,
                'sentiment': sentiment
            })
        
        # Персонализация
        self._update_user_preferences(user_id, result)
        
        # --- ЛОГИРОВАНИЕ ---
        print(f"[NLP] intent: {result['intent']}, method: {result.get('method')}, entities: {entities}")
        
        return result
    
    def _ml_predict(self, text: str) -> Dict[str, Any]:
        """ML предсказание"""
        try:
            if not all([self.vectorizer, self.intent_classifier, self.sentiment_classifier]):
                return {}
            
            # Векторизация
            if self.vectorizer is not None:
                X = self.vectorizer.transform([text])
            else:
                return {}
            
            # Предсказание интента
            if self.intent_classifier is not None:
                intent_proba = self.intent_classifier.predict_proba(X)[0]
                intent_idx = np.argmax(intent_proba)
                intent_confidence = intent_proba[intent_idx]
                predicted_intent = self.intent_classifier.classes_[intent_idx]
            else:
                return {}
            
            # Предсказание тональности
            if self.sentiment_classifier is not None:
                sentiment_proba = self.sentiment_classifier.predict_proba(X)[0]
                sentiment_idx = np.argmax(sentiment_proba)
                sentiment_confidence = sentiment_proba[sentiment_idx]
                predicted_sentiment = self.sentiment_classifier.classes_[sentiment_idx]
            else:
                return {}
            
            return {
                'intent': predicted_intent,
                'intent_confidence': intent_confidence,
                'sentiment': predicted_sentiment,
                'sentiment_confidence': sentiment_confidence
            }
            
        except Exception as e:
            logger.error(f"Ошибка ML предсказания: {e}")
            return {}
    
    def _rule_based_analysis(self, text: str) -> Dict[str, Any]:
        """Rule-based анализ"""
        intent_scores = defaultdict(int)
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    intent_scores[intent] += len(matches)
        
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            confidence = min(best_intent[1] / 3.0, 1.0)  # Нормализация уверенности
            return {
                'intent': best_intent[0],
                'confidence': confidence
            }
        
        return {'intent': 'unknown', 'confidence': 0.0}
    
    def _combine_results(self, ml_result: Optional[Dict], rule_result: Dict, text: str) -> Dict[str, Any]:
        """Объединение ML и rule-based результатов"""
        if ml_result and ml_result['intent_confidence'] > 0.7:
            # Высокая уверенность ML
            return {
                'intent': ml_result['intent'],
                'confidence': ml_result['intent_confidence'],
                'method': 'ml'
            }
        elif rule_result['confidence'] > 0.5:
            # Хорошая уверенность rule-based
            return {
                'intent': rule_result['intent'],
                'confidence': rule_result['confidence'],
                'method': 'rule_based'
            }
        else:
            # Fallback на rule-based с низкой уверенностью
            return {
                'intent': rule_result['intent'],
                'confidence': rule_result['confidence'],
                'method': 'fallback'
            }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Извлечение сущностей с нормализацией"""
        entities = defaultdict(list)
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    normalized = self._normalize_entity(entity_type, match)
                    if normalized and normalized not in entities[entity_type]:
                        entities[entity_type].append(normalized)
        # Приводим все значения к строке через get_first_deep
        for k in entities:
            entities[k] = [get_first_deep(v) for v in entities[k]]
        return dict(entities)
    
    def _normalize_entity(self, entity_type: str, value: Optional[str]) -> Optional[str]:
        """Нормализация сущностей"""
        value = get_first_deep(value)
        if value is None:
            return None
        value = str(value).lower().strip()
        normalization_map = {
            'brand': {
                'бмв': 'BMW',
                'bmw': 'BMW',
                'мерседес': 'Mercedes',
                'mercedes': 'Mercedes',
                'ауди': 'Audi',
                'audi': 'Audi'
            },
            'fuel_type': {
                'бензин': 'petrol',
                'дизель': 'diesel',
                'гибрид': 'hybrid',
                'электро': 'electric'
            },
            'transmission': {
                'автомат': 'automatic',
                'механика': 'manual',
                'робот': 'robot'
            },
            'body_type': {
                'седан': 'sedan',
                'хэтчбек': 'hatchback',
                'внедорожник': 'suv',
                'купе': 'coupe'
            }
        }
        
        if entity_type in normalization_map:
            return normalization_map[entity_type].get(value, value.title())
        
        return value.title()
    
    def _analyze_sentiment(self, text: str) -> str:
        """Анализ тональности"""
        # Сначала пробуем ML, если доступно
        if ML_AVAILABLE and self.ml_available and self.sentiment_classifier and self.vectorizer:
            try:
                X = self.vectorizer.transform([text])
                sentiment = self.sentiment_classifier.predict(X)[0]
                return sentiment
            except Exception as e:
                logger.warning(f"ML анализ тональности не удался: {e}")
        
        # Fallback на rule-based анализ тональности
        positive_words = ['хороший', 'отличный', 'прекрасный', 'великолепный', 'нравится', 'люблю', 'хочу', 'нужен']
        negative_words = ['плохой', 'ужасный', 'не нравится', 'не хочу', 'дорогой', 'проблема', 'ошибка']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _update_user_preferences(self, user_id: str, result: Dict[str, Any]):
        """Обновление пользовательских предпочтений"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = defaultdict(list)
        
        entities = result.get('entities', {})
        for entity_type, values in entities.items():
            if values:
                # Проверяем тип значения перед использованием extend
                if isinstance(values, list):
                    self.user_preferences[user_id][entity_type].extend(values)
                else:
                    # Если значение не список, добавляем как единичное значение
                    if values not in self.user_preferences[user_id][entity_type]:
                        self.user_preferences[user_id][entity_type].append(values)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, List[str]]:
        """Получение предпочтений пользователя"""
        return self.user_preferences.get(user_id, {})
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Получение истории пользователя"""
        history = self.user_history.get(user_id, [])
        return history[-limit:] if limit else history
    
    def cluster_cars(self, cars_data: List[Dict]) -> List[int]:
        """Кластеризация автомобилей"""
        if not ML_AVAILABLE or not self.car_clusterer or not self.scaler:
            return [0] * len(cars_data)
        
        try:
            # Подготовка признаков
            features = []
            for car in cars_data:
                car_features = [
                    car.get('price', 0),
                    car.get('year', 2020),
                    car.get('mileage', 0),
                    car.get('engine_power', 0),
                    car.get('engine_volume', 0)
                ]
                features.append(car_features)
            
            # Нормализация
            features_scaled = self.scaler.fit_transform(features)
            
            # Кластеризация
            clusters = self.car_clusterer.fit_predict(features_scaled)
            
            return clusters.tolist()
            
        except Exception as e:
            logger.error(f"Ошибка кластеризации: {e}")
            return [0] * len(cars_data)
    
    def get_recommendations(self, user_id: str, cars_data: List[Dict], limit: int = 5) -> List[Dict]:
        """Получение персонализированных рекомендаций с учетом приоритетов пользователя"""
        preferences = self.get_user_preferences(user_id)
        history = self.get_user_history(user_id, 5)
        priority_groups = preferences.get('priority_groups', [])
        car_scores = []
        for car in cars_data:
            score = 0
            # Приоритеты по группам характеристик (frontend передает как 'priority_groups')
            if priority_groups:
                for group in priority_groups:
                    # Список ключей для группы (должен совпадать с ADVANTAGE_GROUPS на фронте)
                    group_keys = {
                        'finance': ['price','fuel_consumption','tax','insurance','maintenance','resale'],
                        'comfort': ['climate','interior','multimedia','seat_heating','noise','ergonomics','trunk','space'],
                        'safety': ['abs','esp','airbags','isofix','crash_test','active_safety','passive_safety'],
                        'tech': ['multimedia','led','adaptive_light','cruise','keyless','panorama','assist'],
                        'dynamic': ['power','acceleration','drive','engine','sport'],
                        'eco': ['eco_class','co2','electric','hybrid','materials'],
                        'reliability': ['warranty','reliability','service','brand_reputation'],
                        'image': ['design','brand','color','status'],
                        'space': ['trunk','space','seats','dimensions']
                    }.get(group, [])
                    if any(car.get(k) not in (None, '', 0) for k in group_keys):
                        score += 2
            # Остальные предпочтения (бренд, топливо и т.д.)
            if 'brand' in preferences and car.get('brand') in preferences['brand']:
                score += 3
            if 'fuel_type' in preferences and car.get('fuel_type') in preferences['fuel_type']:
                score += 2
            if 'body_type' in preferences and car.get('body_type') in preferences['body_type']:
                score += 2
            if 'price' in preferences:
                for price_pref in preferences['price']:
                    if 'до' in price_pref and car.get('price', 0) <= self._extract_price(price_pref):
                        score += 2
            if 'year' in preferences and car.get('year') in preferences['year']:
                score += 1
            car_scores.append((car, score))
        # Если нет приоритетов — score только по остальным предпочтениям, но возвращаем все авто
        if not priority_groups:
            return [car for car, _ in car_scores]
        # Сортировка по весам
        car_scores.sort(key=lambda x: x[1], reverse=True)
        return [car for car, score in car_scores[:limit]]
    
    def _extract_price(self, price_text: str) -> int:
        """Извлечение цены из текста"""
        try:
            numbers = re.findall(r'\d+', price_text)
            if numbers:
                return int(numbers[0]) * 1000  # Предполагаем тысячи
        except:
            pass
        return 0
    
    def retrain_models(self, new_data: List[Dict]):
        """Переобучение моделей на новых данных"""
        if not ML_AVAILABLE:
            return False
        
        try:
            # Добавление новых данных к существующим
            training_data = self._get_extended_training_data() + new_data
            
            # Переобучение
            self._initialize_ml()
            
            logger.info("Модели успешно переобучены")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переобучения: {e}")
            return False
    
    def get_model_performance(self) -> Dict[str, float]:
        """Получение производительности моделей"""
        if not ML_AVAILABLE or not self.vectorizer or not self.intent_classifier or not self.sentiment_classifier:
            return {}
        
        try:
            training_data = self._get_extended_training_data()
            texts = [item['text'] for item in training_data]
            intents = [item['intent'] for item in training_data]
            sentiments = [item['sentiment'] for item in training_data]
            
            X = self.vectorizer.transform(texts)
            
            intent_accuracy = accuracy_score(intents, self.intent_classifier.predict(X))
            sentiment_accuracy = accuracy_score(sentiments, self.sentiment_classifier.predict(X))
            
            return {
                'intent_accuracy': intent_accuracy,
                'sentiment_accuracy': sentiment_accuracy
            }
            
        except Exception as e:
            logger.error(f"Ошибка оценки производительности: {e}")
            return {}

    def get_all_brands_cached(self) -> List[str]:
        """Получение всех брендов из кеша или БД"""
        if not self._brands_cache:
            try:
                # Получаем реальные бренды из БД
                brands_result = execute_query("SELECT DISTINCT mark FROM car WHERE mark IS NOT NULL ORDER BY mark")
                self._brands_cache = [brand[0] for brand in brands_result if brand[0]]
            except Exception as e:
                logger.error(f"Ошибка получения брендов: {e}")
                # Fallback на базовые бренды
                self._brands_cache = ["BMW", "Mercedes", "Audi", "Volkswagen", "Toyota", "Honda", "Ford", "Chevrolet"]
        return self._brands_cache

    def get_all_models_cached(self, brand: Optional[str] = None) -> List[str]:
        """Получение всех моделей из кеша или БД"""
        cache_key = f"models_{brand}" if brand else "models_all"
        
        if cache_key not in self._models_cache:
            try:
                # Получаем реальные модели из БД
                if brand:
                    models_result = execute_query(
                        "SELECT DISTINCT model FROM car WHERE mark = ? AND model IS NOT NULL ORDER BY model",
                        [brand]
                    )
                else:
                    models_result = execute_query(
                        "SELECT DISTINCT model FROM car WHERE model IS NOT NULL ORDER BY model"
                    )
                self._models_cache[cache_key] = [model[0] for model in models_result if model[0]]
            except Exception as e:
                logger.error(f"Ошибка получения моделей: {e}")
                # Fallback на базовые модели
                if brand == "BMW":
                    self._models_cache[cache_key] = ["X1", "X3", "X5", "3 Series", "5 Series", "7 Series"]
                elif brand == "Mercedes":
                    self._models_cache[cache_key] = ["A-Class", "C-Class", "E-Class", "S-Class", "GLA", "GLC"]
                else:
                    self._models_cache[cache_key] = ["Model 1", "Model 2", "Model 3"]
        
        return self._models_cache[cache_key]

    def get_all_cities_cached(self) -> List[str]:
        """Получение всех городов из кеша или БД"""
        if not self._cities_cache:
            try:
                # Получаем реальные города из БД
                cities_result = execute_query("SELECT DISTINCT city FROM car WHERE city IS NOT NULL ORDER BY city")
                self._cities_cache = [city[0] for city in cities_result if city[0]]
            except Exception as e:
                logger.error(f"Ошибка получения городов: {e}")
                # Fallback на базовые города
                self._cities_cache = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"]
        return self._cities_cache

    def get_all_dealers_cached(self) -> List[str]:
        """Получение всех дилерских центров из кеша или БД"""
        if not self._dealers_cache:
            try:
                # Получаем реальные дилерские центры из БД
                dealers_result = execute_query("SELECT DISTINCT dealer_center FROM car WHERE dealer_center IS NOT NULL ORDER BY dealer_center")
                self._dealers_cache = [dealer[0] for dealer in dealers_result if dealer[0]]
            except Exception as e:
                logger.error(f"Ошибка получения дилеров: {e}")
                # Fallback на базовые дилеры
                self._dealers_cache = ["Автоцентр BMW", "Мерседес-Бенц Центр", "Ауди Центр", "Фольксваген Центр"]
        return self._dealers_cache

    def get_all_fuel_types_cached(self) -> List[str]:
        """Получение всех типов топлива из кеша или БД"""
        if not self._fuel_types_cache:
            try:
                # Получаем реальные типы топлива из БД
                fuel_result = execute_query("SELECT DISTINCT fuel_type FROM car WHERE fuel_type IS NOT NULL ORDER BY fuel_type")
                self._fuel_types_cache = [fuel[0] for fuel in fuel_result if fuel[0]]
            except Exception as e:
                logger.error(f"Ошибка получения типов топлива: {e}")
                # Fallback на базовые типы
                self._fuel_types_cache = ["бензин", "дизель", "электро", "гибрид"]
        return self._fuel_types_cache

    def get_all_body_types_cached(self) -> List[str]:
        """Получение всех типов кузова из кеша или БД"""
        if not self._body_types_cache:
            try:
                # Получаем реальные типы кузова из БД
                body_result = execute_query("SELECT DISTINCT body_type FROM car WHERE body_type IS NOT NULL ORDER BY body_type")
                self._body_types_cache = [body[0] for body in body_result if body[0]]
            except Exception as e:
                logger.error(f"Ошибка получения типов кузова: {e}")
                # Fallback на базовые типы
                self._body_types_cache = ["седан", "хэтчбек", "универсал", "внедорожник", "купе"]
        return self._body_types_cache

    def get_all_transmissions_cached(self) -> List[str]:
        """Получение всех типов трансмиссии из кеша или БД"""
        if not self._transmissions_cache:
            try:
                # Получаем реальные типы трансмиссии из БД
                trans_result = execute_query("SELECT DISTINCT gear_box_type FROM car WHERE gear_box_type IS NOT NULL ORDER BY gear_box_type")
                self._transmissions_cache = [trans[0] for trans in trans_result if trans[0]]
            except Exception as e:
                logger.error(f"Ошибка получения типов трансмиссии: {e}")
                # Fallback на базовые типы
                self._transmissions_cache = ["автомат", "механика", "робот", "вариатор"]
        return self._transmissions_cache

    def get_all_drive_types_cached(self) -> List[str]:
        """Получение всех типов привода из кеша или БД"""
        if not self._drive_types_cache:
            try:
                # Получаем реальные типы привода из БД
                drive_result = execute_query("SELECT DISTINCT driving_gear_type FROM car WHERE driving_gear_type IS NOT NULL ORDER BY driving_gear_type")
                self._drive_types_cache = [drive[0] for drive in drive_result if drive[0]]
            except Exception as e:
                logger.error(f"Ошибка получения типов привода: {e}")
                # Fallback на базовые типы
                self._drive_types_cache = ["передний", "задний", "полный"]
        return self._drive_types_cache

# Функции для извлечения дополнительных сущностей
def extract_down_payment(text: str) -> Optional[float]:
    """Извлечение первоначального взноса"""
    patterns = [
        r'первоначальный\s+взнос\s*(\d+)',
        r'первый\s+взнос\s*(\d+)',
        r'взнос\s*(\d+)',
        r'(\d+)\s*первоначальный'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1)) * 1000  # Предполагаем тысячи рублей
    return None

def extract_term(text: str) -> Optional[int]:
    """Извлечение срока кредита"""
    patterns = [
        r'срок\s*(\d+)\s*лет',
        r'(\d+)\s*лет',
        r'на\s*(\d+)\s*лет',
        r'кредит\s*на\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return None

def extract_price(text: str) -> Optional[float]:
    """Извлечение цены"""
    patterns = [
        r'цена\s*(\d+)',
        r'стоимость\s*(\d+)',
        r'(\d+)\s*рубл',
        r'(\d+)\s*млн'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            price = float(match.group(1))
            if 'млн' in pattern:
                price *= 1000000
            return price
    return None

def extract_year(text: str) -> Optional[int]:
    """Извлечение года"""
    patterns = [
        r'(\d{4})\s*год',
        r'(\d{4})\s*г',
        r'(\d{4})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            if 1990 <= year <= 2030:
                return year
    return None

def extract_mileage(text: str) -> Optional[int]:
    """Извлечение пробега"""
    patterns = [
        r'пробег\s*(\d+)',
        r'(\d+)\s*км',
        r'(\d+)\s*тысяч\s*км'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            mileage = int(match.group(1))
            if 'тысяч' in pattern:
                mileage *= 1000
            return mileage
    return None

def extract_contact(text: str) -> Optional[str]:
    """Извлечение контактной информации"""
    # Телефон
    phone_pattern = r'(\+7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        return ''.join(phone_match.groups())
    
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        return email_match.group()
    
    return None

def extract_date(text: str) -> Optional[str]:
    """Извлечение даты"""
    patterns = [
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        r'(\d{1,2})\.(\d{1,2})',
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',
        r'завтра',
        r'послезавтра',
        r'сегодня'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            if pattern in ['завтра', 'послезавтра', 'сегодня']:
                return match.group()
            else:
                return match.group()
    return None

def extract_price_range(text: str) -> Tuple[Optional[float], Optional[float]]:
    """Извлечение диапазона цен"""
    patterns = [
        r'от\s*(\d+)\s*до\s*(\d+)',
        r'(\d+)\s*-\s*(\d+)',
        r'цена\s*от\s*(\d+)\s*до\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            min_price = float(match.group(1)) * 1000
            max_price = float(match.group(2)) * 1000
            return min_price, max_price
    
    return None, None

def extract_year_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Извлечение диапазона лет"""
    patterns = [
        r'от\s*(\d{4})\s*до\s*(\d{4})',
        r'(\d{4})\s*-\s*(\d{4})',
        r'год\s*от\s*(\d{4})\s*до\s*(\d{4})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            min_year = int(match.group(1))
            max_year = int(match.group(2))
            if 1990 <= min_year <= max_year <= 2030:
                return min_year, max_year
    
    return None, None

def extract_city(text: str, city_list: List[str]) -> Optional[str]:
    """Извлечение города"""
    text_lower = text.lower()
    
    for city in city_list:
        if city.lower() in text_lower:
            return city
    
    return None 