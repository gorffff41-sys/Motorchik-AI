import json
import re
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
import numpy as np
from collections import defaultdict
import logging
import jellyfish
from difflib import get_close_matches
import unicodedata

# Импорт функций из entity_extractor
try:
    from modules.classifiers.entity_extractor import advanced_similarity_score
except ImportError:
    # Fallback функция если импорт не удался
    def advanced_similarity_score(word1: str, word2: str) -> float:
        """Простая функция схожести если основная недоступна"""
        if word1.lower() == word2.lower():
            return 1.0
        return 0.0

# Импорт для работы с базой данных
try:
    from database import search_all_cars
except ImportError:
    # Fallback если модуль недоступен
    def search_all_cars(**kwargs):
        return []

logger = logging.getLogger("enhanced_llama_processor")

def advanced_fuzzy_match_llama(query_word: str, synonym_set: set, threshold: float = 0.85) -> bool:
    """
    Продвинутое fuzzy matching для Enhanced Llama Processor
    """
    query_word = query_word.lower().strip()
    
    # 1. Точное совпадение
    if query_word in synonym_set:
        return True
    
    # 2. Jaro-Winkler расстояние
    for synonym in synonym_set:
        if jellyfish.jaro_winkler_similarity(query_word, synonym) >= threshold:
            return True
    
    # 3. Расстояние Левенштейна
    for synonym in synonym_set:
        if jellyfish.levenshtein_distance(query_word, synonym) <= 2:
            return True
    
    # 4. Метод Soundex для фонетического сравнения
    try:
        query_soundex = jellyfish.soundex(query_word)
        for synonym in synonym_set:
            if jellyfish.soundex(synonym) == query_soundex:
                return True
    except:
        pass
    
    # 5. Метод Metaphone
    try:
        query_metaphone = jellyfish.metaphone(query_word)
        for synonym in synonym_set:
            if jellyfish.metaphone(synonym) == query_metaphone:
                return True
    except:
        pass
    
    # 6. Частичное совпадение (для составных слов)
    for synonym in synonym_set:
        if len(query_word) > 3 and len(synonym) > 3:
            if query_word in synonym or synonym in query_word:
                return True
    
    return False

def smart_text_normalization(text: str) -> str:
    """
    Умная нормализация текста с учетом автомобильной терминологии
    """
    # Базовая нормализация
    text = text.lower().strip()
    text = text.replace('ё', 'е').replace('й', 'и')
    
    # Удаление лишних пробелов
    text = re.sub(r'\s+', ' ', text)
    
    # Нормализация автомобильных терминов
    car_terms = {
        'автоматическая коробка': 'автомат',
        'механическая коробка': 'механика',
        'панорамная крыша': 'панорамная крыша',
        'подогрев сидений': 'подогрев сидений',
        'климат-контроль': 'климат-контроль',
        'all wheel drive': 'полный привод',
        'front wheel drive': 'передний привод',
        'rear wheel drive': 'задний привод'
    }
    
    for term, normalized in car_terms.items():
        text = text.replace(term, normalized)
    
    return text

def enhanced_entity_extraction(text: str, entity_dicts: List[Dict[str, List[str]]]) -> Dict[str, Any]:
    """
    Улучшенное извлечение сущностей с использованием нескольких алгоритмов
    """
    extracted_entities = {}
    normalized_text = smart_text_normalization(text)
    words = re.findall(r'\b\w+\b', normalized_text)
    
    for entity_dict in entity_dicts:
        for entity_type, synonyms in entity_dict.items():
            synonym_set = {smart_text_normalization(s) for s in synonyms}
            
            for word in words:
                if advanced_fuzzy_match_llama(word, synonym_set):
                    if entity_type not in extracted_entities:
                        extracted_entities[entity_type] = []
                    extracted_entities[entity_type].append(word)
    
    return extracted_entities

class ProcessingMetrics:
    """Система метрик для мониторинга производительности"""
    
    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'llama_calls': 0,
            'cache_hits': 0,
            'response_times': [],
            'error_count': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'ner_extractions': 0,
            'ner_success_rate': 0,
            'context_usage': 0,
            'fallback_usage': 0
        }
    
    def log_request(self, processing_time: float, llama_used: bool = False, 
                   cache_hit: bool = False, error: bool = False, 
                   parse_success: bool = False, ner_success: bool = False,
                   context_used: bool = False, fallback_used: bool = False):
        """Логирует метрики запроса"""
        self.stats['total_requests'] += 1
        self.stats['response_times'].append(processing_time)
        
        if llama_used:
            self.stats['llama_calls'] += 1
        if cache_hit:
            self.stats['cache_hits'] += 1
        if error:
            self.stats['error_count'] += 1
        if parse_success:
            self.stats['successful_parses'] += 1
        else:
            self.stats['failed_parses'] += 1
        if ner_success:
            self.stats['ner_extractions'] += 1
        if context_used:
            self.stats['context_usage'] += 1
        if fallback_used:
            self.stats['fallback_usage'] += 1
        
        # Обновляем успешность NER
        if self.stats['total_requests'] > 0:
            self.stats['ner_success_rate'] = self.stats['ner_extractions'] / self.stats['total_requests']
    
    def get_report(self) -> Dict[str, Any]:
        """Возвращает отчет по метрикам"""
        avg_time = np.mean(self.stats['response_times']) if self.stats['response_times'] else 0
        cache_efficiency = self.stats['cache_hits'] / max(1, self.stats['llama_calls'])
        success_rate = (self.stats['total_requests'] - self.stats['error_count']) / max(1, self.stats['total_requests'])
        parse_success_rate = self.stats['successful_parses'] / max(1, self.stats['successful_parses'] + self.stats['failed_parses'])
        context_usage_rate = self.stats['context_usage'] / max(1, self.stats['total_requests'])
        fallback_usage_rate = self.stats['fallback_usage'] / max(1, self.stats['total_requests'])
        
        return {
            'total_requests': self.stats['total_requests'],
            'llama_usage': self.stats['llama_calls'],
            'cache_efficiency': f"{cache_efficiency:.2%}",
            'avg_response_time': f"{avg_time:.2f} сек",
            'success_rate': f"{success_rate:.2%}",
            'parse_success_rate': f"{parse_success_rate:.2%}",
            'ner_success_rate': f"{self.stats['ner_success_rate']:.2%}",
            'context_usage_rate': f"{context_usage_rate:.2%}",
            'fallback_usage_rate': f"{fallback_usage_rate:.2%}",
            'error_count': self.stats['error_count']
        }

class DialogContext:
    """Менеджер контекста диалога с улучшенной логикой"""
    
    def __init__(self, max_history: int = 5):
        self.history = []
        self.max_history = max_history
        self.current_session = None
        self.user_preferences = {}
        self.conversation_state = 'initial'
    
    def add_query(self, query: str, response: str, entities: Dict[str, Any] = None):
        """Добавляет пару запрос-ответ в историю с извлеченными сущностями"""
        self.history.append({
            'query': query,
            'response': response,
            'entities': entities,
            'timestamp': time.time()
        })
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Обновляем предпочтения пользователя
        if entities:
            self._update_user_preferences(entities)
    
    def _update_user_preferences(self, entities: Dict[str, Any]):
        """Обновляет предпочтения пользователя на основе извлеченных сущностей"""
        for key, value in entities.items():
            if key in ['brand', 'color', 'body_type', 'price_category']:
                if key not in self.user_preferences:
                    self.user_preferences[key] = []
                if value not in self.user_preferences[key]:
                    self.user_preferences[key].append(value)
    
    def build_context_prompt(self, current_query: str) -> str:
        """Строит промт с контекстом истории и предпочтениями"""
        if not self.history:
            return current_query
        
        # Анализируем контекст
        context_analysis = self._analyze_context()
        
        # Строим контекстный промпт
        context_lines = []
        for entry in self.history[-3:]:  # Последние 3 обмена
            context_lines.append(f"Пользователь: {entry['query']}")
            context_lines.append(f"Ассистент: {entry['response']}")
        
        context_str = "\n".join(context_lines) if context_lines else ""
        
        # Добавляем информацию о предпочтениях
        preferences_str = ""
        if self.user_preferences:
            pref_lines = []
            for key, values in self.user_preferences.items():
                if values:
                    pref_lines.append(f"{key}: {', '.join(map(str, values))}")
            if pref_lines:
                preferences_str = f"\nПРЕДПОЧТЕНИЯ ПОЛЬЗОВАТЕЛЯ:\n" + "\n".join(pref_lines)
        
        return f"""Ты - автомобильный ассистент Моторчик. Учитывай контекст предыдущего диалога.

КОНТЕКСТ:
{context_str}

{preferences_str}

АНАЛИЗ КОНТЕКСТА: {context_analysis}

ТЕКУЩИЙ ЗАПРОС: "{current_query}"

ИНСТРУКЦИИ:
1. Учитывай предыдущие вопросы пользователя
2. Если пользователь уточняет параметры - используй их
3. Если это новый запрос - обрабатывай независимо
4. Будь последовательным в рекомендациях
5. Учитывай предпочтения пользователя

ОТВЕТ:"""
    
    def _analyze_context(self) -> str:
        """Анализирует контекст диалога"""
        if not self.history:
            return "Новый диалог"
        
        # Анализируем последние запросы
        recent_entities = []
        for entry in self.history[-2:]:
            if entry.get('entities'):
                recent_entities.append(entry['entities'])
        
        if not recent_entities:
            return "Диалог без конкретных параметров"
        
        # Определяем тип контекста
        if len(recent_entities) > 1:
            return "Уточнение параметров поиска"
        else:
            return "Первичный поиск"
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Возвращает предпочтения пользователя"""
        return self.user_preferences.copy()
    
    def clear_history(self):
        """Очищает историю диалога"""
        self.history.clear()
        self.user_preferences.clear()
        self.conversation_state = 'initial'

class JSONValidator:
    """Валидатор и корректор JSON ответов от LLAMA с улучшенной логикой"""
    
    @staticmethod
    def parse_llama_filters(response: str) -> Dict[str, Any]:
        """Парсит и валидирует JSON фильтры от LLAMA с улучшенной обработкой"""
        try:
            # Автоматическое исправление common mistakes
            corrected = response.replace("'", '"').replace("True", "true").replace("False", "false")
            corrected = re.sub(r'(\w+):', r'"\1":', corrected)  # Добавляем кавычки к ключам
            
            # Удаляем лишние символы
            corrected = re.sub(r'[^\x20-\x7E]', '', corrected)  # Только ASCII
            
            # Проверяем, что это действительно JSON объект
            if not corrected.strip().startswith('{'):
                raise ValueError("Not a JSON object")
            
            parsed = json.loads(corrected)
            
            # Валидация структуры
            if not isinstance(parsed, dict):
                raise ValueError("Not a dictionary")
            
            # Дополнительная валидация полей
            valid_fields = {
                'brand', 'model', 'color', 'price', 'price_from', 'price_to',
                'year', 'year_from', 'year_to', 'city', 'body_type',
                'gear_box_type', 'driving_gear_type', 'fuel_type',
                'option_description', 'dealer_center', 'mileage', 'mileage_from', 'mileage_to',
                'transmission', 'drive_type', 'fuel_type', 'state', 'scenario'
            }
            
            # Фильтруем только валидные поля
            filtered = {}
            for key, value in parsed.items():
                if key in valid_fields:
                    filtered[key] = value
                else:
                    logger.warning(f"Invalid field '{key}' in JSON response")
            
            return filtered
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Извлечение JSON с помощью регулярных выражений
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            if match:
                try:
                    extracted = json.loads(match.group(0))
                    if isinstance(extracted, dict):
                        return extracted
                except:
                    pass
            
            # Fallback: попытка извлечь отдельные поля
            return JSONValidator._extract_fields_manually(response)
    
    @staticmethod
    def _extract_fields_manually(response: str) -> Dict[str, Any]:
        """Fallback извлечение полей с помощью regex"""
        fields = {}
        
        # Бренды (более точные паттерны)
        brand_patterns = [
            r'\b(bmw|mercedes|audi|toyota|honda|nissan|ford|chevrolet|volkswagen|hyundai|kia|renault|peugeot|opel|fiat|skoda|seat|volvo|saab|mazda|mitsubishi|subaru|lexus|infiniti|acura|porsche|jaguar|land\s*rover|bentley|rolls\s*royce|ferrari|lamborghini|maserati|aston\s*martin|mclaren|lotus|alpine)\b',
            r'\b(бмв|мерседес|ауди|тойота|хонда|ниссан|форд|шевроле|фольксваген|хендай|киа|рено|пежо|опель|фиат|шкода|сеат|вольво|сааб|мазда|мицубиси|субару|лексус|инфинити|акура|порше|ягуар|ленд\s*ровер|бентли|роллс\s*ройс|ферари|ламборгини|мазерати|астон\s*мартин|маклерен|лотос|альпин)\b'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['brand'] = match.group(1).upper()
                break
        
        # Модели (улучшенные паттерны)
        model_patterns = [
            r'\b(x[1-7]|m[1-8]|z[1-8]|i[1-8]|1\s*series|2\s*series|3\s*series|4\s*series|5\s*series|6\s*series|7\s*series|8\s*series|gle|glc|gla|glb|gls|s\s*class|e\s*class|c\s*class|a\s*class|b\s*class|v\s*class|r\s*class|amg|camry|corolla|rav4|highlander|accord|civic|cr-v|pilot|altima|sentra|rogue|pathfinder|escape|explorer|edge|fusion|focus|f-150|silverado|malibu|cruze|equinox|traverse|golf|passat|jetta|tiguan|atlas|tucson|santa\s*fe|sportage|sorento|optima|forte|soul|megane|clio|captur|kadjar|3008|5008|208|308|astra|corsa|insignia|vectra|punto|panda|500|doblo|linea|bravo|stilo|octavia|fabia|rapid|superb|leon|ibiza|toledo|s60|s80|s90|v60|v90|xc40|xc60|xc90|cx-3|cx-5|cx-9|mx-5|miata|outlander|lancer|asx|impreza|forester|legacy|outback|wrx|sti|is|es|gs|ls|rc|lc|nx|rx|lx|gx|qx30|qx50|qx60|qx70|qx80|tlx|rdx|mdx|ilx|nsx|911|cayenne|macan|panamera|boxster|cayman|f-type|e-pace|f-pace|i-pace|range\s*rover|discovery|defender|continental|flying\s*spur|mulsanne|phantom|ghost|wraith|dawn|488|f8|812|sf90|huracan|aventador|urus|ghibli|quattroporte|levante|db11|vantage|dbs|rapide|vulcan|valkyrie|720s|570s|540c|elise|exige|evora|emira|a110)\b',
            r'\b(серия\s*[1-8]|класс\s*[a-z]|amg|камри|королла|рав4|хайлендер|аккорд|сивик|пилот|альтима|сентра|рог|патфайндер|эскейп|эксплорер|эдж|фьюжн|фокус|сильверадо|малибу|круз|эквинокс|траверс|гольф|пассат|джетта|тигуан|атлас|туксон|санта\s*фе|спортаж|соренто|оптима|форте|соул|меган|клио|каптур|каджар|каптур|пежо|астра|корса|инсигния|вектра|пунто|панда|добло|линеа|браво|стило|октавия|фабия|рапид|суперб|леон|ибица|толедо|вольво|мазда|мицубиси|субару|лексус|инфинити|акура|порше|ягуар|ленд\s*ровер|бентли|роллс\s*ройс|ферари|ламборгини|мазерати|астон\s*мартин|маклерен|лотос|альпин)\b'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['model'] = match.group(1).upper()
                break
        
        # Цвета
        color_patterns = [
            r'\b(красный|синий|зеленый|желтый|белый|черный|серый|серебристый|золотой|коричневый|оранжевый|фиолетовый|розовый|голубой|красная|синяя|зеленая|желтая|белая|черная|серая|серебристая|золотая|коричневая|оранжевая|фиолетовая|розовая|голубая)\b',
            r'\b(red|blue|green|yellow|white|black|gray|silver|gold|brown|orange|purple|pink|cyan)\b'
        ]
        
        for pattern in color_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['color'] = match.group(1)
                break
        
        # Цены
        price_patterns = [
            r'(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)',
            r'до\s*(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)',
            r'цена\s*(?:до|от)?\s*(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, response.lower())
            if match:
                price_str = match.group(1).replace(' ', '')
                if 'млн' in response.lower() or 'миллион' in response.lower():
                    fields['price_to'] = int(price_str) * 1000000
                elif 'тыс' in response.lower() or 'тысяч' in response.lower():
                    fields['price_to'] = int(price_str) * 1000
                else:
                    fields['price_to'] = int(price_str)
                break
        
        # Годы
        year_patterns = [
            r'(\d{4})\s*(?:год|года|году)',
            r'(\d{4})-(\d{4})',
            r'от\s*(\d{4})\s*до\s*(\d{4})'
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, response)
            if match:
                if len(match.groups()) == 2:
                    fields['year_from'] = int(match.group(1))
                    fields['year_to'] = int(match.group(2))
                else:
                    fields['year_from'] = int(match.group(1))
                break
        
        # Типы кузова
        body_patterns = [
            r'\b(седан|хэтчбек|универсал|внедорожник|кроссовер|кабриолет|купе|лимузин|пикап|фургон|микроавтобус)\b',
            r'\b(sedan|hatchback|wagon|suv|crossover|cabriolet|coupe|limousine|pickup|van|minibus)\b'
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['body_type'] = match.group(1)
                break
        
        # Типы топлива
        fuel_patterns = [
            r'\b(бензин|дизель|электро|гибрид|бензиновый|дизельный|электрический|гибридный)\b',
            r'\b(petrol|diesel|electric|hybrid|gasoline)\b'
        ]
        
        for pattern in fuel_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['fuel_type'] = match.group(1)
                break
        
        # Коробки передач
        transmission_patterns = [
            r'\b(автомат|механика|робот|вариатор|автоматическая|механическая|роботизированная)\b',
            r'\b(automatic|manual|robot|cvt|auto|manual)\b'
        ]
        
        for pattern in transmission_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['transmission'] = match.group(1)
                break
        
        # Привод
        drive_patterns = [
            r'\b(передний|задний|полный|передний привод|задний привод|полный привод)\b',
            r'\b(front|rear|all|awd|fwd|rwd|4wd)\b'
        ]
        
        for pattern in drive_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['drive_type'] = match.group(1)
                break
        
        # Состояние
        state_patterns = [
            r'\b(новый|подержанный|б/у|с пробегом|без пробега)\b',
            r'\b(new|used|second-hand|with mileage|without mileage)\b'
        ]
        
        for pattern in state_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['state'] = match.group(1)
                break
        
        # Сценарии
        scenario_patterns = [
            r'\b(семейный|городской|путешествие|бизнес|экономичный|семья|город|путешествия|экономия)\b',
            r'\b(family|city|travel|business|economy|economic)\b'
        ]
        
        for pattern in scenario_patterns:
            match = re.search(pattern, response.lower())
            if match:
                scenario_map = {
                    'семейный': 'family', 'семья': 'family',
                    'городской': 'city', 'город': 'city',
                    'путешествие': 'travel', 'путешествия': 'travel',
                    'бизнес': 'business',
                    'экономичный': 'economy', 'экономия': 'economy',
                    'family': 'family', 'city': 'city', 'travel': 'travel',
                    'business': 'business', 'economy': 'economy', 'economic': 'economy'
                }
                fields['scenario'] = scenario_map.get(match.group(1), match.group(1))
                break
        
        # Города
        city_patterns = [
            r'\b(москва|спб|питер|санкт-петербург|ростов|новосибирск|екатеринбург|казань|нижний новгород|челябинск|самара|омск|уфа|красноярск|пермь|воронеж|волгоград|краснодар|саратов|тихорецк|тихорецкая)\b',
            r'\b(moscow|spb|petersburg|rostov|novosibirsk|yekaterinburg|kazan|nizhny novgorod|chelyabinsk|samara|omsk|ufa|krasnoyarsk|perm|voronezh|volgograd|krasnodar|saratov|tikhoretsk)\b'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, response.lower())
            if match:
                fields['city'] = match.group(1)
                break
        
        return fields

class SmartCarSelector:
    """Интеллектуальный выбор наиболее релевантных автомобилей"""
    
    def __init__(self):
        self.simple_keywords = {
            'bmw': ['bmw', 'бмв', 'BMW', 'БМВ'],
            'mercedes': ['mercedes', 'мерседес', 'mercedes-benz', 'мерседес-бенц'],
            'audi': ['audi', 'ауди', 'Audi', 'Ауди'],
            'toyota': ['toyota', 'тойота', 'Toyota', 'Тойота'],
            'honda': ['honda', 'хонда', 'Honda', 'Хонда'],
            'ford': ['ford', 'форд', 'Ford', 'Форд'],
            'volkswagen': ['volkswagen', 'фольксваген', 'vw', 'VW'],
            'hyundai': ['hyundai', 'хендай', 'Hyundai', 'Хендай'],
            'kia': ['kia', 'киа', 'Kia', 'Киа'],
            'nissan': ['nissan', 'ниссан', 'Nissan', 'Ниссан'],
            'lada': ['lada', 'лада', 'ваз', 'ВАЗ', 'Lada', 'Лада']
        }
    
    def select_relevant_cars(self, cars: List[Dict], query: str, limit: int = 5) -> List[Dict]:
        """Выбирает наиболее релевантные автомобили"""
        if not cars:
            return []
        
        # Простая релевантность на основе ключевых слов
        scored_cars = []
        query_lower = query.lower()
        
        for car in cars:
            score = 0
            car_text = f"{car.get('mark', '')} {car.get('model', '')} {car.get('body_type', '')} {car.get('color', '')}".lower()
            
            # Проверка брендов
            for brand, keywords in self.simple_keywords.items():
                if any(kw in query_lower for kw in keywords) and any(kw in car_text for kw in keywords):
                    score += 10
            
            # Проверка цветов
            if any(color in query_lower for color in ['красный', 'синий', 'белый', 'черный', 'зеленый']):
                if any(color in car_text for color in ['красный', 'синий', 'белый', 'черный', 'зеленый']):
                    score += 5
            
            # Проверка типа кузова
            body_types = ['седан', 'кроссовер', 'suv', 'хэтчбек', 'универсал']
            if any(body in query_lower for body in body_types):
                if any(body in car_text for body in body_types):
                    score += 3
            
            scored_cars.append((car, score))
        
        # Сортировка по релевантности
        scored_cars.sort(key=lambda x: x[1], reverse=True)
        
        return [car for car, score in scored_cars[:limit]]

class EnhancedLlamaProcessor:
    """Улучшенный процессор LLAMA с кэшированием и валидацией"""
    
    def __init__(self):
        self.metrics = ProcessingMetrics()
        self.dialog_context = DialogContext()
        self.json_validator = JSONValidator()
        self.car_selector = SmartCarSelector()
        
        # Кэш для промптов
        self.prompt_cache = {}
        self.cache_ttl = 3600  # 1 час
        
        # Кэш для NER извлечения
        self.ner_cache = {}
        self.ner_cache_ttl = 1800  # 30 минут
    
    @lru_cache(maxsize=500)
    def _generate_cached_response(self, prompt_hash: str) -> str:
        """Кэшированная генерация ответа"""
        from llama_service import generate_with_llama
        
        # Извлекаем оригинальный промпт из хеша (упрощенная версия)
        # В реальной реализации нужно хранить промпт отдельно
        return generate_with_llama(f"Prompt: {prompt_hash}")
    
    @lru_cache(maxsize=1000)
    def _cached_ner_extraction(self, query: str) -> Dict[str, Any]:
        """Кэшированное извлечение сущностей через NER"""
        return self._real_entity_extraction(query)
    
    def _get_cached_ner(self, query: str) -> Dict[str, Any]:
        """Получает кэшированный результат NER или выполняет извлечение"""
        query_hash = hash(query.lower().strip())
        
        # Проверяем кэш
        if query_hash in self.ner_cache:
            cache_entry = self.ner_cache[query_hash]
            if time.time() - cache_entry['timestamp'] < self.ner_cache_ttl:
                logger.info(f"NER cache hit for query: {query[:50]}...")
                return cache_entry['entities']
        
        # Выполняем извлечение
        entities = self._cached_ner_extraction(query)
        
        # Сохраняем в кэш
        self.ner_cache[query_hash] = {
            'entities': entities,
            'timestamp': time.time()
        }
        
        logger.info(f"NER cache miss for query: {query[:50]}...")
        return entities
    
    def _clear_ner_cache(self):
        """Очищает кэш NER"""
        self._cached_ner_extraction.cache_clear()
        self.ner_cache.clear()
        logger.info("NER cache cleared")
    
    def _real_entity_extraction(self, query: str) -> Dict[str, Any]:
        """Интеграция с существующим NER модулем с улучшенной обработкой"""
        try:
            from modules.classifiers.ner_intent_classifier import NERIntentClassifier
            
            ner = NERIntentClassifier()
            entities = ner.extract_entities(query)
            
            # Нормализация результатов с улучшенной логикой
            normalized = {}
            
            # Обработка брендов
            if entities.get('brand'):
                if isinstance(entities['brand'], dict):
                    # Извлекаем английское название бренда
                    brand_en = entities['brand'].get('en', '')
                    if brand_en:
                        normalized['brand'] = brand_en.upper()
                    else:
                        normalized['brand'] = entities['brand'].get('ru', '').upper()
                elif isinstance(entities['brand'], list):
                    if entities['brand']:
                        brand_item = entities['brand'][0]
                        if isinstance(brand_item, dict):
                            normalized['brand'] = brand_item.get('en', '').upper()
                        else:
                            normalized['brand'] = str(brand_item).upper()
                else:
                    normalized['brand'] = str(entities['brand']).upper()
            
            # Обработка моделей
            if entities.get('model'):
                if isinstance(entities['model'], dict):
                    normalized['model'] = entities['model'].get('value', '')
                elif isinstance(entities['model'], list):
                    normalized['model'] = entities['model'][0] if entities['model'] else ''
                else:
                    normalized['model'] = entities['model']
            
            # Обработка цветов
            if entities.get('color'):
                if isinstance(entities['color'], list):
                    normalized['color'] = entities['color']
                elif isinstance(entities['color'], dict):
                    normalized['color'] = entities['color'].get('value', '')
                else:
                    normalized['color'] = entities['color']
            
            # Обработка цен
            if entities.get('price'):
                if isinstance(entities['price'], dict):
                    normalized['price'] = entities['price'].get('value', '')
                else:
                    normalized['price'] = entities['price']
            
            # Обработка диапазонов цен
            if entities.get('price_from'):
                normalized['price_from'] = entities['price_from']
            if entities.get('price_to'):
                normalized['price_to'] = entities['price_to']
            
            # Обработка городов
            if entities.get('city'):
                if isinstance(entities['city'], dict):
                    normalized['city'] = entities['city'].get('value', '')
                else:
                    normalized['city'] = entities['city']
            
            # Обработка типов кузова
            if entities.get('body_type'):
                if isinstance(entities['body_type'], dict):
                    normalized['body_type'] = entities['body_type'].get('value', '')
                elif isinstance(entities['body_type'], list):
                    normalized['body_type'] = entities['body_type']
                else:
                    normalized['body_type'] = entities['body_type']
            
            # Обработка опций
            if entities.get('option_codes'):
                normalized['option_description'] = entities['option_codes']
            elif entities.get('options'):
                if isinstance(entities['options'], list):
                    normalized['option_description'] = entities['options']
                elif isinstance(entities['options'], dict):
                    normalized['option_description'] = [entities['options'].get('value', '')]
                else:
                    normalized['option_description'] = [entities['options']]
            
            # Обработка пробега
            if entities.get('mileage'):
                normalized['mileage'] = entities['mileage']
            if entities.get('mileage_from'):
                normalized['mileage_from'] = entities['mileage_from']
            if entities.get('mileage_to'):
                normalized['mileage_to'] = entities['mileage_to']
            
            # Обработка года выпуска
            if entities.get('year'):
                normalized['year'] = entities['year']
            if entities.get('year_from'):
                normalized['year_from'] = entities['year_from']
            if entities.get('year_to'):
                normalized['year_to'] = entities['year_to']
            
            # Обработка состояния автомобиля
            if entities.get('state'):
                normalized['state'] = entities['state']
            
            # Обработка сценария (не передаем в search_all_cars)
            if entities.get('scenario'):
                # Сохраняем для внутреннего использования, но не передаем в БД
                pass
            
            # Обработка типа топлива
            if entities.get('fuel_type'):
                normalized['fuel_type'] = entities['fuel_type']
            
            # Обработка типа трансмиссии
            if entities.get('transmission'):
                normalized['transmission'] = entities['transmission']
            
            # Обработка типа привода
            if entities.get('drive_type'):
                normalized['drive_type'] = entities['drive_type']
            
            # Обработка дилера
            if entities.get('dealer'):
                normalized['dealer'] = entities['dealer']
            
            logger.info(f"NER extraction successful: {normalized}")
            
            # Дополнительное извлечение опций и типов топлива
            self._extract_additional_entities(query, normalized)
            
            return normalized
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            # Fallback на простую логику
            return self._fallback_entity_extraction(query)
    
    def _extract_additional_entities(self, query: str, entities: Dict[str, Any]):
        """Извлекает дополнительные сущности с улучшенными алгоритмами"""
        query_lower = query.lower()
        words = query_lower.split()
        
        # Извлечение опций с улучшенными алгоритмами
        from modules.classifiers.entity_extractor import OPTION_SYNONYMS
        
        found_options = []
        for option, patterns in OPTION_SYNONYMS.items():
            # 1. Прямое совпадение
            for pattern in patterns:
                if pattern in query_lower:
                    found_options.append(option)
                    break
            
            # 2. Контекстно-осведомленное сопоставление
            if option not in found_options:
                # Проверяем контекстное совпадение
                context_match = False
                for word in words:
                    for pattern in patterns:
                        if word in pattern or pattern in word:
                            context_match = True
                            break
                    if context_match:
                        break
                
                if context_match:
                    found_options.append(option)
                    continue
            
            # 3. Продвинутое fuzzy matching
            if option not in found_options:
                for word in words:
                    for pattern in patterns:
                        similarity = advanced_similarity_score(word, pattern)
                        if similarity >= 0.8:
                            found_options.append(option)
                            break
                    if option in found_options:
                        break
            
            # 4. TF-IDF косинусное сходство
            if option not in found_options:
                for word in words:
                    for pattern in patterns:
                        try:
                            from sklearn.feature_extraction.text import TfidfVectorizer
                            from sklearn.metrics.pairwise import cosine_similarity
                            
                            tfidf = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
                            tfidf_matrix = tfidf.fit_transform([word, pattern])
                            cosine_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                            
                            if cosine_score >= 0.7:
                                found_options.append(option)
                                break
                        except:
                            pass
                    if option in found_options:
                        break
        
        if found_options:
            entities['option_description'] = list(set(found_options))
        
        # Извлечение типов топлива с улучшенными алгоритмами
        from modules.classifiers.entity_extractor import FUEL_SYNONYMS
        
        found_fuels = []
        for fuel, patterns in FUEL_SYNONYMS.items():
            # 1. Прямое совпадение
            for pattern in patterns:
                if pattern in query_lower:
                    found_fuels.append(fuel)
                    break
            
            # 2. Контекстно-осведомленное сопоставление
            if fuel not in found_fuels:
                # Проверяем контекстное совпадение
                context_match = False
                for word in words:
                    for pattern in patterns:
                        if word in pattern or pattern in word:
                            context_match = True
                            break
                    if context_match:
                        break
                
                if context_match:
                    found_fuels.append(fuel)
                    continue
            
            # 3. Продвинутое fuzzy matching
            if fuel not in found_fuels:
                for word in words:
                    for pattern in patterns:
                        similarity = advanced_similarity_score(word, pattern)
                        if similarity >= 0.8:
                            found_fuels.append(fuel)
                            break
                    if fuel in found_fuels:
                        break
            
            # 4. TF-IDF косинусное сходство
            if fuel not in found_fuels:
                for word in words:
                    for pattern in patterns:
                        try:
                            from sklearn.feature_extraction.text import TfidfVectorizer
                            from sklearn.metrics.pairwise import cosine_similarity
                            
                            tfidf = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
                            tfidf_matrix = tfidf.fit_transform([word, pattern])
                            cosine_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                            
                            if cosine_score >= 0.7:
                                found_fuels.append(fuel)
                                break
                        except:
                            pass
                    if fuel in found_fuels:
                        break
        
        if found_fuels:
            entities['fuel_type'] = found_fuels[0] if len(found_fuels) == 1 else list(set(found_fuels))
    
    def _fuzzy_string_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Улучшенное нечеткое сравнение строк с использованием нескольких алгоритмов"""
        str1_lower = str1.lower().strip()
        str2_lower = str2.lower().strip()
        
        # 1. Точное совпадение
        if str1_lower == str2_lower:
            return True
        
        # 2. Jaro-Winkler расстояние
        if jellyfish.jaro_winkler_similarity(str1_lower, str2_lower) >= threshold:
            return True
        
        # 3. Расстояние Левенштейна
        if jellyfish.levenshtein_distance(str1_lower, str2_lower) <= 2:
            return True
        
        # 4. Метод Soundex для фонетического сравнения
        try:
            if jellyfish.soundex(str1_lower) == jellyfish.soundex(str2_lower):
                return True
        except:
            pass
        
        # 5. Метод Metaphone
        try:
            if jellyfish.metaphone(str1_lower) == jellyfish.metaphone(str2_lower):
                return True
        except:
            pass
        
        # 6. Частичное совпадение
        if len(str1_lower) > 3 and len(str2_lower) > 3:
            if str1_lower in str2_lower or str2_lower in str1_lower:
                return True
        
        # 7. TF-IDF косинусное сходство
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            tfidf = TfidfVectorizer(analyzer='char', ngram_range=(2, 4))
            tfidf_matrix = tfidf.fit_transform([str1_lower, str2_lower])
            cosine_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            if cosine_score >= threshold:
                return True
        except:
            pass
        
        # 8. Классический SequenceMatcher как fallback
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1_lower, str2_lower).ratio() >= threshold

    def _fallback_entity_extraction(self, query: str) -> Dict[str, Any]:
        """Fallback извлечение сущностей с улучшенной логикой"""
        entities = {}
        query_lower = query.lower()
        
        # Расширенный список брендов
        brands = [
            'bmw', 'mercedes', 'audi', 'toyota', 'honda', 'nissan', 'ford', 'chevrolet', 'volkswagen', 
            'hyundai', 'kia', 'renault', 'peugeot', 'opel', 'fiat', 'skoda', 'seat', 'volvo', 'saab', 
            'mazda', 'mitsubishi', 'subaru', 'lexus', 'infiniti', 'acura', 'porsche', 'jaguar', 
            'land rover', 'bentley', 'rolls royce', 'ferrari', 'lamborghini', 'maserati', 
            'aston martin', 'mclaren', 'lotus', 'alpine',
            'бмв', 'мерседес', 'ауди', 'тойота', 'хонда', 'ниссан', 'форд', 'шевроле', 'фольксваген', 
            'хендай', 'киа', 'рено', 'пежо', 'опель', 'фиат', 'шкода', 'сеат', 'вольво', 'сааб', 
            'мазда', 'мицубиси', 'субару', 'лексус', 'инфинити', 'акура', 'порше', 'ягуар', 
            'ленд ровер', 'бентли', 'роллс ройс', 'ферари', 'ламборгини', 'мазерати', 
            'астон мартин', 'маклерен', 'лотос', 'альпин'
        ]
        
        for brand in brands:
            if brand in query_lower:
                entities['brand'] = brand.upper()
                break
        
        # Расширенный список моделей
        models = [
            'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8',
            'z1', 'z2', 'z3', 'z4', 'z8', 'i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8',
            'gle', 'glc', 'gla', 'glb', 'gls', 's class', 'e class', 'c class', 'a class', 'b class',
            'camry', 'corolla', 'rav4', 'highlander', 'accord', 'civic', 'cr-v', 'pilot',
            'altima', 'sentra', 'rogue', 'pathfinder', 'escape', 'explorer', 'edge', 'fusion', 'focus',
            'silverado', 'malibu', 'cruze', 'equinox', 'traverse', 'golf', 'passat', 'jetta', 'tiguan',
            'tucson', 'santa fe', 'sportage', 'sorento', 'optima', 'forte', 'soul',
            'megane', 'clio', 'captur', 'kadjar', '3008', '5008', '208', '308', 'astra', 'corsa',
            'insignia', 'vectra', 'punto', 'panda', '500', 'doblo', 'linea', 'bravo', 'stilo',
            'octavia', 'fabia', 'rapid', 'superb', 'leon', 'ibiza', 'toledo',
            's60', 's80', 's90', 'v60', 'v90', 'xc40', 'xc60', 'xc90',
            'cx-3', 'cx-5', 'cx-9', 'mx-5', 'miata', 'outlander', 'lancer', 'asx',
            'impreza', 'forester', 'legacy', 'outback', 'wrx', 'sti',
            'is', 'es', 'gs', 'ls', 'rc', 'lc', 'nx', 'rx', 'lx', 'gx',
            'qx30', 'qx50', 'qx60', 'qx70', 'qx80', 'tlx', 'rdx', 'mdx', 'ilx', 'nsx',
            '911', 'cayenne', 'macan', 'panamera', 'boxster', 'cayman',
            'f-type', 'e-pace', 'f-pace', 'i-pace', 'range rover', 'discovery', 'defender',
            'continental', 'flying spur', 'mulsanne', 'phantom', 'ghost', 'wraith', 'dawn',
            '488', 'f8', '812', 'sf90', 'huracan', 'aventador', 'urus',
            'ghibli', 'quattroporte', 'levante', 'db11', 'vantage', 'dbs', 'rapide',
            '720s', '570s', '540c', 'elise', 'exige', 'evora', 'emira', 'a110'
        ]
        
        for model in models:
            if model in query_lower:
                entities['model'] = model.upper()
                break
        
        # Расширенный список цветов
        colors = [
            'красный', 'синий', 'зеленый', 'желтый', 'белый', 'черный', 'серый', 'серебристый',
            'золотой', 'коричневый', 'оранжевый', 'фиолетовый', 'розовый', 'голубой',
            'красная', 'синяя', 'зеленая', 'желтая', 'белая', 'черная', 'серая', 'серебристая',
            'золотая', 'коричневая', 'оранжевая', 'фиолетовая', 'розовая', 'голубая',
            'red', 'blue', 'green', 'yellow', 'white', 'black', 'gray', 'silver',
            'gold', 'brown', 'orange', 'purple', 'pink', 'cyan'
        ]
        
        for color in colors:
            if color in query_lower:
                entities['color'] = color
                break
        
        # Извлечение цен
        price_patterns = [
            r'(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)',
            r'до\s*(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)',
            r'цена\s*(?:до|от)?\s*(\d+(?:\s*\d+)*)\s*(?:млн|миллион|тысяч|тыс|руб|рублей|₽)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, query_lower)
            if match:
                price_str = match.group(1).replace(' ', '')
                if 'млн' in query_lower or 'миллион' in query_lower:
                    entities['price_to'] = int(price_str) * 1000000
                elif 'тыс' in query_lower or 'тысяч' in query_lower:
                    entities['price_to'] = int(price_str) * 1000
                else:
                    entities['price_to'] = int(price_str)
                break
        
        # Извлечение годов
        year_patterns = [
            r'(\d{4})\s*(?:год|года|году)',
            r'(\d{4})-(\d{4})',
            r'от\s*(\d{4})\s*до\s*(\d{4})'
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, query)
            if match:
                if len(match.groups()) == 2:
                    entities['year_from'] = int(match.group(1))
                    entities['year_to'] = int(match.group(2))
                else:
                    entities['year_from'] = int(match.group(1))
                break
        
        # Извлечение типов кузова
        body_types = [
            'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер', 'кабриолет', 'купе',
            'лимузин', 'пикап', 'фургон', 'микроавтобус',
            'sedan', 'hatchback', 'wagon', 'suv', 'crossover', 'cabriolet', 'coupe',
            'limousine', 'pickup', 'van', 'minibus'
        ]
        
        for body_type in body_types:
            if body_type in query_lower:
                entities['body_type'] = body_type
                break
        
        # Извлечение типов топлива
        fuel_types = [
            'бензин', 'дизель', 'электро', 'гибрид', 'бензиновый', 'дизельный', 'электрический', 'гибридный',
            'petrol', 'diesel', 'electric', 'hybrid', 'gasoline'
        ]
        
        for fuel_type in fuel_types:
            if fuel_type in query_lower:
                entities['fuel_type'] = fuel_type
                break
        
        # Извлечение коробок передач
        transmission_types = [
            'автомат', 'механика', 'робот', 'вариатор', 'автоматическая', 'механическая', 'роботизированная',
            'automatic', 'manual', 'robot', 'cvt', 'auto', 'manual'
        ]
        
        for transmission in transmission_types:
            if transmission in query_lower:
                entities['transmission'] = transmission
                break
        
        # Извлечение типов привода
        drive_types = [
            'передний', 'задний', 'полный', 'передний привод', 'задний привод', 'полный привод',
            'front', 'rear', 'all', 'awd', 'fwd', 'rwd', '4wd'
        ]
        
        for drive_type in drive_types:
            if drive_type in query_lower:
                entities['drive_type'] = drive_type
                break
        
        # Извлечение состояний
        states = [
            'новый', 'подержанный', 'б/у', 'с пробегом', 'без пробега',
            'new', 'used', 'second-hand', 'with mileage', 'without mileage'
        ]
        
        for state in states:
            if state in query_lower:
                entities['state'] = state
                break
        
        # Извлечение сценариев
        scenarios = {
            'семейный': 'family', 'семья': 'family',
            'городской': 'city', 'город': 'city',
            'путешествие': 'travel', 'путешествия': 'travel',
            'бизнес': 'business',
            'экономичный': 'economy', 'экономия': 'economy',
            'family': 'family', 'city': 'city', 'travel': 'travel',
            'business': 'business', 'economy': 'economy', 'economic': 'economy'
        }
        
        for scenario_key, scenario_value in scenarios.items():
            if scenario_key in query_lower:
                entities['scenario'] = scenario_value
                break
        
        # Извлечение городов
        cities = [
            'москва', 'спб', 'питер', 'санкт-петербург', 'ростов', 'новосибирск', 'екатеринбург',
            'казань', 'нижний новгород', 'челябинск', 'самара', 'омск', 'уфа', 'красноярск',
            'пермь', 'воронеж', 'волгоград', 'краснодар', 'саратов', 'тихорецк', 'тихорецкая',
            'moscow', 'spb', 'petersburg', 'rostov', 'novosibirsk', 'yekaterinburg', 'kazan',
            'nizhny novgorod', 'chelyabinsk', 'samara', 'omsk', 'ufa', 'krasnoyarsk', 'perm',
            'voronezh', 'volgograd', 'krasnodar', 'saratov', 'tikhoretsk'
        ]
        
        for city in cities:
            if city in query_lower:
                entities['city'] = city
                break
        
        return entities
    
    def _clean_filters_for_search(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Очищает фильтры от неподдерживаемых параметров для search_all_cars"""
        # Параметры, которые поддерживает search_all_cars
        supported_params = {
            'brand', 'model', 'year_from', 'year_to', 'price_from', 'price_to',
            'fuel_type', 'transmission', 'body_type', 'drive_type', 'state',
            'sort_by', 'sort_order', 'option_code', 'option_description', 'city'
        }
        
        cleaned_filters = {}
        for key, value in filters.items():
            if key in supported_params:
                cleaned_filters[key] = value
            elif key == 'price':
                # Преобразуем price в price_to для совместимости
                cleaned_filters['price_to'] = value
        
        return cleaned_filters
    
    def _summarize_prompt(self, prompt: str, max_length: int = 2000) -> str:
        """Сокращает длинный промпт"""
        if len(prompt) <= max_length:
            return prompt
        
        # Простое сокращение - берем начало и конец
        half_length = max_length // 2
        return prompt[:half_length] + "\n...\n" + prompt[-half_length:]
    
    async def async_process_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Асинхронная обработка пакета запросов"""
        tasks = []
        for query in queries:
            task = asyncio.create_task(self.async_process_single_query(query))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing query '{queries[i]}': {result}")
                processed_results.append({
                    'type': 'error',
                    'message': f'Ошибка обработки: {str(result)}',
                    'query': queries[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def async_process_single_query(self, query: str) -> Dict[str, Any]:
        """Асинхронная обработка одного запроса"""
        start_time = time.time()
        
        try:
            # Извлечение сущностей (кэшированное)
            entities = self._get_cached_ner(query)
            
            # Асинхронная генерация фильтров
            filter_prompt = self._build_filter_prompt(query)
            llama_response = await self.async_generate_with_llama(filter_prompt)
            
            # Парсинг JSON
            filters = self.json_validator.parse_llama_filters(llama_response)
            
            # Очищаем фильтры от неподдерживаемых параметров
            filters = self._clean_filters_for_search(filters)
            
            # Поиск автомобилей
            from database import search_all_cars
            cars = search_all_cars(**filters, limit=50)
            
            # Выбор релевантных автомобилей
            relevant_cars = self.car_selector.select_relevant_cars(cars, query, limit=5)
            
            # Генерация финального ответа
            if relevant_cars:
                final_prompt = self._build_final_prompt(query, relevant_cars)
                final_response = await self.async_generate_with_llama(final_prompt)
            else:
                final_response = "К сожалению, не найдено автомобилей, соответствующих вашим критериям."
            
            # Логирование метрик
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                parse_success=bool(filters),
                error=False,
                ner_success=True
            )
            
            return {
                'type': 'car_search_response',
                'message': final_response,
                'cars': relevant_cars,
                'filters': filters,
                'processing_time': processing_time,
                'query': query
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                error=True
            )
            
            logger.error(f"Async error processing query '{query}': {e}")
            return {
                'type': 'error',
                'message': 'Извините, произошла ошибка при обработке запроса.',
                'error': str(e),
                'query': query
            }
    
    async def async_generate_with_llama(self, prompt: str) -> str:
        """Асинхронная генерация через LLAMA"""
        from llama_service import LLAMA_URLS
        
        payload = {
            "model": "llama3:8b",
            "prompt": prompt,
            "stream": False
        }
        
        for url in LLAMA_URLS:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=90) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("response", "")
                        else:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.error(f"Async LLAMA error for {url}: {e}")
                continue
        
        raise Exception("All LLAMA endpoints failed")
    
    def _generate_with_llama_sync(self, prompt: str) -> str:
        """Синхронная генерация через LLAMA"""
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3:8b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Извините, не удалось получить ответ.')
            else:
                return f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при генерации через Llama: {e}")
            return "Извините, произошла ошибка при обработке запроса."
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Основной метод обработки запроса (синхронный) с улучшенной логикой"""
        start_time = time.time()
        
        try:
            # Валидируем запрос
            is_valid, error_msg = self.validate_query(query)
            if not is_valid:
                return {
                    'type': 'error',
                    'response': error_msg,
                    'cars': [],
                    'entities': {},
                    'missing_info': [],
                    'scenario': '',
                    'processing_time': time.time() - start_time
                }
            
            # Получаем сущности из NER
            entities = self._get_cached_ner(query)
            
            # Анализируем полноту запроса
            missing_info = self._analyze_query_completeness(entities)
            
            # Определяем сценарий
            scenario = entities.get('scenario', '')
            
            # Определяем тип ответа
            response_type = self._determine_response_type(query, entities)
            
            # Обрабатываем специальные типы запросов
            if response_type == 'loan':
                logger.info(f"Обрабатываем кредитный запрос: {query}")
                return self.process_loan_request(query)
            elif response_type == 'help':
                logger.info(f"Обрабатываем запрос помощи: {query}")
                return self.process_help_request(query)
            elif response_type == 'chitchat':
                logger.info(f"Обрабатываем светскую беседу: {query}")
                return self.process_chitchat_request(query)
            
            # Проверяем, является ли запрос общим (не автомобильным)
            general_patterns = [
                # Сложные запросы с множественными темами
                'сравни подходы', 'сравнительный анализ', 'проведи анализ',
                'эпидемии', 'чума', 'оспа', 'средневековье', 'эпоха Просвещения',
                'культурные представления', 'религиозные представления',
                'стихи', 'прозу', 'автор', 'Достоевского', 'философия искусства',
                'концепция авторства', 'творчество', 'ИИ создающий',
                'музыкальные жанры', 'классика', 'рок', 'электронная музыка',
                'мозговые волны', 'когнитивные функции', 'терапевтические эффекты',
                'религиозные войны', 'Ближний Восток', 'геополитические',
                'социокультурные паттерны', 'сравнительный анализ причин',
                # Личные вопросы
                'как тебя зовут', 'кто ты', 'что ты', 'расскажи о себе', 'кто ты такой',
                'твоя семья', 'твои друзья', 'твои увлечения', 'твои интересы',
                'твоя работа', 'твоя учеба', 'твои планы', 'твои мечты',
                'твои чувства', 'твои эмоции', 'твои мысли', 'твое мнение',
                
                # Общение и отслеживание
                'отслеживаешь ли ты', 'тему нашего общения', 'понимаешь ли ты',
                'запоминаешь', 'помнишь', 'знаешь', 'осознаешь', 'понимаешь',
                
                # Домашние животные и личные вещи
                'у тебя живут', 'рыбки дома', 'домашние животные', 'питомцы',
                'твоя квартира', 'твой дом', 'твоя комната', 'твои вещи',
                
                # Общие вопросы о возможностях
                'что ты умеешь', 'какие у тебя возможности', 'функции', 'способности',
                'помощь', 'справка', 'инструкция', 'руководство', 'как пользоваться',
                
                # Приветствия и общение
                'как дела', 'привет', 'здравствуй', 'добрый день', 'добрый вечер',
                'как ты', 'как жизнь', 'как настроение', 'как поживаешь',
                
                # Философские и абстрактные вопросы
                'какая марка наиболее быстрая', 'смысл жизни', 'цель существования',
                'философия', 'религия', 'душа', 'сознание', 'мышление',
                'истина', 'ложь', 'добро', 'зло', 'красота', 'искусство',
                
                # Время и дата
                'сколько времени', 'который час', 'какая дата', 'какой день',
                'какой месяц', 'какой год', 'календарь', 'расписание',
                
                # Математика и вычисления
                'посчитай', 'вычисли', 'математика', 'арифметика', 'калькулятор',
                'формула', 'уравнение', 'задача', 'пример', 'процент',
                
                # Погода и природа
                'какая погода', 'температура', 'дождь', 'снег', 'солнце',
                'холодно', 'жарко', 'тепло', 'мороз', 'жара',
                
                # Общие вопросы о мире
                'что происходит', 'что нового', 'что интересного', 'что модно',
                'что популярно', 'что актуально', 'что трендово',
                
                # Вопросы о здоровье и самочувствии
                'как здоровье', 'как самочувствие', 'болит', 'недомогание',
                'усталость', 'энергия', 'силы', 'бодрость',
                
                # Вопросы о работе и учебе
                'как работа', 'как учеба', 'как дела на работе', 'как дела в школе',
                'как дела в университете', 'как экзамены', 'как сессия',
                
                # Вопросы о семье и отношениях
                'как семья', 'как дети', 'как родители', 'как отношения',
                'как любовь', 'как дружба', 'как знакомства',
                
                # Вопросы о хобби и увлечениях
                'как хобби', 'как увлечения', 'как отдых', 'как развлечения',
                'как спорт', 'как музыка', 'как фильмы', 'как книги',
                
                # Вопросы о путешествиях
                'как путешествия', 'как поездки', 'как отпуск', 'как каникулы',
                'как командировки', 'как поездки за границу',
                
                # Вопросы о технологиях
                'как интернет', 'как технологии', 'как гаджеты', 'как приложения',
                'как социальные сети', 'как мессенджеры',
                
                # Вопросы о еде и кулинарии
                'как еда', 'как кухня', 'как готовка', 'как рецепты',
                'как рестораны', 'как кафе', 'как кулинария',
                
                # Вопросы о моде и стиле
                'как мода', 'как стиль', 'как одежда', 'как обувь',
                'как аксессуары', 'как косметика', 'как парфюм',
                
                # Вопросы о деньгах и финансах
                'как деньги', 'как финансы', 'как бюджет', 'как экономика',
                'как инвестиции', 'как банки', 'как кредиты',
                
                # Вопросы о политике и обществе
                'как политика', 'как общество', 'как новости', 'как события',
                'как выборы', 'как законы', 'как права',
                
                # Вопросы о науке и образовании
                'как наука', 'как образование', 'как исследования', 'как открытия',
                'как изобретения', 'как инновации', 'как технологии',
                
                # Вопросы о культуре и искусстве
                'как культура', 'как искусство', 'как музыка', 'как живопись',
                'как литература', 'как театр', 'как кино',
                
                # Вопросы о спорте и фитнесе
                'как спорт', 'как фитнес', 'как тренировки', 'как соревнования',
                'как олимпиада', 'как чемпионат', 'как турнир',
                
                # Вопросы о здоровье и медицине
                'как здоровье', 'как медицина', 'как лечение', 'как врачи',
                'как больницы', 'как лекарства', 'как профилактика',
                
                # Вопросы о психологии
                'как психология', 'как эмоции', 'как чувства', 'как стресс',
                'как депрессия', 'как тревога', 'как счастье',
                
                # Вопросы о языке и лингвистике
                'как язык', 'как грамматика', 'как произношение', 'как перевод',
                'как словарь', 'как лингвистика', 'как филология',
                
                # Вопросы о книгах и литературе
                'как книги', 'как литература', 'как чтение', 'как библиотека',
                'как писатели', 'как поэты', 'как издательства',
                
                # Вопросы о фильмах и сериалах
                'как фильмы', 'как сериалы', 'как кино', 'как актеры',
                'как режиссеры', 'как сценарии', 'как спецэффекты',
                
                # Вопросы об играх
                'как игры', 'как видеоигры', 'как настольные игры',
                'как компьютерные игры', 'как мобильные игры',
                
                # Вопросы о семье
                'как семья', 'как дети', 'как родители', 'как братья',
                'как сестры', 'как бабушки', 'как дедушки',
                
                # Вопросы о друзьях
                'как друзья', 'как подруги', 'как знакомые', 'как приятели',
                'как общение', 'как разговоры', 'как встречи',
                
                # Вопросы об эмоциях
                'как настроение', 'как радость', 'как грусть', 'как злость',
                'как страх', 'как любовь', 'как симпатия',
                
                # Вопросы о характере
                'как характер', 'как личность', 'как темперамент',
                'как привычки', 'как черты', 'как качества',
                
                # Вопросы о целях
                'как цели', 'как мечты', 'как планы', 'как амбиции',
                'как будущее', 'как перспективы', 'как возможности',
                
                # Вопросы о проблемах
                'как проблемы', 'как трудности', 'как решения', 'как выходы',
                'как способы', 'как методы', 'как подходы',
                
                # Вопросы о вопросах
                'как вопросы', 'как ответы', 'как объяснения', 'как информация',
                'как данные', 'как факты', 'как исследования',
                
                            # Абстрактные вопросы
            'как случайность', 'как совпадение', 'как удача', 'как везение',
            'как абстракция', 'как концепция', 'как идея', 'как мысль',
            'как фантазия', 'как воображение', 'как творчество',
            
            # Философия и этика
            'философия', 'этика', 'смысл жизни', 'сознание', 'человеческое сознание',
            'этические дебаты', 'мораль', 'ценности', 'истина', 'добро', 'зло',
            'свобода воли', 'детерминизм', 'экзистенциализм', 'гуманизм',
            
            # Технологии и ИИ
            'искусственный интеллект', 'ИИ', 'робототехника', 'технологии',
            'цифровизация', 'автоматизация', 'алгоритмы', 'машинное обучение',
            'нейросети', 'большие данные', 'анализ данных', 'криптовалюты',
            'блокчейн', 'виртуальная реальность', 'дополненная реальность',
            
            # Наука и исследования
            'наука', 'исследования', 'эксперименты', 'теория', 'гипотеза',
            'физика', 'химия', 'биология', 'генетика', 'нейробиология',
            'психология', 'социология', 'антропология', 'археология',
            
            # Медицина и здоровье
            'медицина', 'здоровье', 'лечение', 'профилактика', 'диагностика',
            'генетическое редактирование', 'CRISPR', 'эпидемии', 'вакцинация',
            'иммунитет', 'метаболизм', 'физиология',
            
            # Экономика и финансы
            'экономика', 'финансы', 'инфляция', 'безработица', 'конкурентоспособность',
            'налоговая реформа', 'углеродный налог', 'субсидии', 'инвестиции',
            'рынок', 'спрос', 'предложение', 'ВВП', 'инфраструктура',
            
            # Экология и климат
            'экология', 'климат', 'глобальное потепление', 'углеродный след',
            'возобновляемые источники энергии', 'ВИЭ', 'зеленая энергия',
            'вечная мерзлота', 'метан', 'озоновые дыры', 'загрязнение',
            
            # Политика и международные отношения
            'политика', 'международные отношения', 'геополитика', 'конфликты',
            'войны', 'религиозные войны', 'Ближний Восток', 'ЕС', 'ООН',
            'соглашения', 'протоколы', 'санкции', 'дипломатия',
            
            # История и культура
            'история', 'культура', 'средневековье', 'эпоха Просвещения',
            'религия', 'традиции', 'обычаи', 'цивилизация', 'архитектура',
            'памятники', 'музеи', 'наследие', 'археология',
            
            # Психология и отношения
            'психология', 'эмоции', 'эмпатия', 'отношения', 'дружба',
            'социальные сети', 'мессенджеры', 'поколение Z', 'когнитивные функции',
            'память', 'внимание', 'стресс', 'тревога', 'депрессия',
            
            # Искусство и творчество
            'искусство', 'творчество', 'литература', 'поэзия', 'проза',
            'авторство', 'философия искусства', 'стихи', 'автор', 'писатель',
            'художник', 'композитор', 'режиссер', 'актер',
            
            # Образование и работа
            'образование', 'работа', 'профессии', 'навыки', 'hard skills',
            'soft skills', 'образовательные траектории', 'университет', 'школа',
            'курсы', 'тренинги', 'сертификация', 'карьера',
            
            # Транспорт и логистика
            'транспорт', 'логистика', 'вакуумные поезда', 'Hyperloop',
            'материалы', 'энергоснабжение', 'безопасность', 'инфраструктура',
            'скорость', 'эффективность', 'экологичность',
            
            # Музыка и звук
            'музыка', 'музыкальные жанры', 'классика', 'рок', 'электронная музыка',
            'мозговые волны', 'терапевтические эффекты', 'звук', 'ритм',
            'мелодия', 'гармония', 'инструменты', 'оркестр',
            
            # Кулинария и питание
            'кулинария', 'питание', 'диета', 'средиземноморская диета',
            'пищевая химия', 'ферментация', 'маринование', 'продукты',
            'ингредиенты', 'готовка', 'рецепты', 'калории', 'витамины',
            
            # Спорт и фитнес
            'спорт', 'фитнес', 'тренировки', 'HIIT', 'кардионагрузки',
            'выносливость', 'метаболизм', 'перетренированность', 'физическая активность',
            'упражнения', 'соревнования', 'олимпиада', 'чемпионат',
            
            # Кино и медиа
            'кино', 'фильмы', 'стриминговые платформы', 'Netflix', 'кинопроцесс',
            'финансирование', 'монтаж', 'кинотеатры', 'жанры', 'зрители',
            'актеры', 'режиссеры', 'сценарий', 'спецэффекты',
            
            # Юриспруденция и право
            'юриспруденция', 'право', 'законы', 'соглашения', 'протоколы',
            'международное право', 'санкции', 'обязательства', 'принуждение',
            'юридические механизмы', 'суд', 'законодательство',
            
            # География и регионы
            'география', 'регионы', 'Сибирь', 'Канада', 'Европа',
            'Ближний Восток', 'страны', 'города', 'климат', 'ландшафт',
            'природные ресурсы', 'территория',
            
            # Время и прогнозы
            'будущее', 'прогнозы', 'ближайшие 50 лет', 'через 10 лет',
            'тенденции', 'развитие', 'эволюция', 'прогресс', 'инновации',
            'изменения', 'трансформация',
            
            # Сравнения и анализ
            'сравни', 'сравнительный анализ', 'анализ', 'исследование',
            'изучение', 'объясни', 'опиши', 'проанализируй', 'спрогнозируй',
            'обсуди', 'проведи анализ', 'сравни подходы',
            
            # Данные и исследования
            'данные', 'исследования', 'статистика', 'методы', 'результаты',
            'выводы', 'доказательства', 'научно доказанные', 'эффективность',
            'риски', 'последствия', 'влияние'
        ]
            
            query_lower = query.lower()
            is_general_query = any(pattern in query_lower for pattern in general_patterns)
            
            if is_general_query:
                logger.info(f"Общий запрос: {query}")
                # Отправляем в Ollama для общего ответа
                return self._process_query_without_entities(query)
            
            # Проверяем, есть ли сущности для поиска
            has_entities = bool(entities.get('brand') or entities.get('model') or 
                              entities.get('price') or entities.get('color') or 
                              entities.get('body_type') or entities.get('fuel_type'))
            
            if has_entities:
                logger.info(f"Запрос с сущностями: {entities}")
                # Обрабатываем через поиск и LLAMA
                return self._process_query_with_entities(query, entities, response_type, scenario)
            else:
                logger.info(f"Запрос без сущностей, отправляем в Ollama")
                # Отправляем в Ollama для общего ответа
                return self._process_query_without_entities(query)
                
        except Exception as e:
            logger.error(f"Критическая ошибка в process_query: {e}")
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=False,
                cache_hit=False,
                error=True,
                parse_success=False,
                ner_success=False,
                context_used=False,
                fallback_used=False
            )
            
            return {
                'type': 'error',
                'response': 'Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать.',
                'cars': [],
                'entities': {},
                'missing_info': [],
                'scenario': '',
                'processing_time': processing_time
            }
    
    def _process_query_with_entities(self, query: str, entities: Dict[str, Any], response_type: str, scenario: str) -> Dict[str, Any]:
        """
        Обрабатывает запрос с сущностями через поиск и LLAMA
        """
        try:
            # Строим промпт для поиска
            if scenario:
                prompt = self._build_scenario_prompt(query, scenario)
            else:
                prompt = self._build_filter_prompt(query)
            
            # Генерируем ответ через LLAMA для извлечения фильтров
            try:
                # Используем синхронный вызов вместо asyncio.run
                llama_response = self._generate_with_llama_sync(prompt)
                filters = JSONValidator.parse_llama_filters(llama_response)
            except Exception as e:
                logger.warning(f"Ошибка LLAMA: {e}, используем только NER сущности")
                filters = {}
            
            # Объединяем сущности и фильтры
            combined_filters = {**entities, **filters}
            
            # Очищаем фильтры для поиска
            combined_filters = self._clean_filters_for_search(combined_filters)
            
            # Ищем автомобили
            try:
                cars = search_all_cars(**combined_filters)
            except Exception as e:
                logger.error(f"Ошибка поиска автомобилей: {e}")
                cars = []
            
            # Выбираем топ-5 релевантных автомобилей
            relevant_cars = self.car_selector.select_relevant_cars(cars, query, limit=5)
            
            # Строим промпт для LLAMA с найденными автомобилями
            if relevant_cars:
                final_prompt = self._build_car_analysis_prompt(query, relevant_cars)
            else:
                final_prompt = self._build_no_cars_prompt(query, combined_filters)
            
            # Генерируем финальный ответ через LLAMA
            try:
                # Используем синхронный вызов вместо asyncio.run
                final_response = self._generate_with_llama_sync(final_prompt)
            except Exception as e:
                logger.warning(f"Ошибка финального LLAMA: {e}")
                if relevant_cars:
                    final_response = f"Найдено {len(relevant_cars)} автомобилей по вашему запросу."
                else:
                    final_response = "К сожалению, по вашему запросу не найдено подходящих автомобилей."
            
            return {
                'type': 'car_analysis',
                'response': final_response,
                'cars': relevant_cars,
                'entities': entities,
                'processing_time': time.time()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса с сущностями: {e}")
            return {
                'type': 'error',
                'response': 'Извините, произошла ошибка при обработке запроса.',
                'cars': [],
                'entities': entities,
                'processing_time': time.time()
            }
    
    def _process_query_without_entities(self, query: str) -> Dict[str, Any]:
        """
        Обрабатывает запрос без сущностей через Ollama
        """
        try:
            import requests
            
            # Отправляем запрос в Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3:8b",
                    "prompt": self._build_ollama_prompt(query),
                    "stream": False
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'type': 'ollama_response',
                    'response': result.get('response', 'Извините, не удалось получить ответ.'),
                    'cars': [],
                    'entities': {},
                    'ollama': True,
                    'processing_time': time.time()
                }
            else:
                return {
                    'type': 'error',
                    'response': 'Извините, не удалось обработать запрос.',
                    'cars': [],
                    'entities': {},
                    'processing_time': time.time()
                }
                
        except Exception as e:
            logger.error(f"Ошибка при отправке запроса в Ollama: {e}")
            return {
                'type': 'error',
                'response': 'Извините, произошла ошибка при обработке запроса.',
                'cars': [],
                'entities': {},
                'processing_time': time.time()
            }
    
    def _build_ollama_prompt(self, query: str) -> str:
        """
        Строит промпт для Ollama
        """
        return f"""Вы являетесь профессиональным автоассистентом компании ААА МОТОРС - ведущего автомобильного дилера в России. 

ВАШИ ОБЯЗАННОСТИ:
- Отвечайте на вопросы клиентов максимально вежливо, дружелюбно и профессионально
- Обращайтесь к клиентам на "Вы" с большой буквы
- Используйте теплый, приветливый тон, но оставайтесь профессиональным
- Предоставляйте полные, полезные и информативные ответы
- Помогайте с любыми вопросами о автомобилях, сервисе, финансировании
- Если вопрос не связан с автомобилями, отвечайте вежливо и тактично направляйте к автомобильной тематике
- Всегда будьте готовы помочь и поддержать клиента

СТИЛЬ ОБЩЕНИЯ:
- Строго формальное обращение на "Вы" с большой буквы
- Обращение "Здравствуйте" вместо "Привет"
- Использование "Вас", "Вам", "Ваш" вместо "тебя", "тебе", "твой"
- Использование "хотите", "интересуетесь" вместо "хочешь", "интересуешься"
- Профессиональный, но дружелюбный тон
- Никаких неформальных обращений
- Полезный и информативный

КОМПАНИЯ ААА МОТОРС:
- Официальный дилер ведущих автомобильных брендов
- Полный спектр услуг: продажа, сервис, кредитование, страхование
- Профессиональные консультации и индивидуальный подход
- Гарантия качества и надежности

ВОПРОС КЛИЕНТА: {query}

Пожалуйста, дайте дружелюбный, вежливый и профессиональный ответ:"""
    
    def _build_car_analysis_prompt(self, query: str, cars: List[Dict]) -> str:
        """
        Строит промпт для анализа найденных автомобилей
        """
        cars_info = []
        for i, car in enumerate(cars, 1):
            cars_info.append(f"""
{i}. {car.get('mark', '')} {car.get('model', '')} {car.get('manufacture_year', '')}
   Цена: {car.get('price', 0):,} ₽
   Город: {car.get('city', '')}
   Тип кузова: {car.get('body_type', '')}
   Топливо: {car.get('fuel_type', '')}
   Пробег: {car.get('mileage', 0):,} км""")
        
        return f"""Вы являетесь профессиональным автоассистентом компании ААА МОТОРС. Проанализируйте найденные автомобили и дайте подробный ответ клиенту.

СТИЛЬ ОБЩЕНИЯ:
- Строго формальное обращение на "Вы" с большой буквы
- Обращение "Здравствуйте" вместо "Привет"
- Использование "Вас", "Вам", "Ваш" вместо "тебя", "тебе", "твой"
- Использование "хотите", "интересуетесь" вместо "хочешь", "интересуешься"
- Профессиональный, но дружелюбный тон
- Никаких неформальных обращений
- Полезный и информативный

ЗАПРОС КЛИЕНТА: {query}

НАЙДЕННЫЕ АВТОМОБИЛИ:
{chr(10).join(cars_info)}

Пожалуйста, дайте подробный анализ найденных автомобилей, учитывая запрос клиента. Обращайтесь на "Вы" и будьте вежливы, дружелюбны и профессиональны."""
    
    def _build_no_cars_prompt(self, query: str, filters: Dict[str, Any]) -> str:
        """
        Строит промпт для случая, когда автомобили не найдены
        """
        return f"""Вы являетесь профессиональным автоассистентом компании ААА МОТОРС. Клиент искал автомобили, но ничего не найдено.

СТИЛЬ ОБЩЕНИЯ:
- Строго формальное обращение на "Вы" с большой буквы
- Обращение "Здравствуйте" вместо "Привет"
- Использование "Вас", "Вам", "Ваш" вместо "тебя", "тебе", "твой"
- Использование "хотите", "интересуетесь" вместо "хочешь", "интересуешься"
- Профессиональный, но дружелюбный тон
- Никаких неформальных обращений
- Полезный и информативный

ЗАПРОС КЛИЕНТА: {query}

ПРИМЕНЕННЫЕ ФИЛЬТРЫ: {filters}

Пожалуйста, вежливо и дружелюбно сообщите клиенту, что по его запросу ничего не найдено, и предложите альтернативы или уточнения параметров поиска. Обращайтесь на "Вы" и будьте максимально полезны."""
    
    def process_comparison_request(self, query: str, car_ids: List[int] = None) -> Dict[str, Any]:
        """Обрабатывает запрос на сравнение автомобилей"""
        start_time = time.time()
        
        try:
            from database import search_all_cars
            
            # Если указаны конкретные ID автомобилей
            if car_ids:
                cars = []
                for car_id in car_ids:
                    car = search_all_cars(id=car_id, limit=1)
                    if car:
                        cars.extend(car)
            else:
                # Извлекаем сущности для поиска
                entities = self._get_cached_ner(query)
                cars = search_all_cars(**entities, limit=10)
            
            if len(cars) < 2:
                return {
                    'type': 'error',
                    'message': 'Для сравнения нужно минимум 2 автомобиля. Уточните параметры поиска.'
                }
            
            # Строим промпт для сравнения
            comparison_prompt = self._build_comparison_prompt(query, cars[:5])  # Ограничиваем до 5
            comparison_response = self._generate_cached_response(hash(comparison_prompt))
            
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                parse_success=True,
                error=False
            )
            
            return {
                'type': 'comparison',
                'message': comparison_response,
                'cars': cars[:5],
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                error=True
            )
            
            logger.error(f"Error processing comparison request '{query}': {e}")
            return {
                'type': 'error',
                'message': 'Извините, произошла ошибка при сравнении автомобилей.',
                'error': str(e)
            }
    
    def process_scenario_request(self, query: str, scenario: str) -> Dict[str, Any]:
        """Обрабатывает запрос для конкретного сценария"""
        start_time = time.time()
        
        try:
            # Извлекаем сущности
            entities = self._get_cached_ner(query)
            
            # Добавляем сценарий в сущности (только для внутреннего использования)
            entities['scenario'] = scenario
            
            # Строим промпт для сценария
            scenario_prompt = self._build_scenario_prompt(query, scenario)
            llama_response = self._generate_cached_response(hash(scenario_prompt))
            
            # Парсим фильтры
            filters = self.json_validator.parse_llama_filters(llama_response)
            
            # Очищаем фильтры от неподдерживаемых параметров
            filters = self._clean_filters_for_search(filters)
            
            # Объединяем фильтры (без scenario)
            combined_filters = {**entities, **filters}
            
            # Убираем scenario из фильтров для поиска
            if 'scenario' in combined_filters:
                del combined_filters['scenario']
            
            # Дополнительная очистка
            combined_filters = self._clean_filters_for_search(combined_filters)
            
            # Поиск автомобилей
            from database import search_all_cars
            cars = search_all_cars(**combined_filters, limit=20)
            
            # Выбор релевантных автомобилей
            relevant_cars = self.car_selector.select_relevant_cars(cars, query, limit=5)
            
            # Генерация ответа
            if relevant_cars:
                final_prompt = self._build_final_prompt(query, relevant_cars)
                final_response = self._generate_cached_response(hash(final_prompt))
            else:
                final_response = f"К сожалению, не найдено автомобилей для сценария '{scenario}'. Попробуйте уточнить параметры."
            
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                parse_success=bool(filters),
                error=False,
                ner_success=True
            )
            
            return {
                'type': 'scenario_response',
                'message': final_response,
                'cars': relevant_cars,
                'scenario': scenario,
                'filters': combined_filters,
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics.log_request(
                processing_time=processing_time,
                llama_used=True,
                error=True
            )
            
            logger.error(f"Error processing scenario request '{query}' for scenario '{scenario}': {e}")
            return {
                'type': 'error',
                'message': f'Извините, произошла ошибка при обработке сценария "{scenario}".',
                'error': str(e)
            }
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Возвращает предпочтения пользователя из контекста"""
        return self.dialog_context.get_user_preferences()
    
    def clear_user_context(self):
        """Очищает контекст пользователя"""
        self.dialog_context.clear_history()
        logger.info("User context cleared")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Возвращает статистику обработки"""
        return {
            'metrics': self.metrics.get_report(),
            'cache_info': {
                'prompt_cache_size': len(self.prompt_cache),
                'ner_cache_size': len(self.ner_cache),
                'dialog_history_size': len(self.dialog_context.history)
            }
        }
    
    def _build_filter_prompt(self, query: str) -> str:
        """Строит промпт для извлечения фильтров из запроса"""
        prompt = f"""Ты - автомобильный ассистент. Извлеки из запроса пользователя параметры для поиска автомобилей.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {query}

ДОСТУПНЫЕ ПОЛЯ:
- brand: марка автомобиля (BMW, Mercedes, Toyota, Honda, Audi, Volkswagen, Ford, Chevrolet, Nissan, Hyundai, Kia, Renault, Peugeot, Opel, Fiat, Skoda, Seat, Volvo, Saab, Mazda, Mitsubishi, Subaru, Lexus, Infiniti, Acura, Porsche, Jaguar, Land Rover, Bentley, Rolls Royce, Ferrari, Lamborghini, Maserati, Aston Martin, McLaren, Lotus, Alpine)
- model: модель автомобиля
- year_from: год выпуска от
- year_to: год выпуска до
- price_from: цена от (в рублях)
- price_to: цена до (в рублях)
- mileage: пробег (в км)
- mileage_from: пробег от (в км)
- mileage_to: пробег до (в км)
- transmission: тип коробки передач (автомат, механика, робот, вариатор)
- drive_type: тип привода (передний, задний, полный)
- state: состояние (новый, подержанный, б/у)
- scenario: сценарий использования (family, city, travel, business, economy)
- color: цвет автомобиля
- body_type: тип кузова (седан, хэтчбек, универсал, внедорожник, кроссовер, кабриолет, купе, лимузин, пикап, фургон, микроавтобус)
- fuel_type: тип топлива (бензин, дизель, электро, гибрид)
- city: город
- dealer: дилерский центр

ПРАВИЛА:
1. Если информация не указана, НЕ добавляй поле
2. Используй точные значения из запроса
3. Для цен указывай в рублях
4. Для годов указывай только год (например, 2020)
5. Для пробега указывай в километрах
6. Если указан диапазон цен, используй price_from и price_to
7. Если указан диапазон лет, используй year_from и year_to
8. Если указан диапазон пробега, используй mileage_from и mileage_to

ВЕРНИ СТРОГО В ФОРМАТЕ JSON:
{{
    "brand": "значение или null",
    "model": "значение или null",
    "year_from": число или null,
    "year_to": число или null,
    "price_from": число или null,
    "price_to": число или null,
    "mileage_from": число или null,
    "mileage_to": число или null,
    "transmission": "значение или null",
    "drive_type": "значение или null",
    "state": "значение или null",
    "scenario": "значение или null",
    "color": "значение или null",
    "body_type": "значение или null",
    "fuel_type": "значение или null",
    "city": "значение или null",
    "dealer": "значение или null"
}}

ПРИМЕРЫ:
Запрос: "BMW X5 до 3 млн"
Ответ: {{"brand": "BMW", "model": "X5", "price_to": 3000000, "year_from": null, "year_to": null, "price_from": null, "mileage_from": null, "mileage_to": null, "transmission": null, "drive_type": null, "state": null, "scenario": null, "color": null, "body_type": null, "fuel_type": null, "city": null, "dealer": null}}

Запрос: "Красный седан Toyota Camry 2020-2023 года"
Ответ: {{"brand": "Toyota", "model": "Camry", "year_from": 2020, "year_to": 2023, "price_from": null, "price_to": null, "mileage_from": null, "mileage_to": null, "transmission": null, "drive_type": null, "state": null, "scenario": null, "color": "красный", "body_type": "седан", "fuel_type": null, "city": null, "dealer": null}}

Запрос: "Семейный автомобиль с автоматической коробкой"
Ответ: {{"brand": null, "model": null, "year_from": null, "year_to": null, "price_from": null, "price_to": null, "mileage_from": null, "mileage_to": null, "transmission": "автомат", "drive_type": null, "state": null, "scenario": "family", "color": null, "body_type": null, "fuel_type": null, "city": null, "dealer": null}}

ОТВЕТ:"""
        return prompt

    def _build_final_prompt(self, query: str, cars: List[Dict]) -> str:
        """Строит улучшенный промпт для генерации финального ответа"""
        cars_str = '\n'.join([
            f"• {c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')}г. - {c.get('body_type','')} - {c.get('color','')} - {c.get('price','')}₽ - {c.get('city','')}"
            for c in cars
        ])
        
        return f"""Ты - автомобильный консультант. Пользователь задал вопрос: "{query}"

НАЙДЕННЫЕ АВТОМОБИЛИ:
{cars_str}

ИНСТРУКЦИИ:
1. Отвечай ТОЛЬКО на русском языке
2. Будь дружелюбным и профессиональным
3. Если автомобили найдены - опиши их кратко и понятно
4. Если ничего не найдено - вежливо объясни это
5. Предложи уточнить параметры поиска
6. Не придумывай информацию, которой нет в данных
7. Укажи ключевые преимущества каждого автомобиля
8. Предложи следующие шаги (связаться с дилером, уточнить детали)

СТИЛЬ ОТВЕТА:
- Краткий и информативный
- С указанием ключевых характеристик
- С предложением дальнейших действий
- Дружелюбный тон

ОТВЕТ:"""

    def _build_context_prompt(self, query: str, history: List[tuple]) -> str:
        """Строит промпт с учетом контекста диалога"""
        context_lines = []
        for user_msg, assistant_msg in history[-3:]:  # Последние 3 обмена
            context_lines.append(f"Пользователь: {user_msg}")
            context_lines.append(f"Ассистент: {assistant_msg}")
        
        context_str = "\n".join(context_lines) if context_lines else ""
        
        return f"""Ты - автомобильный ассистент Моторчик. Учитывай контекст предыдущего диалога.

КОНТЕКСТ:
{context_str}

ТЕКУЩИЙ ЗАПРОС: "{query}"

ИНСТРУКЦИИ:
1. Учитывай предыдущие вопросы пользователя
2. Если пользователь уточняет параметры - используй их
3. Если это новый запрос - обрабатывай независимо
4. Будь последовательным в рекомендациях
5. Учитывай предпочтения пользователя

ОТВЕТ:"""

    def _build_clarification_prompt(self, query: str, missing_info: List[str]) -> str:
        """Строит промпт для уточнения недостающей информации"""
        missing_str = ", ".join(missing_info)
        
        return f"""Пользователь задал неполный запрос: "{query}"

НЕДОСТАЮЩАЯ ИНФОРМАЦИЯ: {missing_str}

ИНСТРУКЦИИ:
1. Задай 1-2 уточняющих вопроса
2. Будь вежливым и полезным
3. Предложи конкретные варианты
4. Объясни, зачем нужны уточнения
5. Предложи популярные варианты

ПРИМЕРЫ ВОПРОСОВ:
- "Какой бюджет у вас на покупку?"
- "Какой тип кузова предпочитаете?"
- "Важна ли экономичность?"
- "Для каких целей нужен автомобиль?"

ВОПРОС ДЛЯ УТОЧНЕНИЯ:"""
    
    def _analyze_query_completeness(self, entities: Dict[str, Any]) -> List[str]:
        """Анализирует полноту запроса и возвращает недостающую информацию"""
        missing = []
        
        # Проверяем наличие основных параметров
        if not entities.get('brand') and not entities.get('model'):
            missing.append('марка/модель')
        
        if not entities.get('price') and not entities.get('price_to') and not entities.get('price_from'):
            missing.append('бюджет')
        
        if not entities.get('body_type'):
            missing.append('тип кузова')
        
        if not entities.get('scenario'):
            missing.append('цель использования')
        
        return missing
    
    def _build_comparison_prompt(self, query: str, cars: List[Dict]) -> str:
        """Строит промпт для сравнения автомобилей"""
        cars_str = '\n'.join([
            f"• {c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')}г. - {c.get('body_type','')} - {c.get('color','')} - {c.get('price','')}₽ - {c.get('city','')}"
            for c in cars
        ])
        
        return f"""Ты - автомобильный консультант. Пользователь хочет сравнить автомобили: "{query}"

АВТОМОБИЛИ ДЛЯ СРАВНЕНИЯ:
{cars_str}

ИНСТРУКЦИИ:
1. Сравни автомобили по ключевым параметрам
2. Укажи преимущества и недостатки каждого
3. Дай рекомендацию на основе запроса
4. Будь объективным и информативным
5. Учитывай цену и соотношение цена/качество

ПАРАМЕТРЫ ДЛЯ СРАВНЕНИЯ:
- Цена и экономичность
- Размеры и вместительность
- Комфорт и оснащение
- Надежность и репутация
- Экономичность эксплуатации

ОТВЕТ:"""

    def _build_scenario_prompt(self, query: str, scenario: str) -> str:
        """Строит промпт для конкретного сценария"""
        scenario_prompts = {
            'family_car': f"""Ты - автомобильный консультант. Пользователь ищет семейный автомобиль: "{query}"

СЕМЕЙНЫЕ ТРЕБОВАНИЯ:
- Безопасность и надежность
- Вместительность для семьи
- Комфорт для длительных поездок
- Экономичность эксплуатации
- Универсальность использования

РЕКОМЕНДУЕМЫЕ ТИПЫ КУЗОВА:
- Универсал (большой багажник)
- Минивэн (много места)
- Кроссовер (универсальность)
- Внедорожник (для активного отдыха)

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА:""",
            
            'city_car': f"""Ты - автомобильный консультант. Пользователь ищет городской автомобиль: "{query}"

ГОРОДСКИЕ ТРЕБОВАНИЯ:
- Компактность и маневренность
- Экономичность в городских условиях
- Простота парковки
- Низкий расход топлива
- Удобство в пробках

РЕКОМЕНДУЕМЫЕ ТИПЫ КУЗОВА:
- Хэтчбек (компактность)
- Купе (стиль)
- Седан (комфорт)
- Электромобили (экономия)

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА:""",
            
            'travel_car': f"""Ты - автомобильный консультант. Пользователь ищет автомобиль для путешествий: "{query}"

ТРЕБОВАНИЯ ДЛЯ ПУТЕШЕСТВИЙ:
- Вместительный багажник
- Комфорт для длительных поездок
- Надежность в дороге
- Экономичность на трассе
- Универсальность

РЕКОМЕНДУЕМЫЕ ТИПЫ КУЗОВА:
- Универсал (большой багажник)
- Внедорожник (проходимость)
- Кроссовер (универсальность)
- Минивэн (вместительность)

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА:""",
            
            'business_car': f"""Ты - автомобильный консультант. Пользователь ищет бизнес-автомобиль: "{query}"

БИЗНЕС-ТРЕБОВАНИЯ:
- Солидный внешний вид
- Комфорт для деловых поездок
- Надежность и престиж
- Экономичность эксплуатации
- Соответствие статусу

РЕКОМЕНДУЕМЫЕ ТИПЫ КУЗОВА:
- Седан (классика)
- Кроссовер (универсальность)
- Внедорожник (статус)
- Электромобили (современность)

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА:""",
            
            'economy_car': f"""Ты - автомобильный консультант. Пользователь ищет экономичный автомобиль: "{query}"

ЭКОНОМИЧЕСКИЕ ТРЕБОВАНИЯ:
- Низкая стоимость покупки
- Экономичность эксплуатации
- Надежность и долговечность
- Низкий расход топлива
- Доступность запчастей

РЕКОМЕНДУЕМЫЕ ТИПЫ КУЗОВА:
- Хэтчбек (экономичность)
- Седан (классика)
- Электромобили (экономия на топливе)
- Гибриды (экономичность)

ВЕРНИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА:"""
        }
        
        return scenario_prompts.get(scenario, self._build_filter_prompt(query))
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """Возвращает отчет по метрикам"""
        return self.metrics.get_report()
    
    def clear_cache(self):
        """Очищает кэш"""
        self._generate_cached_response.cache_clear()
        self.prompt_cache.clear()
        self._clear_ner_cache()

    def process_help_request(self, query: str) -> Dict[str, Any]:
        """Обрабатывает запрос на помощь"""
        help_text = """Я - автомобильный ассистент Моторчик! Вот что я умею:

🔍 **Поиск автомобилей:**
- Найти машину по марке, модели, цене
- Поиск по цвету, типу кузова, году выпуска
- Фильтрация по пробегу, городу, дилеру

🚗 **Сценарии использования:**
- Семейный автомобиль (вместительность, безопасность)
- Городской автомобиль (компактность, экономичность)
- Автомобиль для путешествий (вместительный багажник)
- Бизнес-автомобиль (престиж, комфорт)
- Экономичный автомобиль (низкая стоимость)

⚖️ **Сравнение автомобилей:**
- Сравнить характеристики нескольких машин
- Анализ преимуществ и недостатков
- Рекомендации по выбору

💰 **Финансовые услуги:**
- Расчет кредита
- Рассрочка
- Страхование

📋 **Примеры запросов:**
- "Найди красный BMW X5 до 3 млн"
- "Семейный автомобиль с большим багажником"
- "Сравни Toyota Camry и Honda Accord"
- "Экономичный автомобиль для города"

Как я могу вам помочь?"""
        
        return {
            'type': 'help',
            'message': help_text,
            'processing_time': 0.1
        }
    
    def process_chitchat_request(self, query: str) -> Dict[str, Any]:
        """Обрабатывает светский разговор"""
        chitchat_responses = [
            "Здравствуйте! Я автоассистент компании ААА МОТОРС. Готов помочь Вам с выбором автомобиля!",
            "Отличный день для поиска автомобиля! Что вас интересует?",
            "Здравствуйте! Я специализируюсь на автомобилях и готов ответить на любые вопросы о машинах.",
            "Приветствую! Я здесь, чтобы помочь вам найти идеальный автомобиль. С чего начнем?"
        ]
        
        import random
        response = random.choice(chitchat_responses)
        
        return {
            'type': 'chitchat',
            'message': response,
            'processing_time': 0.1
        }
    
    def process_loan_request(self, query: str) -> Dict[str, Any]:
        """Обрабатывает запрос на кредит через AutoSearchProcessor"""
        try:
            # Перенаправляем запрос в AutoSearchProcessor для обработки кредитных запросов
            from modules.search.auto_search_processor import AutoSearchProcessor
            auto_processor = AutoSearchProcessor()
            
            # Проверяем, является ли это кредитным запросом
            if auto_processor._is_credit_query(query):
                logger.info(f"Обрабатываем кредитный запрос через AutoSearchProcessor: {query}")
                result = auto_processor._process_credit_query(query, {}, "default")
                return result
            else:
                # Если это не кредитный запрос, возвращаем информацию о кредите
                loan_text = """Для расчета кредита мне нужна дополнительная информация:

💰 **Информация для расчета:**
- Стоимость автомобиля
- Первоначальный взнос
- Срок кредита
- Ваш доход

📊 **Примеры запросов:**
- "Рассчитай кредит на BMW X5 за 3 млн"
- "Кредит на 2 года с первоначальным взносом 500 тыс"
- "Рассрочка на Toyota Camry"

💡 **Что я могу рассчитать:**
- Ежемесячный платеж
- Общую переплату
- Процентную ставку
- График платежей

Укажите параметры кредита, и я сделаю расчет!"""
                
                return {
                    'type': 'loan_info',
                    'message': loan_text,
                    'processing_time': 0.1
                }
        except Exception as e:
            logger.error(f"Ошибка при обработке кредитного запроса: {e}")
            return {
                'type': 'error',
                'message': f"Ошибка при обработке кредитного запроса: {str(e)}",
                'processing_time': 0.1
            }
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """Валидирует запрос пользователя"""
        if not query or len(query.strip()) < 2:
            return False, "Запрос слишком короткий. Пожалуйста, уточните, что вы ищете."
        
        if len(query) > 500:
            return False, "Запрос слишком длинный. Пожалуйста, сформулируйте короче."
        
        # Проверяем на недопустимые символы
        invalid_chars = re.findall(r'[^\w\sа-яёА-ЯЁ\-\.\,\!\?]', query)
        if invalid_chars:
            return False, "Запрос содержит недопустимые символы."
        
        return True, ""
    
    def get_suggestions(self, query: str) -> List[str]:
        """Возвращает предложения для уточнения запроса"""
        suggestions = []
        
        # Базовые предложения
        if not any(word in query.lower() for word in ['bmw', 'mercedes', 'toyota', 'lada']):
            suggestions.append("Укажите марку автомобиля (например: BMW, Mercedes, Toyota)")
        
        if not any(word in query.lower() for word in ['цена', 'стоимость', 'бюджет', 'до']):
            suggestions.append("Укажите бюджет (например: до 2 млн рублей)")
        
        if not any(word in query.lower() for word in ['семейный', 'городской', 'бизнес']):
            suggestions.append("Укажите цель использования (семейный, городской, бизнес)")
        
        return suggestions[:3]  # Ограничиваем до 3 предложений

    def _determine_response_type(self, query: str, entities: Dict[str, Any]) -> str:
        """Определяет тип ответа на основе запроса и извлеченных сущностей"""
        query_lower = query.lower()
        
        # Проверяем на сравнение
        if any(word in query_lower for word in ['сравни', 'сравнение', 'что лучше', 'разница']):
            return 'comparison'
        
        # Проверяем на уточнение
        if any(word in query_lower for word in ['уточни', 'уточнение', 'какой именно', 'конкретнее']):
            return 'clarification'
        
        # Проверяем на помощь
        if any(word in query_lower for word in ['помоги', 'помощь', 'что ты умеешь', 'как использовать']):
            return 'help'
        
        # Проверяем на светскую беседу
        if any(word in query_lower for word in ['привет', 'спасибо', 'до свидания', 'как дела']):
            return 'chitchat'
        
        # Проверяем на кредит
        if any(word in query_lower for word in ['кредит', 'рассчитай', 'первоначальный взнос', 'условия']):
            return 'loan'
        
        # Проверяем на сценарий
        if entities.get('scenario'):
            return 'scenario'
        
        # Проверяем на поиск
        if entities.get('brand') or entities.get('model') or entities.get('color') or entities.get('price'):
            return 'search'
        
        # По умолчанию - общий поиск
        return 'general'

    def _determine_scenario_from_query(self, query: str) -> Optional[str]:
        """Определяет сценарий использования из запроса"""
        query_lower = query.lower()
        
        # Семейный автомобиль
        if any(word in query_lower for word in ['семья', 'семейный', 'детей', 'ребенок', 'большой', 'просторный', 'комфортный', 'безопасный']):
            return 'family'
        
        # Городской автомобиль
        if any(word in query_lower for word in ['город', 'городской', 'компактный', 'маленький', 'парковка', 'маневренный']):
            return 'city'
        
        # Путешествия
        if any(word in query_lower for word in ['путешествие', 'поездка', 'дорога', 'дальняя', 'комфорт', 'багажник', 'вместительный']):
            return 'travel'
        
        # Бизнес
        if any(word in query_lower for word in ['бизнес', 'работа', 'деловой', 'престижный', 'статус', 'представительский']):
            return 'business'
        
        # Экономичный
        if any(word in query_lower for word in ['экономичный', 'дешевый', 'бюджетный', 'экономия', 'расход', 'топливо']):
            return 'economy'
        
        return None

# Глобальный экземпляр для использования в других модулях
enhanced_processor = EnhancedLlamaProcessor() 