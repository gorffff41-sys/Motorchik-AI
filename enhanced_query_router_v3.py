#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная система классификации и маршрутизации запросов v3.0
Фильтрация неавтомобильных запросов - только автомобильные + системная помощь + базовое общение
"""

import re
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Типы запросов"""
    AUTOMOTIVE_SEARCH = "automotive_search"           # Поиск конкретных автомобилей
    AUTOMOTIVE_QUESTION = "automotive_question"       # Вопросы об автомобилях
    AUTOMOTIVE_COMPARISON = "automotive_comparison"   # Сравнение вариантов
    AUTOMOTIVE_RECOMMENDATION = "automotive_recommendation"  # Рекомендации
    AUTOMOTIVE_HELP = "automotive_help"               # Помощь с поиском
    GENERAL_CHAT = "general_chat"                     # Базовое общение (ограниченное)
    SYSTEM_HELP = "system_help"                       # Системная помощь
    CREDIT_CALCULATION = "credit_calculation"         # Кредитные расчеты
    NON_AUTOMOTIVE = "non_automotive"                 # Неавтомобильные запросы (отклоняются)

class EnhancedQueryClassifierV3:
    """Улучшенный классификатор запросов v3.0 с фильтрацией"""
    
    def __init__(self):
        # Разрешенные базовые фразы для общего общения
        self.allowed_general_phrases = [
            'привет', 'здравствуй', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
            'как дела', 'как ты', 'как у вас дела', 'как поживаешь', 'как поживаете',
            'спасибо', 'благодарю', 'спасибо большое', 'благодарю вас',
            'пока', 'до свидания', 'до встречи', 'увидимся', 'всего доброго',
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'супер', 'классно',
            'плохо', 'ужасно', 'кошмар', 'не очень', 'так себе',
            'да', 'нет', 'ок', 'понятно', 'ясно'
        ]
        
        # Запрещенные фразы, которые не должны попадать в GENERAL_CHAT
        self.forbidden_phrases = [
            'на работе', 'блокчейн', 'квантовая', 'физика', 'программирование',
            'математика', 'история', 'политика', 'инвестировать', 'любовь',
            'погода', 'борщ', 'анекдот', 'кино', 'английский', 'похудеть'
        ]
        
        # Ключевые слова для каждого типа
        self.keywords = {
            QueryType.AUTOMOTIVE_QUESTION: [
                # Вопросы "что такое"
                'что такое', 'что это', 'что означает', 'что значит', 'что за',
                'объясни', 'расскажи', 'разъясни', 'опери', 'характеризуй',
                'как работает', 'как устроен', 'как функционирует',
                'какая мощность', 'какой расход', 'какой объем',
                'что такое система', 'что такое устройство',
                # Технические термины
                'abs', 'esp', 'asr', 'ebd', 'tcs', 'vsc', 'hdc', 'hac', 'dsc', 'asc', 'abc',
                'турбо', 'турбонаддув', 'компрессор', 'инжектор', 'карбюратор', 'катализатор',
                'сажевый фильтр', 'гибрид', 'электромобиль', 'plug-in', 'hev', 'phev', 'bev',
                'автомат', 'механика', 'вариатор', 'робот', 'дсг', 'типтроник',
                'передний привод', 'задний привод', 'полный привод', '4wd', 'awd', 'fwd', 'rwd',
                'подвеска', 'амортизатор', 'пружина', 'стабилизатор', 'рычаг',
                'тормоз', 'диск', 'колодка', 'суппорт',
                'двигатель', 'мотор', 'цилиндр', 'клапан', 'поршень', 'коленвал',
                'коробка', 'трансмиссия', 'сцепление', 'дифференциал', 'редуктор',
                'кондиционер', 'климат', 'отопление', 'вентиляция', 'обогрев',
                'навигация', 'gps', 'мультимедиа', 'bluetooth', 'usb', 'aux',
                'страховка', 'каско', 'осаго', 'дтп', 'гаи', 'гибдд',
                'техосмотр', 'то', 'сервис', 'гарантия', 'запчасти',
                'крутящий момент', 'компрессия', 'система экстренного торможения',
                'система контроля слепых зон', 'адаптивный круиз-контроль',
                'система помощи при парковке', 'система мониторинга давления в шинах',
                'климат-контроль', 'система подогрева сидений', 'память настроек сидений',
                'система голосового управления', 'проекционный дисплей',
                'экологический класс', 'евро-6', 'система рекуперации энергии',
                'каталитический нейтрализатор', 'принцип работы электромобиля'
            ],
            
            QueryType.AUTOMOTIVE_COMPARISON: [
                'что лучше', 'что выбрать', 'сравни', 'сравнение', 'разница между',
                'чем отличается', 'чем лучше', 'vs', 'против', 'или',
                'бензин', 'дизель', 'газ', 'электро', 'гибрид',
                'автомат', 'механика', 'вариатор', 'робот',
                'передний', 'задний', 'полный привод',
                'bmw', 'мерседес', 'ауди', 'тойота', 'хонда', 'лада', 'kia', 'hyundai',
                'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер',
                'новый', 'подержанный', 'б/у', 'с пробегом',
                'дешевый', 'дорогой', 'бюджетный', 'премиум',
                'экономичный', 'мощный', 'быстрый', 'надежный'
            ],
            
            QueryType.AUTOMOTIVE_RECOMMENDATION: [
                'порекомендуй', 'рекомендуй', 'посоветуй', 'советуй', 'подскажи',
                'какой автомобиль', 'какую машину', 'какой выбрать',
                'для семьи', 'для города', 'для трассы', 'для работы',
                'семейный', 'городской', 'спортивный', 'экономичный',
                'нужен', 'нужна', 'нужно', 'хочу', 'ищу', 'ищем',
                'начинающий водитель', 'дальние поездки', 'большая семья',
                'зима', 'активный отдых', 'молодая семья', 'пожилой человек',
                'такси', 'частые поездки'
            ],
            
            QueryType.AUTOMOTIVE_HELP: [
                'как найти', 'как выбрать', 'как купить', 'как продать',
                'помоги найти', 'помоги выбрать', 'помоги купить', 'помоги продать',
                'что нужно знать', 'что важно учесть', 'на что обратить внимание',
                'при покупке', 'при выборе', 'при продаже',
                'подходящий', 'хороший', 'надежный', 'качественный',
                'не ошибиться', 'первый автомобиль', 'проверить',
                'подержанный', 'по бюджету', 'тип кузова', 'марка автомобиля'
            ],
            
            QueryType.SYSTEM_HELP: [
                'кто ты', 'кто вы', 'что ты умеешь', 'что вы умеете',
                'расскажи о себе', 'расскажите о себе',
                'что ты можешь', 'что вы можете', 'какие возможности',
                'расскажи о своих возможностях', 'расскажите о своих возможностях',
                'как ты работаешь', 'как вы работаете', 'как функционируешь',
                'помощь', 'help', 'справка', 'инструкция', 'руководство',
                'как пользоваться', 'что ты умеешь делать', 'что вы умеете делать',
                'что ты знаешь', 'что вы знаете', 'о чем можешь рассказать',
                'какие функции', 'какие команды', 'что можешь сделать',
                'твои возможности', 'ваши возможности',
                'расскажи что умеешь', 'расскажите что умеете',
                'покажи возможности', 'покажите возможности'
            ],
            
            QueryType.GENERAL_CHAT: [
                'привет', 'здравствуй', 'добрый день', 'добрый вечер', 'доброе утро',
                'как дела', 'как ты', 'как у вас дела', 'как поживаешь', 'как поживаете',
                'чем занимаешься', 'что делаешь', 'что делаете', 'как работаешь',
                'спасибо', 'благодарю', 'спасибо большое', 'благодарю вас',
                'пока', 'до свидания', 'до встречи', 'увидимся', 'всего доброго',
                'хорошо', 'отлично', 'прекрасно', 'замечательно', 'супер', 'классно',
                'плохо', 'ужасно', 'кошмар', 'не очень', 'так себе',
                'да', 'нет', 'ок', 'понятно', 'ясно'
            ],
            
            QueryType.AUTOMOTIVE_SEARCH: [
                'найди', 'найти', 'покажи', 'показать', 'ищу', 'хочу', 'нужен', 'нужна', 'нужно',
                'выведи', 'вывести', 'покажи мне', 'найди мне',
                'авто', 'машину', 'автомобиль', 'bmw', 'мерседес', 'тойота', 'лада',
                'машины', 'автомобили', 'автомобилей',
                'красный', 'белый', 'черный', 'синий', 'зеленый',
                'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер', 'спорткар',
                'до', 'от', 'миллион', 'миллионов', 'млн', 'тысяч', 'тысячи',
                'рублей', 'руб', '₽', 'стоимость', 'цена',
                '5-местный', 'пятиместный', '7-местный', 'семьместный',
                'бензин', 'дизель', 'автомат', 'механика', 'передний привод', 'полный привод'
            ],
            
            QueryType.CREDIT_CALCULATION: [
                'рассчитай', 'рассчитать', 'посчитай', 'посчитать',
                'кредит', 'кредитный', 'рассчитать кредит', 'кредитный калькулятор',
                'взять в кредит', 'оформить кредит', 'кредит на машину',
                'рассчитать платеж', 'ежемесячный платеж', 'ставка кредита',
                'первоначальный взнос', 'срок кредита', 'кредитные условия',
                'кридит', 'критит', 'рассчитай кредит', 'рассчитай кридит',
                'рассчитай критит', 'кредит на автомобиль', 'кридит на автомобиль',
                'критит на автомобиль', 'кредит на авто', 'кридит на авто',
                'критит на авто', 'рассчитать кридит', 'рассчитать критит',
                'кредитный калькулятор', 'кридитный калькулятор', 'крититный калькулятор',
                'взять в кридит', 'взять в критит', 'оформить кридит', 'оформить критит',
                'платеж', 'платежи', 'ежемесячный', 'рассчитать', 'рассчитай',
                'сколько будет', 'сколько составит', 'какая сумма', 'какая переплата',
                'ставка кредита', 'процентная ставка', 'годовая ставка', 'эффективная ставка',
                'автокредит', 'ипотека на машину', 'общая стоимость кредита'
            ]
        }
        
        # Приоритеты типов (чем выше, тем раньше проверяется)
        self.priorities = {
            QueryType.SYSTEM_HELP: 1,
            QueryType.GENERAL_CHAT: 2,
            QueryType.CREDIT_CALCULATION: 3,
            QueryType.AUTOMOTIVE_HELP: 4,
            QueryType.AUTOMOTIVE_RECOMMENDATION: 5,
            QueryType.AUTOMOTIVE_COMPARISON: 6,
            QueryType.AUTOMOTIVE_QUESTION: 7,
            QueryType.AUTOMOTIVE_SEARCH: 8,
            QueryType.NON_AUTOMOTIVE: 9
        }
    
    def is_automotive_related(self, query: str) -> bool:
        """Проверяет, связан ли запрос с автомобилями"""
        query_lower = query.lower().strip()
        
        # Автомобильные ключевые слова
        automotive_keywords = [
            'авто', 'машина', 'автомобиль', 'bmw', 'мерседес', 'ауди', 'тойота', 'хонда', 'лада', 'kia', 'hyundai',
            'седан', 'хэтчбек', 'универсал', 'внедорожник', 'кроссовер', 'спорткар',
            'бензин', 'дизель', 'газ', 'электро', 'гибрид',
            'автомат', 'механика', 'вариатор', 'робот',
            'передний привод', 'задний привод', 'полный привод',
            'двигатель', 'мотор', 'коробка', 'трансмиссия',
            'подвеска', 'тормоз', 'колесо', 'шина',
            'страховка', 'каско', 'осаго', 'техосмотр',
            'кредит на машину', 'автокредит', 'покупка авто',
            'продажа авто', 'с пробегом', 'новый автомобиль',
            # Технические термины
            'abs', 'esp', 'asr', 'ebd', 'tcs', 'vsc', 'hdc', 'hac', 'dsc', 'asc', 'abc',
            'турбо', 'турбонаддув', 'компрессор', 'инжектор', 'карбюратор', 'катализатор',
            'сажевый фильтр', 'plug-in', 'hev', 'phev', 'bev',
            'дсг', 'типтроник', '4wd', 'awd', 'fwd', 'rwd',
            'амортизатор', 'пружина', 'стабилизатор', 'рычаг',
            'диск', 'колодка', 'суппорт', 'цилиндр', 'клапан', 'поршень', 'коленвал',
            'сцепление', 'дифференциал', 'редуктор', 'кондиционер', 'климат',
            'отопление', 'вентиляция', 'обогрев', 'навигация', 'gps',
            'мультимедиа', 'bluetooth', 'usb', 'aux', 'дтп', 'гаи', 'гибдд',
            'крутящий момент', 'компрессия', 'система экстренного торможения',
            'система контроля слепых зон', 'адаптивный круиз-контроль',
            'система помощи при парковке', 'система мониторинга давления в шинах',
            'климат-контроль', 'система подогрева сидений', 'память настроек сидений',
            'система голосового управления', 'проекционный дисплей',
            'экологический класс', 'евро-6', 'система рекуперации энергии',
            'каталитический нейтрализатор', 'принцип работы электромобиля'
        ]
        
        return any(keyword in query_lower for keyword in automotive_keywords)
    
    def is_allowed_general(self, query: str) -> bool:
        """Проверяет, является ли запрос разрешенным общим общением"""
        query_lower = query.lower().strip()
        
        # Сначала проверяем, нет ли запрещенных фраз
        for forbidden_phrase in self.forbidden_phrases:
            if forbidden_phrase in query_lower:
                return False
        
        # Проверяем точные совпадения с разрешенными фразами
        for phrase in self.allowed_general_phrases:
            if phrase == query_lower:
                return True
        
        # Проверяем частичные совпадения только для коротких фраз
        for phrase in self.allowed_general_phrases:
            if len(phrase.split()) <= 2 and phrase in query_lower:
                return True
        
        return False
    
    def classify_query(self, query: str) -> QueryType:
        """Классифицирует запрос по типу с фильтрацией неавтомобильных запросов"""
        query_lower = query.lower().strip()
        
        # 1. Сначала проверяем системную помощь
        if any(phrase in query_lower for phrase in ['кто ты', 'что ты умеешь', 'помощь', 'возможности']):
            logger.info(f"Запрос '{query}' классифицирован как SYSTEM_HELP")
            return QueryType.SYSTEM_HELP
        
        # 2. Проверяем кредитные запросы (они автомобильные)
        if any(phrase in query_lower for phrase in ['кредит', 'рассчитай', 'посчитай', 'платеж', 'автокредит']):
            logger.info(f"Запрос '{query}' классифицирован как CREDIT_CALCULATION")
            return QueryType.CREDIT_CALCULATION
        
        # 3. Проверяем разрешенное общее общение
        if self.is_allowed_general(query):
            logger.info(f"Запрос '{query}' классифицирован как GENERAL_CHAT")
            return QueryType.GENERAL_CHAT
        
        # 4. Проверяем, связан ли запрос с автомобилями
        if not self.is_automotive_related(query):
            logger.info(f"Запрос '{query}' классифицирован как NON_AUTOMOTIVE (отклонен)")
            return QueryType.NON_AUTOMOTIVE
        
        # 4. Если связан с автомобилями, классифицируем как обычно
        scores = {query_type: 0 for query_type in QueryType if query_type != QueryType.NON_AUTOMOTIVE}
        
        # Подсчитываем совпадения ключевых слов
        for query_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    weight = len(keyword.split()) if ' ' in keyword else 1
                    scores[query_type] += weight
        
        # Специальные правила для улучшения точности
        if any(phrase in query_lower for phrase in ['что такое', 'что это', 'что означает', 'что значит']):
            automotive_terms = ['abs', 'esp', 'asr', 'турбо', 'гибрид', 'автомат', 'механика', 
                              'вариатор', 'подвеска', 'двигатель', 'коробка', 'система']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_QUESTION] += 10
        
        if 'как работает' in query_lower or 'как устроен' in query_lower:
            automotive_terms = ['система', 'двигатель', 'коробка', 'подвеска', 'тормоз']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_QUESTION] += 10
        
        if 'что лучше' in query_lower or 'сравни' in query_lower:
            automotive_terms = ['бензин', 'дизель', 'автомат', 'механика', 'bmw', 'мерседес']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_COMPARISON] += 10
        
        if any(phrase in query_lower for phrase in ['порекомендуй', 'посоветуй', 'какой автомобиль']):
            automotive_terms = ['авто', 'машину', 'автомобиль', 'семьи', 'города', 'трассы']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_RECOMMENDATION] += 10
        
        if any(phrase in query_lower for phrase in ['как найти', 'как выбрать', 'помоги выбрать']):
            automotive_terms = ['авто', 'машину', 'автомобиль', 'подходящий', 'хороший']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_HELP] += 10
        
        if any(phrase in query_lower for phrase in ['найди', 'покажи', 'ищу', 'хочу']):
            automotive_terms = ['авто', 'машину', 'bmw', 'мерседес', 'красный', 'белый']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_SEARCH] += 10
        
        if any(phrase in query_lower for phrase in ['кредит', 'рассчитай', 'посчитай', 'платеж']):
            scores[QueryType.CREDIT_CALCULATION] += 10
        
        # Находим тип с максимальным счетом
        max_score = max(scores.values())
        if max_score == 0:
            # Если нет совпадений, но запрос автомобильный, считаем поиском
            logger.info(f"Запрос '{query}' классифицирован как AUTOMOTIVE_SEARCH (по умолчанию)")
            return QueryType.AUTOMOTIVE_SEARCH
        
        # Если есть несколько типов с одинаковым максимальным счетом, выбираем по приоритету
        best_types = [query_type for query_type, score in scores.items() if score == max_score]
        if len(best_types) > 1:
            best_type = min(best_types, key=lambda x: self.priorities[x])
        else:
            best_type = best_types[0]
        
        logger.info(f"Запрос '{query}' классифицирован как {best_type.value} (счет: {max_score})")
        return best_type

class EnhancedQueryRouterV3:
    """Улучшенный роутер запросов v3.0 с фильтрацией неавтомобильных запросов"""
    
    def __init__(self):
        self.classifier = EnhancedQueryClassifierV3()
    
    def route_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Маршрутизирует запрос к соответствующему обработчику"""
        try:
            query_type = self.classifier.classify_query(query)
            
            logger.info(f"Маршрутизация запроса '{query}' как {query_type.value}")
            
            # Если запрос неавтомобильный, отклоняем его
            if query_type == QueryType.NON_AUTOMOTIVE:
                return self._process_non_automotive(query, user_id)
            
            if query_type == QueryType.AUTOMOTIVE_SEARCH:
                return self._process_automotive_search(query, user_id)
            elif query_type == QueryType.AUTOMOTIVE_QUESTION:
                return self._process_automotive_question(query, user_id)
            elif query_type == QueryType.AUTOMOTIVE_COMPARISON:
                return self._process_automotive_comparison(query, user_id)
            elif query_type == QueryType.AUTOMOTIVE_RECOMMENDATION:
                return self._process_automotive_recommendation(query, user_id)
            elif query_type == QueryType.AUTOMOTIVE_HELP:
                return self._process_automotive_help(query, user_id)
            elif query_type == QueryType.GENERAL_CHAT:
                return self._process_general_chat(query, user_id)
            elif query_type == QueryType.SYSTEM_HELP:
                return self._process_system_help(query, user_id)
            elif query_type == QueryType.CREDIT_CALCULATION:
                return self._process_credit_calculation(query, user_id)
            else:
                return self._process_general_chat(query, user_id)
                
        except Exception as e:
            logger.error(f"Ошибка при маршрутизации запроса '{query}': {e}")
            return self._process_non_automotive(query, user_id)
    
    def _process_non_automotive(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка неавтомобильных запросов - отклонение"""
        logger.info(f"Отклонение неавтомобильного запроса: {query}")
        
        return {
            "type": "non_automotive",
            "query_type": "rejected",
            "message": "Здравствуйте! Это МОТОРЧИК.\nК сожалению, я специализируюсь только на автомобильных вопросах. Пожалуйста, задайте ваш вопрос, связанный с автомобилями, и я с радостью помогу!",
            "llama_used": False,
            "mistral_used": False,
            "rejected": True
        }
    
    def _process_automotive_search(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка поисковых автомобильных запросов"""
        logger.info(f"Обработка поискового запроса: {query}")
        
        try:
            from modules.search.auto_search_processor import AutoSearchProcessor
            processor = AutoSearchProcessor()
            result = processor.process_search_query(query, user_id)
            
            return {
                "type": "automotive_search",
                "query_type": "search",
                "result": result,
                "llama_used": False,
                "mistral_used": False
            }
        except Exception as e:
            logger.error(f"Ошибка в поиске: {e}")
            return {
                "type": "automotive_search",
                "query_type": "search",
                "message": "Извините, произошла ошибка при поиске автомобилей.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_automotive_question(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка вопросов об автомобилях"""
        logger.info(f"Обработка автомобильного вопроса: {query}")
        
        try:
            from llama_service import generate_with_llama as llama_chat
            
            system_prompt = """
            Ты - эксперт по автомобилям с многолетним опытом. Отвечай на вопросы об автомобилях простым и понятным языком.
            
            При ответе:
            - Объясняй технические термины простыми словами
            - Давай практические советы
            - Указывай плюсы и минусы при сравнениях
            - Приводи примеры конкретных моделей когда уместно
            - Будь дружелюбным и полезным
            """
            
            llama_response = llama_chat(f"{system_prompt.strip()}\n\nПользователь: {query}\nАссистент:")
            
            return {
                "type": "automotive_question",
                "query_type": "question",
                "message": llama_response,
                "llama_used": True,
                "mistral_used": False
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "automotive_question",
                "query_type": "question",
                "message": "Извините, произошла ошибка при обработке вопроса.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_automotive_comparison(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка сравнений"""
        logger.info(f"Обработка сравнения: {query}")
        
        try:
            from llama_service import generate_with_llama as llama_chat
            
            system_prompt = """
            Ты - эксперт по автомобилям. Сравнивай автомобильные варианты объективно и детально.
            
            При сравнении:
            - Указывай конкретные плюсы и минусы каждого варианта
            - Объясняй в каких ситуациях лучше выбрать каждый вариант
            - Давай практические рекомендации
            - Учитывай стоимость владения, надежность, комфорт
            - Будь честным и объективным
            """
            
            llama_response = llama_chat(f"{system_prompt.strip()}\n\nПользователь: {query}\nАссистент:")
            
            return {
                "type": "automotive_comparison",
                "query_type": "comparison",
                "message": llama_response,
                "llama_used": True,
                "mistral_used": False
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "automotive_comparison",
                "query_type": "comparison",
                "message": "Извините, произошла ошибка при сравнении.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_automotive_recommendation(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка рекомендаций"""
        logger.info(f"Обработка рекомендации: {query}")
        
        try:
            from llama_service import generate_with_llama as llama_chat
            
            system_prompt = """
            Ты - опытный автомобильный консультант. Давай персональные рекомендации по выбору автомобилей.
            
            При рекомендациях:
            - Учитывай потребности и бюджет пользователя
            - Указывай конкретные модели и марки
            - Объясняй почему именно эти варианты подходят
            - Давай советы по выбору и покупке
            - Учитывай надежность, стоимость владения, комфорт
            - Будь практичным и реалистичным
            """
            
            llama_response = llama_chat(f"{system_prompt.strip()}\n\nПользователь: {query}\nАссистент:")
            
            return {
                "type": "automotive_recommendation",
                "query_type": "recommendation",
                "message": llama_response,
                "llama_used": True,
                "mistral_used": False
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "automotive_recommendation",
                "query_type": "recommendation",
                "message": "Извините, произошла ошибка при формировании рекомендаций.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_automotive_help(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка помощи с поиском"""
        logger.info(f"Обработка помощи: {query}")
        
        try:
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - опытный автомобильный консультант. Помогай пользователям с поиском и выбором автомобилей.
            
            При помощи:
            - Дай пошаговую инструкцию
            - Объясни на что обратить внимание
            - Дай практические советы по выбору
            - Предложи критерии для поиска
            - Будь терпеливым и подробным
            - Учитывай разные уровни знаний пользователей
            """
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "automotive_help",
                "query_type": "help",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "automotive_help",
                "query_type": "help",
                "message": "Извините, произошла ошибка при оказании помощи.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_general_chat(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка базового общения"""
        logger.info(f"Обработка базового общения: {query}")
        
        try:
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - дружелюбный автомобильный ассистент. Отвечай на базовые приветствия вежливо, но помни, что ты специализируешься на автомобилях.
            Если пользователь задает неавтомобильные вопросы, вежливо направляй его к автомобильной тематике.
            """
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "general_chat",
                "query_type": "chat",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "general_chat",
                "query_type": "chat",
                "message": "Привет! Я готов помочь с вопросами об автомобилях.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_system_help(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка системной помощи"""
        logger.info(f"Обработка системной помощи: {query}")
        
        try:
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - автомобильный ассистент с широкими возможностями. Расскажи пользователю о своих функциях.
            
            Твои возможности:
            - Поиск автомобилей по различным критериям (марка, модель, цвет, цена, год и т.д.)
            - Сравнение моделей и характеристик автомобилей
            - Рекомендации по выбору автомобилей для разных потребностей
            - Ответы на технические вопросы об автомобилях
            - Помощь с кредитными расчетами
            - Общие вопросы об автомобилях и автопромышленности
            - Помощь в выборе подходящего автомобиля
            
            Будь дружелюбным, информативным и покажи примеры использования.
            """
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "system_help",
                "query_type": "help",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
            }
        except Exception as e:
            logger.error(f"Ошибка в Mistral: {e}")
            return {
                "type": "system_help",
                "query_type": "help",
                "message": "Я автомобильный ассистент. Могу помочь с поиском, сравнением и выбором автомобилей.",
                "llama_used": False,
                "mistral_used": False
            }
    
    def _process_credit_calculation(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка кредитных расчетов"""
        logger.info(f"Обработка кредитного расчета: {query}")
        
        try:
            from modules.calculators.loan_calculator import LoanCalculator
            calculator = LoanCalculator()
            result = calculator.calculate_loan(query)
            
            return {
                "type": "credit_calculation",
                "query_type": "calculation",
                "result": result,
                "llama_used": False,
                "mistral_used": False
            }
        except Exception as e:
            logger.error(f"Ошибка в кредитном калькуляторе: {e}")
            return {
                "type": "credit_calculation",
                "query_type": "calculation",
                "message": "Извините, произошла ошибка при расчете кредита.",
                "llama_used": False,
                "mistral_used": False
            }

# Пример использования
if __name__ == "__main__":
    router = EnhancedQueryRouterV3()
    
    test_queries = [
        # Автомобильные (должны обрабатываться)
        "Что такое ABS?",
        "Найди красный BMW",
        "Порекомендуй авто для семьи",
        
        # Системная помощь (должна обрабатываться)
        "Что ты умеешь?",
        
        # Базовое общение (должно обрабатываться)
        "Привет",
        "Как дела?",
        
        # Неавтомобильные (должны отклоняться)
        "Расскажи про погоду",
        "Как приготовить борщ?",
        "Что такое квантовая физика?",
        "Помоги с программированием"
    ]
    
    for query in test_queries:
        result = router.route_query(query)
        print(f"Запрос: '{query}'")
        print(f"Тип: {result['type']}")
        print(f"Отклонен: {result.get('rejected', False)}")
        print(f"Mistral использован: {result['mistral_used']}")
        print("-" * 50)
