import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from database import get_db
from user_history import UserHistory
import statistics

logger = logging.getLogger(__name__)

class UserAnalytics:
    """Система аналитики пользовательского поведения"""
    
    def __init__(self):
        self.user_history = UserHistory()
        self.init_analytics_tables()
    
    def init_analytics_tables(self):
        """Инициализирует таблицы для аналитики"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица сессий пользователей
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                query_count INTEGER DEFAULT 0,
                avg_session_duration REAL DEFAULT 0.0,
                most_common_intent TEXT,
                device_type TEXT,
                user_agent TEXT
            )''')
            
            # Таблица паттернов поведения
            cursor.execute('''CREATE TABLE IF NOT EXISTS behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,  -- 'search', 'comparison', 'browsing'
                pattern_data TEXT NOT NULL,  -- JSON
                frequency INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Таблица конверсий
            cursor.execute('''CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversion_type TEXT NOT NULL,  -- 'test_drive', 'contact', 'favorite'
                car_id INTEGER,
                dealer_id INTEGER,
                conversion_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Таблица воронки продаж
            cursor.execute('''CREATE TABLE IF NOT EXISTS sales_funnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                funnel_stage TEXT NOT NULL,  -- 'awareness', 'interest', 'consideration', 'intent', 'purchase'
                stage_data TEXT,  -- JSON с данными этапа
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exited_at TIMESTAMP,
                duration_minutes INTEGER
            )''')
            
            conn.commit()
    
    def analyze_user_behavior(self, user_id: str, days: int = 30) -> Dict:
        """Анализирует поведение пользователя за период"""
        try:
            # Получаем историю запросов
            history = self.user_history.get_user_history(user_id, 1000)
            
            # Фильтруем по периоду
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_history = [
                h for h in history 
                if datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) > cutoff_date
            ]
            
            if not recent_history:
                return {"error": "Нет данных за указанный период"}
            
            analysis = {
                'user_id': user_id,
                'period_days': days,
                'total_queries': len(recent_history),
                'unique_days': len(set(h['timestamp'][:10] for h in recent_history)),
                'avg_queries_per_day': len(recent_history) / days,
                'intent_distribution': self.get_intent_distribution(recent_history),
                'brand_preferences': self.get_brand_preferences(recent_history),
                'price_preferences': self.get_price_preferences(recent_history),
                'time_patterns': self.get_time_patterns(recent_history),
                'session_analysis': self.get_session_analysis(user_id, days),
                'conversion_analysis': self.get_conversion_analysis(user_id, days),
                'engagement_score': self.calculate_engagement_score(recent_history),
                'loyalty_score': self.calculate_loyalty_score(user_id, days)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа поведения пользователя: {e}")
            return {"error": str(e)}
    
    def get_intent_distribution(self, history: List[Dict]) -> Dict:
        """Анализирует распределение интентов"""
        intent_counts = {}
        for item in history:
            intent = item.get('intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        total = len(history)
        return {
            intent: {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for intent, count in intent_counts.items()
        }
    
    def get_brand_preferences(self, history: List[Dict]) -> List[Dict]:
        """Анализирует предпочтения брендов"""
        brand_counts = {}
        for item in history:
            entities = item.get('entities', {})
            brand = entities.get('brand')
            if brand:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                'brand': brand,
                'count': count,
                'percentage': round(count / len(history) * 100, 1)
            }
            for brand, count in sorted_brands[:10]
        ]
    
    def get_price_preferences(self, history: List[Dict]) -> Dict:
        """Анализирует предпочтения по цене"""
        prices = []
        for item in history:
            entities = item.get('entities', {})
            price = entities.get('price')
            if price and isinstance(price, (int, float)):
                prices.append(price)
        
        if not prices:
            return {}
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': round(statistics.mean(prices), 0),
            'median_price': statistics.median(prices),
            'price_ranges': self.get_price_ranges(prices)
        }
    
    def get_price_ranges(self, prices: List[float]) -> List[Dict]:
        """Группирует цены по диапазонам"""
        if not prices:
            return []
        
        min_price, max_price = min(prices), max(prices)
        range_size = (max_price - min_price) / 5 if max_price > min_price else 1
        
        ranges = []
        for i in range(5):
            start = min_price + i * range_size
            end = min_price + (i + 1) * range_size
            count = sum(1 for p in prices if start <= p < end)
            
            ranges.append({
                'range': f"{int(start):,} - {int(end):,} ₽",
                'count': count,
                'percentage': round(count / len(prices) * 100, 1)
            })
        
        return ranges
    
    def get_time_patterns(self, history: List[Dict]) -> Dict:
        """Анализирует временные паттерны"""
        hour_counts = {}
        day_counts = {}
        
        for item in history:
            try:
                dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                hour = dt.hour
                day = dt.strftime('%A')
                
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
            except:
                continue
        
        return {
            'peak_hours': sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            'peak_days': sorted(day_counts.items(), key=lambda x: x[1], reverse=True),
            'hourly_distribution': [hour_counts.get(h, 0) for h in range(24)]
        }
    
    def get_session_analysis(self, user_id: str, days: int) -> Dict:
        """Анализирует сессии пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as session_count,
                           AVG(query_count) as avg_queries_per_session,
                           AVG(avg_session_duration) as avg_duration,
                           most_common_intent
                    FROM user_sessions
                    WHERE user_id = ? AND start_time >= datetime('now', '-{} days')
                """.format(days), (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'session_count': row[0],
                        'avg_queries_per_session': round(row[1] or 0, 1),
                        'avg_duration_minutes': round(row[2] or 0, 1),
                        'most_common_intent': row[3]
                    }
                return {}
        except Exception as e:
            logger.error(f"Ошибка анализа сессий: {e}")
            return {}
    
    def get_conversion_analysis(self, user_id: str, days: int) -> Dict:
        """Анализирует конверсии пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT conversion_type, COUNT(*) as count, AVG(conversion_value) as avg_value
                    FROM conversions
                    WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
                    GROUP BY conversion_type
                """.format(days), (user_id,))
                
                conversions = {}
                for row in cursor.fetchall():
                    conversions[row[0]] = {
                        'count': row[1],
                        'avg_value': round(row[2] or 0, 0)
                    }
                
                return conversions
        except Exception as e:
            logger.error(f"Ошибка анализа конверсий: {e}")
            return {}
    
    def calculate_engagement_score(self, history: List[Dict]) -> float:
        """Рассчитывает score вовлеченности пользователя"""
        if not history:
            return 0.0
        
        score = 0.0
        
        # Количество запросов
        query_count = len(history)
        if query_count >= 50:
            score += 0.3
        elif query_count >= 20:
            score += 0.2
        elif query_count >= 10:
            score += 0.1
        
        # Разнообразие интентов
        intents = set(item.get('intent') for item in history)
        if len(intents) >= 5:
            score += 0.2
        elif len(intents) >= 3:
            score += 0.1
        
        # Регулярность использования
        dates = set(item['timestamp'][:10] for item in history)
        if len(dates) >= 10:
            score += 0.2
        elif len(dates) >= 5:
            score += 0.1
        
        # Использование Llama (сложные запросы)
        llama_queries = sum(1 for item in history if item.get('used_llm'))
        if llama_queries > 0:
            score += 0.1
        
        # Обратная связь (если есть)
        feedback_queries = sum(1 for item in history if item.get('quality_score'))
        if feedback_queries > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def calculate_loyalty_score(self, user_id: str, days: int) -> float:
        """Рассчитывает score лояльности пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Количество дней с активностью
                cursor.execute("""
                    SELECT COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM chat_history
                    WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
                """.format(days), (user_id,))
                
                active_days = cursor.fetchone()[0] or 0
                
                # Количество возвращений
                cursor.execute("""
                    SELECT COUNT(DISTINCT DATE(timestamp)) as return_days
                    FROM chat_history
                    WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    HAVING COUNT(*) > 1
                """.format(days), (user_id,))
                
                return_days = len(cursor.fetchall())
                
                # Рассчитываем score
                score = 0.0
                
                # Активность
                if active_days >= days * 0.5:
                    score += 0.4
                elif active_days >= days * 0.2:
                    score += 0.2
                
                # Возвращения
                if return_days >= active_days * 0.3:
                    score += 0.3
                elif return_days >= active_days * 0.1:
                    score += 0.1
                
                # Длительность использования
                if active_days >= 7:
                    score += 0.3
                elif active_days >= 3:
                    score += 0.1
                
                return min(score, 1.0)
                
        except Exception as e:
            logger.error(f"Ошибка расчета лояльности: {e}")
            return 0.0
    
    def get_user_segments(self) -> List[Dict]:
        """Получает сегменты пользователей"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Анализируем всех пользователей
                cursor.execute("""
                    SELECT user_id, COUNT(*) as query_count,
                           COUNT(DISTINCT DATE(timestamp)) as active_days,
                           AVG(CAST(quality_score AS FLOAT)) as avg_feedback
                    FROM chat_history
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY user_id
                """)
                
                users = cursor.fetchall()
                segments = {
                    'highly_engaged': [],
                    'moderately_engaged': [],
                    'lightly_engaged': [],
                    'inactive': []
                }
                
                for user_id, query_count, active_days, avg_feedback in users:
                    user_data = {
                        'user_id': user_id,
                        'query_count': query_count,
                        'active_days': active_days,
                        'avg_feedback': round(avg_feedback or 0, 1)
                    }
                    
                    # Классифицируем пользователя
                    if query_count >= 50 and active_days >= 10:
                        segments['highly_engaged'].append(user_data)
                    elif query_count >= 20 and active_days >= 5:
                        segments['moderately_engaged'].append(user_data)
                    elif query_count >= 5:
                        segments['lightly_engaged'].append(user_data)
                    else:
                        segments['inactive'].append(user_data)
                
                return [
                    {
                        'segment': segment,
                        'count': len(users),
                        'users': users[:10]  # Топ-10 для каждого сегмента
                    }
                    for segment, users in segments.items()
                ]
                
        except Exception as e:
            logger.error(f"Ошибка получения сегментов: {e}")
            return []
    
    def get_behavior_insights(self, user_id: str) -> List[str]:
        """Генерирует инсайты о поведении пользователя"""
        insights = []
        
        try:
            analysis = self.analyze_user_behavior(user_id, 30)
            
            if 'error' in analysis:
                return insights
            
            # Анализ активности
            if analysis['avg_queries_per_day'] > 3:
                insights.append("Вы очень активный пользователь! Используете систему чаще среднего.")
            elif analysis['avg_queries_per_day'] < 0.5:
                insights.append("Попробуйте задать больше вопросов для получения персонализированных рекомендаций.")
            
            # Анализ интентов
            intent_dist = analysis['intent_distribution']
            if 'search_car' in intent_dist and intent_dist['search_car']['percentage'] > 70:
                insights.append("Вы в основном ищете автомобили. Попробуйте сравнить модели или получить рекомендации!")
            
            # Анализ брендов
            brand_prefs = analysis['brand_preferences']
            if brand_prefs:
                top_brand = brand_prefs[0]
                insights.append(f"Ваш любимый бренд: {top_brand['brand']} ({top_brand['percentage']}% запросов)")
            
            # Анализ времени
            time_patterns = analysis['time_patterns']
            if time_patterns['peak_hours']:
                peak_hour = time_patterns['peak_hours'][0][0]
                insights.append(f"Вы наиболее активны в {peak_hour}:00")
            
            # Анализ вовлеченности
            engagement = analysis['engagement_score']
            if engagement > 0.7:
                insights.append("Отличная вовлеченность! Вы используете все возможности системы.")
            elif engagement < 0.3:
                insights.append("Попробуйте больше функций: сравнение, рекомендации, тест-драйв.")
            
            return insights
            
        except Exception as e:
            logger.error(f"Ошибка генерации инсайтов: {e}")
            return ["Анализ поведения временно недоступен"]
    
    def log_user_session(self, user_id: Optional[str], session_id: Optional[str], query_count: Optional[int] = 1,
                        duration_minutes: Optional[float] = 0, most_common_intent: Optional[str] = None,
                        device_type: Optional[str] = None, user_agent: Optional[str] = None):
        """Логирует сессию пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_sessions 
                    (user_id, session_id, query_count, avg_session_duration, 
                     most_common_intent, device_type, user_agent, end_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    str(user_id or ""), str(session_id or ""), int(query_count or 0), float(duration_minutes or 0.0),
                    str(most_common_intent or ""), str(device_type or ""), str(user_agent or "")
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования сессии: {e}")
    
    def log_conversion(self, user_id: Optional[str], conversion_type: Optional[str], car_id: Optional[int] = None,
                      dealer_id: Optional[int] = None, conversion_value: Optional[float] = None):
        """Логирует конверсию пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversions 
                    (user_id, conversion_type, car_id, dealer_id, conversion_value)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(user_id or ""), str(conversion_type or ""), int(car_id or 0), int(dealer_id or 0), float(conversion_value or 0.0)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования конверсии: {e}")
    
    def get_user_recommendations_insights(self, user_id: str) -> Dict:
        """Получает инсайты для улучшения рекомендаций"""
        try:
            analysis = self.analyze_user_behavior(user_id, 30)
            
            if 'error' in analysis:
                return {}
            
            insights = {
                'preferred_brands': [b['brand'] for b in analysis['brand_preferences'][:3]],
                'price_range': analysis['price_preferences'],
                'preferred_intents': list(analysis['intent_distribution'].keys())[:3],
                'engagement_level': 'high' if analysis['engagement_score'] > 0.7 else 'medium' if analysis['engagement_score'] > 0.3 else 'low',
                'loyalty_level': 'high' if analysis['loyalty_score'] > 0.7 else 'medium' if analysis['loyalty_score'] > 0.3 else 'low',
                'suggested_features': []
            }
            
            # Предложения функций
            if analysis['engagement_score'] < 0.5:
                insights['suggested_features'].append('comparison_tool')
                insights['suggested_features'].append('personalized_recommendations')
            
            if analysis['loyalty_score'] < 0.3:
                insights['suggested_features'].append('loyalty_program')
                insights['suggested_features'].append('exclusive_offers')
            
            return insights
            
        except Exception as e:
            logger.error(f"Ошибка получения инсайтов рекомендаций: {e}")
            return {} 