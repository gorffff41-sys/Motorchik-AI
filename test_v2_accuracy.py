#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для улучшенной версии v2.0 - цель 90% точности
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_query_router_v2 import EnhancedQueryRouterV2, QueryType
from enhanced_test_queries import get_enhanced_test_queries, get_statistics
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_v2_accuracy():
    """Тестирует точность классификации v2.0"""
    
    router = EnhancedQueryRouterV2()
    test_queries = get_enhanced_test_queries()
    
    print("🎯 ТЕСТИРОВАНИЕ V2.0 ДЛЯ ДОСТИЖЕНИЯ 90% ТОЧНОСТИ")
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
    
    for i, (query, expected_type) in enumerate(test_queries, 1):
        # expected_type уже является объектом QueryType
            
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
    print("=" * 70)
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
    print("-" * 70)
    
    for query_type in QueryType:
        if results_by_type[query_type] > 0:
            type_accuracy = (correct_by_type[query_type] / results_by_type[query_type]) * 100
            status = "✅" if type_accuracy >= 80 else "⚠️" if type_accuracy >= 60 else "❌"
            print(f"{status} {query_type.value:25s}: {correct_by_type[query_type]:2d}/{results_by_type[query_type]:2d} ({type_accuracy:5.1f}%)")
    
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
    
    return accuracy, errors

def analyze_errors(errors):
    """Анализирует ошибки классификации"""
    if not errors:
        print("\n🎉 ОШИБОК НЕТ! Идеальная классификация!")
        return
    
    print(f"\n🔍 АНАЛИЗ {len(errors)} ОШИБОК:")
    print("-" * 70)
    
    error_patterns = {}
    for i, query, expected, actual in errors:
        pattern = f"{expected.value} -> {actual.value}"
        if pattern not in error_patterns:
            error_patterns[pattern] = []
        error_patterns[pattern].append(query)
    
    for pattern, queries in error_patterns.items():
        print(f"\n📋 {pattern} ({len(queries)} ошибок):")
        for query in queries[:3]:  # Показываем первые 3 примера
            print(f"  - '{query}'")
        if len(queries) > 3:
            print(f"  ... и еще {len(queries) - 3}")

if __name__ == "__main__":
    accuracy, errors = test_v2_accuracy()
    analyze_errors(errors)
    
    print(f"\n🎯 ФИНАЛЬНАЯ ТОЧНОСТЬ V2.0: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🏆 МИССИЯ ВЫПОЛНЕНА! Достигнута цель 90% точности!")
    else:
        print(f"📈 Нужно улучшить на {90 - accuracy:.1f}% для достижения цели")
