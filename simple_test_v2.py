#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для v2.0 с базовыми запросами
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router_v2 import EnhancedQueryRouterV2, QueryType
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_test_v2():
    """Простой тест v2.0 с базовыми запросами"""
    
    router = EnhancedQueryRouterV2()
    
    # Базовые тестовые запросы
    test_queries = [
        # Автомобильные вопросы
        ("Что такое ABS?", QueryType.AUTOMOTIVE_QUESTION),
        ("Объясни что такое турбонаддув", QueryType.AUTOMOTIVE_QUESTION),
        ("Что такое гибридный двигатель?", QueryType.AUTOMOTIVE_QUESTION),
        ("Как работает вариатор?", QueryType.AUTOMOTIVE_QUESTION),
        ("Что означает ASR в автомобиле?", QueryType.AUTOMOTIVE_QUESTION),
        
        # Сравнения
        ("Что лучше: бензин или газ?", QueryType.AUTOMOTIVE_COMPARISON),
        ("Сравни автомат и механику", QueryType.AUTOMOTIVE_COMPARISON),
        ("Что лучше: BMW или Mercedes?", QueryType.AUTOMOTIVE_COMPARISON),
        ("Сравни дизель и бензин", QueryType.AUTOMOTIVE_COMPARISON),
        ("Что лучше: передний или полный привод?", QueryType.AUTOMOTIVE_COMPARISON),
        
        # Рекомендации
        ("Порекомендуй авто для семьи", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Какой автомобиль выбрать для города?", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Посоветуй экономичный автомобиль", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Рекомендуй машину для начинающего водителя", QueryType.AUTOMOTIVE_RECOMMENDATION),
        ("Какой автомобиль лучше для дальних поездок?", QueryType.AUTOMOTIVE_RECOMMENDATION),
        
        # Помощь
        ("Как найти подходящий автомобиль?", QueryType.AUTOMOTIVE_HELP),
        ("Помоги выбрать машину", QueryType.AUTOMOTIVE_HELP),
        ("Что нужно знать при покупке авто?", QueryType.AUTOMOTIVE_HELP),
        ("Как правильно выбрать автомобиль?", QueryType.AUTOMOTIVE_HELP),
        ("Помоги найти хорошую машину", QueryType.AUTOMOTIVE_HELP),
        
        # Системная помощь
        ("Что ты умеешь?", QueryType.SYSTEM_HELP),
        ("Расскажи о своих возможностях", QueryType.SYSTEM_HELP),
        ("Кто ты?", QueryType.SYSTEM_HELP),
        ("Какие у тебя функции?", QueryType.SYSTEM_HELP),
        ("Что ты можешь делать?", QueryType.SYSTEM_HELP),
        
        # Общий чат
        ("Привет", QueryType.GENERAL_CHAT),
        ("Как дела?", QueryType.GENERAL_CHAT),
        ("Спасибо", QueryType.GENERAL_CHAT),
        ("Здравствуйте", QueryType.GENERAL_CHAT),
        ("Добрый день", QueryType.GENERAL_CHAT),
        
        # Поиск автомобилей
        ("Найди красный BMW", QueryType.AUTOMOTIVE_SEARCH),
        ("Покажи машины до 2 млн", QueryType.AUTOMOTIVE_SEARCH),
        ("Ищу седан 2020 года", QueryType.AUTOMOTIVE_SEARCH),
        ("Найди белый Mercedes", QueryType.AUTOMOTIVE_SEARCH),
        ("Покажи внедорожники", QueryType.AUTOMOTIVE_SEARCH),
        
        # Кредитные расчеты
        ("Рассчитай кредит на 2 млн", QueryType.CREDIT_CALCULATION),
        ("Кредитный калькулятор", QueryType.CREDIT_CALCULATION),
        ("Посчитай ежемесячный платеж", QueryType.CREDIT_CALCULATION),
        ("Рассчитай кредит на автомобиль", QueryType.CREDIT_CALCULATION),
        ("Сколько будет переплата по кредиту?", QueryType.CREDIT_CALCULATION),
    ]
    
    print("🎯 ПРОСТОЙ ТЕСТ V2.0")
    print("=" * 60)
    
    # Результаты по типам
    results_by_type = {}
    correct_by_type = {}
    
    for query_type in QueryType:
        results_by_type[query_type] = 0
        correct_by_type[query_type] = 0
    
    total_correct = 0
    total_tests = len(test_queries)
    
    print("🧪 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("-" * 60)
    
    errors = []
    
    for i, (query, expected_type) in enumerate(test_queries, 1):
        # Классифицируем запрос
        actual_type = router.classifier.classify_query(query)
        
        # Обновляем статистику
        results_by_type[expected_type] += 1
        if actual_type == expected_type:
            correct_by_type[expected_type] += 1
            total_correct += 1
        else:
            errors.append((i, query, expected_type, actual_type))
    
    # Выводим только ошибки
    for i, query, expected, actual in errors:
        print(f"❌ {i:2d}. '{query}'")
        print(f"    Ожидалось: {expected.value}")
        print(f"    Получено:  {actual.value}")
        print()
    
    # Итоговая статистика
    accuracy = (total_correct / total_tests) * 100
    
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 60)
    print(f"✅ Правильных классификаций: {total_correct}/{total_tests}")
    print(f"📊 Общая точность: {accuracy:.1f}%")
    print(f"❌ Ошибок: {len(errors)}")
    
    if accuracy >= 90:
        print("🎉 ЦЕЛЬ ДОСТИГНУТА! Точность >= 90%")
    elif accuracy >= 85:
        print("👍 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Точность >= 85%")
    elif accuracy >= 80:
        print("✅ ХОРОШИЙ РЕЗУЛЬТАТ! Точность >= 80%")
    else:
        print("⚠️ НУЖНО УЛУЧШИТЬ! Точность < 80%")
    
    print("\n📊 ТОЧНОСТЬ ПО ТИПАМ ЗАПРОСОВ:")
    print("-" * 60)
    
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            status = "✅" if type_accuracy >= 80 else "⚠️" if type_accuracy >= 60 else "❌"
            print(f"{status} {query_type.value:25s}: {correct_by_type[query_type]:2d}/{results_by_type[query_type]:2d} ({type_accuracy:5.1f}%)")
    
    return accuracy, errors

if __name__ == "__main__":
    accuracy, errors = simple_test_v2()
    
    print(f"\n🎯 ФИНАЛЬНАЯ ТОЧНОСТЬ V2.0: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🏆 МИССИЯ ВЫПОЛНЕНА! Достигнута цель 90% точности!")
    else:
        print(f"📈 Нужно улучшить на {90 - accuracy:.1f}% для достижения цели")
