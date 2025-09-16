import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from database import get_db
from user_history import UserHistory
import random

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Движок рекомендаций для автоассистента"""
    
    def __init__(self):
        self.user_history = UserHistory()
        self.init_recommendation_tables()
    
    def init_recommendation_tables(self):
        """Инициализирует таблицы для рекомендаций"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица рекомендаций
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,  -- 'car', 'dealer', 'promotion'
                item_id TEXT NOT NULL,
                score REAL NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                shown_at TIMESTAMP,
                clicked_at TIMESTAMP,
                feedback_score INTEGER  -- 1-5
            )''')
            
            # Таблица популярных запросов
            cursor.execute('''CREATE TABLE IF NOT EXISTS popular_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                intent TEXT,
                count INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success_rate REAL DEFAULT 0.0
            )''')
            
            # Таблица трендов
            cursor.execute('''CREATE TABLE IF NOT EXISTS trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_type TEXT NOT NULL,  -- 'brand', 'model', 'price_range'
                trend_value TEXT NOT NULL,
                popularity_score REAL DEFAULT 0.0,
                growth_rate REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
    
    def get_car_recommendations(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Получает персональные рекомендации автомобилей"""
        try:
            # Получаем предпочтения пользователя
            preferences = self.get_user_preferences(user_id)
            
            # Получаем историю запросов
            history = self.user_history.get_user_history(user_id, 20)
            
            # Анализируем предпочтения из истории
            brand_preferences = self.analyze_brand_preferences(history)
            price_preferences = self.analyze_price_preferences(history)
            
            # Формируем SQL запрос с учетом предпочтений
            query = """
                SELECT c.*, dc.name as dealer_name, dc.city
                FROM car c
                LEFT JOIN dealer_centers dc ON c.dealer_center = dc.name
                WHERE 1=1
            """
            params = []
            
            # Фильтры по предпочтениям
            if brand_preferences:
                placeholders = ','.join(['?' for _ in brand_preferences])
                query += f" AND c.mark IN ({placeholders})"
                params.extend(brand_preferences)
            
            if price_preferences:
                min_price, max_price = price_preferences
                if min_price and max_price:
                    query += " AND c.price BETWEEN ? AND ?"
                    params.extend([min_price, max_price])
            
            # Сортировка по релевантности
            query += " ORDER BY c.manufacture_year DESC, c.price ASC"
            params.append(limit)
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                cars = cursor.fetchall()
                
                recommendations = []
                for car in cars:
                    score = self.calculate_car_score(car, preferences, history)
                    recommendations.append({
                        'id': car[0],
                        'brand': car[1],
                        'model': car[2],
                        'year': car[3],
                        'price': car[4],
                        'mileage': car[5],
                        'dealer_name': car[-2],
                        'city': car[-1],
                        'score': score,
                        'reason': self.get_recommendation_reason(car, preferences)
                    })
                
                # Сортируем по score
                recommendations.sort(key=lambda x: x['score'], reverse=True)
                return recommendations[:limit]
                
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Получает предпочтения пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT preferred_brands, preferred_price_range, preferred_body_types,
                           preferred_fuel_types, preferred_cities
                    FROM user_preferences
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'brands': json.loads(row[0]) if row[0] else [],
                        'price_range': json.loads(row[1]) if row[1] else [0, 10000000],
                        'body_types': json.loads(row[2]) if row[2] else [],
                        'fuel_types': json.loads(row[3]) if row[3] else [],
                        'cities': json.loads(row[4]) if row[4] else []
                    }
                return {}
        except Exception as e:
            logger.error(f"Ошибка получения предпочтений: {e}")
            return {}
    
    def analyze_brand_preferences(self, history: List[Dict]) -> List[str]:
        """Анализирует предпочтения брендов из истории"""
        brand_counts = {}
        for item in history:
            entities = item.get('entities', {})
            brand = entities.get('brand')
            if brand:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        # Возвращаем топ-3 бренда
        sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
        return [brand for brand, count in sorted_brands[:3]]
    
    def analyze_price_preferences(self, history: List[Dict]) -> tuple:
        """Анализирует предпочтения по цене из истории"""
        prices = []
        for item in history:
            entities = item.get('entities', {})
            price = entities.get('price')
            if price:
                prices.append(price)
        
        if prices:
            min_price = min(prices) * 0.8  # 20% ниже минимальной
            max_price = max(prices) * 1.2  # 20% выше максимальной
            return (min_price, max_price)
        return (None, None)
    
    def calculate_car_score(self, car: tuple, preferences: Dict, history: List[Dict]) -> float:
        """Рассчитывает score для автомобиля"""
        score = 0.0
        
        # Базовый score по году
        current_year = datetime.now().year
        year_diff = current_year - car[3]
        if year_diff <= 2:
            score += 0.3
        elif year_diff <= 5:
            score += 0.2
        elif year_diff <= 10:
            score += 0.1
        
        # Score по бренду
        if car[1] in preferences.get('brands', []):
            score += 0.3
        
        # Score по цене
        price_range = preferences.get('price_range', [0, 10000000])
        if price_range[0] <= car[4] <= price_range[1]:
            score += 0.2
        
        # Score по городу
        if car[-1] in preferences.get('cities', []):
            score += 0.1
        
        # Случайный фактор для разнообразия
        score += random.uniform(0, 0.1)
        
        return min(score, 1.0)
    
    def get_recommendation_reason(self, car: tuple, preferences: Dict) -> str:
        """Формирует причину рекомендации"""
        reasons = []
        
        if car[1] in preferences.get('brands', []):
            reasons.append(f"ваш любимый бренд {car[1]}")
        
        current_year = datetime.now().year
        year_diff = current_year - car[3]
        if year_diff <= 2:
            reasons.append("новый автомобиль")
        elif year_diff <= 5:
            reasons.append("недавний год выпуска")
        
        if reasons:
            return f"Рекомендуем потому что: {', '.join(reasons)}"
        return "Персональная рекомендация на основе ваших предпочтений"
    
    def get_popular_cars(self, limit: int = 10) -> List[Dict]:
        """Получает популярные автомобили"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, dc.name as dealer_name, dc.city,
                           COUNT(ch.id) as view_count
                    FROM car c
                    LEFT JOIN dealer_centers dc ON c.dealer_center = dc.name
                    LEFT JOIN chat_history ch ON ch.entities LIKE '%' || c.mark || '%'
                    GROUP BY c.id
                    ORDER BY view_count DESC, c.manufacture_year DESC
                """, (limit,))
                
                cars = cursor.fetchall()
                return [
                    {
                        'id': car[0],
                        'brand': car[1],
                        'model': car[2],
                        'year': car[3],
                        'price': car[4],
                        'mileage': car[5],
                        'dealer_name': car[-3],
                        'city': car[-2],
                        'view_count': car[-1]
                    }
                    for car in cars
                ]
        except Exception as e:
            logger.error(f"Ошибка получения популярных автомобилей: {e}")
            return []
    
    def get_trending_brands(self, days: int = 30) -> List[Dict]:
        """Получает трендовые бренды"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT c.mark, COUNT(*) as query_count,
                           AVG(c.price) as avg_price,
                           COUNT(DISTINCT ch.user_id) as unique_users
                    FROM car c
                    LEFT JOIN chat_history ch ON ch.entities LIKE '%' || c.mark || '%'
                    WHERE ch.timestamp >= datetime('now', '-{days} days')
                    GROUP BY c.mark
                    ORDER BY query_count DESC
                """)
                
                brands = cursor.fetchall()
                return [
                    {
                        'brand': brand[0],
                        'query_count': brand[1],
                        'avg_price': round(brand[2] or 0, 0),
                        'unique_users': brand[3]
                    }
                    for brand in brands
                ]
        except Exception as e:
            logger.error(f"Ошибка получения трендовых брендов: {e}")
            return []
    
    def log_recommendation_click(self, user_id: str, recommendation_id: int):
        """Логирует клик по рекомендации"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_recommendations
                    SET clicked_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (recommendation_id, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования клика: {e}")
    
    def log_recommendation_feedback(self, user_id: str, recommendation_id: int, score: int):
        """Логирует обратную связь по рекомендации"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_recommendations
                    SET feedback_score = ?
                    WHERE id = ? AND user_id = ?
                """, (score, recommendation_id, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования обратной связи: {e}")
    
    def get_similar_cars(self, car_id: int, limit: int = 5) -> List[Dict]:
        """Получает похожие автомобили"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Получаем характеристики автомобиля
                cursor.execute("""
                    SELECT mark, model, manufacture_year, price, mileage, fuel_type, body_type
                    FROM car WHERE id = ?
                """, (car_id,))
                
                car = cursor.fetchone()
                if not car:
                    return []
                
                brand, model, year, price, mileage, fuel_type, body_type = car
                
                # Ищем похожие автомобили
                cursor.execute("""
                    SELECT c.*, dc.name as dealer_name, dc.city
                    FROM car c
                    LEFT JOIN dealer_centers dc ON c.dealer_center = dc.name
                    WHERE c.id != ?
                    AND (
                        c.mark = ? OR
                        c.model = ? OR
                        ABS(c.manufacture_year - ?) <= 2 OR
                        ABS(c.price - ?) <= ? * 0.2 OR
                        c.fuel_type = ? OR
                        c.body_type = ?
                    )
                    ORDER BY 
                        CASE WHEN c.mark = ? THEN 1 ELSE 0 END DESC,
                        CASE WHEN c.model = ? THEN 1 ELSE 0 END DESC,
                        ABS(c.manufacture_year - ?) ASC,
                        ABS(c.price - ?) ASC
                """, (car_id, brand, model, year, price, price, fuel_type, body_type,
                      brand, model, year, price, limit))
                
                cars = cursor.fetchall()
                return [
                    {
                        'id': car[0],
                        'brand': car[1],
                        'model': car[2],
                        'year': car[3],
                        'price': car[4],
                        'mileage': car[5],
                        'dealer_name': car[-2],
                        'city': car[-1],
                        'similarity_score': self.calculate_similarity_score(car, car)
                    }
                    for car in cars
                ]
        except Exception as e:
            logger.error(f"Ошибка получения похожих автомобилей: {e}")
            return []
    
    def calculate_similarity_score(self, car1: tuple, car2: tuple) -> float:
        """Рассчитывает score схожести между автомобилями"""
        score = 0.0
        
        # Бренд и модель
        if car1[1] == car2[1]:  # brand
            score += 0.4
        if car1[2] == car2[2]:  # model
            score += 0.3
        
        # Год (близость)
        year_diff = abs(car1[3] - car2[3])
        if year_diff == 0:
            score += 0.2
        elif year_diff <= 2:
            score += 0.1
        
        # Цена (близость)
        price_diff = abs(car1[4] - car2[4]) / max(car1[4], car2[4])
        if price_diff <= 0.1:
            score += 0.1
        
        return min(score, 1.0) 