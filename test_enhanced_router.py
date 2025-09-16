#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки улучшенной системы маршрутизации запросов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router import EnhancedQueryRouter, QueryType
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_router():
    """Тестирует улучшенный роутер запросов"""
    
    router = EnhancedQueryRouter()
    
    # Тестовые запросы
    test_queries = [
        # Автомобильные вопросы
        ("Что такое ABS?", QueryType.AUTOMOTIVE_QUESTION),
        ("Объясни что такое турбонаддув", QueryType.AUTOMOTIVE_QUESTION),
        ("Что такое гибридный двигатель?", QueryType.AUTOMOTIVE_QUESTION),
        
        # Сравнения
        ("Что лучше: бензин или газ?", QueryType.AUTOMOTIVE_COMPARISON),
        ("Сравни автомат и механику", QueryType.AUTOMOTIVE_COMPARISON),
        ("Что лучше: BMW или Mercedes?", QueryType.AUTOMOTIVE_COMPARISON),
        
        # Рекомендации
        ("Порекомендуй авто для семьи", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Какой автомобиль выбрать для города?", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Посоветуй экономичный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION),
        
        # Помощь
        ("Как найти подходящий автомобиль?", QueryType.AUTOMOTIVE_HELP),
        ("Помоги выбрать машину", QueryType.AUTOMOTIVE_HELP),
        ("Что нужно знать при покупке авто?", QueryType.AUTOMOTIVE_HELP),
        
        # Системная помощь
        ("Что ты умеешь?", QueryType.SYSTEM_HELP),
        ("Расскажи о своих возможностях", QueryType.SYSTEM_HELP),
        ("Кто ты?", QueryType.SYSTEM_HELP),
        
        # Общий чат
        ("Привет", QueryType.GENERAL_CHAT),
        ("Как дела?", QueryType.GENERAL_CHAT),
        ("Спасибо", QueryType.GENERAL_CHAT),
        
        # Поиск автомобилей
        ("Найди красный BMW", QueryType.AUTOMOTIVE_SEARCH),
        ("Покажи машины до 2 млн", QueryType.AUTOMOTIVE_SEARCH),
        ("Ищу седан 2020 года", QueryType.AUTOMOTIVE_SEARCH),
        
        # Кредитные расчеты
        ("Рассчитай кредит на 2 млн", QueryType.CREDIT_CALCULATION),
        ("Кредитный калькулятор", QueryType.CREDIT_CALCULATION),
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО РОУТЕРА")
    print("=" * 60)
    
    correct_classifications = 0
    total_tests = len(test_queries)
    
    for query, expected_type in test_queries:
        print(f"\n📝 Запрос: '{query}'")
        print(f"🎯 Ожидаемый тип: {expected_type.value}")
        
        # Классифицируем запрос
        actual_type = router.classifier.classify_query(query)
        print(f"✅ Полученный тип: {actual_type.value}")
        
        # Проверяем правильность классификации
        if actual_type == expected_type:
            print("✅ КЛАССИФИКАЦИЯ ПРАВИЛЬНАЯ")
            correct_classifications += 1
        else:
            print("❌ КЛАССИФИКАЦИЯ НЕПРАВИЛЬНАЯ")
        
        # Тестируем маршрутизацию
        try:
            result = router.route_query(query, "test_user")
            print(f"🔄 Результат маршрутизации: {result.get('type', 'unknown')}")
            print(f"🤖 Llama использован: {result.get('llama_used', False)}")
            print(f"🧠 Mistral использован: {result.get('mistral_used', False)}")
        except Exception as e:
            print(f"❌ Ошибка маршрутизации: {e}")
        
        print("-" * 40)
    
    # Результаты тестирования
    accuracy = (correct_classifications / total_tests) * 100
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Правильных классификаций: {correct_classifications}/{total_tests}")
    print(f"📈 Точность: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ!")
    elif accuracy >= 60:
        print("👍 ХОРОШИЙ РЕЗУЛЬТАТ")
    else:
        print("⚠️ НУЖНО УЛУЧШИТЬ КЛАССИФИКАЦИЮ")

def test_mistral_integration():
    """Тестирует интеграцию с Mistral API"""
    
    print("\n🧠 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ С MISTRAL")
    print("=" * 60)
    
    try:
        from mistral_service import generate_mistral_response
        
        test_prompts = [
            "Что такое ABS в автомобиле?",
            "Что лучше: бензин или дизель?",
            "Порекомендуй семейный автомобиль"
        ]
        
        for prompt in test_prompts:
            print(f"\n📝 Тестируем: '{prompt}'")
            try:
                response = generate_mistral_response(prompt)
                print(f"✅ Ответ получен: {response[:100]}...")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
    except ImportError as e:
        print(f"❌ Не удалось импортировать mistral_service: {e}")

if __name__ == "__main__":
    test_enhanced_router()
    test_mistral_integration()