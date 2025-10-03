#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор ответов для поиска автомобилей с использованием DeepSeek или Llama
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SearchResponseGenerator:
    """Генератор ответов для поиска автомобилей"""
    
    def __init__(self):
        self.deepseek_available = self._check_deepseek_availability()
        self._llama_cached_available: Optional[bool] = None
        
    def _check_deepseek_availability(self) -> bool:
        """Проверяет доступность DeepSeek API"""
        try:
            from deepseek_service import deepseek_service
            # Простая проверка доступности
            return hasattr(deepseek_service, 'generate_response')
        except ImportError:
            return False
        except Exception:
            return False

    def _check_llama_availability(self) -> bool:
        """Быстрая проверка доступности Ollama Llama (/api/tags). Кэшируется в памяти на время процесса."""
        if self._llama_cached_available is not None:
            return self._llama_cached_available
        try:
            import requests
            for base in ("http://host.docker.internal:11434", "http://localhost:11434", "http://127.0.0.1:11434"):
                try:
                    r = requests.get(f"{base}/api/tags", timeout=2)
                    if r.status_code == 200:
                        self._llama_cached_available = True
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        self._llama_cached_available = False
        return False
    
    def generate_search_response(self, query: str, cars: List[Dict], statistics: Dict, entities: Dict) -> str:
        """
        Генерирует ответ с информацией о найденных автомобилях
        
        Args:
            query: Исходный запрос пользователя
            cars: Список найденных автомобилей
            statistics: Статистика поиска
            entities: Извлеченные сущности
            
        Returns:
            Сгенерированный ответ
        """
        try:
            # Приоритет: DeepSeek v3 → фолбэк на Llama
            try:
                ds_txt = self._generate_with_deepseek(query, cars, statistics, entities)
                ds_txt_stripped = (ds_txt or "").strip()
                if ds_txt_stripped:
                    logger.info(f"SearchResponse: using DeepSeek result (len={len(ds_txt_stripped)})")
                    return ds_txt_stripped
            except Exception:
                # Продолжаем к Llama
                pass

            # Fallback: Llama
            try:
                llama_txt = self._generate_with_llama(query, cars, statistics, entities)
                llama_txt_stripped = (llama_txt or "").strip()
                if llama_txt_stripped:
                    logger.info(f"SearchResponse: DeepSeek empty → using Llama result (len={len(llama_txt_stripped)})")
                    return llama_txt_stripped
            except Exception:
                pass

            logger.warning("SearchResponse: both DeepSeek and Llama returned empty responses")
            return ""
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return self._generate_fallback_response(cars, statistics)
    
    def _generate_with_deepseek(self, query: str, cars: List[Dict], statistics: Dict, entities: Dict) -> str:
        """Генерация ответа с помощью DeepSeek"""
        try:
            from deepseek_service import deepseek_service
            
            # Берем не более 5 автомобилей для показа/генерации
            cars_limited = (cars or [])[:5]
            # Формируем жестко ограниченный контекст только из имеющихся данных
            context = self._build_context(cars_limited, statistics, entities)
            
            prompt = f"""Ты — автомобильный ассистент «Моторчик». Пользователь искал: "{query}".

Ты должен дать ответ, основанный в первую очередь на подтвержденных данных ниже.

**ЧТО РАЗРЕШЕНО:**
- Использовать свои знания для дополнения ответа справочной информацией о марках автомобилей, технологиях, характеристиках
- Объяснять особенности различных моделей, классов автомобилей
- Давать общие рекомендации по выбору автомобиля
- Отвечать на вопросы об автомобильной тематике

**ЧТО ЗАПРЕЩЕНО:**
- Придумывать, выдумывать или добавлять конкретные автомобили, которых нет в данных ниже
- Указывать цены, года выпуска, комплектации, которых нет в данных
- Создавать несуществующие предложения о продаже
- Вводить в заблуждение о наличии автомобилей

**Данные для формирования ответа:**

1.  **Статистика:**
    - Всего найдено автомобилей: {statistics.get('total_count', 0)}
    - Уникальные марки: {', '.join(statistics.get('unique_brands', [])) if statistics.get('unique_brands') else '—'}

2.  **Список автомобилей (не более 5):**
    {self._format_cars_list_for_prompt(cars_limited)}

**Инструкции для ответа:**

- Ответ должен быть на русском языке.
- **Если в данных есть автомобили:**
    1. Сообщи, сколько всего найдено автомобилей и перечисли уникальные марки
    2. Перечисли до 5 автомобилей из данных, указывая ТОЛЬКО те атрибуты, которые есть в данных
    3. Можешь дополнить ответ справочной информацией о марках из данных, их особенностях, истории
    4. Можешь дать общие рекомендации по выбору подобных автомобилей

- **Если данных нет:**
    - Сообщи, что по запросу автомобилей не найдено
    - Можешь дать общую справочную информацию по теме запроса
    - Можешь порекомендовать уточнить параметры поиска

**Пример правильного ответа:**
"Найдено 3 автомобиля BMW. Марки в результатах: BMW.
Конкретные предложения:
- BMW 3 Series 2020 года, 2 500 000 руб., Москва
- BMW X5 2019 года, 3 800 000 руб., Санкт-Петербург

Справочная информация: BMW — немецкий производитель, известный своими спортивными характеристиками. Модель 3 Series относится к бизнес-классу, а X5 — кроссовер премиум-сегмента. Рекомендую обратить внимание на год выпуска и пробег при выборе."

Всегда четко разделяй конкретные данные из системы и справочную информацию!
"""
            
            # В ЭТОМ РЕЖИМЕ DeepSeek НЕ ДОЛЖЕН САМОСТОЯТЕЛЬНО ИСКАТЬ ДАННЫЕ, только генерировать текст из готового промпта
            response_text = deepseek_service.generate_text(
                prompt,
                system_prompt="Ты — ассистент. Отвечай на русском языке. Используй ТОЛЬКО предоставленные данные."
            )
            # Fallback на Llama, если DeepSeek вернул пусто/ошибку
            if not response_text or "не удалось сгенерировать" in response_text.lower():
                return self._generate_with_llama(query, cars, statistics, entities)
            return response_text
            
        except Exception as e:
            logger.error(f"Ошибка DeepSeek: {e}")
            return self._generate_with_llama(query, cars, statistics, entities)
    
    def _generate_with_llama(self, query: str, cars: List[Dict], statistics: Dict, entities: Dict) -> str:
        """Генерация ответа с помощью Llama"""
        try:
            from llama_service import generate_with_llama
            
            cars_limited = (cars or [])[:5]
            context = self._build_context(cars_limited, statistics, entities)
            
            prompt = f"""
Ты — автомобильный ассистент Моторчик. Пользователь искал: "{query}".

Ниже приведены ТОЛЬКО ПОДТВЕРЖДЕННЫЕ ДАННЫЕ. НИЧЕГО НЕ ПРИДУМЫВАЙ.

Статистика (основана на БД):
- Всего найдено автомобилей: {statistics.get('total_count', 0)}
- Количество уникальных марок: {len(statistics.get('unique_brands', []))}
- Марки: {', '.join(statistics.get('unique_brands', [])) if statistics.get('unique_brands') else '—'}

Список автомобилей (максимум 5):
{self._format_cars_list_for_prompt(cars_limited)}

Сформируй КРАТКИЙ ответ на русском языке, СТРОГО ОСНОВЫВАЯСЬ ТОЛЬКО НА ДАННЫХ ВЫШЕ:
- Сколько всего найдено и какие уникальные марки.
- До 5 автомобилей (марка, модель, год, цена/город — только если они есть).
- Если данных нет — так и скажи.
"""
            
            response = generate_with_llama(prompt, {})
            return response
            
        except Exception as e:
            logger.error(f"Ошибка Llama: {e}")
            return self._generate_fallback_response(cars, statistics)
    
    def _build_context(self, cars: List[Dict], statistics: Dict, entities: Dict) -> str:
        """Строит контекст для генерации ответа"""
        context_parts = []
        
        # Основная статистика
        context_parts.append(f"Найдено {statistics['total_count']} автомобилей")
        context_parts.append(f"Уникальных марок: {len(statistics['unique_brands'])}")
        
        # Марки
        if statistics['unique_brands']:
            context_parts.append(f"Марки: {', '.join(statistics['unique_brands'])}")
        
        # Список до 5 автомобилей, только известные поля
        if cars:
            context_parts.append("Автомобили (до 5):")
            for car in cars[:5]:
                parts = []
                if car.get('mark'):
                    parts.append(str(car.get('mark')))
                if car.get('model'):
                    parts.append(str(car.get('model')))
                if car.get('manufacture_year'):
                    parts.append(str(car.get('manufacture_year')))
                base = ' '.join(parts) if parts else 'Автомобиль'
                extras = []
                if car.get('price'):
                    try:
                        extras.append(f"цена {int(car.get('price')):,.0f} руб".replace(',', ' '))
                    except Exception:
                        extras.append(f"цена {car.get('price')}")
                if car.get('city'):
                    extras.append(f"город {car.get('city')}")
                line = base
                if extras:
                    line += ", " + ", ".join(extras)
                context_parts.append(f"- {line}")
        
        return "\n".join(context_parts)
    
    def _format_top_cars(self, top_cars: List[Dict]) -> str:
        """Форматирует топ автомобили для промпта"""
        if not top_cars:
            return "Нет данных"
        
        formatted = []
        for item in top_cars:
            car = item['car']
            formatted.append(f"- {item['brand']} {car.get('model', '')} ({car.get('manufacture_year', '')}) - {car.get('price', 0):,.0f} руб (всего: {item['count']})")
        
        return "\n".join(formatted)

    def _format_cars_list_for_prompt(self, cars: List[Dict]) -> str:
        if not cars:
            return "—"
        lines = []
        for idx, car in enumerate(cars, 1):
            parts = []
            if car.get('mark'):
                parts.append(str(car.get('mark')))
            if car.get('model'):
                parts.append(str(car.get('model')))
            if car.get('manufacture_year'):
                parts.append(str(car.get('manufacture_year')))
            base = ' '.join(parts) if parts else f"Автомобиль {idx}"
            extras = []
            if car.get('price'):
                try:
                    extras.append(f"цена {int(car.get('price')):,.0f} руб".replace(',', ' '))
                except Exception:
                    extras.append(f"цена {car.get('price')}")
            if car.get('city'):
                extras.append(f"город {car.get('city')}")
            line = base
            if extras:
                line += ", " + ", ".join(extras)
            lines.append(f"- {line}")
        return "\n".join(lines)
    
    def _generate_fallback_response(self, cars: List[Dict], statistics: Dict) -> str:
        """Резервный ответ если все API недоступны"""
        if not cars:
            return "По вашему запросу ничего не найдено. Попробуйте изменить критерии поиска."
        
        response_parts = []
        response_parts.append(f"🔍 Найдено {statistics['total_count']} автомобилей")
        
        if statistics['unique_brands']:
            response_parts.append(f"📊 Уникальных марок: {len(statistics['unique_brands'])}")
            response_parts.append(f"🏷️ Марки: {', '.join(statistics['unique_brands'])}")
        
        if statistics['top_cars_by_brand']:
            response_parts.append("\n🚗 Топ автомобили по маркам:")
            for item in statistics['top_cars_by_brand']:
                car = item['car']
                response_parts.append(f"• {item['brand']} {car.get('model', '')} ({car.get('manufacture_year', '')}) - {car.get('price', 0):,.0f} руб")
        
        response_parts.append("\n💡 Можете уточнить поиск по цене, году, типу кузова или другим параметрам!")
        
        return "\n".join(response_parts)

# Создаем глобальный экземпляр
search_response_generator = SearchResponseGenerator()
