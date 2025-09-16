#!/usr/bin/env python3
"""
Анализатор сущностей для определения когда использовать YandexGPT
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("entity_analyzer")

class EntityAnalyzer:
    """Анализатор сущностей для определения типа запроса"""
    
    def __init__(self):
        """Инициализация анализатора"""
        # Словарь известных марок
        self.brands = {
            'bmw': 'BMW', 'мерседес': 'Mercedes', 'mercedes': 'Mercedes',
            'audi': 'Audi', 'ford': 'Ford', 'лада': 'Lada', 'lada': 'Lada',
            'toyota': 'Toyota', 'тойота': 'Toyota', 'volkswagen': 'Volkswagen',
            'vw': 'Volkswagen', 'volvo': 'Volvo', 'lexus': 'Lexus',
            'honda': 'Honda', 'nissan': 'Nissan', 'mazda': 'Mazda',
            'subaru': 'Subaru', 'mitsubishi': 'Mitsubishi', 'hyundai': 'Hyundai',
            'kia': 'Kia', 'skoda': 'Skoda', 'seat': 'Seat', 'renault': 'Renault',
            'peugeot': 'Peugeot', 'citroen': 'Citroen', 'opel': 'Opel',
            'fiat': 'Fiat', 'alfa romeo': 'Alfa Romeo', 'jaguar': 'Jaguar',
            'land rover': 'Land Rover', 'range rover': 'Range Rover',
            'porsche': 'Porsche', 'ferrari': 'Ferrari', 'lamborghini': 'Lamborghini',
            'maserati': 'Maserati', 'bentley': 'Bentley', 'rolls royce': 'Rolls Royce',
            'aston martin': 'Aston Martin', 'mclaren': 'McLaren', 'bugatti': 'Bugatti',
            'koenigsegg': 'Koenigsegg', 'pagani': 'Pagani', 'chery': 'Chery',
            'geely': 'Geely', 'haval': 'Haval', 'great wall': 'Great Wall',
            'changan': 'Changan', 'byd': 'BYD', 'nio': 'NIO', 'xpeng': 'XPeng',
            'li auto': 'Li Auto', 'wuling': 'Wuling', 'hongqi': 'Hongqi'
        }
        
        # Ключевые слова для автомобильных запросов
        self.car_keywords = [
            'машина', 'автомобиль', 'авто', 'тачка', 'колеса',
            'купить', 'продать', 'найти', 'поиск', 'выбор',
            'цена', 'стоимость', 'бюджет', 'дорого', 'дешево',
            'новый', 'б/у', 'подержанный', 'с пробегом',
            'год', 'возраст', 'пробег', 'километраж',
            'цвет', 'красный', 'синий', 'белый', 'черный',
            'топливо', 'бензин', 'дизель', 'электро', 'гибрид',
            'кузов', 'седан', 'внедорожник', 'хэтчбек', 'универсал',
            'коробка', 'автомат', 'механика', 'робот',
            'привод', 'передний', 'задний', 'полный',
            'город', 'москва', 'спб', 'ростов', 'краснодар'
        ]
        
        # Ключевые слова для общих запросов
        self.general_keywords = [
            'привет', 'здравствуй', 'как дела', 'помощь', 'помоги',
            'что ты умеешь', 'возможности', 'функции',
            'спасибо', 'благодарю', 'хорошо', 'плохо',
            'погода', 'время', 'дата', 'календарь',
            'шутка', 'анекдот', 'расскажи', 'объясни'
        ]
    
    def analyze_entities(self, query: str) -> Dict[str, Any]:
        """Анализ сущностей в запросе"""
        query_lower = query.lower()
        
        # Ищем марки
        found_brands = []
        for brand_key, brand_name in self.brands.items():
            if brand_key in query_lower:
                found_brands.append(brand_name)
        
        # Ищем модели (после марки)
        found_models = []
        for brand in found_brands:
            brand_lower = brand.lower()
            query_after_brand = query_lower.replace(brand_lower, '').strip()
            if query_after_brand:
                words = query_after_brand.split()
                if words:
                    potential_model = words[0]
                    if len(potential_model) > 1:
                        found_models.append(potential_model.title())
        
        # Ищем автомобильные ключевые слова
        car_keywords_found = []
        for keyword in self.car_keywords:
            if keyword in query_lower:
                car_keywords_found.append(keyword)
        
        # Ищем общие ключевые слова
        general_keywords_found = []
        for keyword in self.general_keywords:
            if keyword in query_lower:
                general_keywords_found.append(keyword)
        
        # Определяем тип запроса
        query_type = self._determine_query_type(found_brands, found_models, car_keywords_found, general_keywords_found)
        
        return {
            'brands': found_brands,
            'models': found_models,
            'car_keywords': car_keywords_found,
            'general_keywords': general_keywords_found,
            'query_type': query_type,
            'entities_count': len(found_brands) + len(found_models) + len(car_keywords_found),
            'has_car_entities': len(found_brands) > 0 or len(found_models) > 0 or len(car_keywords_found) > 0
        }
    
    def _determine_query_type(self, brands: List[str], models: List[str], car_keywords: List[str], general_keywords: List[str]) -> str:
        """Определение типа запроса"""
        
        # Если есть конкретные марки или модели - это автомобильный запрос
        if brands or models:
            return 'car_specific'
        
        # Если есть автомобильные ключевые слова - это автомобильный запрос
        if car_keywords:
            return 'car_general'
        
        # Если есть общие ключевые слова - это общий запрос
        if general_keywords:
            return 'general'
        
        # По умолчанию считаем общим запросом
        return 'general'
    
    def should_use_yandex_gpt(self, query: str) -> bool:
        """Определяет, нужно ли использовать YandexGPT для запроса"""
        entities = self.analyze_entities(query)
        
        # Если сущностей 0 - сразу отправляем в YandexGPT
        if entities['entities_count'] == 0:
            logger.info(f"🔍 Сущностей не найдено, используем YandexGPT для запроса: {query}")
            return True
        
        # Если это общий запрос - используем YandexGPT
        if entities['query_type'] == 'general':
            logger.info(f"🔍 Общий запрос, используем YandexGPT: {query}")
            return True
        
        # Для автомобильных запросов с сущностями используем обычную обработку
        logger.info(f"🔍 Автомобильный запрос с сущностями, используем обычную обработку: {query}")
        return False
    
    def extract_brand_model(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Извлечение марки и модели из запроса"""
        entities = self.analyze_entities(query)
        
        brand = entities['brands'][0] if entities['brands'] else None
        model = entities['models'][0] if entities['models'] else None
        
        return brand, model

# Создаем глобальный экземпляр анализатора
entity_analyzer = EntityAnalyzer()

def get_entity_analyzer() -> EntityAnalyzer:
    """Получение глобального экземпляра анализатора"""
    return entity_analyzer 