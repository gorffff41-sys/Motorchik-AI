#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная система классификации и маршрутизации запросов v2.0
Цель: достичь 90% точности классификации
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
    GENERAL_CHAT = "general_chat"                     # Общение
    SYSTEM_HELP = "system_help"                       # Системная помощь
    CREDIT_CALCULATION = "credit_calculation"         # Кредитные расчеты

class EnhancedQueryClassifierV2:
    """Улучшенный классификатор запросов v2.0"""
    
    def __init__(self):
        # Базовые ключевые слова для каждого типа
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
                'плохо', 'ужасно', 'кошмар', 'не очень', 'так себе'
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
            QueryType.AUTOMOTIVE_SEARCH: 8
        }
    
    def classify_query(self, query: str) -> QueryType:
        """Классифицирует запрос по типу с улучшенной логикой"""
        query_lower = query.lower().strip()
        
        # Счетчики совпадений для каждого типа
        scores = {query_type: 0 for query_type in QueryType}
        
        # Подсчитываем совпадения ключевых слов
        for query_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Даем больший вес более длинным ключевым словам
                    weight = len(keyword.split()) if ' ' in keyword else 1
                    scores[query_type] += weight
        
        # Специальные правила для улучшения точности
        
        # 1. Если есть "что такое" + автомобильный термин = AUTOMOTIVE_QUESTION
        if any(phrase in query_lower for phrase in ['что такое', 'что это', 'что означает', 'что значит']):
            automotive_terms = ['abs', 'esp', 'asr', 'турбо', 'гибрид', 'автомат', 'механика', 
                              'вариатор', 'подвеска', 'двигатель', 'коробка', 'система']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_QUESTION] += 10
        
        # 2. Если есть "как работает" + автомобильный термин = AUTOMOTIVE_QUESTION
        if 'как работает' in query_lower or 'как устроен' in query_lower:
            automotive_terms = ['система', 'двигатель', 'коробка', 'подвеска', 'тормоз']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_QUESTION] += 10
        
        # 3. Если есть "что лучше" + автомобильные термины = AUTOMOTIVE_COMPARISON
        if 'что лучше' in query_lower or 'сравни' in query_lower:
            automotive_terms = ['бензин', 'дизель', 'автомат', 'механика', 'bmw', 'мерседес']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_COMPARISON] += 10
        
        # 4. Если есть "порекомендуй" + автомобильные слова = AUTOMOTIVE_RECOMMENDATION
        if any(phrase in query_lower for phrase in ['порекомендуй', 'посоветуй', 'какой автомобиль']):
            automotive_terms = ['авто', 'машину', 'автомобиль', 'семьи', 'города', 'трассы']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_RECOMMENDATION] += 10
        
        # 5. Если есть "как найти/выбрать" + автомобильные слова = AUTOMOTIVE_HELP
        if any(phrase in query_lower for phrase in ['как найти', 'как выбрать', 'помоги выбрать']):
            automotive_terms = ['авто', 'машину', 'автомобиль', 'подходящий', 'хороший']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_HELP] += 10
        
        # 6. Если есть "найди/покажи" + автомобильные слова = AUTOMOTIVE_SEARCH
        if any(phrase in query_lower for phrase in ['найди', 'покажи', 'ищу', 'хочу']):
            automotive_terms = ['авто', 'машину', 'bmw', 'мерседес', 'красный', 'белый']
            if any(term in query_lower for term in automotive_terms):
                scores[QueryType.AUTOMOTIVE_SEARCH] += 10
        
        # 7. Если есть кредитные слова = CREDIT_CALCULATION
        if any(phrase in query_lower for phrase in ['кредит', 'рассчитай', 'посчитай', 'платеж']):
            scores[QueryType.CREDIT_CALCULATION] += 10
        
        # 8. Если есть системные слова = SYSTEM_HELP
        if any(phrase in query_lower for phrase in ['что ты умеешь', 'кто ты', 'помощь', 'возможности']):
            scores[QueryType.SYSTEM_HELP] += 10
        
        # 9. Если есть приветственные слова = GENERAL_CHAT
        if any(phrase in query_lower for phrase in ['привет', 'здравствуй', 'как дела', 'спасибо']):
            scores[QueryType.GENERAL_CHAT] += 10
        
        # Находим тип с максимальным счетом
        max_score = max(scores.values())
        if max_score == 0:
            # Если нет совпадений, проверяем общую автомобильную направленность
            automotive_keywords = ['авто', 'машина', 'автомобиль', 'bmw', 'мерседес', 'тойота', 'лада']
            if any(keyword in query_lower for keyword in automotive_keywords):
                logger.info(f"Запрос '{query}' классифицирован как AUTOMOTIVE_SEARCH (по ключевым словам)")
                return QueryType.AUTOMOTIVE_SEARCH
            else:
                logger.info(f"Запрос '{query}' классифицирован как GENERAL_CHAT (по умолчанию)")
                return QueryType.GENERAL_CHAT
        
        # Если есть несколько типов с одинаковым максимальным счетом, выбираем по приоритету
        best_types = [query_type for query_type, score in scores.items() if score == max_score]
        if len(best_types) > 1:
            best_type = min(best_types, key=lambda x: self.priorities[x])
        else:
            best_type = best_types[0]
        
        logger.info(f"Запрос '{query}' классифицирован как {best_type.value} (счет: {max_score})")
        return best_type

class EnhancedQueryRouterV2:
    """Улучшенный роутер запросов v2.0"""
    
    def __init__(self):
        self.classifier = EnhancedQueryClassifierV2()
    
    def route_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Маршрутизирует запрос к соответствующему обработчику"""
        try:
            query_type = self.classifier.classify_query(query)
            
            logger.info(f"Маршрутизация запроса '{query}' как {query_type.value}")
            
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
            return self._process_general_chat(query, user_id)
    
    def _process_automotive_search(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка поисковых автомобильных запросов"""
        logger.info(f"Обработка поискового запроса: {query}")
        
        # Используем существующую логику поиска
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
        
        # Отправляем в Mistral с автомобильным контекстом
        try:
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - эксперт по автомобилям с многолетним опытом. Отвечай на вопросы об автомобилях простым и понятным языком.
            
            При ответе:
            - Объясняй технические термины простыми словами
            - Давай практические советы
            - Указывай плюсы и минусы при сравнениях
            - Приводи примеры конкретных моделей когда уместно
            - Будь дружелюбным и полезным
            """
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "automotive_question",
                "query_type": "question",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
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
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - эксперт по автомобилям. Сравнивай автомобильные варианты объективно и детально.
            
            При сравнении:
            - Указывай конкретные плюсы и минусы каждого варианта
            - Объясняй в каких ситуациях лучше выбрать каждый вариант
            - Давай практические рекомендации
            - Учитывай стоимость владения, надежность, комфорт
            - Будь честным и объективным
            """
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "automotive_comparison",
                "query_type": "comparison",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
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
            from mistral_service import generate_mistral_response
            
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
            
            mistral_response = generate_mistral_response(query, system_prompt)
            
            return {
                "type": "automotive_recommendation",
                "query_type": "recommendation",
                "message": mistral_response,
                "llama_used": False,
                "mistral_used": True
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
        """Обработка общего общения"""
        logger.info(f"Обработка общего чата: {query}")
        
        try:
            from mistral_service import generate_mistral_response
            
            system_prompt = """
            Ты - дружелюбный и полезный ассистент. Отвечай на общие вопросы вежливо и информативно.
            Будь естественным в общении, но помни, что ты специализируешься на автомобилях.
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
            # Используем существующую логику кредитных расчетов
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
    router = EnhancedQueryRouterV2()
    
    test_queries = [
        "Что такое ABS?",
        "Что лучше: бензин или газ?",
        "Порекомендуй авто для семьи",
        "Что ты умеешь?",
        "Привет",
        "Как дела?",
        "Как найти подходящий автомобиль?",
        "Найди красный BMW",
        "Рассчитай кредит на 2 млн"
    ]
    
    for query in test_queries:
        result = router.route_query(query)
        print(f"Запрос: '{query}'")
        print(f"Тип: {result['type']}")
        print(f"Mistral использован: {result['mistral_used']}")
        print("-" * 50)
