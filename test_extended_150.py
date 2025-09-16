#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный тест с 150 запросами для системы фильтрации v3.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router_v3 import EnhancedQueryRouterV3, QueryType
from extended_test_queries import get_extended_test_queries, get_statistics
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extended_150():
    """Тестирует систему с 150 запросами"""
    
    router = EnhancedQueryRouterV3()
    test_queries = get_extended_test_queries()
    
    print("🎯 РАСШИРЕННЫЙ ТЕСТ С 150 ЗАПРОСАМИ")
    print("=" * 70)
    
    # Статистика по типам
    stats = get_statistics()
    print("📊 СТАТИСТИКА ТЕСТОВЫХ ЗАПРОСОВ:")
    for query_type, count in stats.items():
        print(f"  {query_type.value}: {count} запросов")
    print(f"  ОБЩЕЕ КОЛИЧЕСТВО: {len(test_queries)} запросов\n")
    
    # Результаты по типам
    results_by_type = {}
    correct_by_type = {}
    
    for query_type in QueryType:
        results_by_type[query_type] = 0
        correct_by_type[query_type] = 0
    
    total_correct = 0
    total_tests = len(test_queries)
    
    print("🧪 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("-" * 70)
    
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
    
    # Выводим только первые 10 ошибок для краткости
    for i, query, expected, actual, should_process in errors[:10]:
        print(f"❌ {i:3d}. '{query}'")
        print(f"    Ожидалось: {expected.value}")
        print(f"    Получено:  {actual.value}")
        print(f"    Должен обрабатываться: {'Да' if should_process else 'Нет'}")
        print()
    
    if len(errors) > 10:
        print(f"... и еще {len(errors) - 10} ошибок")
        print()
    
    # Итоговая статистика
    accuracy = (total_correct / total_tests) * 100
    
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 70)
    print(f"✅ Правильных классификаций: {total_correct}/{total_tests}")
    print(f"📊 Общая точность: {accuracy:.1f}%")
    print(f"❌ Ошибок: {len(errors)}")
    
    if accuracy >= 95:
        print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Точность >= 95%")
    elif accuracy >= 90:
        print("👍 ХОРОШИЙ РЕЗУЛЬТАТ! Точность >= 90%")
    elif accuracy >= 85:
        print("✅ УДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ! Точность >= 85%")
    else:
        print("⚠️ НУЖНО УЛУЧШИТЬ! Точность < 85%")
    
    print("\n📊 ТОЧНОСТЬ ПО ТИПАМ ЗАПРОСОВ:")
    print("-" * 70)
    
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            status = "✅" if type_accuracy >= 90 else "⚠️" if type_accuracy >= 80 else "❌"
            print(f"{status} {query_type.value:25s}: {correct_by_type[query_type]:2d}/{results_by_type[query_type]:2d} ({type_accuracy:5.1f}%)")
    
    # Анализ проблемных типов
    print("\n🔍 АНАЛИЗ ПРОБЛЕМНЫХ ТИПОВ:")
    print("-" * 70)
    
    problem_types = []
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            if type_accuracy < 90:
                problem_types.append((query_type, type_accuracy))
    
    if problem_types:
        for query_type, accuracy in sorted(problem_types, key=lambda x: x[1]):
            print(f"⚠️ {query_type.value}: {accuracy:.1f}% точность")
    else:
        print("✅ Все типы запросов показывают отличную точность!")
    
    return accuracy, errors

def analyze_error_patterns(errors):
    """Анализирует паттерны ошибок"""
    if not errors:
        print("\n🎉 ОШИБОК НЕТ! Идеальная классификация!")
        return
    
    print(f"\n🔍 АНАЛИЗ {len(errors)} ОШИБОК:")
    print("-" * 70)
    
    error_patterns = {}
    for i, query, expected, actual, should_process in errors:
        pattern = f"{expected.value} -> {actual.value}"
        if pattern not in error_patterns:
            error_patterns[pattern] = []
        error_patterns[pattern].append(query)
    
    print("📋 ТОП-5 ПАТТЕРНОВ ОШИБОК:")
    for pattern, queries in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"\n🔸 {pattern} ({len(queries)} ошибок):")
        for query in queries[:3]:  # Показываем первые 3 примера
            print(f"  - '{query}'")
        if len(queries) > 3:
            print(f"  ... и еще {len(queries) - 3}")

def test_router_responses_sample():
    """Тестирует ответы роутера на выборке запросов"""
    
    router = EnhancedQueryRouterV3()
    
    print("\n🔧 ТЕСТ ОТВЕТОВ РОУТЕРА (ВЫБОРКА):")
    print("=" * 70)
    
    # Выбираем по одному примеру каждого типа
    sample_queries = [
        # Автомобильные
        "Что такое ABS?",
        "Найди красный BMW",
        "Порекомендуй авто для семьи",
        "Что лучше: бензин или дизель?",
        "Как выбрать автомобиль?",
        
        # Системная помощь
        "Что ты умеешь?",
        
        # Базовое общение
        "Привет",
        
        # Кредитные
        "Рассчитай кредит на 2 млн",
        
        # Неавтомобильные
        "Расскажи про погоду",
        "Как приготовить борщ?",
        "Что такое квантовая физика?"
    ]
    
    for query in sample_queries:
        result = router.route_query(query)
        print(f"\n📝 Запрос: '{query}'")
        print(f"   Тип: {result['type']}")
        print(f"   Отклонен: {result.get('rejected', False)}")
        print(f"   Mistral: {result['mistral_used']}")
        if result.get('rejected'):
            print(f"   Ответ: {result['message'][:80]}...")
        print("-" * 50)

if __name__ == "__main__":
    accuracy, errors = test_extended_150()
    analyze_error_patterns(errors)
    test_router_responses_sample()
    
    print(f"\n🎯 ФИНАЛЬНАЯ ТОЧНОСТЬ С 150 ЗАПРОСАМИ: {accuracy:.1f}%")
    
    if accuracy >= 95:
        print("🏆 СИСТЕМА РАБОТАЕТ ОТЛИЧНО!")
    elif accuracy >= 90:
        print("👍 СИСТЕМА РАБОТАЕТ ХОРОШО!")
    else:
        print("📈 Нужно улучшить систему")
