import sqlite3
import os
from contextlib import contextmanager
from brand_synonyms import BRAND_SYNONYMS, OTECHESTVENNYE, MODEL_SYNONYMS, CITY_SYNONYMS  # Добавляем CITY_SYNONYMS
from functools import lru_cache
from flask import g
import redis
import hashlib
import json
from typing import Optional, List, Dict, Any, Tuple
import inspect
import requests
import logging
import unicodedata
import threading
from html import escape
import re

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'cars.db')

# Глобальный лок для инициализации
init_lock = threading.Lock()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Гарантируем, что таблица api_logs существует
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time REAL,
                user_id TEXT,
                ip_address TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        logging.error(f'Ошибка создания api_logs: {e}')
    try:
        yield conn
    finally:
        conn.close()

def get_tables():
    with get_db() as conn:
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        return [t[0] for t in tables]

def get_table_columns(table_name):
    with get_db() as conn:
        cursor = conn.cursor()
        columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        return [{'name': col[1], 'type': col[2]} for col in columns]

# --- Безопасный log_query ---
def log_query(user, query_text, response):
    with get_db() as conn:
        cursor = conn.cursor()
        user = escape(user)
        query_text = escape(query_text)
        response = escape(response)
        try:
            cursor.execute('''CREATE TABLE IF NOT EXISTS chat_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                query_text TEXT,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            cursor.execute('''INSERT INTO chat_log (user, query_text, response) VALUES (?, ?, ?)''',
                           (user, query_text, response))
            conn.commit()
        except Exception as e:
            logging.error(f'Ошибка log_query: {e}')
    ensure_api_logs_table()

def get_chat_history(limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            query_text TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        rows = cursor.execute('''SELECT user, query_text, response, created_at FROM chat_log ORDER BY id DESC''', ()).fetchall()
        return rows

def analyze_database():
    with get_db() as conn:
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        analysis = {}
        for table in tables:
            table_name = table[0]
            columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
            row_count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            analysis[table_name] = {
                'columns': [{'name': col[1], 'type': col[2]} for col in columns],
                'row_count': row_count
            }
        return analysis

# --- Транзакции для изменений ---
def safe_db_write(query, params=None):
    try:
        with get_db() as conn:
            conn.execute('BEGIN')
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        logging.error(f'Ошибка транзакции: {e}')
        return False

# --- Валидация данных (расширенная) ---
def validate_car_data(car):
    year = car.get('manufacture_year')
    price = car.get('price')
    if not isinstance(year, int) or not (1950 <= year <= 2100):
        return False
    if not isinstance(price, (int, float)) or not (100_000 <= price <= 100_000_000):
        return False
    for field in ['mark', 'model', 'fuel_type', 'body_type', 'city']:
        if not isinstance(car.get(field), str) or len(car[field]) > 100:
            return False
    return True

# --- Нормализация бренда и модели ---
def get_first_deep(val):
    if isinstance(val, (list, tuple)):
        return get_first_deep(val[0]) if val else None
    return val

def normalize_brand(brand):
    brand = get_first_deep(brand)
    if not brand:
        return None
    b = str(brand).strip().lower()
    return BRAND_SYNONYMS.get(b, str(brand).title())

def is_otechestvenny(brand):
    return normalize_brand(brand) in OTECHESTVENNYE

def is_modern(year):
    return year >= 2010

# --- Обёртка для загрузки с валидацией и нормализацией ---
def insert_car(cursor, table, car):
    # car: dict
    if not validate_car_data(car):
        return False
    car['mark'] = normalize_brand(car.get('mark'))
    cursor.execute(f'''INSERT INTO {table} (mark, model, manufacture_year, price, fuel_type, power, gear_box_type, body_type, city, availability) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            car.get('mark'), car.get('model'), car.get('manufacture_year'), car.get('price'),
            car.get('fuel_type'), car.get('power'), car.get('gear_box_type'), car.get('body_type'),
            car.get('city'), car.get('availability', 1)
        ))
    return True

def fill_test_data():
    with get_db() as conn:
        cursor = conn.cursor()
        # Не добавляем тестовые данные
        pass 

# Добавляем недостающую функцию close_db для совместимости с app.py
def close_db(exception=None):
    """Закрывает соединение с БД (для совместимости с Flask)"""
    pass

# Добавляем кэшированную функцию получения всех брендов
@lru_cache(maxsize=1)
def get_all_brands_cached():
    """Получает все уникальные бренды из БД с кэшированием"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT mark FROM car ORDER BY mark")
            brands_car = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT mark FROM used_car ORDER BY mark")
            brands_used = [row[0] for row in cursor.fetchall()]
            return sorted(set(brands_car + brands_used))
    except Exception as e:
        print(f"Ошибка получения брендов: {e}")
        return []

# Добавляем кэшированную функцию получения всех моделей
@lru_cache(maxsize=1)
def get_all_models_cached():
    """Получает все уникальные модели из БД с кэшированием"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT model FROM car ORDER BY model")
            models_car = [row[0] for row in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT model FROM used_car ORDER BY model")
            models_used = [row[0] for row in cursor.fetchall()]
            return sorted(set(models_car + models_used))
    except Exception as e:
        print(f"Ошибка получения моделей: {e}")
        return []

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6380, decode_responses=True)

    def get_simple_cache(self, query: str) -> Optional[str]:
        key = f"simple:{hashlib.md5(query.encode()).hexdigest()}"
        value = self.redis.get(key)
        if isinstance(value, bytes):
            return value.decode()
        if isinstance(value, str):
            return value
        return None

    def set_simple_cache(self, query: str, response: str, ttl=3600):
        key = f"simple:{hashlib.md5(query.encode()).hexdigest()}"
        self.redis.setex(key, ttl, response)

    def get_context(self, user_id: str) -> dict:
        key = f"context:{user_id}"
        data = self.redis.get(key)
        if isinstance(data, bytes):
            data = data.decode()
        if data is None or data == '':
            return {}
        if not isinstance(data, str):
            return {}
        return json.loads(data)

    def save_context(self, user_id: str, context: dict, ttl=1800):
        key = f"context:{user_id}"
        self.redis.setex(key, ttl, json.dumps(context))

    def clear_context(self, user_id: str):
        key = f"context:{user_id}"
        self.redis.delete(key)

def get_car_options(brand: Optional[str] = None, model: Optional[str] = None, used: bool = False) -> list:
    """
    Возвращает список опций (характеристик) для заданной марки и модели.
    Если не указаны brand/model, возвращает все доступные варианты.
    """
    table = 'used_car' if used else 'car'
    query = f"SELECT * FROM {table} WHERE 1=1"
    params = []
    if brand:
        query += " AND mark = ?"
        params.append(brand)
    if model:
        query += " AND model = ?"
        params.append(model)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

def get_full_car_info(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    car_id: Optional[int] = None,
    used: bool = False
) -> Optional[dict]:
    table = 'used_car' if used else 'car'
    pic_table = 'used_car_picture' if used else 'picture'
    with get_db() as conn:
        cursor = conn.cursor()
        if car_id is not None:
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (car_id,))
        elif brand is not None and model is not None:
            cursor.execute(f"SELECT * FROM {table} WHERE mark = ? AND model = ?", (brand, model))
        else:
            return None
        car_row = cursor.fetchone()
        if not car_row:
            return None
        columns = [desc[0] for desc in cursor.description]
        car_info = dict(zip(columns, car_row))
        cursor.execute("SELECT code, description FROM option WHERE car_id = ?", (car_info['id'],))
        options = cursor.fetchall()
        car_info['options'] = [dict(zip(['code', 'description'], row)) for row in options]
        pic_id_field = 'used_car_id' if used else 'car_id'
        cursor.execute(f"SELECT url, type FROM {pic_table} WHERE {pic_id_field} = ?", (car_info['id'],))
        pics = cursor.fetchall()
        car_info['pictures'] = [dict(zip(['url', 'type'], row)) for row in pics]
        return car_info

def get_all_brands(used: bool = False) -> list:
    table = 'used_car' if used else 'car'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT mark FROM {table} ORDER BY mark")
        return [row[0] for row in cursor.fetchall()]

def get_all_models(used: bool = False) -> list:
    table = 'used_car' if used else 'car'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT model FROM {table} ORDER BY model")
        return [row[0] for row in cursor.fetchall()]

def get_all_cities(used: bool = False) -> list:
    """Получает все уникальные города из базы данных"""
    table = 'used_car' if used else 'car'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT city FROM {table} WHERE city IS NOT NULL AND city != '' ORDER BY city")
        return [row[0] for row in cursor.fetchall()]

@lru_cache(maxsize=1)
def get_all_cities_cached():
    """Получает все уникальные города из БД с кэшированием"""
    try:
        cities_car = get_all_cities(used=False)
        cities_used = get_all_cities(used=True)
        return sorted(set(cities_car + cities_used))
    except Exception as e:
        print(f"Ошибка получения городов: {e}")
        return []

def get_model_keywords(model):
    """Возвращает список ключевых подстрок для поиска по модели (универсально для BMW, Audi, Mercedes и др.)"""
    if not model:
        return []
    m = str(model).lower().replace(' ', '')
    keywords = set()
    keywords.add(m)
    # Точные соответствия для BMW X-серии
    if m == 'x5':
        keywords.update(['x5', 'х5', 'x 5', 'x-5'])
        # Связываем X5 с 5 серией и всеми её моделями
        keywords.update(['5серии', '5серия', '5series', '5er', '520d', '530d', '530li', '520i', '520', '530'])
    elif m == 'x3':
        keywords.update(['x3', 'х3', 'x 3', 'x-3'])
        # Связываем X3 с 3 серией и всеми её моделями
        keywords.update(['3серии', '3серия', '3series', '3er', '320d', '330d', '320i', '330i', '320', '330'])
    elif m == 'x6':
        keywords.update(['x6', 'х6', 'x 6', 'x-6'])
        keywords.update(['6серии', '6серия', '6series', '6er'])
    elif m == 'x7':
        keywords.update(['x7', 'х7', 'x 7', 'x-7'])
        keywords.update(['7серии', '7серия', '7series', '7er'])
    elif m == 'x4':
        keywords.update(['x4', 'х4', 'x 4', 'x-4'])
        keywords.update(['4серии', '4серия', '4series', '4er'])
    elif m == 'x1':
        keywords.update(['x1', 'х1', 'x 1', 'x-1'])
        keywords.update(['1серии', '1серия', '1series', '1er'])
    elif m == 'x2':
        keywords.update(['x2', 'х2', 'x 2', 'x-2'])
        keywords.update(['2серии', '2серия', '2series', '2er'])
    elif m in ['5серии', '5серия', '5series', '5er']:
        keywords.update(['x5', 'х5', 'x 5', 'x-5', '520d', '530d', '530li', '520i', '520', '530'])
    elif m in ['3серии', '3серия', '3series', '3er']:
        keywords.update(['x3', 'х3', 'x 3', 'x-3', '320d', '330d', '320i', '330i', '320', '330'])
    elif m in ['6серии', '6серия', '6series', '6er']:
        keywords.update(['x6', 'х6', 'x 6', 'x-6'])
    elif m in ['7серии', '7серия', '7series', '7er']:
        keywords.update(['x7', 'х7', 'x 7', 'x-7'])
    elif m in ['4серии', '4серия', '4series', '4er']:
        keywords.update(['x4', 'х4', 'x 4', 'x-4'])
    elif m in ['1серии', '1серия', '1series', '1er']:
        keywords.update(['x1', 'х1', 'x 1', 'x-1'])
    elif m in ['2серии', '2серия', '2series', '2er']:
        keywords.update(['x2', 'х2', 'x 2', 'x-2'])
    elif m in ['520d', '530d', '530li', '520i', '520', '530']:
        keywords.update(['x5', 'х5', 'x 5', 'x-5', '5 серии', '5 серия', '5 series'])
    elif m in ['320d', '330d', '320i', '330i', '320', '330']:
        keywords.update(['x3', 'х3', 'x 3', 'x-3', '3 серии', '3 серия', '3 series'])
    return list(keywords)

def get_brand_keywords(brand):
    """Возвращает список ключевых подстрок для поиска по бренду (например, BMW, B M W, БМВ)"""
    if not brand:
        return []
    b = str(brand).lower().replace(' ', '')
    keywords = set()
    keywords.add(b)
    if b == 'bmw':
        keywords.update(['bmw', 'бмв', 'b m w'])
    if b == 'audi':
        keywords.update(['audi', 'ауди'])
    if b == 'mercedes' or b == 'mercedes-benz':
        keywords.update(['mercedes', 'mercedes-benz', 'мерседес', 'мерседес-бенц'])
    # Можно расширить для других брендов
    return list(keywords)

def filter_cars(brand=None, model=None, year=None, price_min=None, price_max=None, city=None, body_type=None, used=False) -> list:
    table = 'used_car' if used else 'car'
    query = f"SELECT * FROM {table} WHERE 1=1"
    params = []
    # --- Фильтрация по бренду: LIKE + поддержка синонимов ---
    if brand:
        brand_keywords = get_brand_keywords(brand)
        if brand_keywords:
            brand_filters = []
            for kw in brand_keywords:
                brand_filters.append("LOWER(REPLACE(mark, ' ', '')) LIKE ?")
                params.append(f"%{kw}%")
            query += " AND (" + " OR ".join(brand_filters) + ")"
        else:
            query += " AND LOWER(REPLACE(mark, ' ', '')) LIKE ?"
            params.append(f"%{str(brand).replace(' ', '').lower()}%")
    # --- Фильтрация по модели: ищем по всем ключевым словам ---
    if model:
        keywords = get_model_keywords(model)
        if keywords:
            model_filters = []
            for kw in keywords:
                model_filters.append("LOWER(REPLACE(model, ' ', '')) LIKE ?")
                params.append(f"%{kw}%")
            # Добавляем NOT LIKE для X5/X3
            m = str(model).lower().replace(' ', '')
            if m == 'x5':
                model_filters.append("LOWER(REPLACE(model, ' ', '')) NOT LIKE ?")
                params.append("%x3%")
            elif m == 'x3':
                model_filters.append("LOWER(REPLACE(model, ' ', '')) NOT LIKE ?")
                params.append("%x5%")
            query += " AND (" + " OR ".join(model_filters) + ")"
        else:
            query += " AND LOWER(REPLACE(model, ' ', '')) LIKE ?"
            params.append(f"%{str(model).replace(' ', '').lower()}%")
    if year:
        query += " AND manufacture_year = ?"
        params.append(year)
    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)
    if city:
        query += " AND city = ?"
        params.append(city)
    if body_type:
        query += " AND body_type = ?"
        params.append(body_type)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cars = [dict(zip(columns, row)) for row in rows]
    # --- Fallback: если не найдено по модели, возвращаем все машины бренда ---
    if model and not cars and brand:
        brand_keywords = get_brand_keywords(brand)
        if brand_keywords:
            fallback_query = f"SELECT * FROM {table} WHERE " + " OR ".join(["LOWER(REPLACE(mark, ' ', '')) LIKE ?" for _ in brand_keywords])
            fallback_params = [f"%{kw}%" for kw in brand_keywords]
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(fallback_query, fallback_params)
                rows = cursor.fetchall()
                cars = [dict(zip(columns, row)) for row in rows]
    # --- Пост-фильтр для X5/X3 ---
    if model:
        m = str(model).lower().replace(' ', '').replace('-', '')
        if m in ['x5', 'х5', 'x-5']:
            cars = [car for car in cars if str(car.get('model', '')).lower().replace(' ', '').replace('-', '').startswith('x5')]
        elif m in ['x3', 'х3', 'x-3']:
            cars = [car for car in cars if str(car.get('model', '')).lower().replace(' ', '').replace('-', '').startswith('x3')]
    # --- Универсальный пост-фильтр для X-серии и "серий" ---
    if model:
        m = str(model).lower().replace(' ', '').replace('-', '')
        import re
        x_match = re.match(r'x(\d)', m)
        if x_match:
            n = x_match.group(1)
            def is_xn_or_n_series(car_model):
                cm = str(car_model).lower().replace(' ', '').replace('-', '')
                if cm.startswith(f'x{n}'):
                    return True
                for s in [f'{n}серии', f'{n}серия', f'{n}series']:
                    if s in cm:
                        return True
                return False
            cars = [car for car in cars if is_xn_or_n_series(car.get('model', ''))]
    return cars

def compare_cars(car_list: list) -> list:
    """
    car_list: список словарей {'brand': ..., 'model': ..., 'used': ...}
    Возвращает список dict с полной инфой для сравнения (через smart_filter_cars)
    """
    results = []
    for car in car_list:
        brand = car.get('brand')
        model = car.get('model')
        used = car.get('used', None)
        cars, _ = smart_filter_cars(brand=brand, model=model, used=used)
        if cars:
            results.append(cars[0])
    return results

def get_dealer_centers_for_car(brand: str, model: str, city: Optional[str] = None) -> list:
    """
    Получает список дилерских центров для конкретного автомобиля
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Сначала ищем в таблице car/used_car
        query = """
            SELECT DISTINCT dealer_center, city 
            FROM car 
            WHERE mark = ? AND model = ? AND dealer_center IS NOT NULL AND dealer_center != 'Не указан'
            UNION
            SELECT DISTINCT dealer_center, city 
            FROM used_car 
            WHERE mark = ? AND model = ? AND dealer_center IS NOT NULL AND dealer_center != 'Не указан'
        """
        params = [brand, model, brand, model]
        
        if city:
            query += " AND city = ?"
            params.extend([city, city])
            
        cursor.execute(query, params)
        car_dealers = cursor.fetchall()
        
        # Затем ищем в таблице dealer_centers
        dealer_query = """
            SELECT name, address, phone, website, city, brands, working_hours
            FROM dealer_centers 
            WHERE brands LIKE ? OR brands LIKE ?
        """
        dealer_params = [f'%"{brand}"%', f'%{brand}%']
        
        if city:
            dealer_query += " AND city = ?"
            dealer_params.append(city)
            
        cursor.execute(dealer_query, dealer_params)
        dealer_centers = cursor.fetchall()
        
        result = []
        
        # Добавляем ДЦ из таблицы car/used_car
        for dealer_center, dealer_city in car_dealers:
            result.append({
                'name': dealer_center,
                'city': dealer_city,
                'source': 'car_database'
            })
        
        # Добавляем ДЦ из таблицы dealer_centers
        for name, address, phone, website, dealer_city, brands, working_hours in dealer_centers:
            result.append({
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'city': dealer_city,
                'brands': brands,
                'working_hours': working_hours,
                'source': 'dealer_centers_table'
            })
        
        return result

def get_dealer_center_info(dealer_name: str) -> Optional[Dict[str, Any]]:
    """
    Получает подробную информацию о дилерском центре
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Ищем в таблице dealer_centers
        cursor.execute("""
            SELECT name, address, phone, website, city, brands, working_hours
            FROM dealer_centers 
            WHERE name = ?
        """, (dealer_name,))
        
        result = cursor.fetchone()
        if result:
            name, address, phone, website, city, brands, working_hours = result
            return {
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'city': city,
                'brands': brands,
                'working_hours': working_hours,
                'source': 'dealer_centers_table'
            }
        
        # Если не найдено в dealer_centers, ищем в car/used_car
        cursor.execute("""
            SELECT DISTINCT dealer_center, city 
            FROM car 
            WHERE dealer_center = ?
            UNION
            SELECT DISTINCT dealer_center, city 
            FROM used_car 
            WHERE dealer_center = ?
        """, (dealer_name, dealer_name))
        
        result = cursor.fetchone()
        if result:
            dealer_center, city = result
            return {
                'name': dealer_center,
                'city': city,
                'source': 'car_database'
            }
        
        return None

def add_dealer_center(name: str, address: Optional[str] = None, phone: Optional[str] = None, 
                     website: Optional[str] = None, city: Optional[str] = None, 
                     brands: Optional[List[str]] = None, working_hours: Optional[str] = None) -> bool:
    """
    Добавляет новый дилерский центр
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            brands_json = json.dumps(brands) if brands is not None else None
            
            cursor.execute("""
                INSERT INTO dealer_centers (name, address, phone, website, city, brands, working_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, address, phone, website, city, brands_json, working_hours))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при добавлении дилерского центра: {e}")
        return False

def get_all_dealer_centers():
    import sqlite3
    conn = sqlite3.connect('instance/cars.db')
    cursor = conn.cursor()
    dealers = set()
    # Из car
    cursor.execute('SELECT DISTINCT dealer_center, city FROM car WHERE dealer_center IS NOT NULL')
    for name, city in cursor.fetchall():
        if name:
            dealers.add((name, city))
    # Из used_car
    try:
        cursor.execute('SELECT DISTINCT dealer_center, city FROM used_car WHERE dealer_center IS NOT NULL')
        for name, city in cursor.fetchall():
            if name:
                dealers.add((name, city))
    except Exception:
        pass
    conn.close()
    return [{'name': name, 'city': city} for name, city in dealers]

def add_column_if_not_exists(cursor, table, column, coltype):
    cursor.execute(f"PRAGMA table_info({table})")
    if column not in [row[1] for row in cursor.fetchall()]:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

def add_lat_lon_to_dealer_centers():
    """Добавляет поля latitude и longitude в таблицу dealer_centers, если их нет"""
    with get_db() as conn:
        cursor = conn.cursor()
        add_column_if_not_exists(cursor, 'dealer_centers', 'latitude', 'REAL')
        add_column_if_not_exists(cursor, 'dealer_centers', 'longitude', 'REAL')
        conn.commit()

YANDEX_API_KEY = 'd839c21f-c590-43dc-a18b-f2e5c62baf8b'

def geocode_address(address: str) -> tuple[float, float] | None:
    """Получает координаты по адресу через Яндекс.Карты"""
    url = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_API_KEY}&geocode={address}&format=json'
    resp = requests.get(url)
    if resp.status_code == 200:
        try:
            pos = resp.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            lon, lat = map(float, pos.split())
            return lat, lon
        except Exception:
            return None
    return None

def update_all_dealer_coords():
    """Обновляет координаты всех ДЦ по адресу"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, address FROM dealer_centers')
        for row in cursor.fetchall():
            dc_id, address = row
            coords = geocode_address(address)
            if coords:
                lat, lon = coords
                cursor.execute('UPDATE dealer_centers SET latitude=?, longitude=? WHERE id=?', (lat, lon, dc_id))
        conn.commit()

def get_dealer_centers_with_coords() -> list:
    """Возвращает все ДЦ с координатами"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name, address, latitude, longitude, phone, website FROM dealer_centers')
        return [dict(zip(['name','address','latitude','longitude','phone','website'], row)) for row in cursor.fetchall()] 

def ensure_dealer_centers_filled():
    """Заполняет таблицу dealer_centers адресами и контактами из предоставленного списка, если их нет."""
    dealers = [
        # Воронеж
        {"name": "ААА Моторс", "address": "Воронеж, ул. Остужева, 68", "city": "Воронеж", "brands": "", "phone": "", "website": "", "working_hours": ""},
        # Краснодар
        {"name": "ААА Моторс", "address": "Краснодар, ул. Аэропортовская, 4/1", "city": "Краснодар", "brands": "", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер DongFeng", "address": "Краснодар, ул. Аэропортовская, 4а", "city": "Краснодар", "brands": "DongFeng", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс", "address": "Краснодар, ул. Дзержинского, 231/2", "city": "Краснодар", "brands": "", "phone": "", "website": "", "working_hours": ""},
        # Ростов-на-Дону
        {"name": "ААА Моторс, Mazda", "address": "Ростов-на-Дону, ул. Текучёва, 159А", "city": "Ростов-на-Дону", "brands": "Mazda", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Changan Центр", "address": "Ростов-на-Дону, ул. Текучёва, 352Б", "city": "Ростов-на-Дону", "brands": "Changan", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Solaris", "address": "Ростов-на-Дону, ул. Текучёва, 352Б", "city": "Ростов-на-Дону", "brands": "Solaris", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Hyundai", "address": "Ростов-на-Дону, ул. Текучёва, 352Б", "city": "Ростов-на-Дону", "brands": "Hyundai", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Москвич", "address": "Ростов-на-Дону, ул. Текучёва, 352А", "city": "Ростов-на-Дону", "brands": "Москвич", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Belgee", "address": "Ростов-на-Дону, ул. Текучёва, 352А", "city": "Ростов-на-Дону", "brands": "Belgee", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Chery", "address": "Ростов-на-Дону, Театральный просп., 60Б", "city": "Ростов-на-Дону", "brands": "Chery", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Skoda", "address": "Ростов-на-Дону, Театральный просп., 60Б", "city": "Ростов-на-Дону", "brands": "Skoda", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Geely", "address": "Ростов-на-Дону, ул. Текучёва, 350А", "city": "Ростов-на-Дону", "brands": "Geely", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Renault", "address": "Ростов-на-Дону, ул. Текучёва, 352А", "city": "Ростов-на-Дону", "brands": "Renault", "phone": "", "website": "", "working_hours": ""},
        {"name": "Чанган центр, ААА Моторс", "address": "Ростов-на-Дону, ул. Текучёва, 352Б", "city": "Ростов-на-Дону", "brands": "Changan", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Seres", "address": "Ростов-на-Дону, ул. Текучёва, 159А", "city": "Ростов-на-Дону", "brands": "Seres", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс, Volkswagen", "address": "Ростов-на-Дону, ул. Доватора, 259", "city": "Ростов-на-Дону", "brands": "Volkswagen", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Jaguar, Land Rover", "address": "Ростов-на-Дону, ул. Текучёва, 350а", "city": "Ростов-на-Дону", "brands": "Jaguar,Land Rover", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Geely", "address": "Ростов-на-Дону, ул. Текучёва, 350а", "city": "Ростов-на-Дону", "brands": "Geely", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Tank", "address": "Ростов-на-Дону, пр-т Театральный, 60е", "city": "Ростов-на-Дону", "brands": "Tank", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Haval", "address": "Ростов-на-Дону, пр-т Театральный, 60е", "city": "Ростов-на-Дону", "brands": "Haval", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Volkswagen", "address": "Ростов-на-Дону, ул. Доватора, 259", "city": "Ростов-на-Дону", "brands": "Volkswagen", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Mazda", "address": "Ростов-на-Дону, ул. Текучёва, 159а", "city": "Ростов-на-Дону", "brands": "Mazda", "phone": "", "website": "", "working_hours": ""},
        {"name": "ААА Моторс — дилер Renault", "address": "Ростов-на-Дону, ул. Текучёва, 352а", "city": "Ростов-на-Дону", "brands": "Renault", "phone": "", "website": "", "working_hours": ""},
    ]
    with get_db() as conn:
        cursor = conn.cursor()
        # Добавить недостающие поля
        try:
            cursor.execute('ALTER TABLE dealer_centers ADD COLUMN brands TEXT')
        except Exception: pass
        try:
            cursor.execute('ALTER TABLE dealer_centers ADD COLUMN city TEXT')
        except Exception: pass
        try:
            cursor.execute('ALTER TABLE dealer_centers ADD COLUMN website TEXT')
        except Exception: pass
        try:
            cursor.execute('ALTER TABLE dealer_centers ADD COLUMN phone TEXT')
        except Exception: pass
        try:
            cursor.execute('ALTER TABLE dealer_centers ADD COLUMN working_hours TEXT')
        except Exception: pass
        # Заполнить, если пусто
        cursor.execute('SELECT COUNT(*) FROM dealer_centers')
        if cursor.fetchone()[0] == 0:
            for d in dealers:
                cursor.execute('INSERT INTO dealer_centers (name, address, city, brands, website, phone, working_hours) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (d['name'], d['address'], d['city'], d['brands'], d['website'], d['phone'], d['working_hours']))
        conn.commit() 

def create_dealer_centers_table_if_not_exists():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dealer_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                city TEXT,
                brands TEXT,
                website TEXT,
                phone TEXT,
                working_hours TEXT,
                latitude REAL,
                longitude REAL
            )
        ''')
        conn.commit() 
        return [] 

def map_dealer_center_codes():
    """
    Сопоставляет коды dealer_center из car/used_car с дилерскими центрами из dealer_centers.
    Возвращает dict: код → {name, address, city, ...}
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # Получаем все дилерские центры
        cursor.execute('SELECT id, name, address, city, brands FROM dealer_centers')
        all_dealers = cursor.fetchall()
        # Получаем все уникальные dealer_center из car и used_car
        codes = set()
        for table in ['car', 'used_car']:
            try:
                cursor.execute(f'SELECT DISTINCT dealer_center FROM {table}')
                for row in cursor.fetchall():
                    if row[0]:
                        codes.add(row[0].strip())
            except Exception:
                pass
        mapping = {}
        for code in codes:
            # Пробуем сопоставить по бренду, городу, части названия
            found = None
            for d in all_dealers:
                did, name, address, city, brands = d
                if code.lower() in (name or '').lower() or code.lower() in (brands or '').lower():
                    found = {'id': did, 'name': name, 'address': address, 'city': city, 'brands': brands}
                    break
            mapping[code] = found or {}
        return mapping

def get_dealer_center_info_by_code(code: str):
    """
    Возвращает полную информацию о дилерском центре по коду dealer_center (например, AUDI_KRD).
    Если не найдено — возвращает None.
    """
    mapping = map_dealer_center_codes()
    return mapping.get(code) or None 

# --- Безопасный execute_query ---
def execute_query(query: str, params: Optional[List[Any]] = None) -> List[Tuple]:
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Ограничение SELECT
            if query.strip().upper().startswith('SELECT') and 'LIMIT' not in query.upper():
                query += ' LIMIT 1000'
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Query failed: {query} | Error: {e}")
        return []
    except Exception as e:
        logging.exception("Unexpected error in execute_query")
        return []

@lru_cache(maxsize=1)
def get_all_unique_values():
    """Кэширует уникальные значения по ключевым полям для car и used_car"""
    import sqlite3
    DB_PATH = 'instance/cars.db'
    fields = ['mark', 'model', 'fuel_type', 'body_type', 'gear_box_type', 'driving_gear_type']
    uniques = {f: set() for f in fields}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table in ['car', 'used_car']:
        for f in fields:
            try:
                cursor.execute(f'SELECT DISTINCT {f} FROM {table}')
                for row in cursor.fetchall():
                    v = row[0]
                    if v is not None and v != '':
                        uniques[f].add(str(v).strip())
            except Exception:
                pass
    conn.close()
    return uniques

@lru_cache(maxsize=1)
def get_all_unique_values_lower():
    import sqlite3
    DB_PATH = 'instance/cars.db'
    fields = ['mark', 'model', 'fuel_type', 'body_type', 'gear_box_type', 'driving_gear_type']
    uniques = {f: set() for f in fields}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table in ['car', 'used_car']:
        for f in fields:
            try:
                cursor.execute(f'SELECT DISTINCT {f} FROM {table}')
                for row in cursor.fetchall():
                    v = row[0]
                    if v is not None and v != '':
                        uniques[f].add(str(v).strip().lower())
            except Exception:
                pass
    conn.close()
    return uniques

def normalize_str(val):
    if not val:
        return ''
    return unicodedata.normalize('NFKC', str(val)).strip().lower()

# Импортируем улучшенный словарь синонимов брендов
from brand_synonyms import BRAND_SYNONYMS

def is_brand_match(brand, target):
    brand = normalize_str(brand)
    target = normalize_str(target)
    for canon, variants in BRAND_SYNONYMS.items():
        if brand in variants and (target in variants or canon in target):
            return True
    return brand == target

# --- Маппинг значений фильтров с английских на русские ---
FILTER_VALUE_MAP = {
    'fuel_type': {
        'petrol': 'бензин',
        'gasoline': 'бензин',
        'diesel': 'дизель',
        'hybrid': 'гибрид',
        'электро': 'электрический',
        'electric': 'электрический',
        'электрический': 'электрический',
        'бензин': 'бензин',
        'дизель': 'дизель',
        'гибрид': 'гибрид',
    },
    'body_type': {
        'suv': 'внедорожник',
        'crossover': 'кроссовер',
        'coupe-suv': 'купе-кроссовер',
        'liftback': 'лифтбэк',
        'minivan': 'минивэн',
        'pickup': 'пикап',
        'sedan': 'седан',
        'wagon': 'универсал',
        'hatchback': 'хетчбэк',
        'van': 'фургон',
        'microbus': 'микроавтобус',
        'внедорожник': 'внедорожник',
        'седан': 'седан',
        'универсал': 'универсал',
        'купе': 'купе',
        'минивэн': 'минивэн',
        'фургон': 'фургон',
        'микроавтобус': 'микроавтобус',
        'купе-кроссовер': 'купе-кроссовер',
        'кроссовер': 'кроссовер',
        'лифтбэк': 'лифтбэк',
        'пикап': 'пикап',
        'хэтчбек': 'хетчбэк',
        'хетчбэк': 'хетчбэк',
    },
    'transmission': {
        'automatic': 'автомат',
        'manual': 'механика',
        'автомат': 'автомат',
        'механика': 'механика',
    },
    'drive_type': {
        'awd': 'полный',
        '4wd': 'полный',
        'fwd': 'передний',
        'rwd': 'задний',
        'полный': 'полный',
        'передний': 'передний',
        'задний': 'задний',
    }
}

def map_filter_value(field, value):
    value = get_first_deep(value)
    if not value:
        return value
    v = str(value).strip().lower()
    return FILTER_VALUE_MAP.get(field, {}).get(v, value)

def _search_cars_with_filters(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    body_type: Optional[str] = None,
    drive_type: Optional[str] = None,
    state: Optional[str] = None,
    sort_by: str = "price",
    sort_order: str = "asc",
    option_code: Optional[str] = None,
    option_description: Optional[str] = None,
    city: Optional[str] = None,
    color: Optional[str] = None,
    seats: Optional[int] = None,
    limit: Optional[int] = None,
    # Новые параметры для расширенных характеристик
    power_from: Optional[int] = None,
    power_to: Optional[int] = None,
    power_exact: Optional[int] = None,
    engine_vol_from: Optional[float] = None,
    engine_vol_to: Optional[float] = None,
    engine_vol_exact: Optional[float] = None,
    mileage_from: Optional[int] = None,
    mileage_to: Optional[int] = None,
    mileage_exact: Optional[int] = None,
    owners_count: Optional[int] = None,
    owners_from: Optional[int] = None,
    owners_to: Optional[int] = None,
    steering_wheel: Optional[str] = None,
    accident_history: Optional[str] = None,
    # Параметры производительности
    acceleration_from: Optional[float] = None,
    acceleration_to: Optional[float] = None,
    fuel_efficiency: Optional[str] = None
) -> list:
    print(f"[search_all_cars] Входящие параметры: brand={brand}, model={model}, year_from={year_from}, year_to={year_to}, price_from={price_from}, price_to={price_to}, fuel_type={fuel_type}, transmission={transmission}, body_type={body_type}, drive_type={drive_type}, state={state}, sort_by={sort_by}, sort_order={sort_order}, option_code={option_code}, option_description={option_description}, city={city}")
    import logging
    columns = [
        "id", "title", "doc_num", "mark", "model", "vin", "color", "price", "city", "manufacture_year", "body_type", "gear_box_type", "driving_gear_type", "engine_vol", "power", "fuel_type", "dealer_center", "seats"
    ]
    uniques = get_all_unique_values_lower()
    filters_car = ["1=1"]
    params_car = []
    filters_used = ["1=1"]
    params_used = []
    only_used = False
    # --- Гибкий поиск по бренду с синонимами и падежными вариациями ---
    if brand:
        # Используем улучшенную систему нормализации
        from brand_synonyms import normalize_brand_extended
        normalized_brand = normalize_brand_extended(brand)
        
        # Если улучшенная система нашла бренд, используем его
        if normalized_brand and normalized_brand != brand.title():
            b_norm = normalize_str(normalized_brand)
        else:
            b_norm = normalize_str(brand)
        
        brand_syns = set([b_norm])
        
        # Добавляем все варианты из улучшенного словаря
        for canon, variants in BRAND_SYNONYMS.items():
            if b_norm in variants:
                brand_syns.update(variants)
                brand_syns.add(canon)
        
        # Также добавляем оригинальный бренд и его нормализованную версию
        brand_syns.add(normalize_str(brand))
        if normalized_brand:
            brand_syns.add(normalize_str(normalized_brand))
        
        brand_filters = []
        for syn in brand_syns:
            # Используем простой LIKE без LOWER() для поддержки кириллицы
            # Добавляем варианты с разным регистром
            brand_filters.append("REPLACE(mark, ' ', '') LIKE ?")
            params_car.append(f"%{syn}%")
            params_used.append(f"%{syn}%")
            # Также добавляем поиск с большой буквы
            brand_filters.append("REPLACE(mark, ' ', '') LIKE ?")
            params_car.append(f"%{syn.capitalize()}%")
            params_used.append(f"%{syn.capitalize()}%")
        filters_car.append("(" + " OR ".join(brand_filters) + ")")
        filters_used.append("(" + " OR ".join(brand_filters) + ")")
    # --- Гибкий поиск по модели с синонимами и подстроками ---
    if model:
        model_values = model if isinstance(model, list) else [model]
        all_model_syns = set()
        for m in model_values:
            m_norm = normalize_str(m)
            model_syns = set([m_norm])
            # Добавляем синонимы из словаря MODEL_SYNONYMS
            if m_norm in MODEL_SYNONYMS:
                canonical_model = MODEL_SYNONYMS[m_norm]
                model_syns.add(canonical_model)
                for syn, canon in MODEL_SYNONYMS.items():
                    if canon == canonical_model:
                        model_syns.add(syn)
            # Точная обработка для BMW X-серии
            if m_norm == 'x5':
                model_syns.update(['X5', 'х5', 'x 5', 'x-5', '5 серии', '5 серия', '5 series', '520d', '530d', '530li', '520i', '520', '530'])
            elif m_norm == 'x3':
                model_syns.update(['X3', 'х3', 'x 3', 'x-3', '3 серии', '3 серия', '3 series', '320d', '330d', '320i', '330i', '320', '330'])
            elif m_norm == 'x6':
                model_syns.update(['X6', 'х6', 'x 6', 'x-6', '6 серии', '6 серия', '6 series'])
            elif m_norm == 'x7':
                model_syns.update(['X7', 'х7', 'x 7', 'x-7', '7 серии', '7 серия', '7 series'])
            elif m_norm == 'x4':
                model_syns.update(['X4', 'х4', 'x 4', 'x-4', '4 серии', '4 серия', '4 series'])
            elif m_norm == 'x1':
                model_syns.update(['X1', 'х1', 'x 1', 'x-1', '1 серии', '1 серия', '1 series'])
            elif m_norm == 'x2':
                model_syns.update(['X2', 'х2', 'x 2', 'x-2', '2 серии', '2 серия', '2 series'])
            elif m_norm in ['5 серии', '5 серия', '5 series']:
                model_syns.update(['X5', 'х5', 'x 5', 'x-5', '520d', '530d', '530li', '520i', '520', '530'])
            elif m_norm in ['3 серии', '3 серия', '3 series']:
                model_syns.update(['X3', 'х3', 'x 3', 'x-3', '320d', '330d', '320i', '330i', '320', '330'])
            elif m_norm in ['6 серии', '6 серия', '6 series']:
                model_syns.update(['X6', 'х6', 'x 6', 'x-6'])
            elif m_norm in ['7 серии', '7 серия', '7 series']:
                model_syns.update(['X7', 'х7', 'x 7', 'x-7'])
            elif m_norm in ['4 серии', '4 серии', '4 series']:
                model_syns.update(['X4', 'х4', 'x 4', 'x-4'])
            elif m_norm in ['1 серии', '1 серии', '1 series']:
                model_syns.update(['X1', 'х1', 'x 1', 'x-1'])
            elif m_norm in ['2 серии', '2 серии', '2 series']:
                model_syns.update(['X2', 'х2', 'x 2', 'x-2'])
            elif m_norm in ['520d', '530d', '530li', '520i', '520', '530']:
                model_syns.update(['X5', 'х5', 'x 5', 'x-5', '5 серии', '5 серия', '5 series'])
            elif m_norm in ['320d', '330d', '320i', '330i', '320', '330']:
                model_syns.update(['X3', 'х3', 'x 3', 'x-3', '3 серии', '3 серия', '3 series'])
            else:
                if m_norm.isdigit():
                    model_syns.add(f"x{m_norm}")
            all_model_syns.update(model_syns)
        model_filters = []
        for syn in all_model_syns:
            # Используем простой LIKE без LOWER() для поддержки кириллицы
            # Добавляем варианты с разным регистром
            model_filters.append("REPLACE(model, ' ', '') LIKE ?")
            params_car.append(f"%{syn}%")
            params_used.append(f"%{syn}%")
            # Также добавляем поиск с большой буквы
            model_filters.append("REPLACE(model, ' ', '') LIKE ?")
            params_car.append(f"%{syn.capitalize()}%")
            params_used.append(f"%{syn.capitalize()}%")
        filters_car.append("(" + " OR ".join(model_filters) + ")")
        filters_used.append("(" + " OR ".join(model_filters) + ")")
    if year_from is not None:
        filters_car.append("manufacture_year >= ?")
        params_car.append(year_from)
        filters_used.append("manufacture_year >= ?")
        params_used.append(year_from)
    if year_to is not None:
        filters_car.append("manufacture_year <= ?")
        params_car.append(year_to)
        filters_used.append("manufacture_year <= ?")
        params_used.append(year_to)
    if price_from is not None:
        filters_car.append("price >= ?")
        params_car.append(price_from)
        filters_used.append("price >= ?")
        params_used.append(price_from)
    if price_to is not None:
        filters_car.append("price <= ?")
        params_car.append(price_to)
        filters_used.append("price <= ?")
        params_used.append(price_to)
    def match_any(val, field):
        if not val:
            return False
        v = normalize_str(val)
        return v in [normalize_str(x) for x in uniques[field]]
    if fuel_type and match_any(fuel_type, 'fuel_type'):
        # Учитываем оба варианта регистра для fuel_type
        fuel_type_lower = normalize_str(fuel_type)
        filters_car.append("(LOWER(fuel_type) = ? OR fuel_type = ?)")
        params_car.append(fuel_type_lower)
        params_car.append(fuel_type)
        filters_used.append("(LOWER(fuel_type) = ? OR fuel_type = ?)")
        params_used.append(fuel_type_lower)
        params_used.append(fuel_type)
    if transmission and match_any(transmission, 'gear_box_type'):
        # Учитываем оба варианта регистра для gear_box_type
        transmission_lower = normalize_str(transmission)
        filters_car.append("(LOWER(gear_box_type) = ? OR gear_box_type = ?)")
        params_car.append(transmission_lower)
        params_car.append(transmission)
        filters_used.append("(LOWER(gear_box_type) = ? OR gear_box_type = ?)")
        params_used.append(transmission_lower)
        params_used.append(transmission)
    if body_type:
        if isinstance(body_type, list):
            # Handle list of body types (OR logic)
            body_type_filters = []
            for bt in body_type:
                if match_any(bt, 'body_type'):
                    bt_lower = normalize_str(bt)
                    bt_cap = bt_lower.capitalize()
                    body_type_filters.append("(LOWER(body_type) = ? OR body_type = ? OR body_type = ?)")
                    params_car.extend([bt_lower, bt_lower, bt_cap])
                    params_used.extend([bt_lower, bt_lower, bt_cap])
            if body_type_filters:
                filters_car.append("(" + " OR ".join(body_type_filters) + ")")
                filters_used.append("(" + " OR ".join(body_type_filters) + ")")
        else:
            # Handle single body type
            if match_any(body_type, 'body_type'):
                body_type_lower = normalize_str(body_type)
                body_type_cap = body_type_lower.capitalize()
                filters_car.append("(LOWER(body_type) = ? OR body_type = ? OR body_type = ?)")
                params_car.extend([body_type_lower, body_type_lower, body_type_cap])
                filters_used.append("(LOWER(body_type) = ? OR body_type = ? OR body_type = ?)")
                params_used.extend([body_type_lower, body_type_lower, body_type_cap])
    if drive_type:
        drive_type_lower = normalize_str(drive_type)
        drive_type_cap = drive_type_lower.capitalize()
        filters_car.append("(LOWER(driving_gear_type) = ? OR driving_gear_type = ? OR driving_gear_type = ?)")
        params_car.extend([drive_type_lower, drive_type_lower, drive_type_cap])
        filters_used.append("(LOWER(driving_gear_type) = ? OR driving_gear_type = ? OR driving_gear_type = ?)")
        params_used.extend([drive_type_lower, drive_type_lower, drive_type_cap])
    if state == "new":
        filters_used.append("0")
    elif state == "used":
        filters_car.append("0")
    
    # --- Новые фильтры для расширенных характеристик ---
    if power_from is not None:
        filters_car.append("power >= ?")
        params_car.append(power_from)
        filters_used.append("power >= ?")
        params_used.append(power_from)
    
    if power_to is not None:
        filters_car.append("power <= ?")
        params_car.append(power_to)
        filters_used.append("power <= ?")
        params_used.append(power_to)
    
    if power_exact is not None:
        filters_car.append("power = ?")
        params_car.append(power_exact)
        filters_used.append("power = ?")
        params_used.append(power_exact)
    
    if engine_vol_from is not None:
        filters_car.append("engine_vol >= ?")
        params_car.append(engine_vol_from)
        filters_used.append("engine_vol >= ?")
        params_used.append(engine_vol_from)
    
    if engine_vol_to is not None:
        filters_car.append("engine_vol <= ?")
        params_car.append(engine_vol_to)
        filters_used.append("engine_vol <= ?")
        params_used.append(engine_vol_to)
    
    if engine_vol_exact is not None:
        filters_car.append("engine_vol = ?")
        params_car.append(engine_vol_exact)
        filters_used.append("engine_vol = ?")
        params_used.append(engine_vol_exact)
    
    # Пробег и количество владельцев пока не поддерживаются в базе данных
    # Эти поля нужно будет добавить в схему базы данных
    
    # Фильтры по количеству владельцев
    if owners_count is not None:
        filters_car.append("owners_count = ?")
        params_car.append(owners_count)
        filters_used.append("owners_count = ?")
        params_used.append(owners_count)
    
    if owners_from is not None:
        filters_car.append("owners_count >= ?")
        params_car.append(owners_from)
        filters_used.append("owners_count >= ?")
        params_used.append(owners_from)
    
    if owners_to is not None:
        filters_car.append("owners_count <= ?")
        params_car.append(owners_to)
        filters_used.append("owners_count <= ?")
        params_used.append(owners_to)
    
    # Тип руля и история аварий пока не поддерживаются в базе данных
    # Эти поля нужно будет добавить в схему базы данных
    
    # --- Фильтры производительности ---
    # Примечание: acceleration_from, acceleration_to, fuel_efficiency пока не поддерживаются в базе данных
    # Эти поля нужно будет добавить в схему базы данных
    
    # --- Добавляю фильтрацию по городу ---
    if city:
        import re
        def normalize_city_py(val):
            return re.sub(r'[-\s]', '', str(val).strip().lower())
        
        # Нормализуем входящий город
        c_norm = normalize_city_py(city)
        city_syns = set()
        
        # Ищем подходящие синонимы
        for canon, variants in CITY_SYNONYMS.items():
            if c_norm == normalize_city_py(canon) or c_norm in [normalize_city_py(v) for v in variants]:
                city_syns.update([canon] + variants)
        
        if not city_syns:
            city_syns = {city}
        
        city_filters = []
        for syn in city_syns:
            # Используем простой LIKE без LOWER() для кириллицы
            city_filters.append("city LIKE ?")
            params_car.append(f"%{syn}%")
            params_used.append(f"%{syn}%")
        
        filters_car.append("(" + " OR ".join(city_filters) + ")")
        filters_used.append("(" + " OR ".join(city_filters) + ")")
    
    # --- Фильтрация по количеству мест ---
    if seats is not None:
        filters_car.append("seats = ?")
        filters_used.append("seats = ?")
        params_car.append(seats)
        params_used.append(seats)
    
    # --- Фильтрация по цвету с правильным SQLite синтаксисом ---
    if color:
        # Обработка множественных цветов
        if isinstance(color, list):
            # Если передан список цветов, обрабатываем каждый отдельно
            all_color_cars = []
            for single_color in color:
                # Создаем копию параметров без color для избежания рекурсии
                search_params = {
                    'brand': brand, 'model': model, 'year_from': year_from, 'year_to': year_to,
                    'price_from': price_from, 'price_to': price_to, 'fuel_type': fuel_type,
                    'transmission': transmission, 'body_type': body_type, 'drive_type': drive_type,
                    'state': state, 'sort_by': sort_by, 'sort_order': sort_order,
                    'option_code': option_code, 'option_description': option_description,
                    'city': city
                }
                # Добавляем один цвет
                search_params['color'] = single_color
                
                # Вызываем внутреннюю функцию поиска
                cars_for_color = _search_cars_with_filters(**search_params)
                all_color_cars.extend(cars_for_color)
            
            # Убираем дубликаты по ID
            unique_cars = {}
            for car in all_color_cars:
                car_id = car.get('id')
                if car_id not in unique_cars:
                    unique_cars[car_id] = car
            
            return list(unique_cars.values())
        
        # Расширенный словарь синонимов для цветов
        color_synonyms = []
        color_lower = color.lower()
        
        if color_lower in ['белый', 'white']:
            color_synonyms = [
                'белый', 'Белый', 'white', 'White', 'белая', 'Белая', 'белое', 'Белое', 'белые', 'Белые',
                'перламутровый белый', 'pearlescent white', 'керамический белый', 'ceramic white',
                'белоснежный', 'снежно-белый', 'crystal white', 'alpine white', 'arctic white',
                'ivory white', 'pearl white', 'diamond white', 'platinum white'
            ]
        elif color_lower in ['черный', 'black', 'чёрный']:
            color_synonyms = [
                'черный', 'Черный', 'black', 'Black', 'чёрный', 'Чёрный',
                'глубокий черный', 'deep black', 'cosmic black', 'midnight black',
                'onyx black', 'ebony black', 'jet black', 'carbon black',
                'obsidian black', 'pitch black', 'void black'
            ]
        elif color_lower in ['серый', 'gray', 'grey']:
            color_synonyms = [
                'серый', 'Серый', 'gray', 'Gray', 'grey', 'Grey',
                'серебристый', 'silver', 'silver metallic', 'steel gray',
                'platinum gray', 'titanium gray', 'gunmetal gray', 'charcoal gray',
                'slate gray', 'ash gray', 'pewter gray', 'smoke gray'
            ]
        elif color_lower in ['синий', 'blue']:
            color_synonyms = [
                'синий', 'Синий', 'blue', 'Blue', 'голубой', 'Голубой',
                'navy blue', 'royal blue', 'sapphire blue', 'cobalt blue',
                'ocean blue', 'sky blue', 'azure blue', 'electric blue',
                'midnight blue', 'steel blue', 'powder blue', 'cornflower blue'
            ]
        elif color_lower in ['красный', 'red']:
            color_synonyms = [
                'красный', 'Красный', 'red', 'Red',
                'огненно-красный', 'fire red', 'crimson red', 'scarlet red',
                'ruby red', 'cherry red', 'burgundy red', 'candy red',
                'racing red', 'flame red', 'cardinal red', 'maroon red'
            ]
        elif color_lower in ['зеленый', 'зелёный', 'green']:
            color_synonyms = [
                'зеленый', 'Зеленый', 'зелёный', 'Зелёный', 'green', 'Green',
                'изумрудный', 'emerald green', 'forest green', 'olive green',
                'sage green', 'mint green', 'jade green', 'hunter green',
                'kelly green', 'lime green', 'sea green', 'moss green'
            ]
        elif color_lower in ['желтый', 'yellow']:
            color_synonyms = [
                'желтый', 'Желтый', 'yellow', 'Yellow',
                'золотистый', 'golden yellow', 'sunny yellow', 'canary yellow',
                'amber yellow', 'honey yellow', 'lemon yellow', 'butter yellow',
                'banana yellow', 'corn yellow', 'wheat yellow'
            ]
        elif color_lower in ['оранжевый', 'orange']:
            color_synonyms = [
                'оранжевый', 'Оранжевый', 'orange', 'Orange',
                'ярко-оранжевый', 'bright orange', 'tangerine orange', 'pumpkin orange',
                'sunset orange', 'coral orange', 'peach orange', 'apricot orange',
                'carrot orange', 'amber orange', 'copper orange'
            ]
        elif color_lower in ['фиолетовый', 'purple', 'violet']:
            color_synonyms = [
                'фиолетовый', 'Фиолетовый', 'purple', 'Purple', 'violet', 'Violet',
                'пурпурный', 'Пурпурный', 'lavender purple', 'royal purple',
                'plum purple', 'grape purple', 'orchid purple', 'amethyst purple',
                'magenta purple', 'burgundy purple', 'eggplant purple'
            ]
        elif color_lower in ['розовый', 'pink']:
            color_synonyms = [
                'розовый', 'Розовый', 'pink', 'Pink',
                'нежно-розовый', 'light pink', 'hot pink', 'rose pink',
                'salmon pink', 'peach pink', 'blush pink', 'fuchsia pink',
                'magenta pink', 'coral pink', 'dusty pink', 'baby pink'
            ]
        elif color_lower in ['коричневый', 'brown']:
            color_synonyms = [
                'коричневый', 'Коричневый', 'brown', 'Brown',
                'шоколадный', 'chocolate brown', 'coffee brown', 'caramel brown',
                'tan brown', 'beige brown', 'mocha brown', 'walnut brown',
                'mahogany brown', 'chestnut brown', 'saddle brown', 'taupe brown'
            ]
        elif color_lower in ['бежевый', 'beige']:
            color_synonyms = [
                'бежевый', 'Бежевый', 'beige', 'Beige',
                'светло-бежевый', 'light beige', 'cream beige', 'ivory beige',
                'sand beige', 'warm beige', 'cool beige', 'neutral beige',
                'champagne beige', 'pearl beige', 'almond beige'
            ]
        elif color_lower in ['голубой', 'light blue', 'светло-синий']:
            color_synonyms = [
                'голубой', 'Голубой', 'light blue', 'Light Blue', 'светло-синий', 'Светло-синий',
                'baby blue', 'sky blue', 'powder blue', 'periwinkle blue',
                'cornflower blue', 'azure blue', 'robin egg blue', 'steel blue'
            ]
        elif color_lower in ['темно-синий', 'dark blue', 'navy']:
            color_synonyms = [
                'темно-синий', 'Темно-синий', 'dark blue', 'Dark Blue', 'navy', 'Navy',
                'navy blue', 'midnight blue', 'royal blue', 'sapphire blue',
                'cobalt blue', 'indigo blue', 'marine blue', 'ocean blue'
            ]
        elif color_lower in ['серебристый', 'silver']:
            color_synonyms = [
                'серебристый', 'Серебристый', 'silver', 'Silver',
                'silver metallic', 'platinum silver', 'titanium silver',
                'chrome silver', 'aluminum silver', 'pewter silver',
                'steel silver', 'nickel silver', 'brushed silver'
            ]
        elif color_lower in ['золотистый', 'gold', 'golden']:
            color_synonyms = [
                'золотистый', 'Золотистый', 'gold', 'Gold', 'golden', 'Golden',
                'golden yellow', 'champagne gold', 'honey gold', 'amber gold',
                'bronze gold', 'copper gold', 'brass gold', 'metallic gold'
            ]
        elif color_lower in ['бронзовый', 'bronze']:
            color_synonyms = [
                'бронзовый', 'Бронзовый', 'bronze', 'Bronze',
                'antique bronze', 'copper bronze', 'golden bronze',
                'metallic bronze', 'aged bronze', 'patina bronze'
            ]
        elif color_lower in ['медный', 'copper']:
            color_synonyms = [
                'медный', 'Медный', 'copper', 'Copper',
                'copper metallic', 'antique copper', 'rose copper',
                'burnished copper', 'patina copper'
            ]
        else:
            # Для других цветов используем базовые варианты
            color_synonyms = [color, color.capitalize(), color.lower(), color.upper()]
        
        # Строим условия для цвета
        color_conditions = []
        for syn in color_synonyms:
            color_conditions.append("color LIKE ?")
            params_car.append(f"%{syn}%")
            params_used.append(f"%{syn}%")
        
        filters_car.append("(" + " OR ".join(color_conditions) + ")")
        filters_used.append("(" + " OR ".join(color_conditions) + ")")
    
    # ---
    sort_column = sort_by if sort_by in ["price", "manufacture_year", "power"] else "price"
    sort_direction = "ASC" if sort_order == "asc" else "DESC"
    query_car = f"SELECT id, title, doc_num, mark, model, vin, color, price, city, manufacture_year, body_type, gear_box_type, driving_gear_type, engine_vol, power, fuel_type, dealer_center, seats, owners_count FROM car WHERE {' AND '.join(filters_car)}"
    query_used = f"SELECT id, title, doc_num, mark, model, vin, color, price, city, manufacture_year, body_type, gear_box_type, driving_gear_type, engine_vol, power, fuel_type, dealer_center, seats, owners_count FROM used_car WHERE {' AND '.join(filters_used)}"
    query = query_used if only_used else f"{query_car} UNION ALL {query_used} ORDER BY {sort_column} {sort_direction}"
    params = params_used if only_used else params_car + params_used
    # Маппинг значений фильтров
    fuel_type = map_filter_value('fuel_type', fuel_type)
    body_type = map_filter_value('body_type', body_type)
    transmission = map_filter_value('transmission', transmission)
    drive_type = map_filter_value('drive_type', drive_type)
    # Фильтрация по опциям
    if option_code or option_description:
        with get_db() as conn:
            cursor = conn.cursor()
            car_ids = []
            if option_code:
                cursor.execute("SELECT DISTINCT car_id FROM option WHERE code = ?", (option_code,))
                car_ids = [row[0] for row in cursor.fetchall()]
            elif option_description:
                if isinstance(option_description, list):
                    placeholders = ' OR '.join(["lower(description) LIKE ?" for _ in option_description])
                    values = [f"%{desc.lower()}%" for desc in option_description]
                    cursor.execute(f"SELECT DISTINCT car_id FROM option WHERE {placeholders}", values)
                    car_ids = [row[0] for row in cursor.fetchall()]
            else:
                cursor.execute("SELECT DISTINCT car_id FROM option WHERE description LIKE ?", (f"%{option_description}%",))
            car_ids = [row[0] for row in cursor.fetchall()]
            if not car_ids:
                return []
            # Добавляем фильтр id IN (...) только если есть car_ids
            filters_car.append(f"id IN ({','.join(['?']*len(car_ids))})")
            params_car.extend(car_ids)
            filters_used.append(f"id IN ({','.join(['?']*len(car_ids))})")
            params_used.extend(car_ids)
    print(f"[search_all_cars] SQL-запрос: {query}")
    print(f"[search_all_cars] Параметры запроса: {params}")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cars = []
            # Новые авто
            cursor.execute(query_car, params_car)
            for row in cursor.fetchall():
                columns = [desc[0] for desc in cursor.description]
                car = dict(zip(columns, row))
                car['is_used'] = False
                cars.append(car)
            # Поддержанные авто
            cursor.execute(query_used, params_used)
            for row in cursor.fetchall():
                columns = [desc[0] for desc in cursor.description]
                car = dict(zip(columns, row))
                car['is_used'] = True
                cars.append(car)
            # Сортировка
            cars = sorted(cars, key=lambda x: x.get(sort_column, 0), reverse=(sort_direction=="DESC"))
        import logging
        logging.info(f"[search_all_cars] Найдено автомобилей: {len(cars)}")
        return cars
    except Exception as e:
        print(f"Ошибка поиска (search_all_cars): {e}")
        return [] 

def smart_filter_cars(brand=None, model=None, year=None, price_min=None, price_max=None, city=None, body_type=None, used=None):
    """
    Поиск автомобилей:
    - Если задана модель: ищем по бренду и всем синонимам/похожим моделям (LIKE, синонимы, подстроки)
    - Если не найдено — возвращаем все автомобили бренда с пометкой
    - Если не задана модель — ищем только по бренду
    Возвращает: (результат, пояснение)
    """
    tables = ['car', 'used_car']
    all_results = []
    explanation = ''
    brand_keywords = get_brand_keywords(brand) if brand else []
    if not brand_keywords:
        return [], 'Не указан бренд или бренд не найден в базе'
    # --- 1. Если задана модель: ищем по бренду и всем синонимам/похожим моделям ---
    if model:
        model_keywords = get_model_keywords(model)
        found = []
        for table in tables:
            with get_db() as conn:
                cursor = conn.cursor()
                columns = [desc[0] for desc in cursor.execute(f'SELECT * FROM {table} LIMIT 1').description]
                brand_filters = ["LOWER(REPLACE(mark, ' ', '')) LIKE ?" for _ in brand_keywords]
                model_filters = ["LOWER(REPLACE(model, ' ', '')) LIKE ?" for _ in model_keywords]
                query = f"SELECT * FROM {table} WHERE (" + " OR ".join(brand_filters) + ") AND (" + " OR ".join(model_filters) + ")"
                params = [f"%{kw}%" for kw in brand_keywords] + [f"%{kw}%" for kw in model_keywords]
                if year:
                    query += " AND manufacture_year = ?"
                    params.append(year)
                if price_min is not None:
                    query += " AND price >= ?"
                    params.append(price_min)
                if price_max is not None:
                    query += " AND price <= ?"
                    params.append(price_max)
                if city:
                    query += " AND city = ?"
                    params.append(city)
                if body_type:
                    query += " AND body_type = ?"
                    params.append(body_type)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                found.extend([dict(zip(columns, row)) for row in rows])
        if found:
            explanation = 'Найдено по бренду и модели (гибкий поиск)'
            return found, explanation
        # --- 2. Если не найдено — возвращаем все автомобили бренда с пометкой ---
        all_results = []
        for table in tables:
            with get_db() as conn:
                cursor = conn.cursor()
                columns = [desc[0] for desc in cursor.execute(f'SELECT * FROM {table} LIMIT 1').description]
                brand_filters = ["LOWER(REPLACE(mark, ' ', '')) LIKE ?" for _ in brand_keywords]
                query = f"SELECT * FROM {table} WHERE (" + " OR ".join(brand_filters) + ")"
                params = [f"%{kw}%" for kw in brand_keywords]
                if year:
                    query += " AND manufacture_year = ?"
                    params.append(year)
                if price_min is not None:
                    query += " AND price >= ?"
                    params.append(price_min)
                if price_max is not None:
                    query += " AND price <= ?"
                    params.append(price_max)
                if city:
                    query += " AND city = ?"
                    params.append(city)
                if body_type:
                    query += " AND body_type = ?"
                    params.append(body_type)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                all_results.extend([dict(zip(columns, row)) for row in rows])
        if all_results:
            explanation = f'❗️ Не найдено точных совпадений по модели "{model}". Вот другие автомобили {brand}:'
            return all_results, explanation
        else:
            return [], f'Автомобили бренда {brand} не найдены в базе'
    # --- 3. Если не задана модель — ищем только по бренду ---
    for table in tables:
        with get_db() as conn:
            cursor = conn.cursor()
            columns = [desc[0] for desc in cursor.execute(f'SELECT * FROM {table} LIMIT 1').description]
            brand_filters = ["LOWER(REPLACE(mark, ' ', '')) LIKE ?" for _ in brand_keywords]
            query = f"SELECT * FROM {table} WHERE (" + " OR ".join(brand_filters) + ")"
            params = [f"%{kw}%" for kw in brand_keywords]
            if year:
                query += " AND manufacture_year = ?"
                params.append(year)
            if price_min is not None:
                query += " AND price >= ?"
                params.append(price_min)
            if price_max is not None:
                query += " AND price <= ?"
                params.append(price_max)
            if city:
                query += " AND city = ?"
                params.append(city)
            if body_type:
                query += " AND body_type = ?"
                params.append(body_type)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            all_results.extend([dict(zip(columns, row)) for row in rows])
    if all_results:
        explanation = 'Найдено по бренду (car и used_car)'
        return all_results, explanation
    else:
        return [], f'Автомобили бренда {brand} не найдены в базе' 

def get_recent_cars_from_db(limit: Optional[int] = None):
    """
    Возвращает limit последних автомобилей (car + used_car), отсортированных по году выпуска и цене (сначала новые, потом подержанные)
    Теперь для каждого авто подгружаются опции (options).
    Если limit=None, возвращает все автомобили.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # Новые авто
        cursor.execute("""
            SELECT id, mark, model, manufacture_year, price, dealer_center, 'new' as state
            FROM car
            ORDER BY manufacture_year DESC, price DESC, id DESC
        """)
        new_cars = cursor.fetchall()
        # Подержанные авто
        cursor.execute("""
            SELECT id, mark, model, manufacture_year, price, dealer_center, 'used' as state
            FROM used_car
            ORDER BY manufacture_year DESC, price DESC, id DESC
        """)
        used_cars = cursor.fetchall()
        # Объединяем, сортируем по году и цене
        all_cars = [
            {
                'id': row[0],
                'brand': row[1],
                'model': row[2],
                'year': row[3],
                'price': row[4],
                'dealer_center': row[5],
                'state': row[6],
                'options': get_car_options_by_car_id(row[0])
            } for row in new_cars + used_cars
        ]
        all_cars.sort(key=lambda x: (x['year'], x['price']), reverse=True)
        if limit is not None:
            return all_cars[:limit]
        return all_cars

# --- Индексы ---
def create_indexes():
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_car_mark ON car (mark)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_car_model ON car (model)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_car_year ON car (manufacture_year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_car_city ON car (city)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_car_dealer ON car (dealer_center)')
            conn.commit()
        except Exception as e:
            logging.error(f'Ошибка создания индексов: {e}')

# --- Применение локов при инициализации ---
def init_car_db():
    with init_lock:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS car (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mark TEXT,
                model TEXT,
                manufacture_year INTEGER,
                price INTEGER,
                fuel_type TEXT,
                power REAL,
                gear_box_type TEXT,
                body_type TEXT,
                city TEXT,
                availability INTEGER DEFAULT 1,
                owners_count INTEGER DEFAULT 1
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS used_car (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mark TEXT,
                model TEXT,
                manufacture_year INTEGER,
                price INTEGER,
                fuel_type TEXT,
                power REAL,
                gear_box_type TEXT,
                body_type TEXT,
                city TEXT,
                availability INTEGER DEFAULT 1,
                owners_count INTEGER DEFAULT 1
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS dealer_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                website TEXT,
                city TEXT,
                brands TEXT,
                working_hours TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.commit()
        
        # Добавляем поле owners_count к существующим таблицам
        with get_db() as conn2:
            cursor2 = conn2.cursor()
            add_column_if_not_exists(cursor2, 'car', 'owners_count', 'INTEGER DEFAULT 1')
            add_column_if_not_exists(cursor2, 'used_car', 'owners_count', 'INTEGER DEFAULT 1')
            conn2.commit()
        
        create_indexes() 

def ensure_api_logs_table():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time REAL,
                user_id TEXT,
                ip_address TEXT
            )
        ''')
        conn.commit() 

def get_car_options_by_car_id(car_id: int) -> List[Dict[str, Any]]:
    """Получает все опции для конкретного автомобиля"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, car_id, code, description 
                FROM option 
                WHERE car_id = ? 
                ORDER BY code
            """, (car_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"Ошибка получения опций для car_id {car_id}: {e}")
        return []

def get_all_options():
    """
    Получает все уникальные опции (code, description) из таблицы option
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT code, description FROM option ORDER BY code")
        return [
            {"code": row[0], "description": row[1]} for row in cursor.fetchall()
        ]

def get_unique_option_codes() -> List[str]:
    """Получает все уникальные коды опций"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT code 
                FROM option 
                WHERE code IS NOT NULL 
                ORDER BY code
            """)
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Ошибка получения уникальных кодов опций: {e}")
        return []

def search_options_by_code(code: str) -> List[Dict[str, Any]]:
    """Ищет опции по коду"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, car_id, code, description 
                FROM option 
                WHERE code LIKE ? 
                ORDER BY car_id, code
            """, (f"%{code}%",))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logging.error(f"Ошибка поиска опций по коду {code}: {e}")
        return []

def get_options_statistics() -> Dict[str, Any]:
    """Получает статистику по опциям"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Общее количество опций
            total_options = cursor.execute("SELECT COUNT(*) FROM option").fetchone()[0]
            
            # Количество уникальных кодов
            unique_codes = cursor.execute("SELECT COUNT(DISTINCT code) FROM option WHERE code IS NOT NULL").fetchone()[0]
            
            # Топ-10 самых популярных опций
            top_options = cursor.execute("""
                SELECT code, COUNT(*) as count 
                FROM option 
                WHERE code IS NOT NULL 
                GROUP BY code 
                ORDER BY count DESC 

            """).fetchall()
            
            # Количество автомобилей с опциями
            cars_with_options = cursor.execute("SELECT COUNT(DISTINCT car_id) FROM option").fetchone()[0]
            
            return {
                "total_options": total_options,
                "unique_codes": unique_codes,
                "cars_with_options": cars_with_options,
                "top_options": [{"code": row[0], "count": row[1]} for row in top_options]
            }
    except Exception as e:
        logging.error(f"Ошибка получения статистики опций: {e}")
        return {}

def get_car_with_options(car_id: int) -> Optional[Dict[str, Any]]:
    """Получает автомобиль с его опциями"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Получаем информацию об автомобиле
            cursor.execute("""
                SELECT * FROM car WHERE id = ?
            """, (car_id,))
            car_row = cursor.fetchone()
            
            if not car_row:
                return None
            
            car = dict(car_row)
            
            # Получаем опции автомобиля
            options = get_car_options_by_car_id(car_id)
            car['options'] = options
            
            return car
    except Exception as e:
        logging.error(f"Ошибка получения автомобиля с опциями для car_id {car_id}: {e}")
        return None

def init_quick_scenarios_table():
    """Создаёт таблицу сценариев, если не существует"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS quick_scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            icon TEXT,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()

def get_all_quick_scenarios():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, icon, query FROM quick_scenarios ORDER BY id ASC')
        return [
            {'id': row[0], 'title': row[1], 'icon': row[2], 'query': row[3]}
            for row in cursor.fetchall()
        ]

def add_quick_scenario(title, icon, query):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO quick_scenarios (title, icon, query) VALUES (?, ?, ?)''', (title, icon, query))
        conn.commit()
        return cursor.lastrowid

def update_quick_scenario(scenario_id, title, icon, query):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE quick_scenarios SET title=?, icon=?, query=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''', (title, icon, query, scenario_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_quick_scenario(scenario_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quick_scenarios WHERE id=?', (scenario_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_cars_by_ids(ids):
    """Удаляет автомобили с заданными id из car и used_car. Возвращает количество удалённых."""
    if not ids:
        return 0
    with get_db() as conn:
        cursor = conn.cursor()
        q_marks = ','.join(['?']*len(ids))
        deleted = 0
        # Удаляем из car
        cursor.execute(f"DELETE FROM car WHERE id IN ({q_marks})", ids)
        deleted += cursor.rowcount
        # Удаляем из used_car
        cursor.execute(f"DELETE FROM used_car WHERE id IN ({q_marks})", ids)
        deleted += cursor.rowcount
        conn.commit()
        return deleted

def delete_dealers_by_ids(ids):
    """Удаляет дилеров с заданными id из dealer_centers. Возвращает количество удалённых."""
    if not ids:
        return 0
    with get_db() as conn:
        cursor = conn.cursor()
        q_marks = ','.join(['?']*len(ids))
        cursor.execute(f"DELETE FROM dealer_centers WHERE id IN ({q_marks})", ids)
        deleted = cursor.rowcount
        conn.commit()
        return deleted

def get_cities_with_stats():
    """
    Возвращает список городов с количеством машин (car + used_car), пустые значения как 'Не заполнено'.
    [{"name": "Москва", "count": 40}, ...]
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # car
        cursor.execute("SELECT city, COUNT(*) FROM car GROUP BY city")
        car_stats = cursor.fetchall()
        # used_car
        cursor.execute("SELECT city, COUNT(*) FROM used_car GROUP BY city")
        used_stats = cursor.fetchall()
        stats = {}
        for city, count in car_stats + used_stats:
            name = city.strip() if city and city.strip() else 'Не заполнено'
            stats[name] = stats.get(name, 0) + count
        return [{"name": k, "count": v} for k, v in stats.items()]
def search_all_cars(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    body_type: Optional[str] = None,
    drive_type: Optional[str] = None,
    state: Optional[str] = None,
    sort_by: str = "price",
    sort_order: str = "asc",
    option_code: Optional[str] = None,
    option_description: Optional[str] = None,
    city: Optional[str] = None,
    color: Optional[str] = None,
    seats: Optional[int] = None,
    limit: Optional[int] = None,
    # Новые параметры для расширенных характеристик
    power_from: Optional[int] = None,
    power_to: Optional[int] = None,
    power_exact: Optional[int] = None,
    engine_vol_from: Optional[float] = None,
    engine_vol_to: Optional[float] = None,
    engine_vol_exact: Optional[float] = None,
    mileage_from: Optional[int] = None,
    mileage_to: Optional[int] = None,
    mileage_exact: Optional[int] = None,
    owners_count: Optional[int] = None,
    owners_from: Optional[int] = None,
    owners_to: Optional[int] = None,
    steering_wheel: Optional[str] = None,
    accident_history: Optional[str] = None,
    # Параметры производительности
    acceleration_from: Optional[float] = None,
    acceleration_to: Optional[float] = None,
    fuel_efficiency: Optional[str] = None
) -> list:
    return _search_cars_with_filters(
        brand=brand, model=model, year_from=year_from, year_to=year_to,
        price_from=price_from, price_to=price_to, fuel_type=fuel_type,
        transmission=transmission, body_type=body_type, drive_type=drive_type,
        state=state, sort_by=sort_by, sort_order=sort_order,
        option_code=option_code, option_description=option_description,
        city=city, color=color, seats=seats, limit=limit,
        power_from=power_from, power_to=power_to, power_exact=power_exact,
        engine_vol_from=engine_vol_from, engine_vol_to=engine_vol_to, engine_vol_exact=engine_vol_exact,
        mileage_from=mileage_from, mileage_to=mileage_to, mileage_exact=mileage_exact,
        owners_count=owners_count, owners_from=owners_from, owners_to=owners_to,
        steering_wheel=steering_wheel, accident_history=accident_history,
        acceleration_from=acceleration_from, acceleration_to=acceleration_to, fuel_efficiency=fuel_efficiency
    )

