#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для достижения 90% точности классификации
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router import EnhancedQueryRouter, QueryType
from enhanced_test_queries import get_enhanced_test_queries, get_statistics
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_accuracy():
    """Тестирует улучшенную точность классификации"""
    
    router = EnhancedQueryRouter()
    test_queries = get_enhanced_test_queries()
    
    print("🎯 ТЕСТИРОВАНИЕ ДЛЯ ДОСТИЖЕНИЯ 90% ТОЧНОСТИ")
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
    
    for i, (query, expected_type) in enumerate(test_queries, 1):
        # Классифицируем запрос
        actual_type = router.classifier.classify_query(query)
        
        # Обновляем статистику
        results_by_type[expected_type] += 1
        if actual_type == expected_type:
            correct_by_type[expected_type] += 1
            total_correct += 1
            status = "✅"
        else:
            status = "❌"
        
        # Выводим результат (только ошибки для краткости)
        if actual_type != expected_type:
            print(f"{status} {i:2d}. '{query}'")
            print(f"    Ожидалось: {expected_type.value}")
            print(f"    Получено:  {actual_type.value}")
            print()
    
    # Итоговая статистика
    accuracy = (total_correct / total_tests) * 100
    
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 70)
    print(f"✅ Правильных классификаций: {total_correct}/{total_tests}")
    print(f"📊 Общая точность: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🎉 ЦЕЛЬ ДОСТИГНУТА! Точность >= 90%")
    elif accuracy >= 85:
        print("👍 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Точность >= 85%")
    elif accuracy >= 80:
        print("✅ ХОРОШИЙ РЕЗУЛЬТАТ! Точность >= 80%")
    else:
        print("⚠️ НУЖНО УЛУЧШИТЬ! Точность < 80%")
    
    print("\n📊 ТОЧНОСТЬ ПО ТИПАМ ЗАПРОСОВ:")
    print("-" * 70)
    
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            print(f"{query_type.value:25s}: {correct_by_type[query_type]:2d}/{results_by_type[query_type]:2d} ({type_accuracy:5.1f}%)")
    
    # Анализ проблемных типов
    print("\n🔍 АНАЛИЗ ПРОБЛЕМНЫХ ТИПОВ:")
    print("-" * 70)
    
    problem_types = []
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            if type_accuracy < 80:
                problem_types.append((query_type, type_accuracy))
    
    if problem_types:
        for query_type, accuracy in sorted(problem_types, key=lambda x: x[1]):
            print(f"⚠️ {query_type.value}: {accuracy:.1f}% точность")
    else:
        print("✅ Все типы запросов показывают хорошую точность!")
    
    return accuracy

def test_specific_problematic_queries():
    """Тестирует конкретные проблемные запросы"""
    
    router = EnhancedQueryRouter()
    
    # Проблемные запросы из предыдущих тестов
    problematic_queries = [
        ("Объясни что такое турбонаддув", QueryType.AUTOMOTIVE_QUESTION),
        ("Расскажи о своих возможностях", QueryType.SYSTEM_HELP),
        ("Покажи машины до 2 млн", QueryType.AUTOMOTIVE_SEARCH),
        ("Что нужно знать при покупке авто?", QueryType.AUTOMOTIVE_HELP),
    ]
    
    print("\n🔧 ТЕСТИРОВАНИЕ ПРОБЛЕМНЫХ ЗАПРОСОВ:")
    print("-" * 70)
    
    for query, expected_type in problematic_queries:
        actual_type = router.classifier.classify_query(query)
        status = "✅" if actual_type == expected_type else "❌"
        print(f"{status} '{query}'")
        print(f"    Ожидалось: {expected_type.value}")
        print(f"    Получено:  {actual_type.value}")
        print()

if __name__ == "__main__":
    accuracy = test_enhanced_accuracy()
    test_specific_problematic_queries()
    
    print(f"\n🎯 ФИНАЛЬНАЯ ТОЧНОСТЬ: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🏆 МИССИЯ ВЫПОЛНЕНА! Достигнута цель 90% точности!")
    else:
        print(f"📈 Нужно улучшить на {90 - accuracy:.1f}% для достижения цели")
