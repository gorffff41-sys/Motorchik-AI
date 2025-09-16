import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timedelta
import pickle
import os

class AdvancedRecommendationEngine:
    """
    Продвинутый движок рекомендаций с использованием машинного обучения.
    """
    
    def __init__(self, db_path: str = "instance/cars.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Модели ML
        self.tfidf_vectorizer = None
        self.car_similarity_matrix = None
        self.user_clusters = None
        self.scaler = StandardScaler()
        
        # Кэш для производительности
        self.car_features_cache = {}
        self.user_preferences_cache = {}
        
        # Параметры
        self.similarity_threshold = 0.3
        self.max_recommendations = 10
        self.cache_ttl = 3600  # 1 час
        
        # Инициализация
        self._load_or_train_models()
    
    def _load_or_train_models(self):
        """Загружает или обучает модели машинного обучения."""
        model_files = {
            'tfidf': 'ml_models/tfidf_vectorizer.pkl',
            'similarity': 'ml_models/car_similarity_matrix.pkl',
            'clusters': 'ml_models/user_clusters.pkl',
            'scaler': 'ml_models/scaler.pkl'
        }
        
        try:
            # Попытка загрузить существующие модели
            if os.path.exists(model_files['tfidf']):
                with open(model_files['tfidf'], 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
            
            if os.path.exists(model_files['similarity']):
                with open(model_files['similarity'], 'rb') as f:
                    self.car_similarity_matrix = pickle.load(f)
            
            if os.path.exists(model_files['clusters']):
                with open(model_files['clusters'], 'rb') as f:
                    self.user_clusters = pickle.load(f)
            
            if os.path.exists(model_files['scaler']):
                with open(model_files['scaler'], 'rb') as f:
                    self.scaler = pickle.load(f)
                    
            self.logger.info("Модели ML успешно загружены")
            
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить модели ML: {e}")
            self._train_models()
    
    def _train_models(self):
        """Обучает модели машинного обучения."""
        try:
            # Загружаем данные
            cars_data = self._load_cars_data()
            
            if cars_data.empty:
                self.logger.error("Нет данных для обучения моделей")
                return
            
            # Подготовка текстовых данных для TF-IDF
            car_descriptions = cars_data.apply(
                lambda row: f"{row.get('mark', '')} {row.get('model', '')} {row.get('body_type', '')} {row.get('fuel_type', '')} {row.get('transmission', '')}",
                axis=1
            ).fillna('')
            
            # Обучение TF-IDF векторизатора
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(car_descriptions)
            
            # Создание матрицы схожести
            self.car_similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Кластеризация пользователей (если есть данные о пользователях)
            self._train_user_clusters(cars_data)
            
            # Сохранение моделей
            self._save_models()
            
            self.logger.info("Модели ML успешно обучены и сохранены")
            
        except Exception as e:
            self.logger.error(f"Ошибка при обучении моделей: {e}")
    
    def _load_cars_data(self) -> pd.DataFrame:
        """Загружает данные автомобилей из БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Загружаем новые и подержанные автомобили
            new_cars = pd.read_sql_query("""
                SELECT id, mark, model, price, manufacture_year, fuel_type,
                       gear_box_type, driving_gear_type, body_type, color, dealer_center, city
                FROM car WHERE mark IS NOT NULL
            """, conn)
            
            used_cars = pd.read_sql_query("""
                SELECT id, mark, model, price, manufacture_year, mileage, fuel_type,
                       gear_box_type, driving_gear_type, body_type, color, dealer_center, city
                FROM used_car WHERE mark IS NOT NULL
            """, conn)
            
            # Объединяем данные
            # Для новых автомобилей добавляем колонку mileage со значением 0
            new_cars['mileage'] = 0
            new_cars['transmission'] = new_cars['gear_box_type']
            used_cars['transmission'] = used_cars['gear_box_type']
            
            all_cars = pd.concat([new_cars, used_cars], ignore_index=True)
            
            conn.close()
            return all_cars
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке данных: {e}")
            return pd.DataFrame()
    
    def _train_user_clusters(self, cars_data: pd.DataFrame):
        """Обучает кластеризацию пользователей."""
        try:
            # Создаем признаки для кластеризации
            user_features = []
            
            # Группируем по маркам и создаем признаки
            brand_stats = cars_data.groupby('mark').agg({
                'price': ['mean', 'std'],
                'manufacture_year': ['mean', 'std'],
                'mileage': ['mean', 'std']
            }).fillna(0)
            
            # Нормализуем признаки
            feature_matrix = self.scaler.fit_transform(brand_stats.values)
            
            # Кластеризация
            n_clusters = min(5, len(feature_matrix))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(feature_matrix)
            
            self.user_clusters = {
                'model': kmeans,
                'brand_stats': brand_stats,
                'clusters': clusters
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при обучении кластеров пользователей: {e}")
    
    def _save_models(self):
        """Сохраняет обученные модели."""
        try:
            os.makedirs('ml_models', exist_ok=True)
            
            if self.tfidf_vectorizer:
                with open('ml_models/tfidf_vectorizer.pkl', 'wb') as f:
                    pickle.dump(self.tfidf_vectorizer, f)
            
            if self.car_similarity_matrix is not None:
                with open('ml_models/car_similarity_matrix.pkl', 'wb') as f:
                    pickle.dump(self.car_similarity_matrix, f)
            
            if self.user_clusters:
                with open('ml_models/user_clusters.pkl', 'wb') as f:
                    pickle.dump(self.user_clusters, f)
            
            with open('ml_models/scaler.pkl', 'wb') as f:
                pickle.dump(self.scaler, f)
                
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении моделей: {e}")
    
    def get_content_based_recommendations(self, car_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает рекомендации на основе содержимого."""
        try:
            if self.car_similarity_matrix is None:
                return []
            
            # Получаем индекс автомобиля
            cars_data = self._load_cars_data()
            car_index = cars_data[cars_data['id'] == car_id].index
            
            if len(car_index) == 0:
                return []
            
            car_index = car_index[0]
            
            # Получаем схожести
            similarities = self.car_similarity_matrix[car_index]
            
            # Находим наиболее похожие автомобили
            similar_indices = np.argsort(similarities)[::-1][1:limit+1]
            
            recommendations = []
            for idx in similar_indices:
                if similarities[idx] > self.similarity_threshold:
                    car_info = cars_data.iloc[idx].to_dict()
                    car_info['similarity_score'] = float(similarities[idx])
                    recommendations.append(car_info)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении рекомендаций: {e}")
            return []
    
    def get_collaborative_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает рекомендации на основе коллаборативной фильтрации."""
        try:
            # Получаем историю пользователя
            user_history = self._get_user_history(user_id)
            
            if not user_history:
                return self._get_popular_cars(limit)
            
            # Анализируем предпочтения пользователя
            user_preferences = self._analyze_user_preferences(user_history)
            
            # Получаем рекомендации на основе предпочтений
            recommendations = self._get_recommendations_by_preferences(user_preferences, limit)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении коллаборативных рекомендаций: {e}")
            return []
    
    def get_hybrid_recommendations(self, user_id: str, car_id: Optional[int] = None, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Получает гибридные рекомендации."""
        try:
            content_based = []
            collaborative = []
            
            # Контентные рекомендации
            if car_id:
                content_based = self.get_content_based_recommendations(car_id, limit)
            
            # Коллаборативные рекомендации
            collaborative = self.get_collaborative_recommendations(user_id, limit)
            
            # Объединяем и ранжируем
            all_recommendations = {}
            
            # Добавляем контентные рекомендации
            for rec in content_based:
                car_id = rec['id']
                all_recommendations[car_id] = {
                    'car': rec,
                    'content_score': rec.get('similarity_score', 0),
                    'collaborative_score': 0
                }
            
            # Добавляем коллаборативные рекомендации
            for rec in collaborative:
                car_id = rec['id']
                if car_id in all_recommendations:
                    all_recommendations[car_id]['collaborative_score'] = rec.get('score', 0)
                else:
                    all_recommendations[car_id] = {
                        'car': rec,
                        'content_score': 0,
                        'collaborative_score': rec.get('score', 0)
                    }
            
            # Ранжируем по комбинированному скору
            ranked_recommendations = []
            for car_id, data in all_recommendations.items():
                combined_score = (data['content_score'] * 0.6 + data['collaborative_score'] * 0.4)
                data['car']['combined_score'] = combined_score
                ranked_recommendations.append(data['car'])
            
            # Сортируем по комбинированному скору
            ranked_recommendations.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            
            return ranked_recommendations[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении гибридных рекомендаций: {e}")
            return []
    
    def _get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Получает историю пользователя."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем историю просмотров и взаимодействий
            cursor.execute("""
                SELECT car_id, interaction_type, timestamp
                FROM user_interactions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            """, (user_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'car_id': row[0],
                    'interaction_type': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении истории пользователя: {e}")
            return []
    
    def _analyze_user_preferences(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализирует предпочтения пользователя."""
        try:
            if not history:
                return {}
            
            # Получаем данные автомобилей из истории
            car_ids = [h['car_id'] for h in history]
            cars_data = self._load_cars_data()
            user_cars = cars_data[cars_data['id'].isin(car_ids)]
            
            if user_cars.empty:
                return {}
            
            # Анализируем предпочтения
            preferences = {
                'preferred_brands': user_cars['mark'].value_counts().to_dict(),
                'preferred_models': user_cars['model'].value_counts().to_dict(),
                'preferred_body_types': user_cars['body_type'].value_counts().to_dict(),
                'preferred_fuel_types': user_cars['fuel_type'].value_counts().to_dict(),
                'price_range': {
                    'min': float(user_cars['price'].min()),
                    'max': float(user_cars['price'].max()),
                    'avg': float(user_cars['price'].mean())
                },
                'year_range': {
                    'min': int(user_cars['manufacture_year'].min()),
                    'max': int(user_cars['manufacture_year'].max()),
                    'avg': int(user_cars['manufacture_year'].mean())
                }
            }
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе предпочтений: {e}")
            return {}
    
    def _get_recommendations_by_preferences(self, preferences: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Получает рекомендации на основе предпочтений."""
        try:
            cars_data = self._load_cars_data()
            
            if cars_data.empty or not preferences:
                return self._get_popular_cars(limit)
            
            # Создаем скор для каждого автомобиля
            scores = []
            for _, car in cars_data.iterrows():
                score = 0
                
                # Скор за марку (увеличиваем вес)
                if car['mark'] in preferences.get('preferred_brands', {}):
                    score += preferences['preferred_brands'][car['mark']] * 0.4
                
                # Скор за тип кузова
                if car['body_type'] in preferences.get('preferred_body_types', {}):
                    score += preferences['preferred_body_types'][car['body_type']] * 0.25
                
                # Скор за цену (улучшенный алгоритм)
                price_range = preferences.get('price_range', {})
                if price_range:
                    avg_price = price_range.get('avg', 0)
                    min_price = price_range.get('min', 0)
                    max_price = price_range.get('max', 0)
                    
                    if avg_price > 0:
                        # Нормализованная разница в цене
                        price_diff = abs(car['price'] - avg_price) / avg_price
                        score += (1 - price_diff) * 0.3
                        
                        # Бонус за попадание в диапазон
                        if min_price <= car['price'] <= max_price:
                            score += 0.2
                
                # Скор за год (улучшенный алгоритм)
                year_range = preferences.get('year_range', {})
                if year_range:
                    avg_year = year_range.get('avg', 0)
                    min_year = year_range.get('min', 0)
                    max_year = year_range.get('max', 0)
                    
                    if avg_year > 0:
                        # Нормализованная разница в годе
                        year_diff = abs(car['manufacture_year'] - avg_year) / avg_year
                        score += (1 - year_diff) * 0.25
                        
                        # Бонус за попадание в диапазон
                        if min_year <= car['manufacture_year'] <= max_year:
                            score += 0.15
                
                # Скор за пробег (для подержанных автомобилей)
                if 'mileage' in car and car['mileage'] > 0:
                    mileage_range = preferences.get('mileage_range', {})
                    if mileage_range:
                        avg_mileage = mileage_range.get('avg', 0)
                        if avg_mileage > 0:
                            mileage_diff = abs(car['mileage'] - avg_mileage) / avg_mileage
                            score += (1 - mileage_diff) * 0.1
                
                # Бонус за полное совпадение характеристик
                if (car['mark'] in preferences.get('preferred_brands', {}) and
                    car['body_type'] in preferences.get('preferred_body_types', {})):
                    score += 0.3
                
                # Бонус за разнообразие (не рекомендуем только одну марку)
                brand_diversity_bonus = 0.1
                if len(preferences.get('preferred_brands', {})) > 1:
                    score += brand_diversity_bonus
                
                scores.append({
                    'car': car.to_dict(),
                    'score': score
                })
            
            # Сортируем по скору
            scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Возвращаем топ рекомендации с минимальным скором
            recommendations = []
            for item in scores[:limit]:
                if item['score'] > 0.1:  # Минимальный порог качества
                    car_info = item['car']
                    car_info['score'] = item['score']
                    recommendations.append(car_info)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении рекомендаций по предпочтениям: {e}")
            return []
    
    def _get_popular_cars(self, limit: int) -> List[Dict[str, Any]]:
        """Получает популярные автомобили."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем популярные автомобили по просмотрам
            cursor.execute("""
                SELECT car_id, COUNT(*) as views
                FROM user_interactions 
                WHERE interaction_type = 'view'
                GROUP BY car_id 
                ORDER BY views DESC 
                LIMIT ?
            """, (limit,))
            
            popular_car_ids = [row[0] for row in cursor.fetchall()]
            
            if not popular_car_ids:
                conn.close()
                return []
            
            # Получаем данные автомобилей
            cars_data = self._load_cars_data()
            popular_cars = cars_data[cars_data['id'].isin(popular_car_ids)]
            
            recommendations = []
            for _, car in popular_cars.iterrows():
                car_info = car.to_dict()
                car_info['score'] = 0.5  # Базовый скор для популярных
                recommendations.append(car_info)
            
            conn.close()
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении популярных автомобилей: {e}")
            return []
    
    def update_user_interaction(self, user_id: str, car_id: int, interaction_type: str):
        """Обновляет взаимодействие пользователя."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу если не существует
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    car_id INTEGER NOT NULL,
                    interaction_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Добавляем взаимодействие
            cursor.execute("""
                INSERT INTO user_interactions (user_id, car_id, interaction_type)
                VALUES (?, ?, ?)
            """, (user_id, car_id, interaction_type))
            
            conn.commit()
            conn.close()
            
            # Очищаем кэш
            if user_id in self.user_preferences_cache:
                del self.user_preferences_cache[user_id]
                
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении взаимодействия: {e}")
    
    def retrain_models(self):
        """Переобучает модели."""
        self.logger.info("Начинаем переобучение моделей...")
        self._train_models()
        self.logger.info("Переобучение завершено") 
 
 