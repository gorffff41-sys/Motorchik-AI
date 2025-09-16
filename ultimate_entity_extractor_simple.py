import re
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)

class UltimateEntityExtractorSimple:
    """Ультимативный Entity Extractor с максимальной точностью (упрощенная версия)"""
    
    def __init__(self):
        self._load_car_data()
        self._init_ml_models()
        
        # Расширенные словари для максимальной точности
        self._init_extended_dictionaries()
    
    def _load_car_data(self):
        """Загрузка данных о машинах из БД"""
        try:
            conn = sqlite3.connect('instance/cars.db')
            cursor = conn.cursor()
            
            # Загрузка марок и моделей
            cursor.execute("SELECT DISTINCT brand FROM cars")
            self.brands = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT model FROM cars")
            self.models = [row[0] for row in cursor.fetchall()]
            
            # Создание словаря марка -> модели
            cursor.execute("SELECT brand, model FROM cars")
            self.brand_models = {}
            for brand, model in cursor.fetchall():
                if brand not in self.brand_models:
                    self.brand_models[brand] = []
                self.brand_models[brand].append(model)
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            self.brands = ['BMW', 'Mercedes', 'Audi', 'Toyota', 'Volkswagen', 'Hyundai', 'Kia']
            self.models = ['X5', 'X3', 'GLE', 'GLC', 'A4', 'A6', 'Camry', 'Corolla']
            self.brand_models = {
                'BMW': ['X5', 'X3', 'X1', '3 Series', '5 Series'],
                'Mercedes': ['GLE', 'GLC', 'C-Class', 'E-Class'],
                'Audi': ['A4', 'A6', 'Q5', 'Q7'],
                'Toyota': ['Camry', 'Corolla', 'RAV4', 'Highlander']
            }
    
    def _init_ml_models(self):
        """Инициализация ML моделей"""
        try:
            # Простые модели для улучшения точности
            self.brand_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        except Exception as e:
            logger.error(f"Ошибка инициализации ML моделей: {e}")
    
    def _init_extended_dictionaries(self):
        """Инициализация расширенных словарей"""
        
        # Русские названия марок
        self.russian_brands = {
            'ауди': 'Audi', 'бмв': 'BMW', 'мерседес': 'Mercedes', 'тойота': 'Toyota',
            'фольксваген': 'Volkswagen', 'хендай': 'Hyundai', 'киа': 'Kia',
            'лексус': 'Lexus', 'инфинити': 'Infiniti', 'акура': 'Acura',
            'шкода': 'Skoda', 'сеат': 'Seat', 'опель': 'Opel', 'форд': 'Ford',
            'шевроле': 'Chevrolet', 'додж': 'Dodge', 'джип': 'Jeep',
            'мазда': 'Mazda', 'мицубиси': 'Mitsubishi', 'субару': 'Subaru',
            'хонда': 'Honda', 'ниссан': 'Nissan', 'рено': 'Renault',
            'пежо': 'Peugeot', 'ситроен': 'Citroen', 'альфа ромео': 'Alfa Romeo',
            'фиат': 'Fiat', 'ланча': 'Lancia', 'мазерати': 'Maserati',
            'феррари': 'Ferrari', 'ламборгини': 'Lamborghini', 'порше': 'Porsche',
            'бентли': 'Bentley', 'роллс-ройс': 'Rolls-Royce', 'майбах': 'Maybach',
            'астон мартин': 'Aston Martin', 'ягуар': 'Jaguar', 'ленд ровер': 'Land Rover',
            'мини': 'MINI', 'смарт': 'Smart'
        }
        
        # Русские названия моделей
        self.russian_models = {
            'икс5': 'X5', 'икс3': 'X3', 'икс1': 'X1', 'икс6': 'X6', 'икс7': 'X7',
            'гле': 'GLE', 'глк': 'GLC', 'глс': 'GLS', 'гла': 'GLA', 'глб': 'GLB',
            'а4': 'A4', 'а6': 'A6', 'а3': 'A3', 'а5': 'A5', 'а7': 'A7', 'а8': 'A8',
            'ку5': 'Q5', 'ку7': 'Q7', 'ку3': 'Q3', 'ку8': 'Q8',
            'камри': 'Camry', 'королла': 'Corolla', 'рав4': 'RAV4', 'хайлендер': 'Highlander',
            'пассат': 'Passat', 'гольф': 'Golf', 'поло': 'Polo', 'джетта': 'Jetta',
            'туарег': 'Touareg', 'тигуан': 'Tiguan', 'атлас': 'Atlas',
            'санта фе': 'Santa Fe', 'туссан': 'Tucson', 'крета': 'Creta',
            'спортейдж': 'Sportage', 'соренто': 'Sorento', 'пиканто': 'Picanto',
            'рио': 'Rio', 'серато': 'Cerato', 'оптима': 'Optima'
        }
        
        # Цвета с расширенными вариантами
        self.colors = {
            'белый', 'черный', 'красный', 'синий', 'зеленый', 'желтый', 'оранжевый',
            'фиолетовый', 'розовый', 'коричневый', 'серый', 'серебристый', 'золотой',
            'голубой', 'бирюзовый', 'фиолетовый', 'бордовый', 'вишневый', 'винный',
            'шоколадный', 'бежевый', 'кремовый', 'персиковый', 'лавандовый',
            'оливковый', 'морской', 'небесный', 'лазурный', 'изумрудный',
            'белоснежный', 'угольный', 'темно-синий', 'темно-красный', 'светло-серый',
            'темно-серый', 'светло-голубой', 'темно-зеленый', 'светло-зеленый'
        }
        
        # Расширенные опции
        self.options = {
            'панорамная крыша', 'люк', 'климат-контроль', 'подогрев сидений',
            'навигация', 'парктроник', 'ксенон', 'адаптивные фары', 'led фары',
            'противотуманные фары', 'дворники с датчиком дождя', 'датчик света',
            'круиз-контроль', 'адаптивный круиз-контроль', 'система помощи при парковке',
            'камера заднего вида', 'камера 360', 'беспроводная зарядка',
            'bluetooth', 'apple carplay', 'android auto', 'wi-fi',
            'система голосового управления', 'подогрев руля', 'вентиляция сидений',
            'электропривод сидений', 'память сидений', 'массаж сидений',
            'система контроля слепых зон', 'система предупреждения столкновений',
            'система экстренного торможения', 'система контроля полосы',
            'система мониторинга давления в шинах', 'иммобилайзер', 'сигнализация',
            'центральный замок', 'электростеклоподъемники', 'электрозеркала',
            'подогрев зеркал', 'складывающиеся зеркала', 'тонировка',
            'защита от угона', 'система start/stop', 'эко-режим',
            'спорт-режим', 'комфорт-режим', 'снежный режим', 'внедорожный режим'
        }
        
        # Топливо
        self.fuel_types = {
            'бензин', 'дизель', 'гибрид', 'электро', 'газ', 'метан', 'пропан',
            'бензин-газ', 'дизель-гибрид', 'бензин-гибрид'
        }
        
        # Коробки передач
        self.transmissions = {
            'автомат', 'механика', 'робот', 'вариатор', 'автоматическая',
            'механическая', 'автоматическая коробка', 'механическая коробка'
        }
        
        # Привод
        self.drive_types = {
            'полный', 'передний', 'задний', '4x4', 'awd', 'fwd', 'rwd',
            'полный привод', 'передний привод', 'задний привод'
        }
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Извлечение всех сущностей из текста"""
        text = text.lower().strip()
        entities = {}
        
        # Извлечение марок и моделей
        brands_models = self._extract_brands_and_models(text)
        if brands_models:
            entities.update(brands_models)
        
        # Извлечение цветов
        color = self._extract_color(text)
        if color:
            entities['color'] = color
        
        # Извлечение цен
        prices = self._extract_prices(text)
        if prices:
            entities.update(prices)
        
        # Извлечение годов
        years = self._extract_years(text)
        if years:
            entities.update(years)
        
        # Извлечение топлива
        fuel = self._extract_fuel_type(text)
        if fuel:
            entities['fuel_type'] = fuel
        
        # Извлечение коробки передач
        transmission = self._extract_transmission(text)
        if transmission:
            entities['transmission'] = transmission
        
        # Извлечение привода
        drive = self._extract_drive_type(text)
        if drive:
            entities['drive_type'] = drive
        
        # Извлечение опций
        options = self._extract_options(text)
        if options:
            entities['options'] = options
        
        return entities
    
    def _extract_brands_and_models(self, text: str) -> Dict[str, str]:
        """Улучшенное извлечение марок и моделей"""
        result = {}
        
        # Сначала ищем русские названия
        for russian_brand, english_brand in self.russian_brands.items():
            if russian_brand in text:
                result['brand'] = english_brand
                # Ищем соответствующую модель
                model = self._find_model_for_brand(text, english_brand)
                if model:
                    result['model'] = model
                break
        
        # Если не нашли русское название, ищем английское
        if 'brand' not in result:
            for brand in self.brands:
                if brand.lower() in text:
                    result['brand'] = brand
                    model = self._find_model_for_brand(text, brand)
                    if model:
                        result['model'] = model
                    break
        
        # Если нашли только модель, попробуем найти марку
        if 'model' in result and 'brand' not in result:
            brand = self._find_brand_for_model(text, result['model'])
            if brand:
                result['brand'] = brand
        
        return result
    
    def _find_model_for_brand(self, text: str, brand: str) -> Optional[str]:
        """Поиск модели для найденной марки"""
        # Сначала ищем русские названия моделей
        for russian_model, english_model in self.russian_models.items():
            if russian_model in text:
                # Проверяем, что модель принадлежит марке
                if brand in self.brand_models and english_model in self.brand_models[brand]:
                    return english_model
        
        # Ищем английские названия моделей
        for model in self.models:
            if model.lower() in text:
                # Проверяем, что модель принадлежит марке
                if brand in self.brand_models and model in self.brand_models[brand]:
                    return model
        
        return None
    
    def _find_brand_for_model(self, text: str, model: str) -> Optional[str]:
        """Поиск марки для найденной модели"""
        for brand, models in self.brand_models.items():
            if model in models:
                return brand
        return None
    
    def _extract_color(self, text: str) -> Optional[str]:
        """Извлечение цвета"""
        for color in self.colors:
            if color in text:
                return color
        return None
    
    def _extract_prices(self, text: str) -> Dict[str, int]:
        """Улучшенное извлечение цен"""
        result = {}
        
        # Паттерны для цен
        patterns = [
            # До X рублей/руб
            (r'до\s+(\d+(?:\s*\d+)*)\s*(?:рубл|руб)', 'price_to'),
            # От X рублей/руб
            (r'от\s+(\d+(?:\s*\d+)*)\s*(?:рубл|руб)', 'price_from'),
            # X-Y рублей/руб
            (r'(\d+(?:\s*\d+)*)\s*-\s*(\d+(?:\s*\d+)*)\s*(?:рубл|руб)', 'price_range'),
            # X миллионов/млн
            (r'до\s+(\d+)\s*(?:миллион|млн)', 'price_to_million'),
            (r'от\s+(\d+)\s*(?:миллион|млн)', 'price_from_million'),
            # X-Y миллионов/млн
            (r'(\d+)\s*-\s*(\d+)\s*(?:миллион|млн)', 'price_range_million'),
            # X тысяч/к
            (r'до\s+(\d+)\s*(?:тысяч|к)', 'price_to_thousand'),
            (r'от\s+(\d+)\s*(?:тысяч|к)', 'price_from_thousand'),
            # X-Y тысяч/к
            (r'(\d+)\s*-\s*(\d+)\s*(?:тысяч|к)', 'price_range_thousand'),
            # Просто числа (если нет других указаний)
            (r'(\d+(?:\s*\d+)*)\s*(?:рубл|руб)', 'price_exact')
        ]
        
        for pattern, price_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if price_type == 'price_range':
                    from_price, to_price = match
                    result['price_from'] = int(from_price.replace(' ', ''))
                    result['price_to'] = int(to_price.replace(' ', ''))
                elif price_type == 'price_range_million':
                    from_million, to_million = match
                    result['price_from'] = int(from_million) * 1000000
                    result['price_to'] = int(to_million) * 1000000
                elif price_type == 'price_range_thousand':
                    from_thousand, to_thousand = match
                    result['price_from'] = int(from_thousand) * 1000
                    result['price_to'] = int(to_thousand) * 1000
                elif price_type == 'price_to_million':
                    result['price_to'] = int(match) * 1000000
                elif price_type == 'price_from_million':
                    result['price_from'] = int(match) * 1000000
                elif price_type == 'price_to_thousand':
                    result['price_to'] = int(match) * 1000
                elif price_type == 'price_from_thousand':
                    result['price_from'] = int(match) * 1000
                elif price_type == 'price_exact':
                    result['price'] = int(match.replace(' ', ''))
                else:
                    result[price_type] = int(match.replace(' ', ''))
        
        return result
    
    def _extract_years(self, text: str) -> Dict[str, int]:
        """Извлечение годов"""
        result = {}
        
        # Паттерны для годов
        patterns = [
            (r'(\d{4})\s*года?', 'year'),
            (r'от\s+(\d{4})\s*года?', 'year_from'),
            (r'до\s+(\d{4})\s*года?', 'year_to'),
            (r'(\d{4})\s*-\s*(\d{4})', 'year_range'),
            (r'(\d{4})', 'year_simple')
        ]
        
        for pattern, year_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if year_type == 'year_range':
                    from_year, to_year = match
                    result['year_from'] = int(from_year)
                    result['year_to'] = int(to_year)
                elif year_type == 'year_simple':
                    # Проверяем, что это разумный год
                    year = int(match)
                    if 1900 <= year <= 2030:
                        result['year'] = year
                else:
                    result[year_type] = int(match)
        
        return result
    
    def _extract_fuel_type(self, text: str) -> Optional[str]:
        """Извлечение типа топлива"""
        for fuel in self.fuel_types:
            if fuel in text:
                return fuel
        return None
    
    def _extract_transmission(self, text: str) -> Optional[str]:
        """Извлечение коробки передач"""
        for transmission in self.transmissions:
            if transmission in text:
                return transmission
        return None
    
    def _extract_drive_type(self, text: str) -> Optional[str]:
        """Извлечение типа привода"""
        for drive in self.drive_types:
            if drive in text:
                return drive
        return None
    
    def _extract_options(self, text: str) -> List[str]:
        """Улучшенное извлечение опций"""
        found_options = []
        
        for option in self.options:
            # Ищем точное совпадение
            if option in text:
                found_options.append(option)
            # Ищем с предлогом "с"
            elif f"с {option}" in text:
                found_options.append(option)
            # Ищем с предлогом "и"
            elif f"и {option}" in text:
                found_options.append(option)
        
        return found_options if found_options else [] 