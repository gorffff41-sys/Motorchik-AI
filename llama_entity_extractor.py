#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для извлечения автомобильных сущностей с помощью Llama
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Union
from llama_service import generate_with_llama

logger = logging.getLogger(__name__)

class LlamaEntityExtractor:
    """Извлечение автомобильных сущностей с помощью Llama"""
    
    def __init__(self):
        self.entity_prompt = """
Ты - эксперт по извлечению автомобильных сущностей из пользовательских запросов. 
Твоя задача - извлечь все характеристики автомобиля из текста и вернуть их в формате JSON.

## ИЗВЛЕКАЕМЫЕ СУЩНОСТИ:

### Основные идентификаторы:
- mark (марка): BMW, Mercedes, Toyota, Lada, KIA и т.д.
- model (модель): X5, Camry, Vesta, Sportage и т.д.
- vin (VIN-код): 17-символьный код
- manufacture_year (год производства): 2020, 2021, 2022 и т.д.
- model_year (модельный год): может отличаться от года производства

### Внешний вид и кузов:
- body_type (тип кузова): седан, хэтчбек, универсал, внедорожник, кроссовер, купе, кабриолет, пикап
- color (цвет кузова): белый, черный, красный, синий, серый, серебристый и т.д.
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
- power (мощность): в л.с.
- gear_box_type (тип коробки передач): автомат, механика, вариатор, робот
- driving_gear_type (тип привода): передний, задний, полный

### Производительность и экология:
- fuel_consumption (расход топлива): в л/100км

- max_torque (максимальный крутящий момент): в Нм
- acceleration_0_100 (разгон 0-100): в секундах
- max_speed (максимальная скорость): в км/ч
- eco_class (экологический класс): EURO-5, EURO-6 и т.д.

### Комплектация:
- compl_level (уровень комплектации): базовая, комфорт, люкс и т.д.
- code_compl (код комплектации): буквенно-цифровой код

### Для подержанных автомобилей:
- mileage (пробег): в км
- owners_count (количество владельцев): 1, 2, 3 и т.д.
- accident (участие в ДТП): да, нет
- wheel_type (тип руля): левый, правый

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
7. Для привода:
   - "переднеприводный" → driving_gear_type: "передний"
   - "заднеприводный" → driving_gear_type: "задний"
   - "полноприводный" → driving_gear_type: "полный"
8. Для тегов распознавай:
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
Ответ: {"body_type": "седан", "color": "красный", "price_min": 2000000, "price_max": 4000000}

Запрос: "Нужен дизельный внедорожник с полным приводом"
Ответ: {"fuel_type": "дизель", "body_type": "внедорожник", "driving_gear_type": "полный"}

Запрос: "Ищу машину для семьи, 7 мест, до 3 млн"
Ответ: {"seats": 7, "price_max": 3000000, "family_tag": true}

Запрос: "Нужен дешевый городской автомобиль"
Ответ: {"budget_tag": true, "city_tag": true}

Запрос: "Покажи быстрые спортивные машины"
Ответ: {"sport_tag": true}

Запрос: "Ищу надежный премиум внедорожник"
Ответ: {"reliable_tag": true, "premium_tag": true, "offroad_tag": true}

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
            
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                entities = json.loads(json_str)
                
                # Валидируем, нормализуем и удаляем неупомянутые сущности, основываясь на исходном запросе
                entities = self._validate_and_normalize_entities(entities, query)
                # Грубая подстраховка для intent, если Llama не вернула
                if 'intent' not in entities:
                    entities['intent'] = self._infer_intent_local(query)
                
                logger.info(f"Извлечены сущности: {entities}")
                return entities
            else:
                logger.warning(f"JSON не найден в ответе Llama: {response}")
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
            'compl_level','code_compl',
            'mileage','owners_count','accident','wheel_type',
            'price_min','price_max','price',
            'budget_tag','premium_tag','family_tag','sport_tag','city_tag','offroad_tag','eco_tag','reliable_tag','new_tag','used_tag',
            'show_cars','intent',
            'city',
            # множественные значения
            'marks','models','cities','body_types','colors'
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

    def _infer_intent_local(self, query: str) -> str:
        """Локальная эвристика для intent: 'automotive' | 'general' | 'other'"""
        q = (query or "").lower().strip()
        if not q:
            return 'other'
        # general приветствия/вежливые
        general_tokens = [
            'привет', 'здравствуй', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
            'как дела', 'как ты', 'как у вас дела', 'спасибо', 'пока', 'до свидания', 'что умеешь',
            'кто ты', 'что ты умеешь', 'о себе', 'расскажи о себе', 'help', 'помощь'
        ]
        if any(tok in q for tok in general_tokens):
            return 'general'
        # automotive ключи
        automotive_tokens = [
            'авто', 'машин', 'автомобил', 'bmw', 'мерседес', 'тойота', 'kia', 'hyundai', 'sedan',
            'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер', 'цена', 'год', 'пробег',
            'найди', 'покажи', 'подбери', 'выведи', 'сравни', 'рекомендуй', 'кредит', 'автокредит'
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
        
        # Извлечение цен
        price_patterns = [
            r'до\s+(\d+(?:\.\d+)?)\s*млн',
            r'от\s+(\d+(?:\.\d+)?)\s*млн',
            r'(\d+(?:\.\d+)?)\s*млн',
            r'(\d+(?:\.\d+)?)\s*миллион',
            r'(\d+)\s*тысяч',
            r'(\d+)\s*тыс'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                price = float(match)
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
            
        # Извлечение типов кузова
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
                
        # Извлечение цветов
        colors = ['белый', 'черный', 'красный', 'синий', 'серый', 'серебристый', 'зеленый', 'желтый', 'оранжевый', 'коричневый', 'бежевый']
        for color in colors:
            if color in query_lower:
                entities['color'] = color
                break
                
        # Извлечение типа топлива
        fuel_types = {
            'бензин': 'бензин',
            'дизель': 'дизель',
            'гибрид': 'гибрид',
            'электро': 'электрический',
            'электрический': 'электрический'
        }
        
        for fuel_type, normalized in fuel_types.items():
            if fuel_type in query_lower:
                entities['fuel_type'] = normalized
                break
                
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
                
        return entities


# Глобальный экземпляр для использования в других модулях
llama_entity_extractor = LlamaEntityExtractor()