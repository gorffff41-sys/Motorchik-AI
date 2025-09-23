from fastapi import FastAPI, HTTPException, Request, Body, Query, Path, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Tuple, Optional, Any, Union
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import os
import tempfile
import time
from starlette.status import HTTP_401_UNAUTHORIZED
import secrets
import traceback
from flask import request
import asyncio

# Импорт наших модулей
from database import execute_query, get_db, search_all_cars, get_all_brands_cached, get_all_models_cached, smart_filter_cars, get_recent_cars_from_db, get_all_quick_scenarios, add_quick_scenario, update_quick_scenario, delete_quick_scenario, init_quick_scenarios_table, get_all_cities, get_all_options, get_all_unique_values_lower
from dialog_manager import DialogManager, ContextAwareDialogManager
from nlp_processor import NLPProcessor, extract_entities_from_text
from fuzzy_search import FuzzySearch
from nlp_utils import find_similar_words, extract_entities
from user_history import UserHistory
from filter_mapping import map_filter_value
from brand_synonyms import BRAND_SYNONYMS, normalize_brand_extended, generate_case_variations, expand_brand_synonyms
from llama_service import generate_with_llama
from deepseek_service import deepseek_service
from monitoring import system_monitor
from modules.classifiers.query_processor import UniversalQueryProcessor
from modules.classifiers.ner_intent_classifier import NERIntentClassifier
from modules.classifiers.sentiment_analyzer import SentimentAnalyzer
from modules.recommendation.advanced_recommendation_engine import AdvancedRecommendationEngine
from modules.dialogue.enhanced_dialog_manager import EnhancedDialogManager
from modules.analytics.data_analyzer import DataAnalyzer
from recommendation_engine import RecommendationEngine
from user_analytics import UserAnalytics
from notification_system import NotificationSystem
from car_parser import car_parser
from smart_query_router import route_query
from enhanced_query_router import EnhancedQueryRouter
from enhanced_query_router_v2 import EnhancedQueryRouterV2
from enhanced_query_router_v3 import EnhancedQueryRouterV3
from enhanced_llama_processor import EnhancedLlamaProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Автоассистент API", version="2.0.0")

# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/avatar", StaticFiles(directory="avatar"), name="avatar")

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    print("🚀 Приложение запускается...")
    print("✅ База данных готова к работе")
    print("🎯 Приложение готово к работе!")

# Инициализация компонентов
USE_CONTEXT_MANAGER = True  # Флаг для включения контекстного менеджера

dialog_manager = DialogManager()
context_dialog_manager = ContextAwareDialogManager()
nlp_processor = NLPProcessor()
fuzzy_search = FuzzySearch()
user_history_manager = UserHistory()
nlp = NLPProcessor()
processor = UniversalQueryProcessor()

# Новые модули
ner_classifier = NERIntentClassifier()
sentiment_analyzer = SentimentAnalyzer()
advanced_recommendation_engine = AdvancedRecommendationEngine()
enhanced_dialog_manager = EnhancedDialogManager()
data_analyzer = DataAnalyzer()

recommendation_engine = RecommendationEngine()
user_analytics = UserAnalytics()
notification_system = NotificationSystem()

# Улучшенный LLAMA процессор
enhanced_llama_processor = EnhancedLlamaProcessor()

# Улучшенный роутер запросов
enhanced_router = EnhancedQueryRouter()
enhanced_router_v2 = EnhancedQueryRouterV2()
enhanced_router_v3 = EnhancedQueryRouterV3()

# База данных готова к работе
print("✅ База данных готова к работе")

# Модели данных
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    use_yandex_gpt: Optional[bool] = False  # Новый параметр для режима YandexGPT
    use_deepseek: Optional[bool] = False  # Новый параметр для режима DeepSeek

class SearchRequest(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    drive_type: Optional[str] = None
    state: Optional[str] = None
    sort_by: str = "price"
    sort_order: str = "asc"

class CompareRequest(BaseModel):
    car1_id: int
    car2_id: int

class RecommendationRequest(BaseModel):
    user_id: str
    preferences: Optional[Dict[str, Any]] = None
    budget: Optional[float] = None
    purpose: Optional[str] = None  # family, sport, business, etc.

class TestDriveRequest(BaseModel):
    user_id: str
    car_id: int
    preferred_date: str
    preferred_time: str
    contact_phone: str

class CreditRequest(BaseModel):
    user_id: str
    car_id: int
    down_payment: float
    term_months: int
    monthly_income: float

class ApplyFilterRequest(BaseModel):
    user_id: str
    filter_name: Optional[str] = None
    filter_id: Optional[int] = None

class LlamaRequest(BaseModel):
    query: str
    context: Optional[dict] = None

class LlamaFeedbackRequest(BaseModel):
    user_id: str
    query: str
    llama_response: str
    quality_score: int  # 1-5
    comment: str = ""

class CarCreateRequest(BaseModel):
    mark: str
    model: str
    price: float
    city: str
    manufacture_year: int
    fuel_type: str = ''
    body_type: str = ''
    gear_box_type: str = ''
    driving_gear_type: str = ''
    dealer_center: str = ''
    state: str = 'new'
    mileage: int = 0

class DealerCreateRequest(BaseModel):
    name: str
    address: str
    phone: str = ''
    email: str = ''
    website: str = ''
    latitude: float = 0.0
    longitude: float = 0.0
    brands: str = ''

class NotificationRequest(BaseModel):
    user_id: str
    notification_type: str
    title: str
    message: str
    priority: int = 1
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NotificationSettingsRequest(BaseModel):
    user_id: str
    email_notifications: bool = True
    push_notifications: bool = True
    recommendation_notifications: bool = True
    system_alerts: bool = True
    promotion_notifications: bool = True
    notification_frequency: str = "daily"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"

class UserBehaviorRequest(BaseModel):
    user_id: str
    days: int = 30

class SystemAlertRequest(BaseModel):
    alert_type: str
    severity: str
    title: str
    description: str
    metadata: Optional[Dict[str, Any]] = None

class CarParseRequest(BaseModel):
    brand: str
    model: str
    price: int
    city: Optional[str] = None
    tolerance: Optional[float] = 0.1

class CarLinkRequest(BaseModel):
    brand: str
    model: str
    city: Optional[str] = None

class CarParseResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[int] = None
    found_price: Optional[int] = None
    price_difference: Optional[int] = None
    title: Optional[str] = None
    tech_info: Optional[Dict[str, str]] = None
    status: Optional[str] = None
    address: Optional[str] = None
    img_url: Optional[str] = None
    region: Optional[str] = None
    url_catalog_fallback: Optional[str] = None
    error: Optional[str] = None

API_KEY = os.environ.get('API_KEY', 'supersecret')
RATE_LIMIT = 30  # запросов в минуту на эндпоинт
rate_limit_state = {}

def check_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

# --- Rate limiting ---
def rate_limiter(endpoint: str, user_id: str = 'anon'):
    now = int(time.time() // 60)
    key = f"{endpoint}:{user_id}:{now}"
    count = rate_limit_state.get(key, 0)
    if count >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_state[key] = count + 1

def get_cars_count() -> int:
    """Получение количества автомобилей"""
    result1 = execute_query("SELECT COUNT(*) FROM car")
    result2 = execute_query("SELECT COUNT(*) FROM used_car")
    return (result1[0][0] if result1 else 0) + (result2[0][0] if result2 else 0)

def get_car_by_id(car_id: int) -> Optional[dict]:
    """Получение автомобиля по ID"""
    columns = [
        "id", "title", "doc_num", "mark", "model", "vin", "color", "price", "city", "manufacture_year", "body_type", "gear_box_type", "driving_gear_type", "engine_vol", "power", "fuel_type", "dealer_center"
    ]
    car = execute_query("SELECT id, title, doc_num, mark, model, vin, color, price, city, manufacture_year, body_type, gear_box_type, driving_gear_type, engine_vol, power, fuel_type, dealer_center FROM car WHERE id = ?", [car_id])
    if car:
        car_dict = dict(zip(columns, car[0]))
        extras = execute_query("SELECT stock_qty, code_compl FROM car WHERE id = ?", [car_id])
        if extras:
            car_dict['stock_qty'] = extras[0][0]
            car_dict['code_compl'] = extras[0][1]
        return car_dict
    car = execute_query("SELECT id, title, doc_num, mark, model, vin, color, price, city, manufacture_year, body_type, gear_box_type, driving_gear_type, engine_vol, power, fuel_type, dealer_center FROM used_car WHERE id = ?", [car_id])
    if car:
        car_dict = dict(zip(columns, car[0]))
        extras = execute_query("SELECT mileage FROM used_car WHERE id = ?", [car_id])
        if extras:
            car_dict['mileage'] = extras[0][0]
        return car_dict
    return None

def initialize_database():
    """Инициализация базы данных"""
    # Создание таблицы автомобилей если не существует (с существующей структурой)
    execute_query("""
        CREATE TABLE IF NOT EXISTS car (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(100),
            doc_num VARCHAR(50),
            stock_qty INTEGER,
            mark VARCHAR(100),
            model VARCHAR(100),
            code_compl VARCHAR(100),
            vin VARCHAR(50),
            color VARCHAR(50),
            price FLOAT,
            city VARCHAR(100),
            manufacture_year INTEGER,
            fuel_type VARCHAR(50),
            power FLOAT,
            body_type VARCHAR(50),
            gear_box_type VARCHAR(50),
            driving_gear_type VARCHAR(50),
            engine_vol INTEGER,
            dealer_center VARCHAR(100)
        )
    """)
    # Создание таблицы подержанных автомобилей
    execute_query("""
        CREATE TABLE IF NOT EXISTS used_car (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(100),
            doc_num VARCHAR(50),
            mark VARCHAR(100),
            model VARCHAR(100),
            vin VARCHAR(50),
            color VARCHAR(50),
            price FLOAT,
            city VARCHAR(100),
            manufacture_year INTEGER,
            mileage INTEGER,
            body_type VARCHAR(50),
            gear_box_type VARCHAR(50),
            driving_gear_type VARCHAR(50),
            engine_vol INTEGER,
            power FLOAT,
            fuel_type VARCHAR(50),
            dealer_center VARCHAR(100)
        )
    """)
    # Создание таблицы дилерских центров если не существует
    execute_query("""
        CREATE TABLE IF NOT EXISTS dealer_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            latitude REAL,
            longitude REAL,
            brands TEXT
        )
    """)
    # Создание таблицы истории пользователей если не существует
    execute_query("""
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
    # Создание таблицы предпочтений пользователей если не существует
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Создание таблицы истории чата (для мониторинга)
    execute_query("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            response TEXT,
            intent TEXT,
            response_time REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Создание таблицы фидбека по Llama-ответам
    execute_query("""
        CREATE TABLE IF NOT EXISTS llama_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query TEXT,
            llama_response TEXT,
            quality_score INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    try:
        # Инициализация базы данных
        initialize_database()
        logger.info("База данных инициализирована")
        init_quick_scenarios_table()
            
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница"""
    try:
        with open("static/index_new.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Автоассистент</h1><p>Интерфейс не найден</p>")

@app.get("/test-filters", response_class=HTMLResponse)
async def test_filters():
    """Тестовая страница для проверки фильтров"""
    try:
        with open("test_filters.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Тест фильтров</h1><p>Файл не найден</p>")

@app.get("/test-filters-simple", response_class=HTMLResponse)
async def test_filters_simple():
    """Простая тестовая страница для проверки фильтров"""
    try:
        with open("test_filters_simple.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Тест фильтров</h1><p>Файл не найден</p>")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Обработка чат-запросов с умной маршрутизацией"""
    try:
        # Проверяем тип сообщения сразу
        logger.info(f"DEBUG: request.message = {request.message}")
        logger.info(f"DEBUG: type(request.message) = {type(request.message)}")
        if not isinstance(request.message, str):
            request.message = str(request.message)
            logger.info(f"DEBUG: converted to string: {request.message}")
        # Подробное логирование запроса
        logger.info(f"=== НОВЫЙ ЗАПРОС ===")
        logger.info(f"Сообщение: {request.message}")
        logger.info(f"Тип сообщения: {type(request.message)}")
        logger.info(f"User ID: {request.user_id}")
        logger.info(f"DeepSeek режим: {request.use_deepseek}")
        logger.info(f"Время запроса: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Проверяем, нужно ли использовать DeepSeek
        if request.use_deepseek:
            logger.info(f"🚀 Используем DeepSeek для запроса: {request.message}")
            result = deepseek_service.generate_response(request.message, request.user_id or "default")
            logger.info(f"✅ DeepSeek ответ получен: {type(result)}")
        else:
            # Явные общие (разрешённые) фразы → сразу в Llama
            lower_msg = (request.message or "").lower().strip()
            general_llama_keywords = [
                'привет', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
                'как дела', 'как ты', 'как у вас дела', 'чем занимаешься', 'что делаешь',
                'кто ты', 'кто вы', 'что ты умеешь', 'что вы умеете', 'расскажи о себе', 'расскажите о себе'
            ]
            is_car_query = False
            router = None
            if any(k in lower_msg for k in general_llama_keywords):
                from llama_service import generate_general_response
                llama_response = generate_general_response(request.message)
                result = {
                    "type": "llama_response",
                    "message": llama_response,
                    "llama": True,
                    "is_general_query": True
                }
            else:
                # Используем умный роутер для классификации запроса
                from smart_query_router import SmartQueryRouter
                router = SmartQueryRouter()
                is_car_query = router.is_car_related(request.message)

            if 'result' not in locals() and is_car_query:
                logger.info(f"🚗 Автомобильный запрос: {request.message}")
                router_result = router.route_query(request.message, request.user_id or "default")
                if router_result.get('success') and router_result.get('is_car_query'):
                    result = router_result.get('data', {})
                else:
                    result = router_result
                logger.info(f"✅ Автомобильный ответ получен: {type(result)}")
            elif 'result' not in locals():
                # Неавтомобильные или неоднозначные запросы: только приветствия → LLAMA; остальное → спецсообщение
                lower_msg2 = (request.message or "").lower().strip()
                general_llama_keywords2 = [
                    'привет', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
                    'как дела', 'как ты', 'как у вас дела', 'чем занимаешься', 'что делаешь',
                    'кто ты', 'кто вы', 'что ты умеешь', 'что вы умеете', 'расскажи о себе', 'расскажите о себе'
                ]
                if any(k in lower_msg2 for k in general_llama_keywords2):
                    logger.info(f"💬 Общий разрешённый запрос → LLAMA: {request.message}")
                    from llama_service import generate_general_response
                    llama_response = generate_general_response(request.message)
                    result = {
                        "type": "llama_response",
                        "message": llama_response,
                        "llama": True,
                        "is_general_query": True
                    }
                else:
                    logger.info(f"ℹ️ Неавтомобильный запрос → Специализация ассистента")
                    result = {
                        "type": "specialization_notice",
                        "message": (
                            "Я Моторчик — специализированный ассистент по подбору автомобилей. "
                            "Помогу найти авто по параметрам, сравнить модели, подсказать конфигурации, "
                            "условия кредита и др. Задайте, пожалуйста, вопрос про автомобили."
                        ),
                        "is_general_query": True
                    }
        
        # Логируем результат
        if isinstance(result, dict):
            logger.info(f"📋 Тип ответа: {result.get('type', 'unknown')}")
            logger.info(f"📝 Длина сообщения: {len(str(result.get('message', '')))} символов")
            logger.info(f"🔍 Структура ответа: {result}")
        else:
            logger.info(f"📋 Тип ответа: {type(result)}")
            logger.info(f"📝 Длина ответа: {len(str(result))} символов")
            logger.info(f"🔍 Содержимое ответа: {result}")
        
        # Добавляем url для каждой машины, если есть список cars
        if isinstance(result, dict) and 'cars' in result and isinstance(result['cars'], list):
            for car in result['cars']:
                car_data = {'mark': car.get('mark') or car.get('brand'), 'model': car.get('model')}
                url = car_parser.generate_car_link(car_data)
                if url:
                    car['url'] = url
        
        # Сохраняем запрос и ответ в историю
        try:
            user_history_manager.add_query(
                user_id=request.user_id or "default",
                query=request.message,
                response=result.get('message', str(result)),
                intent=result.get('type', 'deepseek_response' if request.use_deepseek else 'unknown'),
                entities=result.get('entities', {})
            )
            logger.info(f"💾 История запроса сохранена")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось сохранить историю запроса: {e}")
        
        logger.info(f"=== ЗАПРОС ОБРАБОТАН ===\n")
        # LLAMA используется только для общих запросов, не для автомобильных
        # Автомобильные запросы обрабатываются через processor.process() и возвращают результат напрямую
        return {"success": True, "response": result}
    except Exception as e:
        logger.error(f"Ошибка в обработчике /api/chat: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/chat")
async def chat_info():
    """Информация о чат-эндпоинте"""
    return {
        "message": "Используйте POST метод для отправки сообщений",
        "available_methods": ["POST"],
        "example": {
            "method": "POST",
            "url": "/api/chat",
            "body": {
                "message": "Найти BMW X5",
                "user_id": "user_123"
            }
        }
    }

def get_first_deep(val):
    if isinstance(val, (list, tuple)):
        return get_first_deep(val[0]) if val else None
    return val

def normalize_brand(value):
    """Улучшенная функция нормализации брендов с поддержкой падежных вариаций"""
    value = get_first_deep(value)
    if not value:
        return value
    if not isinstance(value, str):
        value = str(value)
    
    # Используем улучшенную систему распознавания брендов
    from brand_synonyms import normalize_brand_extended
    normalized = normalize_brand_extended(value)
    
    # Если улучшенная система не нашла бренд, используем старую логику
    if normalized and normalized != value.title():
        return normalized
    
    # Fallback к старой логике
    brands = get_all_brands_cached()
    for b in brands:
        if isinstance(b, tuple):
            b = b[0]
        if isinstance(b, str) and value.lower() == b.lower():
            return b
    return value

def normalize_model(value):
    value = get_first_deep(value)
    if not value:
        return value
    if not isinstance(value, str):
        value = str(value)
    models = get_all_models_cached()
    for m in models:
        if isinstance(m, tuple):
            m = m[0]
        if isinstance(m, str) and value.lower() == m.lower():
            return m
    return value

@app.post("/api/cars/create", dependencies=[Depends(check_api_key)])
async def create_car(car: CarCreateRequest, x_api_key: str = Header(...)):
    rate_limiter("create_car", x_api_key)
    try:
        query = ("INSERT INTO car (mark, model, price, city, manufacture_year, fuel_type, body_type, gear_box_type, driving_gear_type, dealer_center) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
        params = [car.mark, car.model, car.price, car.city, car.manufacture_year, car.fuel_type, car.body_type, car.gear_box_type, car.driving_gear_type, car.dealer_center]
        execute_query(query, params)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка создания автомобиля: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/cars/create")
async def add_car(car: CarCreateRequest):
    """Добавление нового автомобиля (car или used_car по state)"""
    try:
        table = 'car' if car.state == 'new' else 'used_car'
        columns = [
            'mark', 'model', 'price', 'city', 'manufacture_year', 'fuel_type',
            'body_type', 'gear_box_type', 'driving_gear_type', 'dealer_center', 'mileage'
        ]
        values = [
            car.mark, car.model, car.price, car.city, car.manufacture_year, car.fuel_type,
            car.body_type, car.gear_box_type, car.driving_gear_type, car.dealer_center, car.mileage
        ]
        # Для новых авто mileage не обязателен
        if table == 'car':
            columns = columns[:-1]
            values = values[:-1]
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
        execute_query(query, values)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка добавления автомобиля: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/cars")
async def search_cars(request: dict = Body(...)):
    user_id = request.get('user_id', 'default')
    query = request.get('query', '')
    offset = int(request.get('offset', 0))
    limit = int(request.get('limit', 10))
    show_cars = bool(request.get('show_cars', False))
    entities = request.get('entities', {})
    result = processor.process(query, entities=entities, user_id=user_id, offset=offset, limit=limit, show_cars=show_cars)
    return JSONResponse(content=result)

@app.get("/api/filters/available")
async def get_available_filters(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    price_from: Optional[str] = Query(None),
    price_to: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    transmission: Optional[str] = Query(None),
    body_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    """Получение доступных опций для фильтров на основе текущих значений"""
    try:
        # Формируем фильтры для поиска
        filters = {}
        if brand:
            filters['brand'] = brand
        if model:
            filters['model'] = model
        if year:
            filters['year_from'] = int(year)
        if price_from:
            filters['price_from'] = float(price_from) * 1000000
        if price_to:
            filters['price_to'] = float(price_to) * 1000000
        if fuel_type:
            filters['fuel_type'] = fuel_type
        if transmission:
            filters['transmission'] = transmission
        if body_type:
            filters['body_type'] = body_type
        if city:
            filters['city'] = city
        
        # Получаем автомобили с текущими фильтрами
        from database import search_all_cars
        cars = search_all_cars(**filters)
        
        # Извлекаем уникальные значения для каждого фильтра
        years = sorted(list(set(car.get('manufacture_year') for car in cars if car.get('manufacture_year'))), reverse=True)
        
        # Получаем оригинальные значения для нормализации
        fuel_types_raw = list(set(car.get('fuel_type') for car in cars if car.get('fuel_type')))
        body_types_raw = list(set(car.get('body_type') for car in cars if car.get('body_type')))
        transmissions_raw = list(set(car.get('gear_box_type') for car in cars if car.get('gear_box_type')))
        
        # Нормализуем значения
        fuel_types = normalize_filter_values(fuel_types_raw, 'fuel_type')
        body_types = normalize_filter_values(body_types_raw, 'body_type')
        transmissions = normalize_filter_values(transmissions_raw, 'gear_box_type')
        
        cities = sorted(list(set(car.get('city') for car in cars if car.get('city'))))
        
        # Извлекаем марки и модели
        brands = sorted(list(set(car.get('mark') for car in cars if car.get('mark'))))
        models = sorted(list(set(car.get('model') for car in cars if car.get('model'))))
        
        # Вычисляем диапазон цен
        prices = [car.get('price') for car in cars if car.get('price')]
        price_range = {}
        if prices:
            min_price = min(prices) / 1000000
            max_price = max(prices) / 1000000
            price_range = {
                'min': round(min_price, 1),
                'max': round(max_price, 1)
            }
        
        return JSONResponse(content={
            "success": True,
            "years": years,
            "fuel_types": fuel_types,
            "body_types": body_types,
            "transmissions": transmissions,
            "cities": cities,
            "brands": brands,
            "models": models,
            "price_range": price_range,
            "total_cars": len(cars)
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения доступных фильтров: {e}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка при получении доступных фильтров",
            "years": [],
            "fuel_types": [],
            "body_types": [],
            "transmissions": [],
            "cities": [],
            "price_range": {},
            "total_cars": 0
        })

@app.post("/api/cars/search")
async def search_cars_with_filters(request: dict = Body(...)):
    """Поиск автомобилей с применением фильтров"""
    try:
        # Логируем входящий запрос
        logger.info(f"🔍 API /api/cars/search получил запрос: {request}")
        
        # Извлекаем фильтры из запроса
        brand = request.get('brand')
        model = request.get('model')
        year_from = request.get('year_from')
        year_to = request.get('year_to')
        price_from = request.get('price_from')
        price_to = request.get('price_to')
        fuel_type = request.get('fuel_type')
        transmission = request.get('transmission')
        body_type = request.get('body_type')
        drive_type = request.get('drive_type')
        city = request.get('city')
        state = request.get('state')
        limit = request.get('limit', 100)  # Ограничиваем результаты
        
        # Логируем извлеченные фильтры
        logger.info(f"🔍 Извлеченные фильтры: brand={brand}, model={model}, year_from={year_from}, "
                   f"price_from={price_from}, price_to={price_to}, fuel_type={fuel_type}, "
                   f"body_type={body_type}, transmission={transmission}, city={city}")
        
        # Используем функцию поиска из database.py
        from database import search_all_cars
        
        cars = search_all_cars(
            brand=brand,
            model=model,
            year_from=year_from,
            year_to=year_to,
            price_from=price_from,
            price_to=price_to,
            fuel_type=fuel_type,
            transmission=transmission,
            body_type=body_type,
            drive_type=drive_type,
            state=state,
            city=city,
            limit=limit
        )
        
        # Логируем результат поиска
        logger.info(f"🔍 Поиск завершен. Найдено автомобилей: {len(cars)}")
        
        # Форматируем результаты
        formatted_cars = []
        for car in cars:
            # Добавляем дополнительные поля для отображения
            car['price_millions'] = round(car.get('price', 0) / 1000000, 1) if car.get('price') else 0
            # Надежно определяем признак подержанного авто: используем флаг из результата БД
            is_used = car.get('is_used')
            if is_used is None:
                is_used = (car.get('state') == 'used')
            car['is_used'] = bool(is_used)
            car['status_text'] = 'Поддержанный' if car['is_used'] else 'Новый'
            formatted_cars.append(car)
        
        return JSONResponse(content={
            "success": True,
            "cars": formatted_cars,
            "total": len(formatted_cars),
            "filters_applied": {
                "brand": brand,
                "model": model,
                "year_from": year_from,
                "year_to": year_to,
                "price_from": price_from,
                "price_to": price_to,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "body_type": body_type,
                "drive_type": drive_type,
                "city": city,
                "state": state
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка поиска автомобилей: {e}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка при поиске автомобилей",
            "cars": []
        })

@app.post("/api/compare")
async def compare_cars(request: CompareRequest):
    user_id = getattr(request, 'user_id', 'default')
    query = f"Сравни автомобили с id {request.car1_id} и {request.car2_id}"
    result = processor.process(query, entities={'car1_id': request.car1_id, 'car2_id': request.car2_id}, user_id=user_id)
    return JSONResponse(content=result)

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    user_id = request.user_id
    query = f"Подбери автомобиль по предпочтениям: {request.preferences or ''} бюджет: {request.budget or ''} назначение: {request.purpose or ''}"
    entities = request.preferences or {}
    if request.budget:
         entities['budget'] = request.budget
    if request.purpose:
        entities['purpose'] = request.purpose
    result = processor.process(query, entities=entities, user_id=user_id)
    return JSONResponse(content=result)

@app.post("/api/test-drive")
async def request_test_drive(request: TestDriveRequest):
    """Запрос на тест-драйв"""
    try:
        car = get_car_by_id(request.car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        columns = [
            "id", "title", "doc_num", "mark", "model", "vin", "color", "price", "city", "manufacture_year", "body_type", "gear_box_type", "driving_gear_type", "engine_vol", "power", "fuel_type", "dealer_center"
        ]
        if isinstance(car, tuple):
            car = dict(zip(columns, car))
        title = car.get('title', '')
        model = car.get('model', '')
        fuel_type = car.get('fuel_type', '')
        dealer = car.get('dealer_center', '')
        return {
            "success": True,
            "message": f"Заявка на тест-драйв {title} {model} принята",
            "details": {
                "car": f"{title} {model} {fuel_type}",
                "dealer": dealer,
                "date": request.preferred_date,
                "time": request.preferred_time,
                "contact": request.contact_phone
            }
        }
    except Exception as e:
        logger.error(f"Ошибка тест-драйва: {e}")
        return {
            "success": False,
            "error": "Ошибка при оформлении тест-драйва"
        }

@app.post("/api/credit")
async def calculate_credit(request: CreditRequest):
    user_id = request.user_id
    query = f"Рассчитай кредит для авто {request.car_id} с первоначальным взносом {request.down_payment}, сроком {request.term_months} мес, доходом {request.monthly_income}"
    entities = {'car_id': request.car_id, 'down_payment': request.down_payment, 'term_months': request.term_months, 'monthly_income': request.monthly_income}
    result = processor.process(query, entities=entities, user_id=user_id)
    return JSONResponse(content=result)

@app.get("/api/statistics")
async def get_statistics():
    """Получение статистики по базе автомобилей"""
    try:
        # Получаем статистику напрямую из базы данных
        from database import search_all_cars
        all_cars = search_all_cars()
        
        # Подсчитываем статистику
        total_cars = len(all_cars)
        
        # Статистика по брендам
        brands = {}
        for car in all_cars:
            brand = car.get('mark', 'Неизвестно')
            brands[brand] = brands.get(brand, 0) + 1
        
        # Статистика по городам
        cities = {}
        for car in all_cars:
            city = car.get('city', 'Неизвестно')
            cities[city] = cities.get(city, 0) + 1
        
        # Статистика по годам
        years = {}
        for car in all_cars:
            year = car.get('manufacture_year', 'Неизвестно')
            years[year] = years.get(year, 0) + 1
        
        # Статистика по типам кузова
        body_types = {}
        for car in all_cars:
            body_type = car.get('body_type', 'Неизвестно')
            body_types[body_type] = body_types.get(body_type, 0) + 1
        
        # Статистика по ценам
        prices = [car.get('price', 0) for car in all_cars if car.get('price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        result = {
            "success": True,
            "statistics": {
                "total_cars": total_cars,
                "brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]),
                "cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]),
                "years": dict(sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]),
                "body_types": dict(sorted(body_types.items(), key=lambda x: x[1], reverse=True)[:10]),
                "price_stats": {
                    "average": round(avg_price, 2),
                    "min": min_price,
                    "max": max_price
                }
            }
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка при получении статистики"
        })

@app.get("/api/dealers")
async def get_dealers():
    """Получение списка дилерских центров"""
    try:
        dealers = execute_query("SELECT * FROM dealer_centers")
        
        dealers_list = []
        for dealer in dealers:
            dealer_dict = {
                "id": dealer[0],
                "name": dealer[1],
                "address": dealer[2],
                "phone": dealer[3],
                "email": dealer[4],
                "website": dealer[5],
                "latitude": dealer[6],
                "longitude": dealer[7],
                "brands": dealer[8]
            }
            dealers_list.append(dealer_dict)
        
        return {
            "success": True,
            "dealers": dealers_list
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения дилеров: {e}")
        return {
            "success": False,
            "error": "Ошибка при получении дилерских центров"
        }

@app.get("/api/brands")
async def get_brands():
    """Получение списка брендов"""
    try:
        brands = execute_query("SELECT DISTINCT mark FROM car UNION SELECT DISTINCT mark FROM used_car ORDER BY mark")
        brands_list = [brand[0] for brand in brands]
        return {
            "success": True,
            "brands": brands_list
        }
    except Exception as e:
        logger.error(f"Ошибка получения брендов: {e}")
        return {
            "success": False,
            "error": "Ошибка при получении брендов"
        }

@app.get("/api/models/{brand}")
async def get_models(brand: str):
    """Получение моделей по бренду"""
    try:
        models = execute_query(
            "SELECT DISTINCT model FROM car WHERE mark = ? UNION SELECT DISTINCT model FROM used_car WHERE mark = ? ORDER BY model",
            [brand, brand]
        )
        models_list = [model[0] for model in models]
        return {
            "success": True,
            "brand": brand,
            "models": models_list
        }
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        return {
            "success": False,
            "error": "Ошибка при получении моделей"
        }

@app.post("/api/fuzzy-search")
async def fuzzy_search_endpoint(request: ChatRequest):
    """Нечеткий поиск по брендам и моделям (car + used_car)"""
    try:
        # Получаем все бренды и модели из обеих таблиц
        all_cars = search_all_cars()
        brands = set(car["mark"] for car in all_cars if car.get("mark"))
        models = set(car["model"] for car in all_cars if car.get("model"))
        # Используем FuzzySearch для поиска по брендам и моделям
        brand_matches = [fuzzy_search.correct_brand(request.message)] if request.message else []
        model_matches = [fuzzy_search.correct_model(request.message)] if request.message else []
        # Также ищем похожие слова среди всех брендов и моделей
        similar_brands = find_similar_words(request.message, list(brands))
        similar_models = find_similar_words(request.message, list(models))
        results = list(set([b for b in brand_matches if b] + [m for m in model_matches if m] + similar_brands + similar_models))
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Ошибка нечеткого поиска: {e}")
        return {
            "success": False,
            "error": f"Ошибка при нечетком поиске: {e}"
        }

@app.get("/api/history")
async def get_user_history(user_id: str):
    """Получение истории пользователя"""
    try:
        history = user_history_manager.get_user_history(user_id)
        return {"success": True, "history": history}
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return {"success": False, "error": f"Ошибка при получении истории: {e}"}

@app.get("/api/preferences")
async def get_user_preferences(user_id: str):
    """Получение предпочтений пользователя"""
    try:
        prefs = user_history_manager.get_preferences(user_id)
        return {"success": True, "preferences": prefs}
    except Exception as e:
        logger.error(f"Ошибка получения предпочтений: {e}")
        return {"success": False, "error": f"Ошибка при получении предпочтений: {e}"}

@app.post("/api/preferences")
async def update_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """Обновление предпочтений пользователя"""
    try:
        user_history_manager.update_preferences(user_id, preferences)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка обновления предпочтений: {e}")
        return {"success": False, "error": f"Ошибка при обновлении предпочтений: {e}"}

@app.get("/api/health")
async def health_check():
    """Проверка состояния системы"""
    try:
        # Проверка базы данных
        db_status = "ok"
        try:
            execute_query("SELECT 1")
        except:
            db_status = "error"
        
        # Проверка ML моделей
        ml_status = "ok" if nlp_processor.intent_classifier else "not_available"
        
        # Проверка диалогового менеджера
        dialog_status = "ok" if dialog_manager else "error"
        
        # Проверка нечеткого поиска
        fuzzy_status = "ok" if fuzzy_search else "error"
        
        return {
            "status": "healthy" if all(s == "ok" for s in [db_status, dialog_status, fuzzy_status]) else "degraded",
            "components": {
                "database": db_status,
                "ml_models": ml_status,
                "dialog_manager": dialog_status,
                "fuzzy_search": fuzzy_status
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/filters")
async def get_user_filters(user_id: str):
    """Получение сохранённых фильтров пользователя"""
    try:
        filters = user_history_manager.get_saved_filters(user_id)
        return {"success": True, "filters": filters}
    except Exception as e:
        logger.error(f"Ошибка получения фильтров: {e}")
        return {"success": False, "error": f"Ошибка при получении фильтров: {e}"}

@app.post("/api/filters/apply")
async def apply_user_filter(request: ApplyFilterRequest = Body(...)):
    """Применение сохранённого фильтра пользователя (по имени или id) и возврат результата через smart_filter_cars"""
    try:
        filters = user_history_manager.get_saved_filters(request.user_id)
        selected = None
        if request.filter_id is not None:
            for idx, f in enumerate(filters):
                if idx == request.filter_id:
                    selected = f
                    break
        elif request.filter_name:
            for f in filters:
                if f['name'] == request.filter_name:
                    selected = f
                    break
        if not selected:
            return {"success": False, "error": "Фильтр не найден"}
        params = selected['params']
        cars, explanation = smart_filter_cars(**params)
        return {
            "success": True,
            "cars": cars,
            "explanation": explanation,
            "filter": selected
        }
    except Exception as e:
        logger.error(f"Ошибка применения фильтра: {e}")
        return {"success": False, "error": f"Ошибка при применении фильтра: {e}"}

@app.post("/api/llama")
async def llama_handler(request: LlamaRequest):
    """Обработка сложных запросов через Llama"""
    try:
        response = generate_with_llama(request.query, request.context or {})
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/llama-feedback")
async def llama_feedback(request: LlamaFeedbackRequest):
    """Сбор обратной связи по Llama-ответу"""
    try:
        system_monitor.log_llama_feedback(
            user_id=request.user_id,
            query=request.query,
            llama_response=request.llama_response,
            quality_score=request.quality_score,
            comment=request.comment or ""
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/voice-message")
async def process_voice_message(request: Request):
    """Обработка голосовых сообщений с локальной транскрипцией через faster-whisper"""
    try:
        # Получаем данные из FormData
        form = await request.form()
        audio_file = form.get("audio")
        duration = form.get("duration", "0")
        user_id = form.get("user_id", "default")
        client_transcription = form.get("transcription", "").strip()

        if not audio_file:
            raise HTTPException(status_code=400, detail="Аудио файл не найден")

        # Создаем папку для голосовых сообщений
        voice_dir = "voice_messages"
        os.makedirs(voice_dir, exist_ok=True)

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{user_id}_{timestamp}.wav"
        filepath = os.path.join(voice_dir, filename)

        # Сохраняем аудио файл
        content = await audio_file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # Транскрипция через faster-whisper
        try:
            from faster_whisper import WhisperModel
            # Выбор модели: small / medium / large-v3 (по ресурсам)
            model_size = os.getenv("WHISPER_MODEL", "small")
            compute_type = os.getenv("WHISPER_COMPUTE", "int8")  # int8/int8_float16/float16
            model = WhisperModel(model_size, device="auto", compute_type=compute_type)

            segments, info = model.transcribe(filepath, language="ru", vad_filter=True)
            transcript_parts = [seg.text for seg in segments]
            server_transcription = (" ".join(transcript_parts)).strip()
        except Exception as tr_err:
            logger.error(f"Ошибка транскрипции faster-whisper: {tr_err}")
            server_transcription = client_transcription  # fallback

        final_transcription = server_transcription or client_transcription or ""

        # Сохраняем информацию о голосовом сообщении в БД
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS voice_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        duration INTEGER NOT NULL,
                        transcription TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO voice_messages (user_id, filename, duration, transcription)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, filename, int(duration or 0), final_transcription),
                )
                conn.commit()
        except Exception as db_error:
            logger.error(f"Ошибка сохранения в БД: {db_error}")

        logger.info(f"Голос сохранен: {filename}, длит.: {duration}с, текст: {final_transcription[:80]}...")

        return JSONResponse(
            content={
                "success": True,
                "filename": filename,
                "duration": int(duration or 0),
                "transcription": final_transcription,
                "message": "Голосовое сообщение успешно обработано"
            }
        )

    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/voice-messages/{user_id}")
async def get_voice_messages(user_id: str):
    """Получение голосовых сообщений пользователя"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Гарантируем наличие таблицы
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS voice_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    transcription TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("""
                SELECT id, filename, duration, transcription, created_at
                FROM voice_messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "filename": row[1],
                    "duration": row[2],
                    "transcription": row[3],
                    "created_at": row[4]
                })
            
            return JSONResponse(content={
                "success": True,
                "messages": messages
            })
            
    except Exception as e:
        logger.error(f"Ошибка получения голосовых сообщений: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/voice-messages/audio/{filename}")
async def get_voice_audio(filename: str):
    """Получение аудио файла голосового сообщения"""
    try:
        voice_dir = "voice_messages"
        filepath = os.path.join(voice_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Аудио файл не найден")
        
        return FileResponse(filepath, media_type="audio/wav")
        
    except Exception as e:
        logger.error(f"Ошибка получения аудио файла: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/report")
async def monitoring_report():
    """Отчёт мониторинга для dashboard (включая llama_feedback)"""
    try:
        report = system_monitor.generate_report()
        return report
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/llama-feedback/trend")
async def llama_feedback_trend(days: int = 14):
    """Динамика среднего балла Llama-ответов по дням"""
    try:
        trend = system_monitor.get_llama_feedback_daily_trend(days)
        return {"trend": trend}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/llama-feedback/comments")
async def llama_feedback_comments(limit: int = 10, period: int = 14, min_score: int = 1):
    """Последние комментарии пользователей к Llama-ответам за период и с минимальной оценкой"""
    try:
        comments = system_monitor.get_llama_feedback_comments(limit, period, min_score)
        return {"comments": comments}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/llama-feedback/alerts")
async def llama_feedback_alerts(days: int = 7, min_avg: float = 3.5, max_bad: int = 3):
    """Проверка качества Llama-ответов и алерты"""
    try:
        alerts = system_monitor.check_llama_quality_alerts(days, min_avg, max_bad)
        return {"alerts": alerts}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/cars")
async def get_recent_cars():
    """
    Получение всех автомобилей (car + used_car) для дашборда и виджетов
    """
    cars = get_recent_cars_from_db(limit=None)
    return {"success": True, "cars": cars}

@app.post("/api/dealer_centers")
async def create_dealer(dealer: DealerCreateRequest):
    try:
        query = ("INSERT INTO dealer_centers (name, address, phone, email, website, latitude, longitude, brands) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        params = [dealer.name, dealer.address, dealer.phone, dealer.email, dealer.website, dealer.latitude, dealer.longitude, dealer.brands]
        execute_query(query, params)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка создания дилера: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/dealer_centers/{dealer_id}")
async def update_dealer(dealer: DealerCreateRequest, dealer_id: int = Path(...)):
    try:
        query = ("UPDATE dealer_centers SET name=?, address=?, phone=?, email=?, website=?, latitude=?, longitude=?, brands=? WHERE id=?")
        params = [dealer.name, dealer.address, dealer.phone, dealer.email, dealer.website, dealer.latitude, dealer.longitude, dealer.brands, dealer_id]
        execute_query(query, params)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка обновления дилера: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/dealers/{dealer_id}")
async def delete_dealer_api(dealer_id: int = Path(...)):
    try:
        execute_query("DELETE FROM dealer_centers WHERE id = ?", [dealer_id])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Новые API endpoints для рекомендаций, аналитики и уведомлений ---

@app.get("/api/recommendations/{user_id}")
async def get_personal_recommendations(user_id: str, limit: int = 5):
    """Получение персональных рекомендаций автомобилей"""
    try:
        recommendations = recommendation_engine.get_car_recommendations(user_id, limit)
        return {"success": True, "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Ошибка получения рекомендаций: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/recommendations/popular")
async def get_popular_cars(limit: int = 10):
    """Получение популярных автомобилей"""
    try:
        popular_cars = recommendation_engine.get_popular_cars(limit)
        return {"success": True, "cars": popular_cars}
    except Exception as e:
        logger.error(f"Ошибка получения популярных автомобилей: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/recommendations/trending")
async def get_trending_brands(days: int = 30):
    """Получение трендовых брендов"""
    try:
        trending_brands = recommendation_engine.get_trending_brands(days)
        return {"success": True, "brands": trending_brands}
    except Exception as e:
        logger.error(f"Ошибка получения трендовых брендов: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/recommendations/similar/{car_id}")
async def get_similar_cars(car_id: int, limit: int = 5):
    """Получение похожих автомобилей"""
    try:
        similar_cars = recommendation_engine.get_similar_cars(car_id, limit)
        return {"success": True, "cars": similar_cars}
    except Exception as e:
        logger.error(f"Ошибка получения похожих автомобилей: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/recommendations/feedback")
async def log_recommendation_feedback(user_id: str, recommendation_id: int, score: int):
    """Логирование обратной связи по рекомендации"""
    try:
        recommendation_engine.log_recommendation_feedback(user_id, recommendation_id, score)
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка логирования обратной связи: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/behavior/{user_id}")
async def get_user_behavior_analysis(user_id: str, days: int = 30):
    """Получение анализа поведения пользователя"""
    try:
        analysis = user_analytics.analyze_user_behavior(user_id, days)
        return {"success": True, "analysis": analysis}
    except Exception as e:
        logger.error(f"Ошибка анализа поведения: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/insights/{user_id}")
async def get_user_insights(user_id: str):
    """Получение инсайтов о поведении пользователя"""
    try:
        insights = user_analytics.get_behavior_insights(user_id)
        return {"success": True, "insights": insights}
    except Exception as e:
        logger.error(f"Ошибка получения инсайтов: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/segments")
async def get_user_segments():
    """Получение сегментов пользователей"""
    try:
        segments = user_analytics.get_user_segments()
        return {"success": True, "segments": segments}
    except Exception as e:
        logger.error(f"Ошибка получения сегментов: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/recommendations-insights/{user_id}")
async def get_recommendations_insights(user_id: str):
    """Получение инсайтов для улучшения рекомендаций"""
    try:
        insights = user_analytics.get_user_recommendations_insights(user_id)
        return {"success": True, "insights": insights}
    except Exception as e:
        logger.error(f"Ошибка получения инсайтов рекомендаций: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/notifications/{user_id}")
async def get_user_notifications(user_id: str, limit: int = 20, unread_only: bool = False):
    """Получение уведомлений пользователя"""
    try:
        notifications = notification_system.get_user_notifications(user_id, limit, unread_only)
        return {"success": True, "notifications": notifications}
    except Exception as e:
        logger.error(f"Ошибка получения уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/notifications/count/{user_id}")
async def get_notification_count(user_id: str, unread_only: bool = True):
    """Получение количества уведомлений"""
    try:
        count = notification_system.get_notification_count(user_id, unread_only)
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"Ошибка подсчета уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/notifications/mark-read/{notification_id}")
async def mark_notification_read(notification_id: int, user_id: str):
    """Отметка уведомления как прочитанного"""
    try:
        success = notification_system.mark_notification_read(notification_id, user_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Ошибка отметки уведомления: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/notifications/mark-all-read/{user_id}")
async def mark_all_notifications_read(user_id: str):
    """Отметка всех уведомлений как прочитанных"""
    try:
        success = notification_system.mark_all_notifications_read(user_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Ошибка отметки всех уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/notifications/{notification_id}")
async def delete_notification(notification_id: int, user_id: str):
    """Удаление уведомления"""
    try:
        success = notification_system.delete_notification(notification_id, user_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Ошибка удаления уведомления: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/notifications/create")
async def create_notification(request: NotificationRequest):
    """Создание нового уведомления"""
    try:
        expires_at = None
        if request.expires_at:
            expires_at = datetime.fromisoformat(request.expires_at)
            
        notification_id = notification_system.create_notification(
            user_id=request.user_id,
            notification_type=request.notification_type,
            title=request.title,
            message=request.message,
            priority=request.priority,
            action_url=request.action_url or None,
            action_text=request.action_text or None,
            expires_at=expires_at,
            metadata=request.metadata or {}
        )
        return {"success": True, "notification_id": notification_id}
    except Exception as e:
        logger.error(f"Ошибка создания уведомления: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/notifications/settings/{user_id}")
async def get_notification_settings(user_id: str):
    """Получение настроек уведомлений пользователя"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_notifications, push_notifications, recommendation_notifications,
                       system_alerts, promotion_notifications, notification_frequency,
                       quiet_hours_start, quiet_hours_end
                FROM notification_settings
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "success": True,
                    "settings": {
                        "email_notifications": bool(row[0]),
                        "push_notifications": bool(row[1]),
                        "recommendation_notifications": bool(row[2]),
                        "system_alerts": bool(row[3]),
                        "promotion_notifications": bool(row[4]),
                        "notification_frequency": row[5],
                        "quiet_hours_start": row[6],
                        "quiet_hours_end": row[7]
                    }
                }
            else:
                # Возвращаем настройки по умолчанию
                return {
                    "success": True,
                    "settings": {
                        "email_notifications": True,
                        "push_notifications": True,
                        "recommendation_notifications": True,
                        "system_alerts": True,
                        "promotion_notifications": True,
                        "notification_frequency": "daily",
                        "quiet_hours_start": "22:00",
                        "quiet_hours_end": "08:00"
                    }
                }
    except Exception as e:
        logger.error(f"Ошибка получения настроек уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/notifications/settings")
async def update_notification_settings(request: NotificationSettingsRequest):
    """Обновление настроек уведомлений пользователя"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO notification_settings 
                (user_id, email_notifications, push_notifications, recommendation_notifications,
                 system_alerts, promotion_notifications, notification_frequency,
                 quiet_hours_start, quiet_hours_end, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                request.user_id, request.email_notifications, request.push_notifications,
                request.recommendation_notifications, request.system_alerts,
                request.promotion_notifications, request.notification_frequency,
                request.quiet_hours_start, request.quiet_hours_end
            ))
            conn.commit()
            return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка обновления настроек уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/alerts")
async def get_active_alerts(severity: Optional[str] = None):
    """Получение активных системных алертов"""
    try:
        alerts = notification_system.get_active_alerts(severity)
        return {"success": True, "alerts": alerts}
    except Exception as e:
        logger.error(f"Ошибка получения алертов: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/alerts/resolve/{alert_id}")
async def resolve_alert(alert_id: int, resolved_by: Optional[str] = None):
    """Разрешение системного алерта"""
    try:
        success = notification_system.resolve_alert(alert_id, resolved_by)
        return {"success": success}
    except Exception as e:
        logger.error(f"Ошибка разрешения алерта: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/alerts/create")
async def create_system_alert(request: SystemAlertRequest):
    """Создание системного алерта"""
    try:
        alert_id = notification_system.create_system_alert(
            alert_type=request.alert_type,
            severity=request.severity,
            title=request.title,
            description=request.description,
            metadata=request.metadata or {}
        )
        return {"success": True, "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Ошибка создания алерта: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/notifications/statistics")
async def get_notification_statistics(days: int = 30):
    """Получение статистики уведомлений"""
    try:
        stats = notification_system.get_notification_statistics(days)
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Ошибка получения статистики уведомлений: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/notifications/check-alerts")
async def check_and_create_alerts():
    """Проверка системы и создание алертов"""
    try:
        notification_system.check_and_create_alerts()
        return {"success": True, "message": "Проверка алертов завершена"}
    except Exception as e:
        logger.error(f"Ошибка проверки алертов: {e}")
        return {"success": False, "error": str(e)}

# --- CSRF ---
CSRF_TOKENS = set()

@app.get('/api/csrf-token')
async def get_csrf_token():
    token = secrets.token_urlsafe(32)
    CSRF_TOKENS.add(token)
    return {"token": token}

@app.middleware('http')
async def csrf_protect(request: Request, call_next):
    # Временно отключаем CSRF защиту для тестирования
    # if request.method in ('POST', 'PUT', 'DELETE'):
    #     token = request.headers.get('X-CSRF-Token')
    #     if not token or token not in CSRF_TOKENS:
    #         return JSONResponse(status_code=403, content={"detail": "CSRF token missing or invalid"})
    response = await call_next(request)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[ERROR] {tb}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "traceback": tb}
    )

@app.get("/api/quick-scenarios")
async def api_get_quick_scenarios():
    try:
        scenarios = get_all_quick_scenarios()
        from database import get_all_brands_cached, get_all_cities, get_all_models, execute_query
        brands = get_all_brands_cached()
        cities = get_all_cities()
        models = get_all_models()
        top_brands = brands[:3] if brands else []
        top_cities = cities[:3] if cities else []
        electric_count_result = execute_query("SELECT COUNT(*) FROM car WHERE fuel_type LIKE '%электро%' OR fuel_type LIKE '%electric%'")
        electric_count = electric_count_result[0][0] if electric_count_result else 0
        dealers = execute_query("SELECT DISTINCT dealer_center FROM car WHERE dealer_center IS NOT NULL AND dealer_center != ''")
        dynamic = []
        # Электромобили в Москве
        if electric_count > 0 and any(city.lower() == 'москва' for city in cities):
            dynamic.append({
                "title": "Электромобиль в Москве до 3 млн",
                "icon": "⚡",
                "query": "Электромобиль в Москве до 3 млн"
            })
        # Сравнение топ-брендов
        if len(top_brands) >= 2:
            dynamic.append({
                "title": f"Сравнить {top_brands[0]} и {top_brands[1]}",
                "icon": "⚖️",
                "query": f"Сравнить {top_brands[0]} и {top_brands[1]}"
            })
        # Дилер рядом
        if dealers and dealers[0][0]:
            dynamic.append({
                "title": f"Дилер {dealers[0][0]} рядом",
                "icon": "📍",
                "query": f"Дилер {dealers[0][0]} рядом"
            })
        # Для семьи с детьми
        if any('семья' in m.lower() for m in models):
            dynamic.append({
                "title": "Для семьи с детьми",
                "icon": "👨‍👩‍👧‍👦",
                "query": "Автомобиль для семьи с детьми"
            })
        # Дизельные SUV 2023 (только если есть такие авто)
        diesel_suv_count = execute_query("SELECT COUNT(*) FROM car WHERE (body_type LIKE '%SUV%' OR body_type LIKE '%внедорожник%') AND fuel_type LIKE '%дизель%' AND manufacture_year=2023")
        if diesel_suv_count and diesel_suv_count[0][0] > 0:
            dynamic.append({
                "title": "Дизельные SUV 2023",
                "icon": "🚙",
                "query": "Дизельный SUV 2023"
            })
        # Кредит на Camry (только если есть Camry)
        if any('camry' in m.lower() for m in models):
            dynamic.append({
                "title": "Кредит на Camry",
                "icon": "🧾",
                "query": "Кредит на Camry"
            })
        all_titles = set((s['title'], s['query']) for s in scenarios)
        for d in dynamic:
            if (d['title'], d['query']) not in all_titles:
                scenarios.append(d)
        return {"success": True, "scenarios": scenarios}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/quick-scenarios")
async def api_add_quick_scenario(data: dict = Body(...)):
    try:
        title = data.get("title")
        icon = data.get("icon", "")
        query = data.get("query")
        if not title or not query:
            return {"success": False, "error": "title и query обязательны"}
        scenario_id = add_quick_scenario(title, icon, query)
        return {"success": True, "id": scenario_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/quick-scenarios/{scenario_id}")
async def api_update_quick_scenario(scenario_id: int, data: dict = Body(...)):
    try:
        title = data.get("title")
        icon = data.get("icon", "")
        query = data.get("query")
        if not title or not query:
            return {"success": False, "error": "title и query обязательны"}
        ok = update_quick_scenario(scenario_id, title, icon, query)
        return {"success": ok}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/quick-scenarios/{scenario_id}")
async def api_delete_quick_scenario(scenario_id: int):
    try:
        ok = delete_quick_scenario(scenario_id)
        return {"success": ok}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/cars/{car_id}")
async def get_car(car_id: int):
    """Получение автомобиля по ID (car или used_car)"""
    car = get_car_by_id(car_id)
    if car:
        return {"success": True, "car": car}
    return {"success": False, "error": "Автомобиль не найден"}

@app.put("/api/cars/{car_id}")
async def update_car(car_id: int, car: CarCreateRequest):
    """Обновление автомобиля по ID (car или used_car по state)"""
    try:
        table = 'car' if car.state == 'new' else 'used_car'
        columns = [
            'mark', 'model', 'price', 'city', 'manufacture_year', 'fuel_type',
            'body_type', 'gear_box_type', 'driving_gear_type', 'dealer_center', 'mileage'
        ]
        values = [
            car.mark, car.model, car.price, car.city, car.manufacture_year, car.fuel_type,
            car.body_type, car.gear_box_type, car.driving_gear_type, car.dealer_center, car.mileage
        ]
        # Для новых авто mileage не обязателен
        if table == 'car':
            columns = columns[:-1]
            values = values[:-1]
        set_clause = ', '.join([f"{col}=?" for col in columns])
        query = f"UPDATE {table} SET {set_clause} WHERE id=?"
        execute_query(query, values + [car_id])
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка обновления автомобиля: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/cars/{car_id}")
async def delete_car(car_id: int):
    """Удаление автомобиля по ID (car и used_car)"""
    try:
        execute_query("DELETE FROM car WHERE id=?", [car_id])
        execute_query("DELETE FROM used_car WHERE id=?", [car_id])
        return {"success": True}
    except Exception as e:
        logger.error(f"Ошибка удаления автомобиля: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/users/analytics")
async def get_users_analytics():
    """Аналитика пользователей для дашборда"""
    try:
        from user_analytics import UserAnalytics
        analytics = UserAnalytics()
        with get_db() as conn:
            cursor = conn.cursor()
            # Всего пользователей
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_history WHERE user_id IS NOT NULL AND user_id != ''")
            total_users = cursor.fetchone()[0] or 0
            # Активные сессии за сегодня
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM user_sessions WHERE start_time >= date('now')")
            active_sessions = cursor.fetchone()[0] or 0
            # Новые пользователи за неделю
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_history WHERE date(timestamp) >= date('now', '-7 days')")
            new_users = cursor.fetchone()[0] or 0
            # Среднее время сессии (минуты)
            cursor.execute("SELECT AVG(avg_session_duration) FROM user_sessions WHERE avg_session_duration > 0")
            avg_session_time = round(cursor.fetchone()[0] or 0, 1)
        return {
            "total_users": total_users,
            "active_sessions": active_sessions,
            "new_users": new_users,
            "avg_session_time": f"{avg_session_time} мин"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/cities")
async def get_cities(with_stats: int = 0):
    try:
        if with_stats:
            from database import get_cities_with_stats
            return {"cities": get_cities_with_stats()}
        cities_car = get_all_cities(used=False)
        cities_used = get_all_cities(used=True)
        cities = sorted(set(cities_car + cities_used))
        return {"cities": cities}
    except Exception as e:
        return {"cities": [], "error": str(e)}

@app.get("/api/cities/with-stats")
async def get_cities_with_stats_api():
    try:
        from database import get_cities_with_stats
        return {"cities": get_cities_with_stats()}
    except Exception as e:
        return {"cities": [], "error": str(e)}

@app.route('/api/cars/bulk-delete', methods=['POST'])
def bulk_delete_cars():
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return {'success': False, 'error': 'No ids provided'}, 400
    try:
        from database import delete_cars_by_ids
        deleted = delete_cars_by_ids(ids)
        return {'success': True, 'deleted': deleted}
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.get("/api/options")
async def get_options():
    """
    Получение всех уникальных опций (code, description)
    """
    try:
        options = get_all_options()
        return {"success": True, "options": options}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/dealers/{dealer_id}")
async def get_dealer(dealer_id: int = Path(...)):
    try:
        dealer = execute_query("SELECT * FROM dealer_centers WHERE id = ?", [dealer_id])
        if dealer:
            d = dealer[0]
            dealer_dict = {
                "id": d[0],
                "name": d[1],
                "address": d[2],
                "phone": d[3],
                "email": d[4],
                "website": d[5],
                "latitude": d[6],
                "longitude": d[7],
                "brands": d[8]
            }
            return {"success": True, "dealer": dealer_dict}
        return {"success": False, "error": "Дилер не найден"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/dealers/{dealer_id}")
async def delete_dealer(dealer_id: int = Path(...)):
    try:
        execute_query("DELETE FROM dealer_centers WHERE id = ?", [dealer_id])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/dealers")
async def add_dealer(data: dict = Body(...)):
    try:
        name = data.get("name")
        address = data.get("address")
        phone = data.get("phone")
        email = data.get("email")
        website = data.get("website")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        brands = data.get("brands")
        execute_query(
            "INSERT INTO dealer_centers (name, address, phone, email, website, latitude, longitude, brands) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [name, address, phone, email, website, latitude, longitude, brands]
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/settings")
async def save_settings(data: dict = Body(...)):
    try:
        # Пример: сохраняем настройки в файл settings.json
        with open("settings.json", "w", encoding="utf-8") as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/analytics")
async def get_analytics():
    try:
        car_count = execute_query("SELECT COUNT(*) FROM car")[0][0]
        used_car_count = execute_query("SELECT COUNT(*) FROM used_car")[0][0]
        dealer_count = execute_query("SELECT COUNT(*) FROM dealer_centers")[0][0]
        # Количество пользователей: если есть таблица user_history
        try:
            user_count = execute_query("SELECT COUNT(DISTINCT user_id) FROM user_history WHERE user_id IS NOT NULL AND user_id != ''")[0][0]
        except:
            user_count = 0
        return {
            "cars": car_count + used_car_count,
            "dealers": dealer_count,
            "users": user_count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/body_types")
async def get_body_types():
    try:
        from database import get_all_unique_values
        original_values = get_all_unique_values()
        types = normalize_filter_values(original_values.get('body_type', []), 'body_type')
        return {"body_types": types}
    except Exception as e:
        logger.error(f"Ошибка получения типов кузова: {e}")
        return {"body_types": []}

# Функция для нормализации значений фильтров
def normalize_filter_values(field_values, field_type):
    """
    Нормализует значения фильтров, объединяя дубликаты с разным регистром
    и выбирая наиболее подходящий вариант для отображения
    """
    if not field_values:
        return []
    
    # Словарь для объединения значений с разным регистром
    value_mapping = {
        'fuel_type': {
            'бензин': 'Бензин',
            'Бензин': 'Бензин',
            'дизель': 'Дизель', 
            'Дизель': 'Дизель',
            'гибрид': 'Гибрид',
            'Гибрид': 'Гибрид',
            'электрический': 'Электрический',
            'Электрический': 'Электрический'
        },
        'gear_box_type': {
            'автомат': 'Автомат',
            'Автомат': 'Автомат',
            'механика': 'Механика',
            'Механика': 'Механика'
        },
        'driving_gear_type': {
            'передний': 'Передний',
            'Передний': 'Передний',
            'задний': 'Задний',
            'Задний': 'Задний',
            'полный': 'Полный',
            'Полный': 'Полный'
        },
        'body_type': {
            'внедорожник': 'Внедорожник',
            'Внедорожник': 'Внедорожник',
            'кроссовер': 'Кроссовер',
            'Кроссовер': 'Кроссовер',
            'седан': 'Седан',
            'Седан': 'Седан',
            'универсал': 'Универсал',
            'Универсал': 'Универсал',
            'хетчбэк': 'Хетчбэк',
            'Хетчбэк': 'Хетчбэк',
            'пикап': 'Пикап',
            'Пикап': 'Пикап',
            'минивэн': 'Минивэн',
            'Минивэн': 'Минивэн',
            'микроавтобус': 'Микроавтобус',
            'Микроавтобус': 'Микроавтобус',
            'фургон': 'Фургон',
            'Фургон': 'Фургон',
            'купе': 'Купе',
            'Купе': 'Купе',
            'лифтбэк': 'Лифтбэк',
            'Лифтбэк': 'Лифтбэк'
        }
    }
    
    # Получаем маппинг для данного типа поля
    mapping = value_mapping.get(field_type, {})
    
    # Нормализуем значения
    normalized = {}
    for value in field_values:
        if value:
            # Ищем нормализованное значение в маппинге
            normalized_value = mapping.get(value, value.capitalize())
            normalized[normalized_value] = True
    
    # Возвращаем отсортированный список нормализованных значений
    return sorted(normalized.keys())

@app.get("/api/fuel_types")
async def get_fuel_types():
    try:
        from database import get_all_unique_values
        original_values = get_all_unique_values()
        types = normalize_filter_values(original_values.get('fuel_type', []), 'fuel_type')
        return {"fuel_types": types}
    except Exception as e:
        logger.error(f"Ошибка получения типов топлива: {e}")
        return {"fuel_types": []}

@app.get("/api/gear_box_types")
async def get_gear_box_types():
    try:
        from database import get_all_unique_values
        original_values = get_all_unique_values()
        types = normalize_filter_values(original_values.get('gear_box_type', []), 'gear_box_type')
        return {"gear_box_types": types}
    except Exception as e:
        logger.error(f"Ошибка получения типов трансмиссии: {e}")
        return {"gear_box_types": []}

@app.get("/api/driving_gear_types")
async def get_driving_gear_types():
    try:
        from database import get_all_unique_values
        original_values = get_all_unique_values()
        types = normalize_filter_values(original_values.get('driving_gear_type', []), 'driving_gear_type')
        return {"driving_gear_types": types}
    except Exception as e:
        logger.error(f"Ошибка получения типов привода: {e}")
        return {"driving_gear_types": []}

@app.get("/api/years")
async def get_years():
    import sqlite3
    DB_PATH = 'instance/cars.db'
    years = set()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table in ['car', 'used_car']:
        try:
            cursor.execute(f'SELECT DISTINCT manufacture_year FROM {table}')
            for row in cursor.fetchall():
                if row[0]:
                    years.add(int(row[0]))
        except Exception:
            pass
    conn.close()
    return {"years": sorted(years, reverse=True)}

@app.get("/api/cars/{car_id}/details")
async def get_car_details(car_id: int, used: Optional[bool] = None):
    """Получить детальную информацию о машине с опциями и фотографиями"""
    print(f"🔍 API: get_car_details called with car_id: {car_id}, used: {used}")
    try:
        # Если явно указан used, ищем только в одной таблице
        if used is not None:
            if used:
                car_query = "SELECT *, 'used' as source FROM used_car WHERE id = ?"
                car_result = execute_query(car_query, [car_id])
                is_used = True
            else:
                car_query = "SELECT *, 'new' as source FROM car WHERE id = ?"
                car_result = execute_query(car_query, [car_id])
                is_used = False
            if not car_result:
                raise HTTPException(status_code=404, detail="Автомобиль не найден")
            car = dict(car_result[0])
            print(f"🔍 API: Found car in {'used' if used else 'new'} table: {car.get('mark', 'Unknown')} {car.get('model', 'Unknown')} {car.get('manufacture_year', 'Unknown')}")
        else:
            # Старое поведение: ищем в обеих таблицах
            car_query = "SELECT *, 'new' as source FROM car WHERE id = ?"
            used_car_query = "SELECT *, 'used' as source FROM used_car WHERE id = ?"
            car_result = execute_query(car_query, [car_id])
            used_car_result = execute_query(used_car_query, [car_id])
            
            print(f"🔍 API: Search results - car table: {len(car_result) if car_result else 0}, used_car table: {len(used_car_result) if used_car_result else 0}")
            
            if car_result and used_car_result:
                car_data = dict(car_result[0])
                used_car_data = dict(used_car_result[0])
                
                print(f"🔍 API: Car from 'car' table: {car_data.get('mark', 'Unknown')} {car_data.get('model', 'Unknown')} {car_data.get('manufacture_year', 'Unknown')}")
                print(f"🔍 API: Car from 'used_car' table: {used_car_data.get('mark', 'Unknown')} {used_car_data.get('model', 'Unknown')} {used_car_data.get('manufacture_year', 'Unknown')}")
                
                # Проверяем наличие специфичных полей для подержанных автомобилей
                has_used_specific_fields = (
                    used_car_data.get('wheel_type') or 
                    used_car_data.get('owners_count') or 
                    used_car_data.get('accident') or
                    used_car_data.get('mileage')
                )
                
                print(f"🔍 API: Has used specific fields: {has_used_specific_fields}")
                
                # НОВАЯ ЛОГИКА: Если явно указан used параметр, используем его
                if used is not None:
                    if used:
                        car = used_car_data
                        is_used = True
                        print(f"🔍 API: Selected used car (explicit used=True)")
                    else:
                        car = car_data
                        is_used = False
                        print(f"🔍 API: Selected new car (explicit used=False)")
                else:
                    # УЛУЧШЕННАЯ ЛОГИКА: Проверяем, какая запись больше соответствует запросу
                    # Если в used_car есть специфичные поля для подержанных автомобилей
                    if has_used_specific_fields:
                        car = used_car_data
                        is_used = True
                        print(f"🔍 API: Selected used car (has specific fields)")
                    else:
                        # Если нет специфичных полей, выбираем на основе марки и модели
                        # Приоритет отдаем той записи, которая больше соответствует поисковому запросу
                        car = car_data
                        is_used = False
                        print(f"🔍 API: Selected new car (no specific fields, default to new)")
            elif car_result:
                car = dict(car_result[0])
                is_used = False
                print(f"🔍 API: Found only in car table: {car.get('mark', 'Unknown')} {car.get('model', 'Unknown')} {car.get('manufacture_year', 'Unknown')}")
            elif used_car_result:
                car = dict(used_car_result[0])
                is_used = True
                print(f"🔍 API: Found only in used_car table: {car.get('mark', 'Unknown')} {car.get('model', 'Unknown')} {car.get('manufacture_year', 'Unknown')}")
            else:
                raise HTTPException(status_code=404, detail="Автомобиль не найден")
        
        # Получаем опции
        try:
            # Пробуем сначала с options_group_id и seqno
            options_query = "SELECT * FROM option WHERE car_id = ? ORDER BY options_group_id, seqno"
            try:
                options_result = execute_query(options_query, [car_id])
            except Exception as e:
                # Если ошибка из-за отсутствия seqno, пробуем без него
                if 'no such column: seqno' in str(e):
                    options_query = "SELECT * FROM option WHERE car_id = ? ORDER BY options_group_id"
                    options_result = execute_query(options_query, [car_id])
                else:
                    raise
            options = [dict(opt) for opt in options_result] if options_result else []
        except Exception as e:
            logger.error(f"Ошибка при получении опций: {e}")
            options = []
        
        # Получаем группы опций
        try:
            option_groups_query = "SELECT * FROM option_group ORDER BY id"
            option_groups_result = execute_query(option_groups_query)
            option_groups = [dict(group) for group in option_groups_result] if option_groups_result else []
        except Exception as e:
            logger.error(f"Ошибка при получении групп опций: {e}")
            # Создаем пустые группы опций если таблица не существует
            option_groups = []
        
        # Группируем опции по группам
        grouped_options = {}
        for option in options:
            group_id = option.get('options_group_id', 0)
            if group_id not in grouped_options:
                grouped_options[group_id] = []
            grouped_options[group_id].append(option)
        
        # Получаем фотографии
        try:
            if is_used:
                pictures_query = "SELECT * FROM used_car_picture WHERE used_car_id = ? ORDER BY seqno"
            else:
                pictures_query = "SELECT * FROM picture WHERE car_id = ? ORDER BY seqno"
            
            try:
                pictures_result = execute_query(pictures_query, [car_id])
            except Exception as e:
                # Если ошибка из-за отсутствия seqno, пробуем без него
                if 'no such column: seqno' in str(e):
                    if is_used:
                        pictures_query = "SELECT * FROM used_car_picture WHERE used_car_id = ?"
                    else:
                        pictures_query = "SELECT * FROM picture WHERE car_id = ?"
                    pictures_result = execute_query(pictures_query, [car_id])
                else:
                    raise
            
            pictures = [dict(pic) for pic in pictures_result] if pictures_result else []
        except Exception as e:
            logger.error(f"Ошибка при получении фотографий: {e}")
            pictures = []
        
        # Формируем характеристики автомобиля
        characteristics = {}
        
        # Основные характеристики
        basic_fields = [
            'mark', 'model', 'manufacture_year', 'price', 'city', 'color', 
            'fuel_type', 'power', 'body_type', 'gear_box_type', 'driving_gear_type', 
            'engine_vol', 'dealer_center', 'vin', 'doc_num', 'title'
        ]
        
        for field in basic_fields:
            if field in car and car[field] is not None:
                characteristics[field] = car[field]
        
        # Дополнительные характеристики (только для новых автомобилей)
        if not is_used:
            additional_fields = [
                'stock_qty', 'code_compl', 'interior_color', 'engine', 'door_qty',
                'pts_colour', 'model_year', 'fuel_consumption_mixed', 'max_torque',
                'acceleration_0_100', 'max_speed', 'eco_class', 'dimensions', 'weight',
                'cargo_volume', 'compl_level', 'interior_code', 'color_code',
                'car_order_int_status', 'sale_price', 'max_additional_discount',
                'max_discount_trade_in', 'max_discount_credit', 'max_discount_casko',
                'max_discount_extra_gear', 'max_discount_life_insurance'
            ]
            
            for field in additional_fields:
                if field in car and car[field] is not None:
                    characteristics[field] = car[field]
        else:
            # Для подержанных автомобилей
            used_fields = ['mileage', 'date_begin', 'date_end', 'ad_status', 'allow_email', 'wheel_type', 'owners_count', 'accident']
            for field in used_fields:
                if field in car and car[field] is not None:
                    characteristics[field] = car[field]
        
        # Формируем ответ
        result = {
            "car": car,
            "is_used": is_used,
            "characteristics": characteristics,
            "options": {
                "groups": option_groups,
                "items": grouped_options
            },
            "pictures": pictures
        }
        
        print(f"🔍 API: Returning car data for ID {car_id}: {car.get('mark', 'Unknown')} {car.get('model', 'Unknown')} {car.get('manufacture_year', 'Unknown')}")
        print(f"🔍 API: is_used: {is_used}")
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Ошибка при получении деталей машины {car_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# --- API endpoints для парсинга автомобилей ---

@app.post("/api/car/parse", response_model=CarParseResponse)
async def parse_car_by_price(request: CarParseRequest):
    """Найти автомобиль по цене на сайте aaa-motors.ru"""
    try:
        logger.info(f"Запрос на парсинг: {request.brand} {request.model} за {request.price} руб, город: {request.city}")
        car_data = {
            'mark': request.brand,
            'model': request.model,
            'city': request.city or ''
        }
        base_url = car_parser.generate_car_link(car_data)
        if not base_url:
            return CarParseResponse(
                success=False,
                error=f"Не удалось сгенерировать ссылку для {request.brand} {request.model}"
            )
        result = car_parser.find_car_by_price(
            base_url=base_url,
            target_price=request.price,
            target_brand=request.brand,
            target_model=request.model,
            tolerance=request.tolerance or 0.1
        )
        if result:
            if 'url' in result:
                return CarParseResponse(
                    success=True,
                    url=result['url'],
                    brand=result['brand'],
                    model=result['model'],
                    price=result['price'],
                    found_price=result['found_price'],
                    price_difference=result['price_difference'],
                    title=result.get('title'),
                    tech_info=result.get('tech_info'),
                    status=result.get('status'),
                    address=result.get('address'),
                    img_url=result.get('img_url'),
                    region=result.get('region')
                )
            elif 'url_catalog_fallback' in result:
                return CarParseResponse(
                    success=False,
                    url=None,
                    url_catalog_fallback=result['url_catalog_fallback'],
                    error=f"Автомобиль не найден по цене, но есть fallback-URL каталога"
                )
        else:
            return CarParseResponse(
                success=False,
                error=f"Автомобиль {request.brand} {request.model} с ценой {request.price} руб не найден"
            )
    except Exception as e:
        logger.error(f"Ошибка при парсинге автомобиля: {e}")
        return CarParseResponse(
            success=False,
            error=f"Внутренняя ошибка сервера: {str(e)}"
        )

@app.post("/api/car/link")
async def generate_car_link(request: CarLinkRequest):
    """Сгенерировать ссылку на каталог автомобилей"""
    try:
        logger.info(f"Запрос на генерацию ссылки: {request.brand} {request.model} {request.city}")
        car_data = {
            'mark': request.brand,
            'model': request.model,
            'city': request.city or ''
        }
        url = car_parser.generate_car_link(car_data)
        if url:
            return {
                "success": True,
                "url": url,
                "brand": request.brand,
                "model": request.model
            }
        else:
            return {
                "success": False,
                "error": f"Не удалось сгенерировать ссылку для {request.brand} {request.model}"
            }
    except Exception as e:
        logger.error(f"Ошибка при генерации ссылки: {e}")
        return {
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }

@app.get("/api/car/parse/{car_id}")
async def parse_car_from_database(car_id: int):
    """Найти автомобиль из базы данных на сайте aaa-motors.ru"""
    try:
        # Получаем информацию об автомобиле из базы
        car = get_car_by_id(car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Автомобиль не найден в базе данных")
        
        logger.info(f"Парсинг автомобиля из БД: {car['mark']} {car['model']} за {car['price']} руб")
        
        # Генерируем ссылку
        base_url = car_parser.generate_car_link(car)
        if not base_url:
            return {
                "success": False,
                "error": f"Не удалось сгенерировать ссылку для {car['mark']} {car['model']}"
            }
        
        # Ищем автомобиль по цене
        result = car_parser.find_car_by_price(
            base_url=base_url,
            target_price=int(car['price']),
            target_brand=car['mark'],
            target_model=car['model'],
            tolerance=0.1
        )
        
        if result:
            return {
                "success": True,
                "car_id": car_id,
                "database_car": car,
                "external_car": result
            }
        else:
            return {
                "success": False,
                "error": f"Автомобиль {car['mark']} {car['model']} с ценой {car['price']} руб не найден на сайте",
                "database_car": car,
                "generated_url": base_url
            }
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге автомобиля из БД: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")



@app.post("/api/cars/show-more-in-message")
async def show_more_cars_in_message(request: dict = Body(...)):
    """Показать дополнительные автомобили в том же сообщении"""
    try:
        brand = request.get('brand', '')
        model = request.get('model', '')
        offset = request.get('offset', 0)
        total_count = request.get('total_count', 0)
        message_index = request.get('message_index', 'index_new')
        
        # Ищем автомобили в базе данных
        cars = search_all_cars(brand=brand if brand else None, model=model if model else None)
        
        if not cars:
            return {
                "success": False,
                "message": "Автомобили не найдены",
                "cars": []
            }
        
        # Определяем, сколько автомобилей показывать
        cars_per_page = 5
        start_index = offset
        end_index = min(start_index + cars_per_page, len(cars))
        
        # Получаем подмножество автомобилей
        cars_to_show = cars[start_index:end_index]
        
        # Форматируем HTML для дополнительных автомобилей
        additional_cars_html = ""
        for i, car in enumerate(cars_to_show, start_index + 1):
            brand = car.get('mark', '')
            model = car.get('model', '')
            year = car.get('manufacture_year', '')
            price = car.get('price', 0)
            city = car.get('city', '')
            car_id = car.get('id', i)
            body_type = car.get('body_type', '')
            fuel_type = car.get('fuel_type', '')
            power = car.get('power', '')
            gear_box = car.get('gear_box_type', '')
            
            additional_cars_html += f"### <span class=\"car-link\" onclick=\"showCarDetails({car_id})\">{i}. {brand} {model} ({year})</span>\n"
            additional_cars_html += f"💰 **Цена:** {price:,.0f} ₽\n"
            if city:
                additional_cars_html += f"📍 **Город:** {city}\n"
            if body_type:
                additional_cars_html += f"🚙 **Кузов:** {body_type}\n"
            if fuel_type:
                additional_cars_html += f"⛽ **Топливо:** {fuel_type}\n"
            if power:
                additional_cars_html += f"💪 **Мощность:** {power}\n"
            if gear_box:
                additional_cars_html += f"⚙️ **Коробка:** {gear_box}\n"
            additional_cars_html += "\n"
        
        # Проверяем, есть ли еще автомобили для показа
        has_more = end_index < len(cars)
        next_offset = end_index if has_more else None
        
        return {
            "success": True,
            "additional_cars_html": additional_cars_html,
            "has_more": has_more,
            "next_offset": next_offset,
            "total_shown": end_index,
            "total_count": len(cars),
            "message_index": message_index
        }
        
    except Exception as e:
        logger.error(f"Ошибка при показе дополнительных автомобилей: {str(e)}")
        return {
            "success": False,
            "message": f"Ошибка: {str(e)}",
            "cars": []
        }

@app.get("/api/mileage_ranges")
async def get_mileage_ranges():
    """Получение популярных диапазонов пробега"""
    try:
        # Получаем статистику пробега из used_car
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN mileage <= 20000 THEN 'до 20 тыс км'
                        WHEN mileage <= 50000 THEN '20-50 тыс км'
                        WHEN mileage <= 100000 THEN '50-100 тыс км'
                        WHEN mileage <= 200000 THEN '100-200 тыс км'
                        ELSE 'более 200 тыс км'
                    END as range,
                    COUNT(*) as count
                FROM used_car 
                WHERE mileage IS NOT NULL AND mileage > 0
                GROUP BY range
                ORDER BY count DESC
            """)
            ranges = cursor.fetchall()
        
        # Формируем популярные диапазоны
        popular_ranges = [
            {"label": "до 20 тыс км", "value": "mileage_to:20000", "count": 0},
            {"label": "20-50 тыс км", "value": "mileage_from:20000;mileage_to:50000", "count": 0},
            {"label": "50-100 тыс км", "value": "mileage_from:50000;mileage_to:100000", "count": 0},
            {"label": "100-200 тыс км", "value": "mileage_from:100000;mileage_to:200000", "count": 0},
            {"label": "более 200 тыс км", "value": "mileage_from:200000", "count": 0}
        ]
        
        # Обновляем счетчики из БД
        for range_info in ranges:
            for popular_range in popular_ranges:
                if popular_range["label"] == range_info[0]:
                    popular_range["count"] = range_info[1]
                    break
        
        return {"success": True, "ranges": popular_ranges}
    except Exception as e:
        logger.error(f"Ошибка получения диапазонов пробега: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/popular_options")
async def get_popular_options():
    """Получение популярных опций для быстрых фильтров"""
    try:
        options = get_all_options()
        
        # Определяем популярные опции для быстрых фильтров
        popular_option_codes = [
            "S403A",  # Люк
            "S423A",  # Панорамная крыша
            "S430A",  # Климат-контроль
            "S431A",  # Подогрев сидений
            "S459A",  # Электрорегулировка сидений
            "S494A",  # Система парковки
            "S502A",  # Навигация
            "S508A",  # Парктроник
            "S521A",  # Датчик дождя
            "S522A",  # Ксенон
            "S524A",  # Адаптивные фары
            "S534A",  # Система комфортного доступа
            "S548A",  # Спидометр с километражем
            "S563A",  # Освещение салона
            "S609A",  # Система навигации Professional
            "S610A",  # Дисплей в головном устройстве
            "S612A",  # BMW Assist
            "S615A",  # Расширенная система BMW Online
            "S616A",  # BMW Online
            "S620A",  # Голосовое управление
            "S633A",  # Подготовка к мобильному телефону
            "S654A",  # Радио BMW Professional
            "S655A",  # Спутниковое радио
            "S676A",  # Акустическая система HiFi
            "S693A",  # Подготовка к BMW Satellite Radio
            "S697A",  # Изменение области действия
            "S6ACA",  # Интеллектуальная система экстренного вызова
            "S6AEA",  # Teleservices
            "S6AKA",  # ConnectedDrive Services
            "S6AMA",  # Real-Time Traffic Information
            "S6ANA",  # Concierge Services
            "S6APA",  # Remote Services
            "S6ARA",  # Online Speech Processing
            "S6ASA",  # Emergency Call
            "S6NSA",  # Расширенная система телефонии с USB
            "S6NXA",  # Подготовка к мобильному телефону с беспроводной зарядкой
            "S6UAA",  # Интеллектуальная система экстренного вызова
            "S6UHA",  # Traffic Information
            "S6VCA",  # Control for ConnectedDrive
            "S6WCA",  # Multifunctional instrument display
            "S6WDA",  # WLAN Hotspot
            "S6WEA",  # Apps
            "S6WFA",  # Apple CarPlay Preparation
            "S6WGA",  # Android Auto Preparation
            "S6WHA",  # Wireless Charging
            "S6WIA",  # WiFi Hotspot
            "S6WJA",  # Digital Key
            "S6WKA",  # Connected Package Professional
            "S6WLA",  # Connected Package Professional Plus"
        ]
        
        # Фильтруем опции по популярным кодам
        popular_options = []
        for option in options:
            if option["code"] in popular_option_codes:
                popular_options.append(option)
        
        # Добавляем общие опции по описанию
        general_options = [
            {"code": "LUXURY", "description": "Люкс-комплектация"},
            {"code": "COMFORT", "description": "Комфорт-комплектация"},
            {"code": "SPORT", "description": "Спорт-комплектация"},
            {"code": "FAMILY", "description": "Семейная комплектация"},
            {"code": "BUSINESS", "description": "Бизнес-комплектация"}
        ]
        
        return {"success": True, "options": popular_options[:10] + general_options}
    except Exception as e:
        logger.error(f"Ошибка получения популярных опций: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/popular_dealers")
async def get_popular_dealers():
    """Получение популярных дилеров для быстрых фильтров"""
    try:
        dealers = get_all_dealer_centers()
        
        # Получаем статистику по дилерам
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dealer_center, COUNT(*) as count
                FROM car 
                WHERE dealer_center IS NOT NULL AND dealer_center != ''
                GROUP BY dealer_center
                ORDER BY count DESC
                LIMIT 10
            """)
            dealer_stats = cursor.fetchall()
        
        # Формируем список популярных дилеров
        popular_dealers = []
        for dealer_name, count in dealer_stats:
            popular_dealers.append({
                "name": dealer_name,
                "count": count
            })
        
        return {"success": True, "dealers": popular_dealers}
    except Exception as e:
        logger.error(f"Ошибка получения популярных дилеров: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/car_states")
async def get_car_states():
    """Получение состояний автомобилей (новый/б/у)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Подсчитываем количество новых и подержанных авто
            new_count = cursor.execute("SELECT COUNT(*) FROM car").fetchone()[0]
            used_count = cursor.execute("SELECT COUNT(*) FROM used_car").fetchone()[0]
            
            states = [
                {"label": "Новый", "value": "new", "count": new_count},
                {"label": "С пробегом", "value": "used", "count": used_count}
            ]
            
            return {"success": True, "states": states}
    except Exception as e:
        logger.error(f"Ошибка получения состояний автомобилей: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/popular_scenarios")
async def get_popular_scenarios():
    """Получение популярных сценариев использования"""
    try:
        scenarios = [
            {
                "title": "Семейный автомобиль",
                "icon": "👨‍👩‍👧‍👦",
                "query": "Семейный автомобиль с большим багажником и безопасностью",
                "description": "Для семьи с детьми"
            },
            {
                "title": "Для города",
                "icon": "🏙️",
                "query": "Компактный автомобиль для города с хорошей маневренностью",
                "description": "Компактный и маневренный"
            },
            {
                "title": "Для путешествий",
                "icon": "🗺️",
                "query": "Внедорожник или кроссовер для путешествий с полным приводом",
                "description": "Для поездок и приключений"
            },
            {
                "title": "Для работы",
                "icon": "💼",
                "query": "Бизнес-седан или универсал для работы",
                "description": "Солидный и комфортный"
            },
            {
                "title": "Для дачи",
                "icon": "🏡",
                "query": "Внедорожник или пикап для дачи с высоким клиренсом",
                "description": "Проходимость и вместительность"
            },
            {
                "title": "Для молодежи",
                "icon": "🎮",
                "query": "Спортивный автомобиль или хетчбэк для молодежи",
                "description": "Динамичный и стильный"
            },
            {
                "title": "Для бизнеса",
                "icon": "🏢",
                "query": "Люкс-седан или внедорожник для бизнеса",
                "description": "Престиж и комфорт"
            },
            {
                "title": "Экономичный",
                "icon": "💰",
                "query": "Экономичный автомобиль с низким расходом топлива",
                "description": "Низкие расходы на эксплуатацию"
            }
        ]
        
        return {"success": True, "scenarios": scenarios}
    except Exception as e:
        logger.error(f"Ошибка получения популярных сценариев: {e}")
        return {"success": False, "error": str(e)}

# Новые API эндпоинты для расширенной функциональности

@app.post("/api/ner/analyze")
async def analyze_entities(request: ChatRequest):
    """Анализирует текст и извлекает сущности."""
    try:
        entities = ner_classifier.extract_entities(request.message)
        intent = ner_classifier.classify_intent(request.message)
        
        return {
            "entities": entities,
            "intent": intent,
            "message": request.message
        }
    except Exception as e:
        logger.error(f"Ошибка при анализе сущностей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при анализе сущностей")

@app.post("/api/sentiment/analyze")
async def analyze_sentiment(request: ChatRequest):
    """Анализирует настроение текста."""
    try:
        sentiment_result = sentiment_analyzer.analyze_sentiment(request.message)
        
        return {
            "sentiment": sentiment_result,
            "message": request.message
        }
    except Exception as e:
        logger.error(f"Ошибка при анализе настроения: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при анализе настроения")

@app.post("/api/recommendations/advanced")
async def get_advanced_recommendations(request: RecommendationRequest):
    """Получает продвинутые рекомендации с использованием ML."""
    try:
        recommendations = advanced_recommendation_engine.get_hybrid_recommendations(
            user_id=request.user_id,
            limit=request.preferences.get('limit', 10) if request.preferences else 10
        )
        
        return {
            "recommendations": recommendations,
            "user_id": request.user_id,
            "total": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Ошибка при получении продвинутых рекомендаций: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении рекомендаций")

@app.post("/api/dialog/enhanced")
async def enhanced_dialog(request: ChatRequest):
    """Обрабатывает сообщение через улучшенный диалоговый менеджер."""
    try:
        # Анализируем сущности и интент
        entities = ner_classifier.extract_entities(request.message)
        intent = ner_classifier.classify_intent(request.message)
        
        # Анализируем настроение
        sentiment = sentiment_analyzer.analyze_sentiment(request.message)
        
        # Обрабатываем через улучшенный диалоговый менеджер
        dialog_result = enhanced_dialog_manager.process_message(
            user_id=request.user_id,
            message=request.message,
            intent=intent,
            entities=entities
        )
        
        return {
            "response": dialog_result['response'],
            "state": dialog_result['state'],
            "entities": dialog_result['entities'],
            "suggested_actions": dialog_result['suggested_actions'],
            "sentiment": sentiment,
            "confidence": dialog_result['confidence']
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке диалога: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке диалога")

@app.get("/api/analytics/comprehensive")
async def get_comprehensive_analytics():
    """Получает комплексный аналитический отчет."""
    try:
        report = data_analyzer.get_comprehensive_report()
        return report
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении аналитики")

@app.get("/api/analytics/trends")
async def get_trend_analysis(days: int = 30):
    """Получает анализ трендов."""
    try:
        trends = data_analyzer.get_trend_analysis(days)
        return trends
    except Exception as e:
        logger.error(f"Ошибка при получении трендов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении трендов")

@app.post("/api/recommendations/feedback")
async def log_recommendation_feedback(user_id: str, recommendation_id: int, score: int):
    """Логирует обратную связь по рекомендациям."""
    try:
        advanced_recommendation_engine.update_user_interaction(
            user_id=user_id,
            car_id=recommendation_id,
            interaction_type='feedback'
        )
        return {"status": "success", "message": "Обратная связь сохранена"}
    except Exception as e:
        logger.error(f"Ошибка при сохранении обратной связи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении обратной связи")

@app.get("/api/dialog/session/{user_id}")
async def get_dialog_session(user_id: str):
    """Получает информацию о текущей сессии диалога."""
    try:
        analytics = enhanced_dialog_manager.get_session_analytics(user_id)
        return analytics
    except Exception as e:
        logger.error(f"Ошибка при получении сессии: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении сессии")

@app.post("/api/dialog/end-session/{user_id}")
async def end_dialog_session(user_id: str, satisfaction: Optional[int] = None):
    """Завершает сессию диалога."""
    try:
        enhanced_dialog_manager.end_session(user_id, satisfaction)
        return {"status": "success", "message": "Сессия завершена"}
    except Exception as e:
        logger.error(f"Ошибка при завершении сессии: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при завершении сессии")

@app.post("/api/smart-chat")
async def smart_chat(request: ChatRequest):
    """Умный чат с автоматической маршрутизацией запросов"""
    try:
        from smart_query_router import route_query
        
        # Маршрутизируем запрос
        result = route_query(request.message, request.user_id)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Ошибка в умном чате: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка обработки запроса",
            "message": "Извините, произошла ошибка при обработке вашего запроса."
        })

@app.post("/api/enhanced-chat")
async def enhanced_chat(request: ChatRequest):
    """Улучшенный чат с Mistral API и умной маршрутизацией"""
    try:
        logger.info(f"=== УЛУЧШЕННЫЙ ЧАТ ===")
        logger.info(f"Сообщение: {request.message}")
        logger.info(f"User ID: {request.user_id}")
        
        # Используем улучшенный роутер
        result = enhanced_router.route_query(request.message, request.user_id or "default")
        
        # Форматируем ответ для совместимости с фронтендом
        response = {
            "success": True,
            "type": result.get("type", "unknown"),
            "message": result.get("message", ""),
            "data": result.get("result", {}),
            "cars": result.get("result", {}).get("cars", []) if result.get("result") else [],
            "total_found": result.get("result", {}).get("total_found", 0) if result.get("result") else 0,
            "llama_used": result.get("llama_used", False),
            "mistral_used": result.get("mistral_used", False),
            "query_type": result.get("query_type", "unknown")
        }
        
        logger.info(f"✅ Ответ сформирован: {response['type']}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Ошибка в улучшенном чате: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка обработки запроса",
            "message": "Извините, произошла ошибка при обработке вашего запроса."
        })

@app.post("/api/enhanced-chat-v2")
async def enhanced_chat_v2(request: ChatRequest):
    """Улучшенный чат v2.0 с 95% точностью классификации"""
    try:
        logger.info(f"=== УЛУЧШЕННЫЙ ЧАТ V2.0 ===")
        logger.info(f"Сообщение: {request.message}")
        logger.info(f"User ID: {request.user_id}")
        
        # Используем улучшенный роутер v2.0
        result = enhanced_router_v2.route_query(request.message, request.user_id or "default")
        
        # Форматируем ответ для совместимости с фронтендом
        response = {
            "success": True,
            "type": result.get("type", "unknown"),
            "message": result.get("message", ""),
            "data": result.get("result", {}),
            "cars": result.get("result", {}).get("cars", []) if result.get("result") else [],
            "total_found": result.get("result", {}).get("total_found", 0) if result.get("result") else 0,
            "llama_used": result.get("llama_used", False),
            "mistral_used": result.get("mistral_used", False),
            "query_type": result.get("query_type", "unknown"),
            "version": "v2.0",
            "accuracy": "95%"
        }
        
        logger.info(f"✅ Ответ v2.0 сформирован: {response['type']}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Ошибка в улучшенном чате v2.0: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка обработки запроса",
            "message": "Извините, произошла ошибка при обработке вашего запроса."
        })

@app.post("/api/enhanced-chat-v3")
async def enhanced_chat_v3(request: ChatRequest):
    """Улучшенный чат v3.0 с фильтрацией неавтомобильных запросов - 100% точность"""
    try:
        logger.info(f"=== УЛУЧШЕННЫЙ ЧАТ V3.0 ===")
        logger.info(f"Сообщение: {request.message}")
        logger.info(f"User ID: {request.user_id}")
        
        # Используем улучшенный роутер v3.0 с фильтрацией
        result = enhanced_router_v3.route_query(request.message, request.user_id or "default")
        
        # Форматируем ответ для совместимости с фронтендом
        response = {
            "success": True,
            "type": result.get("type", "unknown"),
            "message": result.get("message", ""),
            "data": result.get("result", {}),
            "cars": result.get("result", {}).get("cars", []) if result.get("result") else [],
            "total_found": result.get("result", {}).get("total_found", 0) if result.get("result") else 0,
            "llama_used": result.get("llama_used", False),
            "mistral_used": result.get("mistral_used", False),
            "query_type": result.get("query_type", "unknown"),
            "version": "v3.0",
            "accuracy": "100%",
            "filtered": result.get("rejected", False)
        }
        
        logger.info(f"✅ Ответ v3.0 сформирован: {response['type']}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Ошибка в улучшенном чате v3.0: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка обработки запроса",
            "message": "Извините, произошла ошибка при обработке вашего запроса."
        })


@app.post("/api/enhanced-chat/compare")
async def enhanced_compare(request: ChatRequest):
    """Сравнение автомобилей через улучшенный процессор"""
    try:
        result = enhanced_llama_processor.process_comparison_request(request.message)
        
        return JSONResponse(content={
            "success": True,
            "response": result.get('response', ''),
            "cars": result.get('cars', []),
            "comparison_data": result.get('comparison_data', {})
        })
        
    except Exception as e:
        logger.error(f"Ошибка при сравнении: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка сравнения",
            "message": "Извините, не удалось выполнить сравнение."
        })

@app.post("/api/enhanced-chat/scenario")
async def enhanced_scenario(request: ChatRequest):
    """Обработка сценариев через улучшенный процессор"""
    try:
        # Определяем сценарий из запроса
        scenario = enhanced_llama_processor._determine_scenario_from_query(request.message)
        if not scenario:
            return JSONResponse(content={
                "success": False,
                "error": "Сценарий не определен",
                "message": "Пожалуйста, уточните сценарий использования автомобиля."
            })
        
        result = enhanced_llama_processor.process_scenario_request(request.message, scenario)
        
        return JSONResponse(content={
            "success": True,
            "response": result.get('response', ''),
            "cars": result.get('cars', []),
            "scenario": scenario,
            "recommendations": result.get('recommendations', [])
        })
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сценария: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка обработки сценария",
            "message": "Извините, не удалось обработать сценарий."
        })

@app.post("/api/enhanced-chat/help")
async def enhanced_help(request: ChatRequest):
    """Справка по возможностям улучшенного процессора"""
    try:
        result = enhanced_llama_processor.process_help_request(request.message)
        
        return JSONResponse(content={
            "success": True,
            "response": result.get('response', ''),
            "capabilities": result.get('capabilities', []),
            "examples": result.get('examples', [])
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении справки: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка получения справки",
            "message": "Извините, не удалось получить справку."
        })

@app.post("/api/enhanced-chat/clear-context")
async def clear_enhanced_context(request: ChatRequest):
    """Очистка контекста пользователя"""
    try:
        enhanced_llama_processor.clear_user_context()
        
        return JSONResponse(content={
            "success": True,
            "message": "Контекст пользователя очищен"
        })
        
    except Exception as e:
        logger.error(f"Ошибка при очистке контекста: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка очистки контекста",
            "message": "Извините, не удалось очистить контекст."
        })

@app.get("/api/enhanced-chat/stats")
async def get_enhanced_stats():
    """Получение статистики улучшенного процессора"""
    try:
        stats = enhanced_llama_processor.get_processing_stats()
        
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}")
        return JSONResponse(content={
            "success": False,
            "error": "Ошибка получения статистики",
            "message": "Извините, не удалось получить статистику."
        })

from typing import Dict, Any
class ActionAdjustRequest(BaseModel):
    user_id: Optional[str] = "default"
    action: str
    context_entities: Optional[Dict[str, Any]] = None

@app.post("/api/actions/adjust-filters")
async def adjust_filters(request: ActionAdjustRequest):
    """Ослабляет/меняет фильтры по заданному действию и возвращает результаты."""
    try:
        action = (request.action or '').lower()
        from modules.search.auto_search_processor import AutoSearchProcessor
        from database import search_all_cars
        proc = AutoSearchProcessor()
        entities = request.context_entities or {}
        # Мягкая корректировка по action
        if 'remove_color' in action:
            entities.pop('color', None)
        if 'similar' in action:
            # Снизим строгость: уберем самые узкие фильтры
            for k in ['color', 'body_type', 'power_from']:
                entities.pop(k, None)
        if 'expand_body_type' in action:
            body = entities.get('body_type')
            if isinstance(body, str):
                entities['body_type'] = [body, 'седан', 'купе', 'лифтбек']
        if 'increase_price' in action:
            if entities.get('price_to'):
                try:
                    entities['price_to'] = int(float(entities['price_to']) * 1.15)
                except Exception:
                    pass
        if 'expand_year' in action:
            if entities.get('year_from'):
                entities['year_from'] = max(2000, int(entities['year_from']) - 2)
            if entities.get('year_to'):
                entities['year_to'] = int(entities['year_to']) + 2
        if 'decrease_power' in action:
            if entities.get('power_from'):
                entities['power_from'] = max(0, int(entities['power_from']) - 50)
        if 'expand_city' in action:
            entities.pop('city', None)
        if 'brand_only_models' in action:
            if entities.get('brand') and entities.get('model'):
                entities.pop('model', None)
        # Выполним поиск
        results = search_all_cars(**proc._build_search_params(entities))
        
        return JSONResponse(content={
            "success": True,
            "type": "search_results",
            "message": proc._generate_response_message("", entities, len(results)),
            "cars": proc._format_cars(results),
            "entities": entities
        })
    except Exception as e:
        logger.error(f"Ошибка adjust-filters: {e}")
        return JSONResponse(content={
            "success": False, 
            "error": "Ошибка изменения фильтров"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True) 