#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для извлечения автомобильных сущностей с помощью Llama
"""

import json
import re
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union
from functools import lru_cache
from llama_service import generate_with_llama
from db_entity_mapper import DatabaseEntityMapper

logger = logging.getLogger(__name__)

class LlamaEntityExtractor:
    """Извлечение автомобильных сущностей с помощью Llama"""
    
    def __init__(self):
        self.cache = {}
        self.cache_size = 1000
        self.db_mapper = None
        try:
            self.db_mapper = DatabaseEntityMapper()
            self.db_mapper.connect()
        except Exception as e:
            logger.warning(f"Не удалось подключиться к БД для валидации: {e}")
            self.db_mapper = None
        self.entity_prompt = """
Ты - эксперт по извлечению автомобильных сущностей из пользовательских запросов. 
Твоя задача - извлечь ВСЕ характеристики автомобиля из текста и вернуть их ТОЛЬКО в формате JSON.

КРИТИЧЕСКИ ВАЖНО: 
1. Отвечай ТОЛЬКО валидным JSON без дополнительного текста
2. Если в запросе упоминается несколько марок или моделей, извлекай ВСЕ из них!
3. ВСЕГДА используй массивы marks и models для множественных значений
4. НЕ используй одиночные mark и model, только marks и models
5. НЕ добавляй никаких объяснений или текста после JSON

## ИЗВЛЕКАЕМЫЕ СУЩНОСТИ:

### Основные идентификаторы:
- mark (марка): BMW, Mercedes, Toyota, Lada, KIA и т.д. (ТОЛЬКО если одна марка)
- model (модель): X5, Camry, Vesta, Sportage и т.д. (ТОЛЬКО если одна модель)
- vin (VIN-код): 17-символьный код
- manufacture_year (год производства): 2020, 2021, 2022 и т.д.
- model_year (модельный год): может отличаться от года производства
- marks (марки): массив ВСЕХ марок (например, ["BMW", "Mercedes", "Geely", "Jaecoo"])
- models (модели): массив ВСЕХ моделей (например, ["X5", "X3", "Preface", "J7"])

### Внешний вид и кузов:
- body_type (тип кузова): седан, хэтчбек, универсал, внедорожник, кроссовер, купе, кабриолет, пикап
- body_types (типы кузова): массив типов кузова (например, ["седан", "хэтчбек"])
- color (цвет кузова): белый, черный, красный, синий, серый, серебристый, зеленый, желтый, оранжевый, фиолетовый, розовый, коричневый, золотой и т.д.
- colors (цвета кузова): массив цветов (например, ["белый", "черный"])
- interior_color (цвет салона): черный, бежевый, коричневый и т.д.
- door_qty (количество дверей): 2, 3, 4, 5
- seats (количество мест): 2, 4, 5, 7, 8
- dimensions (габариты): в формате "длина x ширина x высота"
- weight (вес): в кг
- cargo_volume (объем багажника): в литрах

### Двигатель и трансмиссия:
- engine (двигатель): описание двигателя
- engine_vol (объем двигателя): 1.6, 2.0, 3.0 и т.д. (в литрах)
- fuel_type (тип топлива): бензин, дизель, гибрид, электрический, газ
- fuel_types (типы топлива): массив типов топлива (например, ["бензин", "дизель"])
- power (мощность): в л.с.
- gear_box_type (тип коробки передач): автомат, механика, вариатор, робот
- gear_box_types (типы коробки передач): массив типов коробки (например, ["автомат", "механика"])
- driving_gear_type (тип привода): передний, задний, полный
- driving_gear_types (типы привода): массив типов привода (например, ["передний", "полный"])

### Производительность и экология:
- fuel_consumption (расход топлива): в л/100км

- max_torque (максимальный крутящий момент): в Нм
- acceleration_0_100 (разгон 0-100): в секундах
- max_speed (максимальная скорость): в км/ч
- eco_class (экологический класс): EURO-5, EURO-6 и т.д.

### Комплектация:
- compl_level (уровень комплектации): базовая, комфорт, люкс и т.д.
- code_compl (код комплектации): буквенно-цифровой код
- option_code (код опции): конкретный код опции (например, S001A, S002A)
- option_description (описание опции): название или описание опции (например, "кондиционер", "кожаный салон", "навигация")
- option_codes (коды опций): массив кодов опций (например, ["S001A", "S002A"])
- option_descriptions (описания опций): массив описаний опций (например, ["кондиционер", "кожаный салон"])

### Для подержанных автомобилей:
- mileage (пробег): в км
- owners_count (количество владельцев): 1, 2, 3 и т.д.
- accident (участие в ДТП): да, нет
- wheel_type (тип руля): левый, правый
- condition (состояние): отличное, хорошее, удовлетворительное, плохое, аварийное, не битый
- region (регион): Москва, Санкт-Петербург, Краснодар, Ростов-на-Дону, Екатеринбург, Новосибирск
- urgency (срочность): срочно, не тороплюсь, в течение недели, в течение месяца, в течение дня

### Цена:
- price_min (минимальная цена): число в рублях
- price_max (максимальная цена): число в рублях
- price (точная цена): число в рублях

### Теги и характеристики:
- budget_tag (бюджетный): дешевый, недорогой, экономичный, доступный
- premium_tag (премиум): дорогой, премиум, люкс, элитный, престижный
- family_tag (семейный): семейный, для семьи, большой, просторный
- sport_tag (спортивный): быстрый, спортивный, мощный, динамичный, скоростной
- city_tag (городской): городской, для города, компактный, маневренный
- offroad_tag (внедорожный): внедорожный, для бездорожья, проходимый
- eco_tag (экологичный): экологичный, экономичный, с низким расходом
- reliable_tag (надежный): надежный, проверенный, качественный, долговечный
- new_tag (новый): новый, свежий, современный, актуальный
- used_tag (подержанный): подержанный, б/у, с пробегом

### Локация:
- city (город): Москва, Санкт-Петербург, Краснодар и т.д.
- cities (города): массив городов (например, ["Москва", "Санкт-Петербург"])

### Управляющие флаги интерфейса:
- show_cars (показывать список автомобилей): true/false. Ставь true, если запрос подразумевает подбор и показ вариантов (например: "найди", "покажи", "подбери"). Ставь false, если запрос — общий вопрос без необходимости показывать карточки.

### Метка намерения (intent):
- intent: "automotive" | "general" | "other"
  - "automotive" — если запрос касается автомобилей, поиска/подбора, характеристик, сравнения, кредитов на авто
  - "general" — если это приветствие, вежливые фразы, "что умеешь" и т.п.
  - "other" — любые темы, не относящиеся к автомобилям

## ПРАВИЛА ИЗВЛЕЧЕНИЯ:

1. Извлекай только те сущности, которые явно упомянуты в тексте
2. Для цен распознавай:
   - "до 2 млн" → price_max: 2000000
   - "от 1.5 млн" → price_min: 1500000
   - "от 1 до 3 млн" → price_min: 1000000, price_max: 3000000
   - "2 миллиона" → price: 2000000
   - "1.5 млн рублей" → price: 1500000
3. Для года распознавай:
   - "2020 года" → manufacture_year: 2020
   - "новый" → manufacture_year: 2024 или 2025
   - "свежий" → manufacture_year: 2023, 2024, 2025
4. Для типа кузова распознавай синонимы:
   - "джип" → body_type: "внедорожник"
   - "хэтч" → body_type: "хэтчбек"
   - "универ" → body_type: "универсал"
5. Для типа топлива:
   - "бензиновый" → fuel_type: "бензин"
   - "дизельный" → fuel_type: "дизель"
   - "электро" → fuel_type: "электрический"
6. Для коробки передач:
   - "автоматическая" → gear_box_type: "автомат"
   - "механическая" → gear_box_type: "механика"
   - "роботизированная" → gear_box_type: "робот"
7. Для цветов распознавай прилагательные и преобразуй в базовую форму:
   - "зеленые", "зеленый", "зеленая" → color: "зеленый"
   - "красные", "красный", "красная" → color: "красный"
   - "синие", "синий", "синяя" → color: "синий"
   - "белые", "белый", "белая" → color: "белый"
   - "черные", "черный", "черная" → color: "черный"
   - "серые", "серый", "серая" → color: "серый"
   - "желтые", "желтый", "желтая" → color: "желтый"
   ВАЖНО: Обращай особое внимание на цвета в запросе!
8. Для привода:
   - "переднеприводный" → driving_gear_type: "передний"
   - "заднеприводный" → driving_gear_type: "задний"
   - "полноприводный" → driving_gear_type: "полный"
9. Для тегов распознавай:
   - "дешевый", "недорогой", "бюджетный", "экономичный" → budget_tag: true
   - "дорогой", "премиум", "люкс", "элитный", "престижный" → premium_tag: true
   - "семейный", "для семьи", "большой", "просторный" → family_tag: true
   - "быстрый", "спортивный", "мощный", "динамичный" → sport_tag: true
   - "городской", "для города", "компактный", "маневренный" → city_tag: true
   - "внедорожный", "для бездорожья", "проходимый" → offroad_tag: true
   - "экологичный", "экономичный", "с низким расходом" → eco_tag: true
   - "надежный", "проверенный", "качественный" → reliable_tag: true
   - "новый", "свежий", "современный" → new_tag: true
   - "подержанный", "б/у", "с пробегом" → used_tag: true
10. Для опций распознавай:
   - "кондиционер", "климат-контроль", "климат" → option_description: "кондиционер"
   - "кожаный салон", "кожа", "кожаные сиденья" → option_description: "кожаный салон"
   - "навигация", "навигационная система", "GPS" → option_description: "навигация"
   - "камера заднего вида", "камера", "парктроник" → option_description: "камера заднего вида"
   - "подогрев сидений", "подогрев", "обогрев сидений" → option_description: "подогрев сидений"
   - "круиз-контроль", "круиз" → option_description: "круиз-контроль"
   - "ксенон", "ксеноновые фары", "LED фары" → option_description: "ксеноновые фары"
   - "люк", "панорамная крыша", "крыша" → option_description: "люк"
   - "мультируль", "мультифункциональный руль" → option_description: "мультируль"
   - "сигнализация", "охранная система" → option_description: "сигнализация"
   
   ВАЖНО: Если в запросе несколько опций, используй option_descriptions как массив:
   - "с навигацией и подогревом" → option_descriptions: ["навигация", "подогрев сидений"]
   - "с кондиционером, кожаным салоном и люком" → option_descriptions: ["кондиционер", "кожаный салон", "люк"]
11. Для множественных сущностей используй массивы:
   - "BMW и Mercedes" → marks: ["BMW", "Mercedes"]
   - "белые и черные" → colors: ["белый", "черный"]
   - "седаны и хэтчбеки" → body_types: ["седан", "хэтчбек"]
   - "бензин и дизель" → fuel_types: ["бензин", "дизель"]
   - "автомат и механика" → gear_box_types: ["автомат", "механика"]
   - "передний и полный привод" → driving_gear_types: ["передний", "полный"]
   - "Москва и СПб" → cities: ["Москва", "Санкт-Петербург"]
12. Для новых сущностей распознавай:
   - Пробег: "до 50к км", "менее 100 тысяч", "пробег 30к" → mileage: 50000, 100000, 30000
   - Владельцы: "первый владелец", "один хозяин", "2 владельца" → owners_count: 1, 1, 2
   - Состояние: "битый", "не битый", "аварийный", "целый" → condition: "аварийное", "не битый", "аварийное", "не битый"
   - Регион: "Москва", "СПб", "Краснодарский край" → region: "Москва", "Санкт-Петербург", "Краснодар"
   - Срочность: "срочно", "не тороплюсь", "в течение недели" → urgency: "срочно", "не тороплюсь", "в течение недели"

## ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО валидный JSON без дополнительного текста:

{
  "mark": "BMW",
  "model": "X5",
  "manufacture_year": 2023,
  "body_type": "внедорожник",
  "color": "черный",
  "fuel_type": "бензин",
  "engine_vol": 3.0,
  "power": 340,
  "gear_box_type": "автомат",
  "driving_gear_type": "полный",
  "price_min": 5000000,
  "price_max": 7000000,
  "seats": 5,
  "budget_tag": true,
  "family_tag": true
  , "show_cars": true
  , "intent": "automotive"
}

Если сущность не найдена, не включай её в JSON.

## ПРИМЕРЫ:

Запрос: "Найди черный BMW X5 2023 года с автоматом до 7 млн"
Ответ: {"mark": "BMW", "model": "X5", "manufacture_year": 2023, "color": "черный", "gear_box_type": "автомат", "price_max": 7000000}

Запрос: "Покажи красные седаны от 2 до 4 млн"
Ответ: {"body_type": "седан", "color": "красный", "price_min": 2000000, "price_max": 4000000, "show_cars": true, "intent": "automotive"}

Запрос: "Покажи зеленые автомобили"
Ответ: {"color": "зеленый", "show_cars": true, "intent": "automotive"}

Запрос: "Найди синие кроссоверы"
Ответ: {"body_type": "кроссовер", "color": "синий", "show_cars": true, "intent": "automotive"}

Запрос: "Нужен дизельный внедорожник с полным приводом"
Ответ: {"fuel_type": "дизель", "body_type": "внедорожник", "driving_gear_type": "полный", "show_cars": true, "intent": "automotive"}

Запрос: "Найди BMW с кожаным салоном и навигацией"
Ответ: {"mark": "BMW", "option_description": "кожаный салон", "show_cars": true, "intent": "automotive"}

Запрос: "сравни Geely Preface и Jaecoo J7"
Ответ: {"marks": ["Geely", "Jaecoo"], "models": ["Preface", "J7"], "show_cars": true, "intent": "automotive"}

Запрос: "Что лучше BMW X5 или Mercedes GLE?"
Ответ: {"marks": ["BMW", "Mercedes"], "models": ["X5", "GLE"], "show_cars": true, "intent": "automotive"}

Запрос: "Покажи BMW X5"
Ответ: {"marks": ["BMW"], "models": ["X5"], "show_cars": true, "intent": "automotive"}

Запрос: "Покажи седаны с кондиционером и подогревом сидений"
Ответ: {"body_type": "седан", "option_descriptions": ["кондиционер", "подогрев сидений"], "show_cars": true, "intent": "automotive"}

Запрос: "Найди BMW с кожаным салоном, навигацией и люком"
Ответ: {"mark": "BMW", "option_descriptions": ["кожаный салон", "навигация", "люк"], "show_cars": true, "intent": "automotive"}

Запрос: "Покажи BMW и Mercedes"
Ответ: {"marks": ["BMW", "Mercedes"], "show_cars": true, "intent": "automotive"}

Запрос: "Найди белые и черные седаны"
Ответ: {"colors": ["белый", "черный"], "body_type": "седан", "show_cars": true, "intent": "automotive"}

Запрос: "Покажи седаны и хэтчбеки с бензином и дизелем"
Ответ: {"body_types": ["седан", "хэтчбек"], "fuel_types": ["бензин", "дизель"], "show_cars": true, "intent": "automotive"}

Запрос: "Ищу машину для семьи, 7 мест, до 3 млн"
Ответ: {"seats": 7, "price_max": 3000000, "family_tag": true}

Запрос: "Нужен дешевый городской автомобиль"
Ответ: {"budget_tag": true, "city_tag": true}

Запрос: "Покажи быстрые спортивные машины"
Ответ: {"sport_tag": true}

Запрос: "Ищу надежный премиум внедорожник"
Ответ: {"reliable_tag": true, "premium_tag": true, "offroad_tag": true}

Запрос: "BMW с пробегом до 50к км, первый владелец"
Ответ: {"mark": "BMW", "mileage": 50000, "owners_count": 1, "show_cars": true, "intent": "automotive"}

Запрос: "Продаю битый Mercedes в Москве, срочно"
Ответ: {"mark": "Mercedes", "condition": "аварийное", "region": "Москва", "urgency": "срочно", "show_cars": true, "intent": "automotive"}

Запрос: "Ищу не битый автомобиль в СПб, не тороплюсь"
Ответ: {"condition": "не битый", "region": "Санкт-Петербург", "urgency": "не тороплюсь", "show_cars": true, "intent": "automotive"}

Теперь извлеки сущности из следующего запроса:
"""


    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Извлекает автомобильные сущности из запроса с помощью Llama
        
        Args:
            query: Пользовательский запрос
            
        Returns:
            Словарь с извлеченными сущностями
        """
        try:
            # Формируем полный промт
            full_prompt = f"{self.entity_prompt}\n\nЗапрос: {query}\n\nJSON:"
            
            # Получаем ответ от Llama
            response = generate_with_llama(full_prompt)
            
            # Очищаем ответ от лишнего текста
            response = response.strip()
            
            # Ищем JSON в ответе (более строгий поиск)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if not json_match:
                # Пробуем найти JSON с вложенными объектами
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    entities = json.loads(json_str)
                except json.JSONDecodeError:
                    # Если JSON невалидный, пробуем исправить
                    json_str = json_str.replace("'", '"')  # Заменяем одинарные кавычки
                    try:
                        entities = json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Не удалось распарсить JSON: {json_str}")
                        return {"intent": self._infer_intent_local(query)}
                
                # Валидируем, нормализуем и удаляем неупомянутые сущности, основываясь на исходном запросе
                entities = self._validate_and_normalize_entities(entities, query)
                
                # Валидация с базой данных
                entities = self._validate_with_database(entities)
                
                # Грубая подстраховка для intent, если Llama не вернула
                if 'intent' not in entities:
                    entities['intent'] = self._infer_intent_local(query)
                
                logger.info(f"Извлечены сущности: {entities}")
                return entities
            else:
                logger.warning(f"JSON не найден в ответе Llama: {response}")
                # Пробуем извлечь сущности с помощью регулярных выражений
                entities = self._extract_entities_with_regex(query)
                if entities:
                    return entities
                return {"intent": self._infer_intent_local(query)}
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}, ответ: {response}")
            return {"intent": self._infer_intent_local(query)}
        except Exception as e:
            logger.error(f"Ошибка извлечения сущностей: {e}")
            return {}

    def _validate_and_normalize_entities(self, entities: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Валидирует и нормализует извлеченные сущности
        
        Args:
            entities: Словарь с сущностями
            query: Исходный текст запроса пользователя
            
        Returns:
            Нормализованный словарь сущностей
        """
        normalized = {}
        q_lower = (query or "").lower()
        
        # Словари для нормализации
        body_type_mapping = {
            'джип': 'внедорожник',
            'хэтч': 'хэтчбек',
            'универ': 'универсал',
            'кросс': 'кроссовер',
            'кабри': 'кабриолет'
        }
        
        fuel_type_mapping = {
            'бензиновый': 'бензин',
            'дизельный': 'дизель',
            'электро': 'электрический',
            'электромобиль': 'электрический'
        }
        
        gear_box_mapping = {
            'автоматическая': 'автомат',
            'механическая': 'механика',
            'роботизированная': 'робот',
            'вариаторная': 'вариатор'
        }
        
        drive_type_mapping = {
            'переднеприводный': 'передний',
            'заднеприводный': 'задний',
            'полноприводный': 'полный',
            '4wd': 'полный',
            'awd': 'полный',
            'fwd': 'передний',
            'rwd': 'задний'
        }
        
        # Допустимые ключи
        allowed_keys = {
            'mark','model','vin','manufacture_year','model_year',
            'body_type','color','interior_color','door_qty','seats','dimensions','weight','cargo_volume',
            'engine','engine_vol','fuel_type','power','gear_box_type','driving_gear_type',
            'fuel_consumption','max_torque','acceleration_0_100','max_speed','eco_class',
            'compl_level','code_compl','option_code','option_description','option_codes','option_descriptions',
            'mileage','owners_count','accident','wheel_type',
            'price_min','price_max','price',
            'budget_tag','premium_tag','family_tag','sport_tag','city_tag','offroad_tag','eco_tag','reliable_tag','new_tag','used_tag',
            'show_cars','intent',
            'city',
            # Множественные сущности
            'marks','models','colors','body_types','fuel_types','gear_box_types','driving_gear_types','cities',
            # Новые сущности
            'mileage','owners_count','condition','region','urgency'
        }

        # Триггеры наличия признаков в тексте
        def grounded(key: str, val: Any) -> bool:
            if key in ['show_cars','intent']:
                return True
            if key in ['mark','model']:
                if not isinstance(val, str) or not val:
                    return False
                v = val.lower().replace(' ', '')
                return v and (v in q_lower.replace(' ', ''))
            if key in ['manufacture_year','model_year']:
                try:
                    y = int(val)
                except Exception:
                    return False
                return str(y) in q_lower
            if key in ['price_min','price_max','price']:
                # Должны быть триггеры цены
                has_price_tokens = any(tok in q_lower for tok in ['млн','миллион','тыс','тысяч','руб','₽','цена','стоимость','до','от']) or bool(re.search(r"\d\s*[\.,]?\d*\s*(млн|тыс)", q_lower))
                if not has_price_tokens:
                    return False
                # Семантика диапазона: если только 'до' — не оставляем price_min; если только 'от' — не оставляем price_max
                if key == 'price_min' and ('до' in q_lower and 'от' not in q_lower):
                    return False
                if key == 'price_max' and ('от' in q_lower and 'до' not in q_lower):
                    return False
                return True
            if key in ['mileage']:
                return any(tok in q_lower for tok in ['пробег','км'])
            if key in ['seats']:
                return ('мест' in q_lower) or bool(re.search(r"\b[2-9]\s*мест", q_lower))
            if key == 'body_type':
                return any(k in q_lower for k in ['седан','хэтч','хэтчбек','универсал','внедорожник','кроссовер','купе','кабриолет','пикап','джип'])
            if key == 'fuel_type':
                return any(k in q_lower for k in ['бензин','дизель','гибрид','электро','электрический','газ'])
            if key == 'gear_box_type':
                return any(k in q_lower for k in ['автомат','механика','вариатор','робот'])
            if key == 'driving_gear_type':
                return any(k in q_lower for k in ['передний привод','задний привод','полный привод','4wd','awd','fwd','rwd','передний','задний','полный'])
            if key == 'color':
                return any(k in q_lower for k in ['белый','черный','красный','синий','серый','серебристый','зеленый','желтый','оранжевый','коричневый','бежевый'])
            if key == 'city':
                return 'в ' in q_lower or 'город' in q_lower
            # Теги — проверяем по словарям ниже после нормализации
            if key.endswith('_tag'):
                return True
            # Прочие числовые/технические — требуем явных упоминаний общих терминов
            generic_tokens = ['двигател', 'мотор', 'мощност', 'объем', 'разгон', 'эколог', 'евро', 'комплектаци']
            return any(tok in q_lower for tok in generic_tokens)

        # Нормализуем каждую сущность
        for key, value in entities.items():
            if key not in allowed_keys:
                continue
            if value is None or value == "":
                continue
            # Поддержка списков для множественных полей
            if key in ['marks','models','cities','body_types','colors']:
                if isinstance(value, list):
                    collected = []
                    for item in value:
                        if isinstance(item, str):
                            item_norm = item.strip()
                            if not item_norm:
                                continue
                            if grounded(key[:-1] if key.endswith('s') else key, item_norm):
                                collected.append(item_norm)
                    if collected:
                        normalized[key] = collected
                # если не список — пропустим
                continue
                
            # Нормализация строковых значений
            if isinstance(value, str):
                value = value.strip().lower()
                
                # Применяем маппинги
                if key == 'body_type' and value in body_type_mapping:
                    value = body_type_mapping[value]
                elif key == 'fuel_type' and value in fuel_type_mapping:
                    value = fuel_type_mapping[value]
                elif key == 'gear_box_type' and value in gear_box_mapping:
                    value = gear_box_mapping[value]
                elif key == 'driving_gear_type' and value in drive_type_mapping:
                    value = drive_type_mapping[value]
                elif key == 'color':
                    # Нормализация цветов
                    color_mapping = {
                        'белый': 'белый',
                        'черный': 'черный',
                        'красный': 'красный',
                        'синий': 'синий',
                        'серый': 'серый',
                        'серебристый': 'серебристый',
                        'зеленый': 'зеленый',
                        'желтый': 'желтый',
                        'оранжевый': 'оранжевый',
                        'коричневый': 'коричневый',
                        'бежевый': 'бежевый'
                    }
                    if value in color_mapping:
                        value = color_mapping[value]
                        
            # Валидация числовых значений
            elif isinstance(value, (int, float)):
                if key in ['price_min', 'price_max', 'price'] and value < 0:
                    continue  # Пропускаем отрицательные цены
                elif key in ['manufacture_year', 'model_year'] and (value < 1990 or value > 2030):
                    continue  # Пропускаем нереалистичные годы
                elif key in ['engine_vol'] and (value < 0.5 or value > 10):
                    continue  # Пропускаем нереалистичные объемы
                elif key in ['power'] and (value < 50 or value > 1000):
                    continue  # Пропускаем нереалистичную мощность
                elif key in ['seats'] and (value < 2 or value > 9):
                    continue  # Пропускаем нереалистичное количество мест
                    
            # Убираем поля, которые не подтверждены в исходном запросе
            if not grounded(key, value):
                continue

            normalized[key] = value
            
        # Теги перепроверяем по ключевым словам (чтобы не тащить лишние)
        tag_mappings = {
            'budget_tag': ['дешев', 'недорог', 'бюджет', 'эконом'],
            'premium_tag': ['премиум', 'люкс', 'элит', 'престиж'],
            'family_tag': ['семей', 'для семьи', '7 мест', 'семь мест', 'просторн'],
            'sport_tag': ['спорт', 'быстр', 'мощн', 'динамич'],
            'city_tag': ['город', 'городск', 'компакт', 'маневрен'],
            'offroad_tag': ['внедорож', 'бездорож', 'проходим', 'джип'],
            'eco_tag': ['эко', 'эколог', 'низким расходом', 'экономич'],
            'reliable_tag': ['надежн', 'проверенн', 'качеств', 'долговеч'],
            'new_tag': ['новый', 'свеж', 'современ', 'актуаль'],
            'used_tag': ['подерж', 'б/у', 'с пробегом', 'бу']
        }
        for tag_key, keywords in tag_mappings.items():
            if tag_key in normalized:
                if not any(kw in q_lower for kw in keywords):
                    normalized.pop(tag_key, None)

        # Бэкап одиночных полей для обратной совместимости
        if 'mark' not in normalized and isinstance(normalized.get('marks'), list) and len(normalized['marks']) == 1:
            normalized['mark'] = normalized['marks'][0]
        if 'model' not in normalized and isinstance(normalized.get('models'), list) and len(normalized['models']) == 1:
            normalized['model'] = normalized['models'][0]
        if 'city' not in normalized and isinstance(normalized.get('cities'), list) and len(normalized['cities']) == 1:
            normalized['city'] = normalized['cities'][0]
        if 'body_type' not in normalized and isinstance(normalized.get('body_types'), list) and len(normalized['body_types']) == 1:
            normalized['body_type'] = normalized['body_types'][0]
        if 'color' not in normalized and isinstance(normalized.get('colors'), list) and len(normalized['colors']) == 1:
            normalized['color'] = normalized['colors'][0]

        return normalized

    def _extract_color_fallback(self, query: str) -> str:
        """Извлекает цвет с помощью регулярных выражений"""
        query_lower = query.lower()
        
        # Словарь цветов с вариациями
        color_patterns = {
            'белый': ['белый', 'белая', 'белое', 'белые', 'белых', 'белым'],
            'черный': ['черный', 'черная', 'черное', 'черные', 'черных', 'черным'],
            'серый': ['серый', 'серая', 'серое', 'серые', 'серых', 'серым', 'серебристый', 'серебристая'],
            'красный': ['красный', 'красная', 'красное', 'красные', 'красных', 'красным'],
            'синий': ['синий', 'синяя', 'синее', 'синие', 'синих', 'синим'],
            'зеленый': ['зеленый', 'зеленая', 'зеленое', 'зеленые', 'зеленых', 'зеленым'],
            'желтый': ['желтый', 'желтая', 'желтое', 'желтые', 'желтых', 'желтым'],
            'оранжевый': ['оранжевый', 'оранжевая', 'оранжевое', 'оранжевые', 'оранжевых', 'оранжевым'],
            'фиолетовый': ['фиолетовый', 'фиолетовая', 'фиолетовое', 'фиолетовые', 'фиолетовых', 'фиолетовым'],
            'розовый': ['розовый', 'розовая', 'розовое', 'розовые', 'розовых', 'розовым'],
            'коричневый': ['коричневый', 'коричневая', 'коричневое', 'коричневые', 'коричневых', 'коричневым'],
            'бежевый': ['бежевый', 'бежевая', 'бежевое', 'бежевые', 'бежевых', 'бежевым'],
            'золотой': ['золотой', 'золотая', 'золотое', 'золотые', 'золотых', 'золотым']
        }
        
        # Проверяем каждый цвет
        for base_color, variations in color_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    return base_color
        
        return None
    
    def _extract_drive_fallback(self, query: str) -> str:
        """Извлекает тип привода с помощью регулярных выражений"""
        query_lower = query.lower()
        
        # Проверяем на полный привод (чем более специфичные термины, тем выше приоритет)
        if any(word in query_lower for word in ['полный привод', 'полноприводн', '4wd', 'awd', '4x4', 'с полным приводом', 'полным приводом']):
            return 'полный'
        
        # Проверяем на передний привод
        if any(word in query_lower for word in ['передний привод', 'переднеприводн', 'fwd', 'с передним приводом', 'передним приводом']):
            return 'передний'
        
        # Проверяем на задний привод
        if any(word in query_lower for word in ['задний привод', 'заднеприводн', 'rwd', 'с задним приводом', 'задним приводом']):
            return 'задний'
        
        return None
    
    def _extract_option_fallback(self, query: str) -> str:
        """Извлекает опции с помощью регулярных выражений"""
        query_lower = query.lower()
        
        # Словарь опций с вариациями
        option_patterns = {
            'кондиционер': ['кондиционер', 'климат-контроль', 'климат', 'кондиционером', 'с кондиционером'],
            'кожаный салон': ['кожаный салон', 'кожа', 'кожаные сиденья', 'кожаный', 'кожаные'],
            'навигация': ['навигация', 'навигационная система', 'gps', 'навигацией', 'с навигацией'],
            'камера заднего вида': ['камера заднего вида', 'камера', 'парктроник', 'камерой', 'с камерой'],
            'подогрев сидений': ['подогрев сидений', 'подогрев', 'обогрев сидений', 'подогревом', 'с подогревом'],
            'круиз-контроль': ['круиз-контроль', 'круиз', 'круизом', 'с круиз-контролем'],
            'ксеноновые фары': ['ксенон', 'ксеноновые фары', 'led фары', 'ксеноновыми', 'с ксеноном'],
            'люк': ['люк', 'панорамная крыша', 'крыша', 'люком', 'с люком'],
            'мультируль': ['мультируль', 'мультифункциональный руль', 'мультирулем', 'с мультирулем'],
            'сигнализация': ['сигнализация', 'охранная система', 'сигнализацией', 'с сигнализацией'],
            'подогрев руля': ['подогрев руля', 'подогревом руля', 'с подогревом руля'],
            'электростеклоподъемники': ['электростеклоподъемники', 'электростекла', 'электростеклами'],
            'центральный замок': ['центральный замок', 'центральным замком', 'с центральным замком'],
            'иммобилайзер': ['иммобилайзер', 'иммобилайзером', 'с иммобилайзером'],
            'ABS': ['abs', 'антиблокировочная система', 'антиблокировочной системой'],
            'ESP': ['esp', 'система стабилизации', 'системой стабилизации'],
            'подушки безопасности': ['подушки безопасности', 'подушками безопасности', 'airbag'],
            'контроль тяги': ['контроль тяги', 'контролем тяги', 'tcs'],
            'датчики парковки': ['датчики парковки', 'парктроник', 'датчиками парковки'],
            'противотуманные фары': ['противотуманные фары', 'противотуманками', 'противотуманными фарами']
        }
        
        # Проверяем каждую опцию
        for base_option, variations in option_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    return base_option
        
        return None
    
    def _extract_multiple_options_fallback(self, query: str) -> List[str]:
        """Извлекает несколько опций с помощью регулярных выражений"""
        query_lower = query.lower()
        found_options = []
        
        # Словарь опций с вариациями
        option_patterns = {
            'кондиционер': ['кондиционер', 'климат-контроль', 'климат', 'кондиционером', 'с кондиционером'],
            'кожаный салон': ['кожаный салон', 'кожа', 'кожаные сиденья', 'кожаный', 'кожаные'],
            'навигация': ['навигация', 'навигационная система', 'gps', 'навигацией', 'с навигацией'],
            'камера заднего вида': ['камера заднего вида', 'камера', 'парктроник', 'камерой', 'с камерой'],
            'подогрев сидений': ['подогрев сидений', 'подогрев', 'обогрев сидений', 'подогревом', 'с подогревом'],
            'круиз-контроль': ['круиз-контроль', 'круиз', 'круизом', 'с круиз-контролем'],
            'ксеноновые фары': ['ксенон', 'ксеноновые фары', 'led фары', 'ксеноновыми', 'с ксеноном'],
            'люк': ['люк', 'панорамная крыша', 'крыша', 'люком', 'с люком'],
            'мультируль': ['мультируль', 'мультифункциональный руль', 'мультирулем', 'с мультирулем'],
            'сигнализация': ['сигнализация', 'охранная система', 'сигнализацией', 'с сигнализацией'],
            'подогрев руля': ['подогрев руля', 'подогревом руля', 'с подогревом руля'],
            'электростеклоподъемники': ['электростеклоподъемники', 'электростекла', 'электростеклами'],
            'центральный замок': ['центральный замок', 'центральным замком', 'с центральным замком'],
            'иммобилайзер': ['иммобилайзер', 'иммобилайзером', 'с иммобилайзером'],
            'ABS': ['abs', 'антиблокировочная система', 'антиблокировочной системой'],
            'ESP': ['esp', 'система стабилизации', 'системой стабилизации'],
            'подушки безопасности': ['подушки безопасности', 'подушками безопасности', 'airbag'],
            'контроль тяги': ['контроль тяги', 'контролем тяги', 'tcs'],
            'датчики парковки': ['датчики парковки', 'парктроник', 'датчиками парковки'],
            'противотуманные фары': ['противотуманные фары', 'противотуманками', 'противотуманными фарами']
        }
        
        # Проверяем каждую опцию
        for base_option, variations in option_patterns.items():
            for variation in variations:
                if variation in query_lower and base_option not in found_options:
                    found_options.append(base_option)
                    break  # Переходим к следующей опции, чтобы избежать дублирования
        
        return found_options
    
    def _extract_multiple_entities_fallback(self, query: str, entities: Dict[str, Any]) -> None:
        """Извлекает множественные сущности с помощью регулярных выражений"""
        query_lower = query.lower()
        
        # Извлекаем множественные марки
        if 'marks' not in entities and 'mark' not in entities:
            marks = self._extract_multiple_brands_fallback(query)
            if marks:
                if len(marks) == 1:
                    entities['mark'] = marks[0]
                else:
                    entities['marks'] = marks
        
        # Извлекаем множественные цвета
        if 'colors' not in entities and 'color' not in entities:
            colors = self._extract_multiple_colors_fallback(query)
            if colors:
                if len(colors) == 1:
                    entities['color'] = colors[0]
                else:
                    entities['colors'] = colors
        
        # Извлекаем множественные типы кузова
        if 'body_types' not in entities and 'body_type' not in entities:
            body_types = self._extract_multiple_body_types_fallback(query)
            if body_types:
                if len(body_types) == 1:
                    entities['body_type'] = body_types[0]
                else:
                    entities['body_types'] = body_types
        
        # Извлекаем множественные типы топлива
        if 'fuel_types' not in entities and 'fuel_type' not in entities:
            fuel_types = self._extract_multiple_fuel_types_fallback(query)
            if fuel_types:
                if len(fuel_types) == 1:
                    entities['fuel_type'] = fuel_types[0]
                else:
                    entities['fuel_types'] = fuel_types
        
        # Извлекаем множественные опции
        if 'option_descriptions' not in entities and 'option_description' not in entities and 'option_codes' not in entities and 'option_code' not in entities:
            options = self._extract_multiple_options_fallback(query)
            if options:
                if len(options) == 1:
                    entities['option_description'] = options[0]
                else:
                    entities['option_descriptions'] = options
        
        # Извлекаем новые сущности
        if 'mileage' not in entities:
            mileage = self._extract_mileage_fallback(query)
            if mileage:
                entities['mileage'] = mileage
        
        if 'owners_count' not in entities:
            owners = self._extract_owners_fallback(query)
            if owners:
                entities['owners_count'] = owners
        
        if 'condition' not in entities:
            condition = self._extract_condition_fallback(query)
            if condition:
                entities['condition'] = condition
        
        if 'region' not in entities:
            region = self._extract_region_fallback(query)
            if region:
                logger.info(f"Извлечен регион из fallback: {region} для запроса: {query}")
                entities['region'] = region
            else:
                logger.info(f"Регион не найден в запросе: {query}")
        
        if 'urgency' not in entities:
            urgency = self._extract_urgency_fallback(query)
            if urgency:
                entities['urgency'] = urgency
        
        # Валидация с базой данных для fallback
        entities = self._validate_with_database(entities)
    
    def _extract_multiple_brands_fallback(self, query: str) -> List[str]:
        """Извлекает множественные марки"""
        query_lower = query.lower()
        found_brands = []
        
        # Словарь марок с вариациями (на основе реальных данных из БД)
        brand_patterns = {
            'BMW': ['bmw', 'бмв'],
            'AUDI': ['audi', 'ауди'],
            'Toyota': ['toyota', 'тойота'],
            'Hyundai': ['hyundai', 'хендай', 'хендай'],
            'KIA': ['kia', 'киа'],
            'Lada': ['lada', 'лада', 'ваз'],
            'Nissan': ['nissan', 'ниссан'],
            'Honda': ['honda', 'хонда'],
            'Mazda': ['mazda', 'мазда'],
            'Skoda': ['skoda', 'шкода'],
            'Renault': ['renault', 'рено'],
            'Peugeot': ['peugeot', 'пежо'],
            'Citroen': ['citroen', 'ситроен'],
            'DONGFENG': ['dongfeng', 'донгфенг'],
            'Chery': ['chery', 'чери'],
            'BYD': ['byd', 'би-вай-ди'],
            'Geely': ['geely', 'джили'],
            'Haval': ['haval', 'хавал'],
            'Ford': ['ford', 'форд'],
            'Chevrolet': ['chevrolet', 'шевроле'],
            'Ford': ['ford', 'форд'],
            'Chevrolet': ['chevrolet', 'шевроле', 'шев'],
            'Opel': ['opel', 'опель']
        }
        
        # Проверяем каждую марку
        for base_brand, variations in brand_patterns.items():
            for variation in variations:
                if variation in query_lower and base_brand not in found_brands:
                    found_brands.append(base_brand)
                    break
        
        return found_brands
    
    def _extract_multiple_colors_fallback(self, query: str) -> List[str]:
        """Извлекает множественные цвета"""
        query_lower = query.lower()
        found_colors = []
        
        # Словарь цветов с вариациями
        color_patterns = {
            'белый': ['белый', 'белая', 'белое', 'белые', 'белых', 'белым'],
            'черный': ['черный', 'черная', 'черное', 'черные', 'черных', 'черным'],
            'серый': ['серый', 'серая', 'серое', 'серые', 'серых', 'серым', 'серебристый', 'серебристая'],
            'красный': ['красный', 'красная', 'красное', 'красные', 'красных', 'красным'],
            'синий': ['синий', 'синяя', 'синее', 'синие', 'синих', 'синим'],
            'зеленый': ['зеленый', 'зеленая', 'зеленое', 'зеленые', 'зеленых', 'зеленым'],
            'желтый': ['желтый', 'желтая', 'желтое', 'желтые', 'желтых', 'желтым'],
            'оранжевый': ['оранжевый', 'оранжевая', 'оранжевое', 'оранжевые', 'оранжевых', 'оранжевым'],
            'фиолетовый': ['фиолетовый', 'фиолетовая', 'фиолетовое', 'фиолетовые', 'фиолетовых', 'фиолетовым'],
            'розовый': ['розовый', 'розовая', 'розовое', 'розовые', 'розовых', 'розовым'],
            'коричневый': ['коричневый', 'коричневая', 'коричневое', 'коричневые', 'коричневых', 'коричневым'],
            'бежевый': ['бежевый', 'бежевая', 'бежевое', 'бежевые', 'бежевых', 'бежевым'],
            'золотой': ['золотой', 'золотая', 'золотое', 'золотые', 'золотых', 'золотым']
        }
        
        # Проверяем каждый цвет
        for base_color, variations in color_patterns.items():
            for variation in variations:
                if variation in query_lower and base_color not in found_colors:
                    found_colors.append(base_color)
                    break
        
        return found_colors
    
    def _extract_multiple_body_types_fallback(self, query: str) -> List[str]:
        """Извлекает множественные типы кузова"""
        query_lower = query.lower()
        found_body_types = []
        
        # Словарь типов кузова с вариациями
        body_type_patterns = {
            'Седан': ['седан', 'седаны', 'седанов', 'седана', 'седаном'],
            'Хетчбэк': ['хэтчбек', 'хэтчбеки', 'хэтч', 'хэтчи', 'хэтчбеков'],
            'Универсал': ['универсал', 'универсалы', 'универ', 'универсалов'],
            'Внедорожник': ['внедорожник', 'внедорожники', 'джип', 'джипы', 'suv', 'внедорожников'],
            'Кроссовер': ['кроссовер', 'кроссоверы', 'кросс', 'кроссоверов'],
            'Купе': ['купе', 'купе'],
            'Кабриолет': ['кабриолет', 'кабриолеты', 'кабрио', 'кабриолетов'],
            'Пикап': ['пикап', 'пикапы', 'пикап', 'пикапов'],
            'Лифтбэк': ['лифтбек', 'лифтбэки', 'лифтбеков'],
            'Минивэн': ['минивен', 'минивэны', 'минивэн', 'минивэнов'],
            'Микроавтобус': ['микроавтобус', 'микроавтобусы', 'микроавтобусов']
        }
        
        # Проверяем каждый тип кузова
        for base_type, variations in body_type_patterns.items():
            for variation in variations:
                if variation in query_lower and base_type not in found_body_types:
                    found_body_types.append(base_type)
                    break
        
        return found_body_types
    
    def _extract_multiple_fuel_types_fallback(self, query: str) -> List[str]:
        """Извлекает множественные типы топлива"""
        query_lower = query.lower()
        found_fuel_types = []
        
        # Словарь типов топлива с вариациями
        fuel_type_patterns = {
            'бензин': ['бензин', 'бензиновый', 'бензиновая', 'бензиновое', 'бензиновые', 'бензином'],
            'дизель': ['дизель', 'дизельный', 'дизельная', 'дизельное', 'дизельные', 'дизелем'],
            'гибрид': ['гибрид', 'гибридный', 'гибридная', 'гибридное', 'гибридные', 'гибридом'],
            'электрический': ['электрический', 'электрическая', 'электрическое', 'электрические', 'электро', 'электромобиль', 'электрическим'],
            'газ': ['газ', 'газовый', 'газовая', 'газовое', 'газовые', 'газобаллонный', 'газом'],
            'Бензин': ['бензин', 'бензиновый', 'бензиновая', 'бензиновое', 'бензиновые', 'бензином'],
            'Дизель': ['дизель', 'дизельный', 'дизельная', 'дизельное', 'дизельные', 'дизелем'],
            'Гибрид': ['гибрид', 'гибридный', 'гибридная', 'гибридное', 'гибридные', 'гибридом'],
            'Электрический': ['электрический', 'электрическая', 'электрическое', 'электрические', 'электро', 'электромобиль', 'электрическим']
        }
        
        # Проверяем каждый тип топлива
        for base_type, variations in fuel_type_patterns.items():
            for variation in variations:
                if variation in query_lower and base_type not in found_fuel_types:
                    found_fuel_types.append(base_type)
                    break
        
        return found_fuel_types
    
    def _extract_mileage_fallback(self, query: str) -> Optional[int]:
        """Извлекает пробег с помощью регулярных выражений"""
        query_lower = query.lower()
        
        # Паттерны для пробега
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:к|тыс|тысяч)\s*км',
            r'(\d+(?:[.,]\d+)?)\s*км',
            r'до\s*(\d+(?:[.,]\d+)?)\s*(?:к|тыс|тысяч)',
            r'менее\s*(\d+(?:[.,]\d+)?)\s*(?:к|тыс|тысяч)',
            r'не\s*более\s*(\d+(?:[.,]\d+)?)\s*(?:к|тыс|тысяч)',
            r'пробег\s*(\d+(?:[.,]\d+)?)\s*(?:к|тыс|тысяч)?',
            r'(\d+(?:[.,]\d+)?)\s*(?:тыс|тысяч)\s*км'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = float(match.group(1).replace(',', '.'))
                # Конвертируем в км
                if 'тыс' in match.group(0) or 'тысяч' in match.group(0):
                    value *= 1000
                return int(value)
        
        return None
    
    def _extract_owners_fallback(self, query: str) -> Optional[int]:
        """Извлекает количество владельцев"""
        query_lower = query.lower()
        
        # Паттерны для владельцев
        patterns = [
            r'(\d+)\s*(?:владелец|хозяин|собственник)',
            r'(\d+)\s*(?:рука|руки)',
            r'первый\s*владелец',
            r'один\s*хозяин',
            r'не\s*более\s*(\d+)\s*(?:владельцев|хозяев)',
            r'(\d+)\s*(?:владельцев|хозяев)',
            r'(\d+)\s*(?:руки|рука)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                if 'первый' in match.group(0) or 'один' in match.group(0):
                    return 1
                return int(match.group(1))
        
        return None
    
    def _extract_condition_fallback(self, query: str) -> Optional[str]:
        """Извлекает состояние автомобиля"""
        query_lower = query.lower()
        
        # Словарь состояний
        condition_patterns = {
            'отличное': ['отличное', 'идеальное', 'прекрасное', 'отлично', 'идеально'],
            'хорошее': ['хорошее', 'нормальное', 'приличное', 'хорошо', 'нормально'],
            'удовлетворительное': ['удовлетворительное', 'среднее', 'средне'],
            'плохое': ['плохое', 'ужасное', 'плохо', 'ужасно'],
            'аварийное': ['аварийное', 'битый', 'побитый', 'в дтп', 'авария', 'аварийный'],
            'не битый': ['не битый', 'не побитый', 'целый', 'без дтп', 'не аварийный', 'не бит']
        }
        
        for condition, variations in condition_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    return condition
        
        return None
    
    def _extract_region_fallback(self, query: str) -> Optional[str]:
        """Извлекает регион только если он упоминается в запросе"""
        query_lower = query.lower()
        
        # Словарь регионов
        region_patterns = {
            'Москва': ['москва', 'мск', 'московская область', 'мо', 'подмосковье', 'московский'],
            'Санкт-Петербург': ['спб', 'питер', 'санкт-петербург', 'ленинградская область', 'ленинградская', 'с-пб', 'с-петербург'],
            'Краснодар': ['краснодар', 'краснодарский край', 'кубань', 'краснодарский'],
            'Ростов-на-Дону': ['ростов', 'ростов-на-дону', 'ростовская область', 'ростовская'],
            'Екатеринбург': ['екатеринбург', 'екат', 'свердловская область', 'свердловская'],
            'Новосибирск': ['новосибирск', 'новосиб', 'новосибирская область', 'новосибирская'],
            'Казань': ['казань', 'татарстан', 'татарская'],
            'Нижний Новгород': ['нижний новгород', 'нижний', 'нижегородская область', 'нижегородская'],
            'Самара': ['самара', 'самарская область', 'самарская'],
            'Волгоград': ['волгоград', 'волгоградская область', 'волгоградская']
        }
        
        # Проверяем только если в запросе есть упоминания о регионе
        for region, variations in region_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    logger.info(f"Найден регион '{region}' по ключевому слову '{variation}' в запросе: {query}")
                    return region
        
        logger.info(f"Регион не найден в запросе: {query}")
        
        return None
    
    def _extract_urgency_fallback(self, query: str) -> Optional[str]:
        """Извлекает срочность продажи"""
        query_lower = query.lower()
        
        # Словарь срочности
        urgency_patterns = {
            'срочно': ['срочно', 'быстро', 'немедленно', 'в срочном порядке', 'срочная продажа'],
            'не тороплюсь': ['не тороплюсь', 'не спешу', 'время есть', 'не торопясь', 'не спешу'],
            'в течение недели': ['в течение недели', 'за неделю', 'на этой неделе', 'до конца недели'],
            'в течение месяца': ['в течение месяца', 'за месяц', 'в этом месяце', 'до конца месяца'],
            'в течение дня': ['в течение дня', 'сегодня', 'завтра', 'в ближайшие дни']
        }
        
        for urgency, variations in urgency_patterns.items():
            for variation in variations:
                if variation in query_lower:
                    return urgency
        
        return None
    
    def _analyze_context(self, query: str, entity: str, position: int) -> Dict[str, Any]:
        """Анализирует контекст вокруг сущности"""
        words = query.lower().split()
        context = {
            'before': words[max(0, position-2):position],
            'after': words[position+1:position+3],
            'negation': False,
            'priority': 1.0
        }
        
        # Проверка на отрицание
        negation_words = ['не', 'нет', 'кроме', 'исключая', 'исключая']
        for word in context['before'] + context['after']:
            if word in negation_words:
                context['negation'] = True
                break
        
        # Определение приоритета по позиции
        if position < len(words) // 3:
            context['priority'] = 1.2  # Выше приоритет для слов в начале
        elif position > len(words) * 2 // 3:
            context['priority'] = 0.8  # Ниже приоритет для слов в конце
        
        return context
    
    def _validate_with_database(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует извлеченные сущности с базой данных"""
        if not self.db_mapper:
            return entities  # Если БД недоступна, возвращаем как есть
        
        validated_entities = entities.copy()
        corrections_made = False
        
        # Словарь соответствий типов сущностей
        entity_type_mapping = {
            'mark': 'mark',
            'model': 'model', 
            'color': 'color',
            'body_type': 'body_type',
            'fuel_type': 'fuel_type',
            'gear_box_type': 'gear_box_type',
            'driving_gear_type': 'driving_gear_type',
            'city': 'city',
            'option_description': 'option_description'
        }
        
        # Валидация одиночных сущностей
        for entity_key, db_entity_type in entity_type_mapping.items():
            if entity_key in validated_entities:
                entity_value = validated_entities[entity_key]
                if not self.db_mapper.validate_entity(db_entity_type, entity_value):
                    # Попытка автокоррекции только для существенных различий
                    corrected_value = self.db_mapper.suggest_similar_entity(db_entity_type, entity_value)
                    if corrected_value and corrected_value.lower() != entity_value.lower():
                        validated_entities[entity_key] = corrected_value
                        corrections_made = True
                        logger.info(f"Автокоррекция {entity_key}: {entity_value} → {corrected_value}")
                    else:
                        # Если разница только в регистре, оставляем оригинальное значение
                        logger.info(f"Сущность {entity_key}: {entity_value} найдена в БД (разница только в регистре)")
        
        # Валидация множественных сущностей
        multiple_entity_mapping = {
            'marks': 'mark',
            'models': 'model',
            'colors': 'color', 
            'body_types': 'body_type',
            'fuel_types': 'fuel_type',
            'gear_box_types': 'gear_box_type',
            'driving_gear_types': 'driving_gear_type',
            'cities': 'city',
            'option_descriptions': 'option_description'
        }
        
        for entity_key, db_entity_type in multiple_entity_mapping.items():
            if entity_key in validated_entities:
                entity_values = validated_entities[entity_key]
                if isinstance(entity_values, list):
                    corrected_values = []
                    for value in entity_values:
                        if self.db_mapper.validate_entity(db_entity_type, value):
                            corrected_values.append(value)
                        else:
                            # Попытка автокоррекции
                            corrected_value = self.db_mapper.suggest_similar_entity(db_entity_type, value)
                            if corrected_value:
                                corrected_values.append(corrected_value)
                                corrections_made = True
                                logger.info(f"Автокоррекция {entity_key}: {value} → {corrected_value}")
                            else:
                                # Если не удалось найти похожую, оставляем оригинальное значение
                                corrected_values.append(value)
                    validated_entities[entity_key] = corrected_values
        
        if corrections_made:
            validated_entities['_corrected'] = True
        
        return validated_entities
    
    def _check_brand_exists(self, brand: str) -> bool:
        """Проверяет существование марки в БД"""
        if not self.db_mapper:
            return True  # Если БД недоступна, считаем что все валидно
        
        return self.db_mapper.validate_entity('mark', brand)
    
    def _suggest_similar_brand(self, brand: str) -> Optional[str]:
        """Предлагает похожую марку"""
        if not self.db_mapper:
            # Fallback на статический словарь
            brand_corrections = {
                'бмв': 'BMW',
                'мерс': 'Mercedes',
                'тойота': 'Toyota',
                'ауди': 'Audi',
                'фольксваген': 'Volkswagen',
                'хендай': 'Hyundai',
                'киа': 'KIA',
                'лада': 'Lada',
                'ниссан': 'Nissan',
                'хонда': 'Honda'
            }
            brand_lower = brand.lower()
            return brand_corrections.get(brand_lower)
        
        return self.db_mapper.suggest_similar_entity('mark', brand)
    
    def _check_model_exists(self, brand: str, model: str) -> bool:
        """Проверяет существование модели в БД"""
        if not self.db_mapper:
            return True  # Если БД недоступна, считаем что все валидно
        
        return self.db_mapper.validate_entity('model', model)
    
    def _suggest_similar_model(self, brand: str, model: str) -> Optional[str]:
        """Предлагает похожую модель"""
        if not self.db_mapper:
            # Fallback на статический словарь
            model_corrections = {
                'x5': 'X5',
                'x3': 'X3',
                'x1': 'X1',
                'e-class': 'E-Class',
                'c-class': 'C-Class',
                'camry': 'Camry',
                'corolla': 'Corolla',
                'a4': 'A4',
                'a6': 'A6'
            }
            model_lower = model.lower()
            return model_corrections.get(model_lower)
        
        return self.db_mapper.suggest_similar_entity('model', model)
    
    @lru_cache(maxsize=100)
    def _cached_extract_entities_fallback(self, query_hash: str) -> Dict[str, Any]:
        """Кэшированное извлечение сущностей через fallback"""
        return self._extract_entities_fallback_impl(query_hash)
    
    def extract_entities_with_cache(self, query: str) -> Dict[str, Any]:
        """Извлекает сущности с кэшированием"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        if query_hash in self.cache:
            return self.cache[query_hash]
        
        # Ограничиваем размер кэша
        if len(self.cache) >= self.cache_size:
            # Удаляем старые записи
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        result = self._cached_extract_entities_fallback(query_hash)
        self.cache[query_hash] = result
        return result
    
    def _extract_entities_with_regex(self, query: str) -> Dict[str, Any]:
        """Извлекает сущности с помощью регулярных выражений как fallback"""
        entities = {}
        query_lower = query.lower()
        
        # Извлекаем марки и модели из запроса
        marks = []
        models = []
        
        # Список известных марок
        known_brands = ['BMW', 'Mercedes', 'Audi', 'Toyota', 'Honda', 'Nissan', 'Hyundai', 'KIA', 'Volkswagen', 
                       'Skoda', 'Renault', 'Peugeot', 'Citroen', 'Ford', 'Chevrolet', 'Geely', 'Jaecoo', 'Lada', 'UAZ']
        
        # Ищем марки в запросе
        for brand in known_brands:
            if brand.lower() in query_lower:
                marks.append(brand)
        
        # Улучшенные паттерны для поиска моделей
        model_patterns = [
            # Паттерн для сравнения: "Geely Preface и Jaecoo J7"
            r'(\w+)\s+(\w+)\s+(?:и|или|vs|vs\.|против)\s+(\w+)\s+(\w+)',
            # Паттерн для одиночной модели: "BMW X5"
            r'(\w+)\s+(\w+)',
        ]
        
        # Сначала пробуем паттерн для сравнения
        comparison_match = re.search(r'(\w+)\s+(\w+)\s+(?:и|или|vs|vs\.|против)\s+(\w+)\s+(\w+)', query, re.IGNORECASE)
        if comparison_match:
            marks.extend([comparison_match.group(1), comparison_match.group(3)])
            models.extend([comparison_match.group(2), comparison_match.group(4)])
        else:
            # Если не найдено сравнение, ищем одиночные модели
            for pattern in model_patterns[1:]:  # Пропускаем первый паттерн сравнения
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        models.append(match[1])  # Берем только модель, марку уже нашли выше
        
        # Всегда используем массивы для множественных значений
        if marks:
            entities['marks'] = marks
        
        if models:
            entities['models'] = models
        
        # Определяем intent
        if any(word in query_lower for word in ['сравни', 'сравнение', 'что лучше', 'лучше']):
            entities['intent'] = 'automotive'
        elif any(word in query_lower for word in ['найди', 'покажи', 'подбери', 'ищу']):
            entities['intent'] = 'automotive'
            entities['show_cars'] = True
        else:
            entities['intent'] = 'automotive'
        
        return entities
    
    def _infer_intent_local(self, query: str) -> str:
        """Локальная эвристика для intent: 'automotive' | 'general' | 'other'"""
        q = (query or "").lower().strip()
        if not q:
            return 'other'
        # general приветствия/вежливые
        general_tokens = [
            'привет', 'здравствуй', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
            'как дела', 'как ты', 'как у вас дела', 'спасибо', 'до свидания', 'что умеешь',
            'кто ты', 'что ты умеешь', 'о себе', 'расскажи о себе', 'help', 'помощь'
        ]
        if any(tok in q for tok in general_tokens):
            return 'general'
        # automotive ключи
        automotive_tokens = [
            'авто', 'машин', 'автомобил', 'bmw', 'мерседес', 'тойота', 'kia', 'hyundai', 'sedan',
            'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер', 'цена', 'год', 'пробег',
            'найди', 'покажи', 'подбери', 'выведи', 'сравни', 'рекомендуй', 'кредит', 'автокредит',
            'зелен', 'зеленые', 'зеленых', 'красн', 'красные', 'красных', 'син', 'синие', 'синих',
            'бел', 'белые', 'белых', 'черн', 'черные', 'черных', 'сер', 'серые', 'серых',
            'желт', 'желтые', 'желтых', 'оранж', 'оранжевые', 'оранжевых', 'фиолет', 'фиолетовые', 'фиолетовых', 'розов', 'розовые', 'розовых'
        ]
        if any(tok in q for tok in automotive_tokens):
            return 'automotive'
        return 'other'

    def extract_entities_with_fallback(self, query: str) -> Dict[str, Any]:
        """
        Извлекает сущности с fallback на регулярные выражения
        
        Args:
            query: Пользовательский запрос
            
        Returns:
            Словарь с извлеченными сущностями
        """
        # Сначала пробуем Llama
        entities = self.extract_entities(query)
        
        # Если Llama не сработала или вернула пустой результат, используем fallback
        if not entities:
            entities = self._extract_entities_fallback(query)
        
        # Дополнительно извлекаем цвет, если Llama его не извлекла
        if 'color' not in entities and 'colors' not in entities:
            color = self._extract_color_fallback(query)
            if color:
                entities['color'] = color
        
        # Дополнительно извлекаем привод, если Llama его не извлек
        if 'driving_gear_type' not in entities:
            drive = self._extract_drive_fallback(query)
            if drive:
                entities['driving_gear_type'] = drive
        
        # Дополнительно извлекаем опции, если Llama их не извлекла
        if 'option_description' not in entities and 'option_code' not in entities and 'option_descriptions' not in entities and 'option_codes' not in entities:
            options = self._extract_multiple_options_fallback(query)
            if options:
                if len(options) == 1:
                    entities['option_description'] = options[0]
                else:
                    entities['option_descriptions'] = options
        
        # Дополнительно извлекаем множественные сущности
        self._extract_multiple_entities_fallback(query, entities)
            
        return entities

    def _extract_entities_fallback(self, query: str) -> Dict[str, Any]:
        """
        Fallback извлечение сущностей с помощью регулярных выражений
        
        Args:
            query: Пользовательский запрос
            
        Returns:
            Словарь с извлеченными сущностями
        """
        entities = {}
        query_lower = query.lower()
        
        # Словари для распознавания тегов
        tag_mappings = {
            'budget_tag': {
                'keywords': ['дешевый', 'недорогой', 'бюджетный', 'экономичный', 'доступный', 'недорого', 'дешево'],
                'price_range': (0, 3000000)  # до 3 млн
            },
            'premium_tag': {
                'keywords': ['дорогой', 'премиум', 'люкс', 'элитный', 'престижный', 'дорого', 'премиальный'],
                'price_range': (5000000, float('inf'))  # от 5 млн
            },
            'family_tag': {
                'keywords': ['семейный', 'для семьи', 'большой', 'просторный', 'комфортный для семьи', 'семье'],
                'seats_range': (5, 9)  # от 5 мест
            },
            'sport_tag': {
                'keywords': ['быстрый', 'спортивный', 'мощный', 'динамичный', 'скоростной', 'спорт'],
                'power_range': (200, float('inf'))  # от 200 л.с.
            },
            'city_tag': {
                'keywords': ['городской', 'для города', 'компактный', 'маневренный', 'город', 'в городе'],
                'body_types': ['хетчбэк', 'седан', 'кроссовер']
            },
            'offroad_tag': {
                'keywords': ['внедорожный', 'для бездорожья', 'проходимый', 'внедорожник', 'джип', 'бездорожье'],
                'body_types': ['внедорожник', 'пикап']
            },
            'eco_tag': {
                'keywords': ['экологичный', 'экономичный', 'с низким расходом', 'эко', 'экологический'],
                'fuel_types': ['гибрид', 'электрический', 'бензин']
            },
            'reliable_tag': {
                'keywords': ['надежный', 'проверенный', 'качественный', 'долговечный', 'надежность'],
                'brands': ['toyota', 'honda', 'lexus', 'mazda', 'subaru']
            },
            'new_tag': {
                'keywords': ['новый', 'свежий', 'современный', 'актуальный', 'последний'],
                'year_range': (2023, 2025)  # с 2023 года
            },
            'used_tag': {
                'keywords': ['подержанный', 'б/у', 'с пробегом', 'б у', 'бу', 'подержанный'],
                'year_range': (1990, 2022)  # до 2022 года
            }
        }
        
        # Извлекаем теги
        for tag_name, tag_config in tag_mappings.items():
            for keyword in tag_config['keywords']:
                if keyword in query_lower:
                    entities[tag_name] = True
                    break
        
        # Извлечение цен с улучшенными паттернами
        price_patterns = [
            r'до\s+(\d+(?:[.,]\d+)?)\s*(?:млн|миллион|тыс|тысяч)',
            r'от\s+(\d+(?:[.,]\d+)?)\s*(?:млн|миллион|тыс|тысяч)',
            r'(\d+(?:[.,]\d+)?)\s*(?:млн|миллион|тыс|тысяч)',
            r'(\d+(?:[.,]\d+)?)\s*(?:руб|рублей|р\.)',
            r'(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)\s*руб',
            r'(\d+(?:[.,]\d+)?)\s*(?:тыс|тысяч)\s*руб',
            r'(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)\s*рублей'
        ]
        
        # Паттерны для диапазонов цен
        range_patterns = [
            r'от\s*(\d+(?:[.,]\d+)?)\s*до\s*(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)',
            r'(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)',
            r'(\d+(?:[.,]\d+)?)\s*—\s*(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)',
            r'(\d+(?:[.,]\d+)?)\s*по\s*(\d+(?:[.,]\d+)?)\s*(?:млн|миллион)'
        ]
        
        # Паттерны для числительных
        numeral_patterns = {
            'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
            'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10
        }
        
        for pattern in price_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                # Заменяем запятую на точку для корректного парсинга
                price = float(match.replace(',', '.'))
                if 'до' in query_lower:
                    entities['price_max'] = int(price * 1000000) if 'млн' in query_lower else int(price * 1000)
                elif 'от' in query_lower:
                    entities['price_min'] = int(price * 1000000) if 'млн' in query_lower else int(price * 1000)
                else:
                    entities['price'] = int(price * 1000000) if 'млн' in query_lower else int(price * 1000)
        
        # Извлечение годов
        year_pattern = r'(\d{4})\s*год'
        year_matches = re.findall(year_pattern, query_lower)
        if year_matches:
            entities['manufacture_year'] = int(year_matches[0])
            
        # Извлечение типов кузова, цветов и топлива теперь обрабатывается в _extract_multiple_entities_fallback
                
        # Извлечение типа коробки передач
        gear_types = {
            'автомат': 'автомат',
            'механика': 'механика',
            'вариатор': 'вариатор',
            'робот': 'робот'
        }
        
        for gear_type, normalized in gear_types.items():
            if gear_type in query_lower:
                entities['gear_box_type'] = normalized
                break
                
        # Извлечение типа привода
        drive_types = {
            'передний': 'передний',
            'задний': 'задний',
            'полный': 'полный'
        }
        
        for drive_type, normalized in drive_types.items():
            if drive_type in query_lower:
                entities['driving_gear_type'] = normalized
                break
        
        # Сначала извлекаем множественные сущности
        self._extract_multiple_entities_fallback(query, entities)
        
        # Если множественные сущности не найдены, используем одиночные
        if 'body_type' not in entities and 'body_types' not in entities:
            body_types = {
                'седан': 'седан',
                'хэтчбек': 'хэтчбек',
                'универсал': 'универсал',
                'внедорожник': 'внедорожник',
                'кроссовер': 'кроссовер',
                'джип': 'внедорожник',
                'хэтч': 'хэтчбек',
                'универ': 'универсал'
            }
            
            for body_type, normalized in body_types.items():
                if body_type in query_lower:
                    entities['body_type'] = normalized
                    break
        
        # Если множественные цвета не найдены, используем одиночные
        if 'color' not in entities and 'colors' not in entities:
            colors = ['белый', 'черный', 'красный', 'синий', 'серый', 'серебристый', 'зеленый', 'желтый', 'оранжевый', 'коричневый', 'бежевый']
            for color in colors:
                if color in query_lower:
                    entities['color'] = color
                    break
        
        # Если множественные типы топлива не найдены, используем одиночные
        if 'fuel_type' not in entities and 'fuel_types' not in entities:
            fuel_types = {
                'бензин': 'бензин',
                'дизель': 'дизель',
                'гибрид': 'гибрид',
                'электрический': 'электрический',
                'газ': 'газ'
            }
            
            for fuel_type, normalized in fuel_types.items():
                if fuel_type in query_lower:
                    entities['fuel_type'] = normalized
                    break
                
        return entities


# Глобальный экземпляр для использования в других модулях
llama_entity_extractor = LlamaEntityExtractor()