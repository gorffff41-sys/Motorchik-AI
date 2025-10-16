#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для маппинга сущностей из базы данных
"""

import sqlite3
import os
from typing import Dict, List, Set, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseEntityMapper:
    """Класс для маппинга сущностей из базы данных"""
    
    def __init__(self, db_path: str = "instance/cars.db"):
        self.db_path = db_path
        self.connection = None
        self._cache = {}
        
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info("Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    def disconnect(self):
        """Отключение от базы данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_all_brands(self) -> Set[str]:
        """Получает все марки автомобилей из БД"""
        if 'brands' in self._cache:
            return self._cache['brands']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем марки из таблицы car
            cursor.execute("SELECT DISTINCT mark FROM car WHERE mark IS NOT NULL AND mark != ''")
            car_brands = {row[0] for row in cursor.fetchall()}
            
            # Получаем марки из таблицы used_car
            cursor.execute("SELECT DISTINCT mark FROM used_car WHERE mark IS NOT NULL AND mark != ''")
            used_car_brands = {row[0] for row in cursor.fetchall()}
            
            all_brands = car_brands.union(used_car_brands)
            self._cache['brands'] = all_brands
            return all_brands
            
        except Exception as e:
            logger.error(f"Ошибка получения марок: {e}")
            return set()
    
    def get_all_models(self) -> Set[str]:
        """Получает все модели автомобилей из БД"""
        if 'models' in self._cache:
            return self._cache['models']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем модели из таблицы car
            cursor.execute("SELECT DISTINCT model FROM car WHERE model IS NOT NULL AND model != ''")
            car_models = {row[0] for row in cursor.fetchall()}
            
            # Получаем модели из таблицы used_car
            cursor.execute("SELECT DISTINCT model FROM used_car WHERE model IS NOT NULL AND model != ''")
            used_car_models = {row[0] for row in cursor.fetchall()}
            
            all_models = car_models.union(used_car_models)
            self._cache['models'] = all_models
            return all_models
            
        except Exception as e:
            logger.error(f"Ошибка получения моделей: {e}")
            return set()
    
    def get_all_colors(self) -> Set[str]:
        """Получает все цвета из БД"""
        if 'colors' in self._cache:
            return self._cache['colors']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем цвета из таблицы car
            cursor.execute("SELECT DISTINCT color FROM car WHERE color IS NOT NULL AND color != ''")
            car_colors = {row[0] for row in cursor.fetchall()}
            
            # Получаем цвета из таблицы used_car
            cursor.execute("SELECT DISTINCT color FROM used_car WHERE color IS NOT NULL AND color != ''")
            used_car_colors = {row[0] for row in cursor.fetchall()}
            
            all_colors = car_colors.union(used_car_colors)
            self._cache['colors'] = all_colors
            return all_colors
            
        except Exception as e:
            logger.error(f"Ошибка получения цветов: {e}")
            return set()
    
    def get_all_body_types(self) -> Set[str]:
        """Получает все типы кузова из БД"""
        if 'body_types' in self._cache:
            return self._cache['body_types']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем типы кузова из таблицы car
            cursor.execute("SELECT DISTINCT body_type FROM car WHERE body_type IS NOT NULL AND body_type != ''")
            car_body_types = {row[0] for row in cursor.fetchall()}
            
            # Получаем типы кузова из таблицы used_car
            cursor.execute("SELECT DISTINCT body_type FROM used_car WHERE body_type IS NOT NULL AND body_type != ''")
            used_car_body_types = {row[0] for row in cursor.fetchall()}
            
            all_body_types = car_body_types.union(used_car_body_types)
            self._cache['body_types'] = all_body_types
            return all_body_types
            
        except Exception as e:
            logger.error(f"Ошибка получения типов кузова: {e}")
            return set()
    
    def get_all_fuel_types(self) -> Set[str]:
        """Получает все типы топлива из БД"""
        if 'fuel_types' in self._cache:
            return self._cache['fuel_types']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем типы топлива из таблицы car
            cursor.execute("SELECT DISTINCT fuel_type FROM car WHERE fuel_type IS NOT NULL AND fuel_type != ''")
            car_fuel_types = {row[0] for row in cursor.fetchall()}
            
            # Получаем типы топлива из таблицы used_car
            cursor.execute("SELECT DISTINCT fuel_type FROM used_car WHERE fuel_type IS NOT NULL AND fuel_type != ''")
            used_car_fuel_types = {row[0] for row in cursor.fetchall()}
            
            all_fuel_types = car_fuel_types.union(used_car_fuel_types)
            self._cache['fuel_types'] = all_fuel_types
            return all_fuel_types
            
        except Exception as e:
            logger.error(f"Ошибка получения типов топлива: {e}")
            return set()
    
    def get_all_gear_box_types(self) -> Set[str]:
        """Получает все типы коробки передач из БД"""
        if 'gear_box_types' in self._cache:
            return self._cache['gear_box_types']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем типы коробки из таблицы car
            cursor.execute("SELECT DISTINCT gear_box_type FROM car WHERE gear_box_type IS NOT NULL AND gear_box_type != ''")
            car_gear_types = {row[0] for row in cursor.fetchall()}
            
            # Получаем типы коробки из таблицы used_car
            cursor.execute("SELECT DISTINCT gear_box_type FROM used_car WHERE gear_box_type IS NOT NULL AND gear_box_type != ''")
            used_car_gear_types = {row[0] for row in cursor.fetchall()}
            
            all_gear_types = car_gear_types.union(used_car_gear_types)
            self._cache['gear_box_types'] = all_gear_types
            return all_gear_types
            
        except Exception as e:
            logger.error(f"Ошибка получения типов коробки: {e}")
            return set()
    
    def get_all_driving_gear_types(self) -> Set[str]:
        """Получает все типы привода из БД"""
        if 'driving_gear_types' in self._cache:
            return self._cache['driving_gear_types']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем типы привода из таблицы car
            cursor.execute("SELECT DISTINCT driving_gear_type FROM car WHERE driving_gear_type IS NOT NULL AND driving_gear_type != ''")
            car_driving_types = {row[0] for row in cursor.fetchall()}
            
            # Получаем типы привода из таблицы used_car
            cursor.execute("SELECT DISTINCT driving_gear_type FROM used_car WHERE driving_gear_type IS NOT NULL AND driving_gear_type != ''")
            used_car_driving_types = {row[0] for row in cursor.fetchall()}
            
            all_driving_types = car_driving_types.union(used_car_driving_types)
            self._cache['driving_gear_types'] = all_driving_types
            return all_driving_types
            
        except Exception as e:
            logger.error(f"Ошибка получения типов привода: {e}")
            return set()
    
    def get_all_cities(self) -> Set[str]:
        """Получает все города из БД"""
        if 'cities' in self._cache:
            return self._cache['cities']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем города из таблицы car
            cursor.execute("SELECT DISTINCT city FROM car WHERE city IS NOT NULL AND city != ''")
            car_cities = {row[0] for row in cursor.fetchall()}
            
            # Получаем города из таблицы used_car
            cursor.execute("SELECT DISTINCT city FROM used_car WHERE city IS NOT NULL AND city != ''")
            used_car_cities = {row[0] for row in cursor.fetchall()}
            
            all_cities = car_cities.union(used_car_cities)
            self._cache['cities'] = all_cities
            return all_cities
            
        except Exception as e:
            logger.error(f"Ошибка получения городов: {e}")
            return set()
    
    def get_all_options(self) -> Set[str]:
        """Получает все опции из БД"""
        if 'options' in self._cache:
            return self._cache['options']
        
        try:
            cursor = self.connection.cursor()
            
            # Получаем опции из таблицы option
            cursor.execute("SELECT DISTINCT description FROM option WHERE description IS NOT NULL AND description != ''")
            options = {row[0] for row in cursor.fetchall()}
            
            self._cache['options'] = options
            return options
            
        except Exception as e:
            logger.error(f"Ошибка получения опций: {e}")
            return set()
    
    def validate_entity(self, entity_type: str, entity_value: str) -> bool:
        """Проверяет существование сущности в БД"""
        try:
            if entity_type == 'mark':
                return entity_value in self.get_all_brands()
            elif entity_type == 'model':
                return entity_value in self.get_all_models()
            elif entity_type == 'color':
                return entity_value in self.get_all_colors()
            elif entity_type == 'body_type':
                return entity_value in self.get_all_body_types()
            elif entity_type == 'fuel_type':
                return entity_value in self.get_all_fuel_types()
            elif entity_type == 'gear_box_type':
                return entity_value in self.get_all_gear_box_types()
            elif entity_type == 'driving_gear_type':
                return entity_value in self.get_all_driving_gear_types()
            elif entity_type == 'city':
                return entity_value in self.get_all_cities()
            elif entity_type == 'option_description':
                return entity_value in self.get_all_options()
            else:
                return True  # Для неизвестных типов возвращаем True
                
        except Exception as e:
            logger.error(f"Ошибка валидации сущности {entity_type}={entity_value}: {e}")
            return True  # В случае ошибки возвращаем True
    
    def suggest_similar_entity(self, entity_type: str, entity_value: str) -> Optional[str]:
        """Предлагает похожую сущность из БД"""
        try:
            from difflib import get_close_matches
            
            if entity_type == 'mark':
                brands = self.get_all_brands()
                matches = get_close_matches(entity_value, brands, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'model':
                models = self.get_all_models()
                matches = get_close_matches(entity_value, models, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'color':
                colors = self.get_all_colors()
                matches = get_close_matches(entity_value, colors, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'body_type':
                body_types = self.get_all_body_types()
                matches = get_close_matches(entity_value, body_types, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'fuel_type':
                fuel_types = self.get_all_fuel_types()
                matches = get_close_matches(entity_value, fuel_types, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'gear_box_type':
                gear_types = self.get_all_gear_box_types()
                matches = get_close_matches(entity_value, gear_types, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'driving_gear_type':
                driving_types = self.get_all_driving_gear_types()
                matches = get_close_matches(entity_value, driving_types, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'city':
                cities = self.get_all_cities()
                matches = get_close_matches(entity_value, cities, n=1, cutoff=0.6)
                return matches[0] if matches else None
            elif entity_type == 'option_description':
                options = self.get_all_options()
                matches = get_close_matches(entity_value, options, n=1, cutoff=0.6)
                return matches[0] if matches else None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка поиска похожей сущности {entity_type}={entity_value}: {e}")
            return None
    
    def get_entity_statistics(self) -> Dict[str, int]:
        """Получает статистику по сущностям"""
        try:
            stats = {
                'brands': len(self.get_all_brands()),
                'models': len(self.get_all_models()),
                'colors': len(self.get_all_colors()),
                'body_types': len(self.get_all_body_types()),
                'fuel_types': len(self.get_all_fuel_types()),
                'gear_box_types': len(self.get_all_gear_box_types()),
                'driving_gear_types': len(self.get_all_driving_gear_types()),
                'cities': len(self.get_all_cities()),
                'options': len(self.get_all_options())
            }
            return stats
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def search_cars_by_entities(self, entities: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск автомобилей по извлеченным сущностям (новые + поддержанные)"""
        try:
            cursor = self.connection.cursor()
            
            # Формируем SQL запрос
            where_conditions = []
            params = []
            
            # Марки
            if entities.get('brands'):
                brands = entities['brands']
                placeholders = ','.join(['?' for _ in brands])
                where_conditions.append(f"mark IN ({placeholders})")
                params.extend(brands)
            
            # Модели
            if entities.get('models'):
                models = entities['models']
                placeholders = ','.join(['?' for _ in models])
                where_conditions.append(f"model IN ({placeholders})")
                params.extend(models)
            
            # Цена от
            if entities.get('price_from'):
                where_conditions.append("price >= ?")
                params.append(entities['price_from'])
            
            # Цена до
            if entities.get('price_to'):
                where_conditions.append("price <= ?")
                params.append(entities['price_to'])
            
            # Типы кузова
            if entities.get('body_types'):
                body_types = entities['body_types']
                placeholders = ','.join(['?' for _ in body_types])
                where_conditions.append(f"body_type IN ({placeholders})")
                params.extend(body_types)
            
            # Цвета
            if entities.get('colors'):
                colors = entities['colors']
                placeholders = ','.join(['?' for _ in colors])
                where_conditions.append(f"color IN ({placeholders})")
                params.extend(colors)
            
            # Города
            if entities.get('cities'):
                cities = entities['cities']
                placeholders = ','.join(['?' for _ in cities])
                where_conditions.append(f"city IN ({placeholders})")
                params.extend(cities)
            
            # Состояние
            if entities.get('conditions'):
                conditions = entities['conditions']
                placeholders = ','.join(['?' for _ in conditions])
                where_conditions.append(f"condition IN ({placeholders})")
                params.extend(conditions)
            
            # Строим финальный запрос для обеих таблиц
            if where_conditions:
                where_clause = " AND ".join(where_conditions)
                # Создаем отдельные параметры для каждой таблицы
                query = f"""
                SELECT *, 'new' as car_type FROM car 
                WHERE {where_clause}
                UNION ALL
                SELECT *, 'used' as car_type FROM used_car 
                WHERE {where_clause}
                ORDER BY price ASC
                LIMIT ?
                """
                # Дублируем параметры для обеих таблиц
                all_params = params + params + [limit]
            else:
                query = """
                SELECT *, 'new' as car_type FROM car 
                UNION ALL
                SELECT *, 'used' as car_type FROM used_car 
                ORDER BY price ASC
                LIMIT ?
                """
                all_params = [limit]
            
            cursor.execute(query, all_params)
            rows = cursor.fetchall()
            
            # Преобразуем в список словарей
            cars = []
            for row in rows:
                car_dict = dict(row)
                cars.append(car_dict)
            
            return cars
            
        except Exception as e:
            logger.error(f"Ошибка поиска автомобилей: {e}")
            return []
    
    def get_popular_cars(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает популярные автомобили (новые + поддержанные)"""
        try:
            cursor = self.connection.cursor()
            
            # Берем автомобили с хорошими характеристиками и разумной ценой
            query = """
            SELECT *, 'new' as car_type FROM car 
            WHERE price > 500000 AND price < 5000000
            AND manufacture_year >= 2015
            UNION ALL
            SELECT *, 'used' as car_type FROM used_car 
            WHERE price > 300000 AND price < 3000000
            AND manufacture_year >= 2015
            ORDER BY price ASC
            LIMIT ?
            """
            
            cursor.execute(query, [limit])
            rows = cursor.fetchall()
            
            cars = []
            for row in rows:
                car_dict = dict(row)
                cars.append(car_dict)
            
            return cars
            
        except Exception as e:
            logger.error(f"Ошибка получения популярных автомобилей: {e}")
            return []
    
    def get_diverse_cars(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает разнообразные автомобили (новые + поддержанные)"""
        try:
            cursor = self.connection.cursor()
            
            # Берем автомобили разных марок и типов
            query = """
            SELECT *, 'new' as car_type FROM car 
            WHERE price > 300000 AND price < 10000000
            UNION ALL
            SELECT *, 'used' as car_type FROM used_car 
            WHERE price > 200000 AND price < 8000000
            ORDER BY price ASC
            LIMIT ?
            """
            
            cursor.execute(query, [limit])
            rows = cursor.fetchall()
            
            cars = []
            for row in rows:
                car_dict = dict(row)
                cars.append(car_dict)
            
            return cars
            
        except Exception as e:
            logger.error(f"Ошибка получения разнообразных автомобилей: {e}")
            return []

if __name__ == "__main__":
    # Тестирование
    with DatabaseEntityMapper() as mapper:
        print("Статистика сущностей в БД:")
        stats = mapper.get_entity_statistics()
        for entity_type, count in stats.items():
            print(f"  {entity_type}: {count}")
        
        print(f"\nПримеры марок: {list(mapper.get_all_brands())[:10]}")
        print(f"Примеры моделей: {list(mapper.get_all_models())[:10]}")
        print(f"Примеры цветов: {list(mapper.get_all_colors())[:10]}")
        print(f"Примеры типов кузова: {list(mapper.get_all_body_types())[:10]}")
        print(f"Примеры опций: {list(mapper.get_all_options())[:10]}")
