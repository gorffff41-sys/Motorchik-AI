#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для v3.0 - проверка фильтрации неавтомобильных запросов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router_v3 import EnhancedQueryRouterV3, QueryType
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_v3_filtering():
    """Тестирует фильтрацию неавтомобильных запросов"""
    
    router = EnhancedQueryRouterV3()
    
    # Тестовые запросы
    test_queries = [
        # АВТОМОБИЛЬНЫЕ (должны обрабатываться)
        ("Что такое ABS?", QueryType.AUTOMOTIVE_QUESTION, True),
        ("Найди красный BMW", QueryType.AUTOMOTIVE_SEARCH, True),
        ("Порекомендуй авто для семьи", QueryType.AUTOMOTIVE_RECOMMENDATION, True),
        ("Что лучше: бензин или дизель?", QueryType.AUTOMOTIVE_COMPARISON, True),
        ("Как выбрать автомобиль?", QueryType.AUTOMOTIVE_HELP, True),
        ("Рассчитай кредит на 2 млн", QueryType.CREDIT_CALCULATION, True),
        
        # СИСТЕМНАЯ ПОМОЩЬ (должна обрабатываться)
        ("Что ты умеешь?", QueryType.SYSTEM_HELP, True),
        ("Кто ты?", QueryType.SYSTEM_HELP, True),
        ("Помощь", QueryType.SYSTEM_HELP, True),
        
        # БАЗОВОЕ ОБЩЕНИЕ (должно обрабатываться)
        ("Привет", QueryType.GENERAL_CHAT, True),
        ("Как дела?", QueryType.GENERAL_CHAT, True),
        ("Спасибо", QueryType.GENERAL_CHAT, True),
        ("Пока", QueryType.GENERAL_CHAT, True),
        ("Хорошо", QueryType.GENERAL_CHAT, True),
        
        # НЕАВТОМОБИЛЬНЫЕ (должны отклоняться)
        ("Расскажи про погоду", QueryType.NON_AUTOMOTIVE, False),
        ("Как приготовить борщ?", QueryType.NON_AUTOMOTIVE, False),
        ("Что такое квантовая физика?", QueryType.NON_AUTOMOTIVE, False),
        ("Помоги с программированием", QueryType.NON_AUTOMOTIVE, False),
        ("Расскажи анекдот", QueryType.NON_AUTOMOTIVE, False),
        ("Как дела на работе?", QueryType.NON_AUTOMOTIVE, False),
        ("Что посмотреть в кино?", QueryType.NON_AUTOMOTIVE, False),
        ("Как выучить английский?", QueryType.NON_AUTOMOTIVE, False),
        ("Расскажи про политику", QueryType.NON_AUTOMOTIVE, False),
        ("Как похудеть?", QueryType.NON_AUTOMOTIVE, False),
        ("Что такое блокчейн?", QueryType.NON_AUTOMOTIVE, False),
        ("Помоги с математикой", QueryType.NON_AUTOMOTIVE, False),
        ("Расскажи про историю", QueryType.NON_AUTOMOTIVE, False),
        ("Как инвестировать?", QueryType.NON_AUTOMOTIVE, False),
        ("Что такое любовь?", QueryType.NON_AUTOMOTIVE, False),
    ]
    
    print("🎯 ТЕСТ ФИЛЬТРАЦИИ V3.0")
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
    
    for i, (query, expected_type, should_process) in enumerate(test_queries, 1):
        # Классифицируем запрос
        actual_type = router.classifier.classify_query(query)
        
        # Обновляем статистику
        results_by_type[expected_type] += 1
        
        # Проверяем правильность классификации
        if actual_type == expected_type:
            correct_by_type[expected_type] += 1
            total_correct += 1
        else:
            errors.append((i, query, expected_type, actual_type, should_process))
    
    # Выводим только ошибки
    for i, query, expected, actual, should_process in errors:
        print(f"❌ {i:2d}. '{query}'")
        print(f"    Ожидалось: {expected.value}")
        print(f"    Получено:  {actual.value}")
        print(f"    Должен обрабатываться: {'Да' if should_process else 'Нет'}")
        print()
    
    # Итоговая статистика
    accuracy = (total_correct / total_tests) * 100
    
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 60)
    print(f"✅ Правильных классификаций: {total_correct}/{total_tests}")
    print(f"📊 Общая точность: {accuracy:.1f}%")
    print(f"❌ Ошибок: {len(errors)}")
    
    if accuracy >= 90:
        print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Точность >= 90%")
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

def test_router_responses():
    """Тестирует ответы роутера на разные типы запросов"""
    
    router = EnhancedQueryRouterV3()
    
    print("\n🔧 ТЕСТ ОТВЕТОВ РОУТЕРА:")
    print("=" * 60)
    
    test_queries = [
        # Автомобильные
        "Что такое ABS?",
        "Найди красный BMW",
        
        # Системная помощь
        "Что ты умеешь?",
        
        # Базовое общение
        "Привет",
        
        # Неавтомобильные
        "Расскажи про погоду",
        "Как приготовить борщ?"
    ]
    
    for query in test_queries:
        result = router.route_query(query)
        print(f"\n📝 Запрос: '{query}'")
        print(f"   Тип: {result['type']}")
        print(f"   Отклонен: {result.get('rejected', False)}")
        print(f"   Mistral: {result['mistral_used']}")
        if result.get('rejected'):
            print(f"   Ответ: {result['message'][:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    accuracy, errors = test_v3_filtering()
    test_router_responses()
    
    print(f"\n🎯 ФИНАЛЬНАЯ ТОЧНОСТЬ V3.0: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🏆 ФИЛЬТРАЦИЯ РАБОТАЕТ ОТЛИЧНО!")
    else:
        print("📈 Нужно улучшить фильтрацию")
