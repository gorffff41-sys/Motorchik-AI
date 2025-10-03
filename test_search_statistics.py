#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест статистики поиска и генерации ответов
"""

import requests
import json

def test_search_statistics():
    """Тестируем новую функциональность поиска с статистикой"""
    
    test_queries = [
        "Найди BMW X5",
        "Покажи все автомобили до 5 млн",
        "Ищу кроссоверы 2024 года",
        "Нужен дизельный внедорожник",
        "Покажи все марки автомобилей"
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ ПОИСКА С СТАТИСТИКОЙ")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Запрос: '{query}'")
        print("-" * 40)
        
        try:
            # Тестируем v4 роутер
            response = requests.post("http://localhost:5000/api/enhanced-chat-v4", json={
                "message": query,
                "user_id": "test_user"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Статус: {data.get('success', False)}")
                print(f"📊 Тип: {data.get('type', 'unknown')}")
                print(f"🔢 Всего найдено: {data.get('total_found', 0)}")
                
                # Показываем статистику
                stats = data.get('statistics', {})
                if stats:
                    print(f"📈 Уникальных марок: {len(stats.get('unique_brands', []))}")
                    print(f"🏷️ Марки: {', '.join(stats.get('unique_brands', []))}")
                    
                    top_cars = stats.get('top_cars_by_brand', [])
                    if top_cars:
                        print("🚗 Топ автомобили по маркам:")
                        for item in top_cars:
                            car = item['car']
                            print(f"  • {item['brand']} {car.get('model', '')} ({car.get('manufacture_year', '')}) - {car.get('price', 0):,.0f} руб")
                
                # Показываем сгенерированный ответ
                message = data.get('message', '')
                if message:
                    print(f"\n💬 Сгенерированный ответ:")
                    print(f"   {message[:200]}{'...' if len(message) > 200 else ''}")
                
                # Показываем информацию о версии
                version = data.get('version', 'unknown')
                features = data.get('features', [])
                print(f"\n🔧 Версия: {version}")
                if features:
                    print(f"✨ Функции: {', '.join(features)}")
                
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")
                print(f"   Ответ: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 40)

def test_database_statistics():
    """Тестируем функцию статистики напрямую"""
    
    print("\n🔍 ТЕСТИРОВАНИЕ ФУНКЦИИ СТАТИСТИКИ")
    print("=" * 60)
    
    try:
        from database import search_all_cars, get_search_statistics
        
        # Тестируем поиск BMW
        print("1. Поиск BMW...")
        cars = search_all_cars(brand="BMW")
        stats = get_search_statistics(cars)
        
        print(f"   Найдено: {stats['total_count']} автомобилей")
        print(f"   Уникальных марок: {len(stats['unique_brands'])}")
        print(f"   Марки: {', '.join(stats['unique_brands'])}")
        
        if stats['top_cars_by_brand']:
            print("   Топ автомобили:")
            for item in stats['top_cars_by_brand']:
                car = item['car']
                print(f"     • {item['brand']} {car.get('model', '')} - {car.get('price', 0):,.0f} руб")
        
        # Тестируем поиск по цене
        print("\n2. Поиск до 5 млн...")
        cars = search_all_cars(price_to=5000000)
        stats = get_search_statistics(cars)
        
        print(f"   Найдено: {stats['total_count']} автомобилей")
        print(f"   Уникальных марок: {len(stats['unique_brands'])}")
        print(f"   Марки: {', '.join(stats['unique_brands'])}")
        
        if stats['top_cars_by_brand']:
            print("   Топ автомобили:")
            for item in stats['top_cars_by_brand']:
                car = item['car']
                print(f"     • {item['brand']} {car.get('model', '')} - {car.get('price', 0):,.0f} руб")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования БД: {e}")

if __name__ == "__main__":
    test_database_statistics()
    test_search_statistics()
