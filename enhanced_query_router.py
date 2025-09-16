#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная система классификации и маршрутизации запросов
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

class EnhancedQueryClassifier:
    """Улучшенный классификатор запросов"""
    
    def __init__(self):
        # Паттерны для разных типов запросов
        self.patterns = {
            QueryType.AUTOMOTIVE_SEARCH: [
                r'\b(найди|найти|покажи|показать|ищу|хочу|нужен|нужна|нужно|выведи|вывести|покажи\s+мне|найди\s+мне)\b.*\b(авто|машину|автомобиль|bmw|мерседес|тойота|лада|машины|автомобили|автомобилей)\b',
                r'\b(авто|машина|автомобиль)\b.*\b(с\s+\d+|для\s+\d+|красный|белый|черный|седан|хэтчбек|внедорожник)\b',
                r'\b(красный|белый|черный|синий|зеленый)\b.*\b(авто|машина|автомобиль|седан|хэтчбек|внедорожник)\b',
                r'\b(седан|хэтчбек|универсал|внедорожник|кроссовер|спорткар)\b.*\b(до\s+\d+|от\s+\d+|с\s+\d+)\b',
                r'\b(5-местный|пятиместный|7-местный|семьместный)\b',
                r'\b(бензин|дизель|автомат|механика|передний\s+привод|полный\s+привод)\b.*\b(авто|машина)\b'
            ],
            
            QueryType.AUTOMOTIVE_QUESTION: [
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о|расскажи|объясни|разъясни|опери|характеризуй)\b.*\b(abs|esp|asr|ebd|tcs|vsc|hdc|hac|dsc|asc|abc|турбо|компрессор|инжектор|карбюратор|катализатор|сажевый\s+фильтр|гибрид|электромобиль|plug-in|hev|phev|bev|автомат|механика|вариатор|робот|дсг|типтроник|передний\s+привод|задний\s+привод|полный\s+привод|4wd|awd|fwd|rwd|подвеска|амортизатор|пружина|стабилизатор|рычаг|тормоз|диск|колодка|суппорт|двигатель|мотор|цилиндр|клапан|поршень|коленвал|коробка|трансмиссия|сцепление|дифференциал|редуктор|кондиционер|климат|отопление|вентиляция|обогрев|навигация|gps|мультимедиа|bluetooth|usb|aux|страховка|каско|осаго|дтп|гаи|гибдд|техосмотр|то|сервис|гарантия|запчасти)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(турбо|компрессор|инжектор|карбюратор|катализатор|сажевый\s+фильтр)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(гибрид|электромобиль|plug-in|hev|phev|bev)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(автомат|механика|вариатор|робот|дсг|типтроник)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(передний\s+привод|задний\s+привод|полный\s+привод|4wd|awd|fwd|rwd)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(подвеска|амортизатор|пружина|стабилизатор|рычаг)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(тормоз|диск|колодка|суппорт|abs|ebd)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(двигатель|мотор|цилиндр|клапан|поршень|коленвал)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(коробка|трансмиссия|сцепление|дифференциал|редуктор)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(кондиционер|климат|отопление|вентиляция|обогрев)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(навигация|gps|мультимедиа|bluetooth|usb|aux)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(страховка|каско|осаго|дтп|гаи|гибдд)\b',
                r'\b(что\s+такое|что\s+это|объясни|расскажи\s+про|расскажи\s+о)\b.*\b(техосмотр|то|сервис|гарантия|запчасти)\b'
            ],
            
            QueryType.AUTOMOTIVE_COMPARISON: [
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(бензин|дизель|газ|электро|гибрид)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(автомат|механика|вариатор|робот)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(передний|задний|полный\s+привод)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(bmw|мерседес|ауди|тойота|хонда|лада)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(седан|хэтчбек|универсал|внедорожник)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(новый|подержанный|б/у|с\s+пробегом)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(дешевый|дорогой|бюджетный|премиум)\b',
                r'\b(что\s+лучше|что\s+выбрать|сравни|сравнение|разница\s+между)\b.*\b(экономичный|мощный|быстрый|надежный)\b'
            ],
            
            QueryType.AUTOMOTIVE_RECOMMENDATION: [
                r'\b(порекомендуй|рекомендуй|посоветуй|советуй|подскажи)\b.*\b(авто|машину|автомобиль)\b',
                r'\b(порекомендуй|рекомендуй|посоветуй|советуй|подскажи)\b.*\b(для\s+семьи|для\s+города|для\s+трассы|для\s+работы)\b',
                r'\b(порекомендуй|рекомендуй|посоветуй|советуй|подскажи)\b.*\b(семейный|городской|спортивный|экономичный)\b',
                r'\b(какой\s+авто|какую\s+машину|какой\s+автомобиль)\b.*\b(выбрать|купить|взять)\b',
                r'\b(какой\s+авто|какую\s+машину|какой\s+автомобиль)\b.*\b(для\s+семьи|для\s+города|для\s+трассы|для\s+работы)\b',
                r'\b(нужен|нужна|нужно)\b.*\b(авто|машина|автомобиль)\b.*\b(для\s+семьи|для\s+города|для\s+трассы|для\s+работы)\b',
                r'\b(хочу|ищу|ищем)\b.*\b(авто|машину|автомобиль)\b.*\b(для\s+семьи|для\s+города|для\s+трассы|для\s+работы)\b'
            ],
            
            QueryType.AUTOMOTIVE_HELP: [
                r'\b(как\s+найти|как\s+выбрать|как\s+купить|как\s+продать)\b.*\b(авто|машину|автомобиль)\b',
                r'\b(как\s+найти|как\s+выбрать|как\s+купить|как\s+продать)\b.*\b(подходящий|хороший|надежный|качественный)\b',
                r'\b(как\s+найти|как\s+выбрать|как\s+купить|как\s+продать)\b.*\b(авто|машину|автомобиль)\b.*\b(подходящий|хороший|надежный|качественный)\b',
                r'\b(помоги\s+найти|помоги\s+выбрать|помоги\s+купить|помоги\s+продать)\b.*\b(авто|машину|автомобиль)\b',
                r'\b(помоги\s+найти|помоги\s+выбрать|помоги\s+купить|помоги\s+продать)\b.*\b(подходящий|хороший|надежный|качественный)\b',
                r'\b(помоги\s+найти|помоги\s+выбрать|помоги\s+купить|помоги\s+продать)\b.*\b(авто|машину|автомобиль)\b.*\b(подходящий|хороший|надежный|качественный)\b',
                r'\b(что\s+нужно\s+знать|что\s+важно\s+учесть|на\s+что\s+обратить\s+внимание)\b.*\b(при\s+покупке|при\s+выборе|при\s+продаже)\b',
                r'\b(что\s+нужно\s+знать|что\s+важно\s+учесть|на\s+что\s+обратить\s+внимание)\b.*\b(авто|машины|автомобиля)\b'
            ],
            
            QueryType.GENERAL_CHAT: [
                r'\b(привет|здравствуй|добрый\s+день|добрый\s+вечер|доброе\s+утро)\b',
                r'\b(как\s+дела|как\s+ты|как\s+у\s+вас\s+дела|как\s+поживаешь|как\s+поживаете)\b',
                r'\b(чем\s+занимаешься|что\s+делаешь|что\s+делаете|как\s+работаешь|как\s+работаете)\b',
                r'\b(спасибо|благодарю|спасибо\s+большое|благодарю\s+вас)\b',
                r'\b(пока|до\s+свидания|до\s+встречи|увидимся|всего\s+доброго)\b',
                r'\b(хорошо|отлично|прекрасно|замечательно|супер|классно)\b',
                r'\b(плохо|ужасно|кошмар|не\s+очень|так\s+себе)\b'
            ],
            
            QueryType.SYSTEM_HELP: [
                r'\b(кто\s+ты|кто\s+вы|что\s+ты\s+умеешь|что\s+вы\s+умеете|расскажи\s+о\s+себе|расскажите\s+о\s+себе)\b',
                r'\b(что\s+ты\s+можешь|что\s+вы\s+можете|какие\s+у\s+тебя\s+возможности|какие\s+у\s+вас\s+возможности|расскажи\s+о\s+своих\s+возможностях|расскажите\s+о\s+своих\s+возможностях)\b',
                r'\b(как\s+ты\s+работаешь|как\s+вы\s+работаете|как\s+ты\s+функционируешь|как\s+вы\s+функционируете)\b',
                r'\b(помощь|help|справка|инструкция|руководство|как\s+пользоваться|что\s+ты\s+умеешь\s+делать|что\s+вы\s+умеете\s+делать)\b',
                r'\b(что\s+ты\s+знаешь|что\s+вы\s+знаете|о\s+чем\s+ты\s+можешь\s+рассказать|о\s+чем\s+вы\s+можете\s+рассказать)\b',
                r'\b(какие\s+функции|какие\s+команды|что\s+можешь\s+сделать|что\s+можете\s+сделать|твои\s+возможности|ваши\s+возможности)\b',
                r'\b(расскажи\s+что\s+умеешь|расскажите\s+что\s+умеете|покажи\s+возможности|покажите\s+возможности)\b'
            ],
            
            QueryType.CREDIT_CALCULATION: [
                r'\b(рассчитай|рассчитать|посчитай|посчитать)\b.*\b(кредит|платеж|платежи|ставку|ставка)\b',
                r'\b(кредитный\s+калькулятор|кредитный\s+калькулятор|кредитный\s+калькулятор)\b',
                r'\b(сколько\s+будет|сколько\s+составит|какая\s+сумма|какая\s+переплата)\b.*\b(кредит|платеж|платежи)\b',
                r'\b(ежемесячный\s+платеж|ежемесячные\s+платежи|первоначальный\s+взнос|срок\s+кредита)\b',
                r'\b(ставка\s+кредита|процентная\s+ставка|годовая\s+ставка|эффективная\s+ставка)\b'
            ]
        }
    
    def classify_query(self, query: str) -> QueryType:
        """Классифицирует запрос по типу"""
        query_lower = query.lower().strip()
        
        # Проверяем паттерны в порядке приоритета
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"Запрос '{query}' классифицирован как {query_type.value}")
                    return query_type
        
        # Если не найден специфический тип, проверяем общую автомобильную направленность
        automotive_keywords = [
            'авто', 'машина', 'автомобиль', 'bmw', 'мерседес', 'тойота', 'лада', 'хонда', 'ниссан',
            'седан', 'хэтчбек', 'внедорожник', 'бензин', 'дизель', 'автомат', 'механика'
        ]
        
        if any(keyword in query_lower for keyword in automotive_keywords):
            logger.info(f"Запрос '{query}' классифицирован как AUTOMOTIVE_SEARCH (по ключевым словам)")
            return QueryType.AUTOMOTIVE_SEARCH
        
        # По умолчанию - общий чат
        logger.info(f"Запрос '{query}' классифицирован как GENERAL_CHAT (по умолчанию)")
        return QueryType.GENERAL_CHAT

class EnhancedQueryRouter:
    """Улучшенный роутер запросов"""
    
    def __init__(self):
        self.classifier = EnhancedQueryClassifier()
    
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
        from modules.search.auto_search_processor import AutoSearchProcessor
        processor = AutoSearchProcessor()
        result = processor.process_search_query(query, user_id)
        
        return {
            "type": "automotive_search",
            "query_type": "search",
            "result": result,
            "llama_used": False
        }
    
    def _process_automotive_question(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка вопросов об автомобилях"""
        logger.info(f"Обработка автомобильного вопроса: {query}")
        
        # Отправляем в Mistral с автомобильным контекстом
        from mistral_service import generate_mistral_response
        
        # Создаем специализированный промт для автомобильных вопросов
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
    
    def _process_automotive_comparison(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка сравнений"""
        logger.info(f"Обработка сравнения: {query}")
        
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
    
    def _process_automotive_recommendation(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка рекомендаций"""
        logger.info(f"Обработка рекомендации: {query}")
        
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
    
    def _process_automotive_help(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка помощи с поиском"""
        logger.info(f"Обработка помощи: {query}")
        
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
    
    def _process_general_chat(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка общего общения"""
        logger.info(f"Обработка общего чата: {query}")
        
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
    
    def _process_system_help(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка системной помощи"""
        logger.info(f"Обработка системной помощи: {query}")
        
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
    
    def _process_credit_calculation(self, query: str, user_id: str) -> Dict[str, Any]:
        """Обработка кредитных расчетов"""
        logger.info(f"Обработка кредитного расчета: {query}")
        
        # Используем существующую логику кредитных расчетов
        from modules.calculators.loan_calculator import LoanCalculator
        calculator = LoanCalculator()
        result = calculator.calculate_loan(query)
        
        return {
            "type": "credit_calculation",
            "query_type": "calculation",
            "result": result,
            "llama_used": False
        }

# Пример использования
if __name__ == "__main__":
    router = EnhancedQueryRouter()
    
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
        print(f"Llama использован: {result['llama_used']}")
        print("-" * 50)

