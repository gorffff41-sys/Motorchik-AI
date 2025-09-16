import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from database import get_db


class UserHistory:
    """Класс для управления историей пользователя"""
    
    def __init__(self):
        self.init_user_tables()
    
    def init_user_tables(self):
        """Инициализирует таблицы для пользователей"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица истории запросов
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT,
                intent TEXT,
                entities TEXT,  -- JSON
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Таблица любимых автомобилей
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                price INTEGER,
                dealer_center TEXT,
                notes TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, brand, model, year)
            )''')
            
            # Таблица сохранённых фильтров
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filter_name TEXT NOT NULL,
                filter_params TEXT NOT NULL,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Таблица предпочтений пользователя
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preferred_brands TEXT,  -- JSON список
                preferred_price_range TEXT,  -- JSON [min, max]
                preferred_body_types TEXT,  -- JSON список
                preferred_fuel_types TEXT,  -- JSON список
                preferred_cities TEXT,  -- JSON список
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )''')
            
            conn.commit()

    def add_query(self, user_id: str, query: str, response: str, 
                  intent: str = '', entities: dict = {}) -> bool:
        """Добавляет запрос в историю (user_queries и user_history)"""
        import time
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                if entities is None:
                    entities = {}
                entities_json = json.dumps(entities)
                # user_queries (старый способ)
                cursor.execute("""
                    INSERT INTO user_queries (user_id, query, response, intent, entities)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id or '',
                    query or '',
                    response or '',
                    intent or '',
                    entities_json
                ))
                # user_history (новый способ)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        message TEXT,
                        response TEXT,
                        intent TEXT,
                        entities TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    INSERT INTO user_history (user_id, message, response, intent, entities, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id or '',
                    query or '',
                    response or '',
                    intent or '',
                    entities_json,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении запроса в историю: {e}")
            return False
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Получает историю запросов пользователя"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT query, response, intent, entities, timestamp
                FROM user_queries 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            results = []
            for row in cursor.fetchall():
                query, response, intent, entities_json, timestamp = row
                entities = json.loads(entities_json) if entities_json else {}
                results.append({
                    'query': query,
                    'response': response,
                    'intent': intent,
                    'entities': entities,
                    'timestamp': timestamp
                })
            return results
    
    def get_user_history_v2(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Получает историю сообщений пользователя и ответов сервера (user_history)"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    message TEXT,
                    response TEXT,
                    intent TEXT,
                    entities TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                SELECT message, response, intent, entities, timestamp
                FROM user_history 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            results = []
            for row in cursor.fetchall():
                message, response, intent, entities_json, timestamp = row
                entities = json.loads(entities_json) if entities_json else {}
                results.append({
                    'message': message,
                    'response': response,
                    'intent': intent,
                    'entities': entities,
                    'timestamp': timestamp
                })
            return results
    
    def add_favorite(self, user_id: str, brand: str, model: str, 
                    year: int = 0, price: int = 0, 
                    dealer_center: str = '', notes: str = '') -> bool:
        """Добавляет автомобиль в избранное"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_favorites 
                    (user_id, brand, model, year, price, dealer_center, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id or '',
                    brand or '',
                    model or '',
                    year or 0,
                    price or 0,
                    dealer_center or '',
                    notes or ''
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении в избранное: {e}")
            return False
    
    def remove_favorite(self, user_id: str, brand: str, model: str, year: int = 0) -> bool:
        """Удаляет автомобиль из избранного"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_favorites 
                    WHERE user_id = ? AND brand = ? AND model = ? AND year = ?
                """, (
                    user_id or '',
                    brand or '',
                    model or '',
                    year or 0
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении из избранного: {e}")
            return False
    
    def get_favorites(self, user_id: str) -> List[Dict]:
        """Получает список избранных автомобилей"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT brand, model, year, price, dealer_center, notes, added_at
                FROM user_favorites 
                WHERE user_id = ?
                ORDER BY added_at DESC
            """, (user_id,))
            
            results = []
            for row in cursor.fetchall():
                brand, model, year, price, dealer_center, notes, added_at = row
                results.append({
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'price': price,
                    'dealer_center': dealer_center,
                    'notes': notes,
                    'added_at': added_at
                })
            
            return results
    
    def save_filter(self, user_id: str, filter_name: str, filter_params: Dict) -> bool:
        """Сохраняет фильтр пользователя (все параметры для smart_filter_cars)"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                # Сохраняем только нужные параметры
                allowed = ["brand", "model", "year", "price_min", "price_max", "body_type", "used"]
                params_json = json.dumps({k: v for k, v in filter_params.items() if k in allowed})
                cursor.execute("""
                    INSERT INTO user_filters (user_id, filter_name, filter_params)
                    VALUES (?, ?, ?)
                """, (user_id, filter_name, params_json))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при сохранении фильтра: {e}")
            return False
    
    def get_saved_filters(self, user_id: str) -> List[Dict]:
        """Получает сохранённые фильтры пользователя (параметры для smart_filter_cars)"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filter_name, filter_params, created_at
                FROM user_filters 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            results = []
            for row in cursor.fetchall():
                filter_name, params_json, created_at = row
                filter_params = json.loads(params_json)
                results.append({
                    'name': filter_name,
                    'params': filter_params,
                    'created_at': created_at
                })
            return results
    
    def update_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Обновляет предпочтения пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Подготавливаем данные
                preferred_brands = json.dumps(preferences.get('brands', []))
                preferred_price_range = json.dumps(preferences.get('price_range', []))
                preferred_body_types = json.dumps(preferences.get('body_types', []))
                preferred_fuel_types = json.dumps(preferences.get('fuel_types', []))
                preferred_cities = json.dumps(preferences.get('cities', []))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, preferred_brands, preferred_price_range, 
                     preferred_body_types, preferred_fuel_types, preferred_cities)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, preferred_brands, preferred_price_range,
                     preferred_body_types, preferred_fuel_types, preferred_cities))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при обновлении предпочтений: {e}")
            return False
    
    def get_preferences(self, user_id: str) -> Dict:
        """Получает предпочтения пользователя"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT preferred_brands, preferred_price_range, 
                       preferred_body_types, preferred_fuel_types, preferred_cities
                FROM user_preferences 
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                brands, price_range, body_types, fuel_types, cities = row
                
                # Безопасная загрузка JSON с проверкой на None
                return {
                    'brands': json.loads(brands) if brands else [],
                    'price_range': json.loads(price_range) if price_range else [],
                    'body_types': json.loads(body_types) if body_types else [],
                    'fuel_types': json.loads(fuel_types) if fuel_types else [],
                    'cities': json.loads(cities) if cities else []
                }
            
            # Возвращаем структуру по умолчанию
            return {
                'brands': [],
                'price_range': [],
                'body_types': [],
                'fuel_types': [],
                'cities': []
            }
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """Получает статистику пользователя"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Общее количество запросов
            cursor.execute("SELECT COUNT(*) FROM user_queries WHERE user_id = ?", (user_id,))
            total_queries = cursor.fetchone()[0]
            
            # Количество избранных авто
            cursor.execute("SELECT COUNT(*) FROM user_favorites WHERE user_id = ?", (user_id,))
            total_favorites = cursor.fetchone()[0]
            
            # Количество сохранённых фильтров
            cursor.execute("SELECT COUNT(*) FROM user_filters WHERE user_id = ?", (user_id,))
            total_filters = cursor.fetchone()[0]
            
            # Самые популярные бренды
            cursor.execute("""
                SELECT brand, COUNT(*) as count
                FROM user_favorites 
                WHERE user_id = ?
                GROUP BY brand
                ORDER BY count DESC
            """, (user_id,))
            popular_brands = [{'brand': brand, 'count': count} for brand, count in cursor.fetchall()]
            
            # Самые популярные intent'ы
            cursor.execute("""
                SELECT intent, COUNT(*) as count
                FROM user_queries 
                WHERE user_id = ? AND intent IS NOT NULL
                GROUP BY intent
                ORDER BY count DESC
            """, (user_id,))
            popular_intents = [{'intent': intent, 'count': count} for intent, count in cursor.fetchall()]
            
            return {
                'total_queries': total_queries,
                'total_favorites': total_favorites,
                'total_filters': total_filters,
                'popular_brands': popular_brands,
                'popular_intents': popular_intents
            }
    
    def get_recommendations(self, user_id: str) -> List[Dict]:
        """Получает персональные рекомендации для пользователя"""
        preferences = self.get_preferences(user_id)
        statistics = self.get_user_statistics(user_id)
        
        recommendations = []
        
        # Рекомендации по брендам
        if preferences.get('brands'):
            recommendations.append({
                'type': 'preference',
                'message': f"Вам могут понравиться автомобили брендов: {', '.join(preferences['brands'])}",
                'priority': 'high'
            })
        
        # Рекомендации по цене (только если есть диапазон)
        price_range = preferences.get('price_range')
        if price_range and len(price_range) == 2:
            min_price, max_price = price_range
            recommendations.append({
                'type': 'price_range',
                'message': f"Рекомендуемый ценовой диапазон: {min_price:,} - {max_price:,} руб",
                'priority': 'medium'
            })
        
        # Рекомендации на основе истории
        if statistics['popular_brands']:
            top_brand = statistics['popular_brands'][0]['brand']
            recommendations.append({
                'type': 'history',
                'message': f"Вы часто интересуетесь {top_brand}. Хотите посмотреть новые модели?",
                'priority': 'medium'
            })
        
        # Рекомендации на основе избранного
        favorites = self.get_favorites(user_id)
        if favorites:
            recommendations.append({
                'type': 'favorites',
                'message': f"У вас {len(favorites)} избранных автомобилей. Хотите сравнить их?",
                'priority': 'low'
            })
        
        return recommendations
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Очищает старые данные"""
        cutoff_date = datetime.now() - timedelta(days=days)
        # Преобразуем datetime в строку для SQL
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_queries 
                WHERE timestamp < ?
            """, (cutoff_date_str,))
            
            deleted_queries = cursor.rowcount
            conn.commit()
            return deleted_queries


# Создаем глобальный экземпляр
user_history = UserHistory() 
 
 
 
 
 
 