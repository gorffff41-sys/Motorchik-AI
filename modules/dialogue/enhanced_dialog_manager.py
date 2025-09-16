import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from dataclasses import dataclass, asdict
from enum import Enum

class DialogState(Enum):
    INITIAL = "initial"
    SEARCHING = "searching"
    COMPARING = "comparing"
    NEGOTIATING = "negotiating"
    CLOSING = "closing"
    HELP = "help"
    LOAN_CALCULATOR = "loan_calculator"
    OPTIONS = "options"
    CHITCHAT = "chitchat"

class UserIntent(Enum):
    SEARCH = "search"
    COMPARE = "compare"
    BUY = "buy"
    LEARN = "learn"
    HELP = "help"
    CHITCHAT = "chitchat"

@dataclass
class DialogContext:
    user_id: str
    current_state: DialogState
    entities: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    session_start: datetime
    last_interaction: datetime
    confidence_score: float = 0.0
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []

class EnhancedDialogManager:
    """
    Улучшенный менеджер диалогов с контекстным анализом и персонализацией.
    """
    
    def __init__(self, db_path: str = "instance/cars.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Кэш активных диалогов
        self.active_dialogs: Dict[str, DialogContext] = {}
        
        # Шаблоны ответов
        self.response_templates = self._load_response_templates()
        
        # Правила переходов состояний
        self.state_transitions = self._load_state_transitions()
        
        # Инициализация БД
        self._init_database()
    
    def _init_database(self):
        """Инициализирует таблицы для диалогов."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица диалогов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialog_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    final_state TEXT,
                    entities TEXT,
                    user_satisfaction INTEGER
                )
            """)
            
            # Таблица сообщений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialog_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES dialog_sessions (id)
                )
            """)
            
            # Таблица пользовательских предпочтений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации БД: {e}")
    
    def _load_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Загружает шаблоны ответов."""
        return {
            'greeting': {
                'initial': [
                    "Привет! Я ваш автомобильный ассистент. Чем могу помочь?",
                    "Добро пожаловать! Готов помочь с выбором автомобиля.",
                    "Здравствуйте! Расскажите, какой автомобиль вас интересует?"
                ]
            },
            'search': {
                'searching': [
                    "Понимаю, вы ищете {brand} {model}. Расскажите подробнее о ваших требованиях.",
                    "Отлично! {brand} {model} - хороший выбор. Какие характеристики важны для вас?",
                    "Начинаю поиск {brand} {model}. Уточните ценовой диапазон и год выпуска."
                ]
            },
            'compare': {
                'comparing': [
                    "Сравниваю {car1} и {car2}. Вот основные различия:",
                    "Анализирую {car1} против {car2}. Обратите внимание на:",
                    "Провожу детальное сравнение {car1} и {car2}."
                ]
            },
            'help': {
                'help': [
                    "Конечно! Я могу помочь с поиском, сравнением, расчетом кредита и многим другим.",
                    "Вот что я умею: поиск автомобилей, сравнение моделей, расчет платежей.",
                    "Мои возможности: поиск по параметрам, сравнение, кредитный калькулятор."
                ]
            },
            'closing': {
                'closing': [
                    "Было приятно помочь! Обращайтесь, если понадобится еще что-то.",
                    "Спасибо за обращение! Удачного выбора автомобиля!",
                    "До свидания! Надеюсь, наш разговор был полезным."
                ]
            }
        }
    
    def _load_state_transitions(self) -> Dict[DialogState, Dict[str, DialogState]]:
        """Загружает правила переходов состояний."""
        return {
            DialogState.INITIAL: {
                'search': DialogState.SEARCHING,
                'compare': DialogState.COMPARING,
                'help': DialogState.HELP,
                'chitchat': DialogState.INITIAL
            },
            DialogState.SEARCHING: {
                'search': DialogState.SEARCHING,
                'compare': DialogState.COMPARING,
                'buy': DialogState.NEGOTIATING,
                'help': DialogState.HELP,
                'close': DialogState.CLOSING
            },
            DialogState.COMPARING: {
                'search': DialogState.SEARCHING,
                'compare': DialogState.COMPARING,
                'buy': DialogState.NEGOTIATING,
                'help': DialogState.HELP,
                'close': DialogState.CLOSING
            },
            DialogState.NEGOTIATING: {
                'buy': DialogState.NEGOTIATING,
                'close': DialogState.CLOSING,
                'help': DialogState.HELP
            },
            DialogState.HELP: {
                'search': DialogState.SEARCHING,
                'compare': DialogState.COMPARING,
                'help': DialogState.HELP,
                'close': DialogState.CLOSING
            }
        }
    
    def process_message(self, user_id: str, message: str, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает сообщение пользователя и возвращает ответ.
        
        Args:
            user_id: ID пользователя
            message: Сообщение пользователя
            intent: Определенный интент
            entities: Извлеченные сущности
            
        Returns:
            Словарь с ответом и дополнительной информацией
        """
        try:
            # Получаем или создаем контекст диалога
            context = self._get_or_create_context(user_id)
            
            # Обновляем контекст
            self._update_context(context, message, intent, entities)
            
            # Определяем следующее состояние
            next_state = self._determine_next_state(context, intent)
            context.current_state = next_state
            
            # Генерируем ответ
            response = self._generate_response(context, intent, entities)
            
            # Обновляем предложения действий
            context.suggested_actions = self._generate_suggested_actions(context)
            
            # Сохраняем контекст
            self.active_dialogs[user_id] = context
            
            # Логируем взаимодействие
            self._log_interaction(context, message, intent, entities, response)
            
            return {
                'response': response,
                'state': context.current_state.value,
                'entities': context.entities,
                'suggested_actions': context.suggested_actions,
                'confidence': context.confidence_score,
                'session_duration': (datetime.now() - context.session_start).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {e}")
            return {
                'response': "Извините, произошла ошибка. Попробуйте еще раз.",
                'state': 'error',
                'entities': {},
                'suggested_actions': ['Повторить запрос', 'Начать заново'],
                'confidence': 0.0
            }
    
    def _get_or_create_context(self, user_id: str) -> DialogContext:
        """Получает или создает контекст диалога."""
        if user_id in self.active_dialogs:
            context = self.active_dialogs[user_id]
            # Проверяем, не истекла ли сессия (30 минут)
            if datetime.now() - context.last_interaction > timedelta(minutes=30):
                # Создаем новую сессию
                context = self._create_new_context(user_id)
        else:
            context = self._create_new_context(user_id)
        
        return context
    
    def _create_new_context(self, user_id: str) -> DialogContext:
        """Создает новый контекст диалога."""
        # Загружаем предпочтения пользователя
        preferences = self._load_user_preferences(user_id)
        
        context = DialogContext(
            user_id=user_id,
            current_state=DialogState.INITIAL,
            entities={},
            conversation_history=[],
            user_preferences=preferences,
            session_start=datetime.now(),
            last_interaction=datetime.now(),
            confidence_score=0.0
        )
        
        return context
    
    def _update_context(self, context: DialogContext, message: str, intent: str, entities: Dict[str, Any]):
        """Обновляет контекст диалога."""
        # Обновляем историю
        context.conversation_history.append({
            'message': message,
            'intent': intent,
            'entities': entities,
            'timestamp': datetime.now()
        })
        
        # Обновляем сущности
        context.entities.update(entities)
        
        # Обновляем время последнего взаимодействия
        context.last_interaction = datetime.now()
        
        # Обновляем уверенность
        context.confidence_score = self._calculate_confidence(context, entities, intent)
    
    def _determine_next_state(self, context: DialogContext, intent: str) -> DialogState:
        """Улучшенное определение следующего состояния диалога."""
        current_state = context.current_state
        
        # Приоритетные переходы на основе интента
        if intent == 'loan':
            return DialogState.LOAN_CALCULATOR
        elif intent == 'compare':
            return DialogState.COMPARING
        elif intent == 'help':
            return DialogState.HELP
        elif intent == 'chitchat':
            return DialogState.CHITCHAT
        
        # Контекстные переходы
        if current_state == DialogState.INITIAL:
            if intent in ['car_search', 'family_car', 'city_car', 'travel_car', 'business_car']:
                return DialogState.SEARCHING
            elif intent == 'car_option':
                return DialogState.OPTIONS
            else:
                return DialogState.INITIAL
        
        elif current_state == DialogState.SEARCHING:
            if intent == 'compare':
                return DialogState.COMPARING
            elif intent == 'loan':
                return DialogState.LOAN_CALCULATOR
            else:
                return DialogState.SEARCHING
        
        elif current_state == DialogState.COMPARING:
            if intent == 'loan':
                return DialogState.LOAN_CALCULATOR
            elif intent == 'car_search':
                return DialogState.SEARCHING
            else:
                return DialogState.COMPARING
        
        elif current_state == DialogState.LOAN_CALCULATOR:
            if intent == 'compare':
                return DialogState.COMPARING
            elif intent == 'car_search':
                return DialogState.SEARCHING
            else:
                return DialogState.LOAN_CALCULATOR
        
        # По умолчанию возвращаемся к начальному состоянию
        return DialogState.INITIAL
    
    def _generate_response(self, context: DialogContext, intent: str, entities: Dict[str, Any]) -> str:
        """Генерирует ответ на основе контекста и интента."""
        try:
            # Выбираем подходящий шаблон
            template_key = self._get_template_key(intent, context.current_state)
            templates = self.response_templates.get(template_key, {}).get(context.current_state.value, [])
            
            if not templates:
                # Используем общий шаблон
                templates = self.response_templates.get('general', {}).get(context.current_state.value, [
                    "Понимаю ваш запрос. Чем еще могу помочь?"
                ])
            
            # Выбираем случайный шаблон
            import random
            template = random.choice(templates)
            
            # Заполняем шаблон данными
            response = self._fill_template(template, context, entities)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации ответа: {e}")
            return "Извините, не могу сгенерировать ответ. Попробуйте переформулировать запрос."
    
    def _get_template_key(self, intent: str, state: DialogState) -> str:
        """Определяет ключ шаблона на основе интента и состояния."""
        intent_mapping = {
            'car_search': 'search',
            'compare': 'compare',
            'help': 'help',
            'chitchat': 'greeting',
            'loan': 'search',
            'car_option': 'search'
        }
        
        return intent_mapping.get(intent, 'general')
    
    def _fill_template(self, template: str, context: DialogContext, entities: Dict[str, Any]) -> str:
        """Заполняет шаблон данными."""
        try:
            # Заменяем плейсхолдеры
            filled_template = template
            
            # Заменяем сущности
            for key, value in entities.items():
                placeholder = f"{{{key}}}"
                if placeholder in filled_template:
                    filled_template = filled_template.replace(placeholder, str(value))
            
            # Заменяем специальные плейсхолдеры
            if '{brand}' in filled_template and 'brand' in entities:
                filled_template = filled_template.replace('{brand}', entities['brand'])
            
            if '{model}' in filled_template and 'model' in entities:
                filled_template = filled_template.replace('{model}', entities['model'])
            
            # Если есть марка и модель, но нет в шаблоне
            if 'brand' in entities and 'model' in entities and '{brand}' not in filled_template:
                filled_template = f"{entities['brand']} {entities['model']}. {filled_template}"
            
            return filled_template
            
        except Exception as e:
            self.logger.error(f"Ошибка при заполнении шаблона: {e}")
            return template
    
    def _generate_suggested_actions(self, context: DialogContext) -> List[str]:
        """Генерирует предложения действий на основе контекста."""
        suggestions = []
        
        if context.current_state == DialogState.INITIAL:
            suggestions = [
                "Найти автомобиль",
                "Сравнить модели",
                "Рассчитать кредит",
                "Получить помощь"
            ]
        elif context.current_state == DialogState.SEARCHING:
            if 'brand' in context.entities:
                suggestions = [
                    f"Показать {context.entities['brand']}",
                    "Уточнить параметры",
                    "Сравнить с другими",
                    "Рассчитать стоимость"
                ]
            else:
                suggestions = [
                    "Указать марку",
                    "Указать модель",
                    "Указать цену",
                    "Указать год"
                ]
        elif context.current_state == DialogState.COMPARING:
            suggestions = [
                "Добавить к сравнению",
                "Показать различия",
                "Рассчитать кредит",
                "Связаться с дилером"
            ]
        elif context.current_state == DialogState.NEGOTIATING:
            suggestions = [
                "Рассчитать кредит",
                "Записаться на тест-драйв",
                "Связаться с дилером",
                "Получить скидку"
            ]
        
        return suggestions[:4]  # Ограничиваем 4 предложениями
    
    def _calculate_confidence(self, context: DialogContext, entities: Dict[str, Any], intent: str) -> float:
        """Улучшенный расчет уверенности в понимании."""
        confidence = 0.5  # Базовая уверенность
        
        # Уверенность на основе количества извлеченных сущностей
        entity_count = len(entities)
        if entity_count > 0:
            confidence += min(0.3, entity_count * 0.1)
        
        # Уверенность на основе контекста
        if context.current_state != 'initial':
            confidence += 0.2
        
        # Уверенность на основе истории
        if len(context.conversation_history) > 0:
            confidence += 0.1
        
        # Уверенность на основе конкретных сущностей
        if 'brand' in entities:
            confidence += 0.15
        if 'model' in entities:
            confidence += 0.15
        if 'price' in entities or 'price_from' in entities or 'price_to' in entities:
            confidence += 0.1
        if 'year' in entities:
            confidence += 0.1
        
        # Штраф за нестабильность состояний
        if len(context.conversation_history) > 5:
            state_changes = sum(1 for i in range(1, len(context.conversation_history)))
            if state_changes > 3:
                confidence -= 0.1
        
        # Бонус за четкий интент
        clear_intents = ['car_search', 'compare', 'loan', 'help']
        if intent in clear_intents:
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Загружает предпочтения пользователя."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT preferences FROM user_preferences WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке предпочтений: {e}")
            return {}
    
    def _log_interaction(self, context: DialogContext, message: str, intent: str, entities: Dict[str, Any], response: str):
        """Логирует взаимодействие в БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем ID сессии
            cursor.execute("""
                SELECT id FROM dialog_sessions 
                WHERE user_id = ? AND session_end IS NULL
                ORDER BY session_start DESC LIMIT 1
            """, (context.user_id,))
            
            result = cursor.fetchone()
            if result:
                session_id = result[0]
            else:
                # Создаем новую сессию
                cursor.execute("""
                    INSERT INTO dialog_sessions (user_id, session_start)
                    VALUES (?, ?)
                """, (context.user_id, context.session_start))
                session_id = cursor.lastrowid
            
            # Логируем сообщение
            cursor.execute("""
                INSERT INTO dialog_messages (session_id, user_id, message, intent, entities, response)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, context.user_id, message, intent, json.dumps(entities), response))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка при логировании: {e}")
    
    def end_session(self, user_id: str, satisfaction: Optional[int] = None):
        """Завершает сессию диалога."""
        try:
            if user_id in self.active_dialogs:
                context = self.active_dialogs[user_id]
                
                # Обновляем сессию в БД
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE dialog_sessions 
                    SET session_end = ?, final_state = ?, user_satisfaction = ?
                    WHERE user_id = ? AND session_end IS NULL
                """, (datetime.now(), context.current_state.value, satisfaction, user_id))
                
                conn.commit()
                conn.close()
                
                # Удаляем из активных диалогов
                del self.active_dialogs[user_id]
                
        except Exception as e:
            self.logger.error(f"Ошибка при завершении сессии: {e}")
    
    def get_session_analytics(self, user_id: str) -> Dict[str, Any]:
        """Получает аналитику сессии."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем статистику сессий
            cursor.execute("""
                SELECT COUNT(*) as total_sessions,
                       AVG(CAST((julianday(session_end) - julianday(session_start)) * 24 * 60 AS INTEGER)) as avg_duration,
                       AVG(user_satisfaction) as avg_satisfaction
                FROM dialog_sessions 
                WHERE user_id = ? AND session_end IS NOT NULL
            """, (user_id,))
            
            session_stats = cursor.fetchone()
            
            # Получаем популярные интенты
            cursor.execute("""
                SELECT intent, COUNT(*) as count
                FROM dialog_messages 
                WHERE user_id = ?
                GROUP BY intent
                ORDER BY count DESC
                LIMIT 5
            """, (user_id,))
            
            popular_intents = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_sessions': session_stats[0] if session_stats else 0,
                'avg_duration_minutes': session_stats[1] if session_stats else 0,
                'avg_satisfaction': session_stats[2] if session_stats else 0,
                'popular_intents': [{'intent': intent, 'count': count} for intent, count in popular_intents]
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении аналитики: {e}")
            return {} 
 
 