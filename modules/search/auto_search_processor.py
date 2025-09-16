#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для автоматической обработки поисковых запросов автомобилей
"""

import re
from typing import Dict, Any, List, Optional
from modules.classifiers.ner_intent_classifier import NERIntentClassifier
from database import search_all_cars

class AutoSearchProcessor:
    """
    Процессор для автоматического поиска автомобилей на основе естественных запросов
    """
    
    def __init__(self):
        self.ner_classifier = NERIntentClassifier()
        
        # Ключевые слова для поиска
        self.search_keywords = [
            'найди', 'найти', 'покажи', 'показать', 'выведи', 'вывести', 'ищу', 'искать',
            'поиск', 'найти', 'покажи', 'выведи', 'показать', 'вывести'
        ]
        
        # Ключевые слова для запросов о количестве
        self.count_keywords = [
            'сколько', 'количество', 'число', 'количество', 'кол-во', 'колво',
            'в наличии', 'доступно', 'есть', 'имеется'
        ]
        
        # Ключевые слова для цен
        self.price_keywords = [
            'до', 'от', 'миллион', 'миллионов', 'млн', 'тысяч', 'тысячи',
            'рублей', 'руб', '₽', 'до', 'от', 'стоимость', 'цена'
        ]
        
        # Ключевые слова для автомобилей
        self.car_keywords = [
            'машина', 'машины', 'автомобиль', 'автомобили', 'авто', 'тачка', 'тачки',
            'bmw', 'audi', 'mercedes', 'ford', 'toyota', 'honda', 'nissan', 'volkswagen',
            'бмв', 'ауди', 'мерседес', 'форд', 'тойота', 'хонда', 'ниссан', 'фольксваген',
            'лада', 'ваз', 'lada', 'kia', 'hyundai', 'renault', 'peugeot', 'citroen',
            'киа', 'хендай', 'рено', 'пежо', 'ситроен', 'машину', 'машины', 'машин',
            'ладу', 'лады', 'ладе', 'внедорожник', 'внедорожники', 'седан', 'седаны',
            'хэтчбек', 'хэтчбеки', 'универсал', 'универсалы', 'купе', 'кабриолет',
            'пикап', 'микроавтобус', 'бензин', 'дизель', 'электро', 'гибрид'
        ]
        
        # Ключевые слова для сравнения
        self.compare_keywords = [
            'сравни', 'сравнить', 'сравнение', 'сравнивай', 'сравнивать',
            'отличия', 'разница', 'чем отличается', 'чем лучше', 'vs', 'против'
        ]
    
    def should_auto_search(self, query: str) -> bool:
        """
        Определяет, нужно ли автоматически выполнить поиск автомобилей
        
        Args:
            query: Текст запроса
            
        Returns:
            bool: True если нужно выполнить поиск
        """
        query_lower = query.lower()
        
        # Проверяем наличие ключевых слов поиска
        has_search_keyword = any(keyword in query_lower for keyword in self.search_keywords)
        
        # Проверяем наличие ключевых слов для запросов о количестве
        has_count_keyword = any(keyword in query_lower for keyword in self.count_keywords)
        
        # Проверяем наличие ключевых слов для сравнения
        has_compare_keyword = any(keyword in query_lower for keyword in self.compare_keywords)
        
        # Проверяем наличие автомобильных ключевых слов
        has_car_keyword = any(keyword in query_lower for keyword in self.car_keywords)
        
        # Проверяем наличие сущностей (марка, модель, цвет и т.д.)
        entities = self.ner_classifier.extract_entities(query)
        has_entities = any([
            entities.get('brand'),
            entities.get('model'),
            entities.get('color'),
            entities.get('body_type'),
            entities.get('fuel_type'),
            entities.get('city'),
            entities.get('price_from'),
            entities.get('price_to')
        ])
        
        # Автоматический поиск если:
        # 1. Есть ключевые слова поиска И есть автомобильные слова/сущности
        # 2. Есть ключевые слова количества И есть автомобильные слова/сущности
        # 3. Есть ключевые слова сравнения И есть автомобильные слова/сущности
        # 4. Есть только сущности (например, "Audi A4", "BMW X3")
        # 5. Есть ключевые слова поиска И есть цвета (например, "найди красную машину")
        has_colors = entities.get('color') is not None
        
        return ((has_search_keyword or has_count_keyword or has_compare_keyword) and (has_car_keyword or has_entities or has_colors)) or has_entities
    
    def process_search_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Обрабатывает поисковый запрос и возвращает результаты
        
        Args:
            query: Текст запроса
            user_id: ID пользователя
            
        Returns:
            Dict с результатами поиска
        """
        try:
            # Извлекаем сущности из запроса
            entities = self.ner_classifier.extract_entities(query)
            
            # Проверяем, является ли это запросом о количестве
            is_count_query = self._is_count_query(query)
            
            # Проверяем, является ли это запросом сравнения
            is_compare_query = self._is_compare_query(query)
            
            # Проверяем, является ли это запросом о кредите
            is_credit_query = self._is_credit_query(query)
            
            if is_compare_query:
                return self._process_comparison_query(query, user_id)
            
            if is_credit_query:
                return self._process_credit_query(query, entities, user_id)
            
            # Формируем параметры поиска
            search_params = self._build_search_params(entities)
            
            # Выполняем базовый поиск
            cars = search_all_cars(**search_params)
            
            # Если ничего не найдено — пробуем комбинированный поиск по сущностям
            fallback_applied = False
            fallback_criteria_desc = ''
            if not cars and self._should_try_combinational_search(query, entities):
                fallback_result = self._fallback_combinational_search(entities)
                cars = fallback_result.get('cars', [])
                fallback_criteria_desc = fallback_result.get('criteria_desc', '')
                fallback_applied = bool(cars)
            
            # Форматируем результаты
            formatted_cars = self._format_cars(cars)
            
            # Формируем ответное сообщение
            if is_count_query:
                message = self._generate_count_response_message(query, entities, len(formatted_cars))
            elif fallback_applied:
                message = self._generate_fallback_message(query, entities, len(formatted_cars), fallback_criteria_desc)
            else:
                message = self._generate_response_message(query, entities, len(formatted_cars))
            
            return {
                "type": "search_results",
                "message": message,
                "cars": formatted_cars,
                "entities": entities,
                "search_params": search_params,
                "total_found": len(formatted_cars)
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Ошибка при поиске: {str(e)}",
                "cars": [],
                "entities": {},
                "total_found": 0
            }

    def _should_try_combinational_search(self, query: str, entities: Dict[str, Any]) -> bool:
        """Определяет, нужно ли пробовать комбинированный поиск при отсутствии результатов.
        Условия: есть поисковые глаголы (найди/покажи/выведи/ищи) ИЛИ в запросе только сущности.
        """
        q = (query or '').lower()
        has_search_verbs = any(k in q for k in self.search_keywords)
        has_entities = any(entities.get(k) is not None for k in [
            'brand','model','color','body_type','fuel_type','city','price_from','price_to',
            'year_from','year_to','power_from','power_to','power_exact','engine_vol_from',
            'engine_vol_to','engine_vol_exact','mileage_from','mileage_to','owners_count',
            'owners_from','owners_to','drive_type','transmission','seats','acceleration_from',
            'acceleration_to','fuel_efficiency'
        ])
        return has_search_verbs or has_entities

    def _fallback_combinational_search(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Пробует поиск по разным сущностям и их комбинациям при пустом результате.
        Правила:
        - Если указаны марка и модель, то они идут только вместе, либо только марка; модель без марки не допускается.
        - Перебираем комбинации от более строгих к менее строгим.
        Возвращает {'cars': List[dict], 'message_suffix': str}
        """
        # Поддерживаемые ключи и порядок приоритета
        priority_keys = [
            'brand','model','body_type','color','fuel_type','drive_type','transmission',
            'power_from','power_to','power_exact','engine_vol_from','engine_vol_to','engine_vol_exact',
            'year_from','year_to','price_from','price_to','city','mileage_from','mileage_to','owners_count',
            'acceleration_from','acceleration_to','fuel_efficiency'
        ]
        # Активные ключи из entities
        active_keys = [k for k in priority_keys if entities.get(k) is not None]
        if not active_keys:
            return { 'cars': [], 'message_suffix': '' }

        # Бренд/модель ограничения
        has_brand = 'brand' in active_keys
        has_model = 'model' in active_keys

        # Функция сборки параметров по набору ключей
        def build_params(keys_subset: list) -> Dict[str, Any]:
            params = {}
            for k in keys_subset:
                params[k] = entities.get(k)
            # Ограничение результатов
            params['limit'] = 20
            return params

        tried = 0
        max_attempts = 20
        # 1) Перебор комбинаций, сохраняя относительный порядок priority_keys.
        # Стартуем с размера (len(active)-1) до 1.
        from itertools import combinations
        for r in range(len(active_keys)-1, 0, -1):
            for subset in combinations(active_keys, r):
                subset = list(subset)
                # Правило модели
                if has_model and 'model' in subset and 'brand' not in subset:
                    continue
                # Если есть brand и model исходно: допускаем пары (brand+model) или (brand) без model
                # Это уже обеспечено условием выше

                params = build_params(subset)
                try:
                    cars = search_all_cars(**params)
                except Exception:
                    cars = []
                tried += 1
                if cars:
                    used_desc = self._format_filter_description(self._pretty_params_for_message(params))
                    return {
                        'cars': cars,
                        'criteria_desc': used_desc
                    }
                if tried >= max_attempts:
                    break
            if tried >= max_attempts:
                break

        # 2) Попытки по одиночным ключам (на всякий случай)
        for k in active_keys:
            if has_model and k == 'model' and not has_brand:
                # Модель без бренда не допускается
                continue
            # Если исходно было и brand, и model — одиночная модель не допускается
            if has_brand and has_model and k == 'model':
                continue
            params = build_params([k] + (['brand'] if (k == 'model' and has_brand) else []))
            try:
                cars = search_all_cars(**params)
            except Exception:
                cars = []
            if cars:
                used_desc = self._format_filter_description(self._pretty_params_for_message(params))
                return {
                    'cars': cars,
                    'criteria_desc': used_desc
                }

        return { 'cars': [], 'criteria_desc': '' }
    
    def _build_search_params(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Строит параметры поиска на основе извлеченных сущностей
        """
        params = {}
        
        # Марка
        if entities.get('brand'):
            brand = entities['brand']
            if isinstance(brand, dict):
                params['brand'] = brand.get('en', brand.get('ru', ''))
            elif isinstance(brand, list):
                # Если бренд - это список, берем первый элемент
                if brand and isinstance(brand[0], dict):
                    params['brand'] = brand[0].get('en', brand[0].get('ru', ''))
                elif brand:
                    params['brand'] = brand[0]
            else:
                params['brand'] = brand
        
        # Модель
        if entities.get('model'):
            params['model'] = entities['model']
        
        # Цвет
        if entities.get('color'):
            color = entities['color']
            if isinstance(color, list):
                # Если цвет - это список, используем первый элемент
                params['color'] = color[0] if color else None
            else:
                params['color'] = color
        
        # Тип кузова
        if entities.get('body_type'):
            params['body_type'] = entities['body_type']
        
        # Тип топлива
        if entities.get('fuel_type'):
            params['fuel_type'] = entities['fuel_type']
        
        # Город
        if entities.get('city'):
            params['city'] = entities['city']
        
        # Цена
        if entities.get('price_from'):
            params['price_from'] = entities['price_from']
        if entities.get('price_to'):
            params['price_to'] = entities['price_to']
        
        # Расширенные характеристики: мощность и объем
        if entities.get('power_from'):
            params['power_from'] = entities['power_from']
        if entities.get('power_to'):
            params['power_to'] = entities['power_to']
        if entities.get('power_exact'):
            params['power_exact'] = entities['power_exact']
        if entities.get('engine_vol_from'):
            params['engine_vol_from'] = entities['engine_vol_from']
        if entities.get('engine_vol_to'):
            params['engine_vol_to'] = entities['engine_vol_to']
        if entities.get('engine_vol_exact'):
            params['engine_vol_exact'] = entities['engine_vol_exact']
        
        # Новые параметры производительности
        if entities.get('acceleration_from'):
            params['acceleration_from'] = entities['acceleration_from']
        if entities.get('acceleration_to'):
            params['acceleration_to'] = entities['acceleration_to']
        if entities.get('fuel_efficiency'):
            params['fuel_efficiency'] = entities['fuel_efficiency']
        
        # Год
        if entities.get('year_from'):
            params['year_from'] = entities['year_from']
        if entities.get('year_to'):
            params['year_to'] = entities['year_to']
        
        # Ограничение результатов
        params['limit'] = 20
        
        return params
    
    def _format_cars(self, cars: List[Dict]) -> List[Dict]:
        """
        Форматирует список автомобилей для отображения
        """
        formatted = []
        
        for car in cars:
            formatted_car = {
                'id': car.get('id'),
                'title': car.get('title', ''),
                'mark': car.get('mark', ''),
                'model': car.get('model', ''),
                'price': car.get('price', 0),
                'price_millions': round(car.get('price', 0) / 1000000, 1),
                'city': car.get('city', ''),
                'year': car.get('manufacture_year', ''),
                'color': car.get('color', ''),
                'fuel_type': car.get('fuel_type', ''),
                'body_type': car.get('body_type', ''),
                'transmission': car.get('gear_box_type', ''),
                'drive_type': car.get('driving_gear_type', ''),
                'state': car.get('state', 'new'),
                'mileage': car.get('mileage', 0),
                'dealer': car.get('dealer_center', ''),
                'is_used': car.get('is_used', False),  # Используем поле is_used из базы данных
                'status_text': 'Поддержанный' if car.get('is_used', False) else 'Новый'
            }
            formatted.append(formatted_car)
        
        return formatted
    
    def _generate_response_message(self, query: str, entities: Dict[str, Any], total_found: int) -> str:
        """
        Генерирует ответное сообщение на основе результатов поиска
        """
        if total_found == 0:
            # Улучшенный нулевой ответ: лаконичный и оформленный HTML-блок
            reason = self._describe_filters_brief(entities)
            suggestions = self._zero_result_suggestions(entities)
            # Рендер кнопок действий (frontend может навесить обработчики по data-action)
            def render_buttons(items: list) -> str:
                actions_html = []
                for s in items:
                    action_key = 'generic'
                    if 'без фильтра по цвету' in s:
                        action_key = 'remove_color_filter'
                    elif 'похожие автомобили' in s:
                        action_key = 'show_similar'
                    elif 'расширить тип кузова' in s:
                        action_key = 'expand_body_type'
                    elif 'предел цены' in s:
                        action_key = 'increase_price_to'
                    elif 'диапазон годов' in s:
                        action_key = 'expand_year_range'
                    elif 'минимальную мощность' in s:
                        action_key = 'decrease_power_from'
                    elif 'город' in s:
                        action_key = 'expand_city'
                    elif 'модели марки' in s:
                        action_key = 'brand_only_models'

                    # Иконки
                    icon = '🛠️'
                    if action_key == 'remove_color_filter':
                        icon = '🎨'
                    elif action_key == 'show_similar':
                        icon = '🔄'
                    elif action_key == 'expand_body_type':
                        icon = '🚗'
                    elif action_key == 'increase_price_to':
                        icon = '💰'
                    elif action_key == 'expand_year_range':
                        icon = '📅'
                    elif action_key == 'decrease_power_from':
                        icon = '⚡'
                    elif action_key == 'expand_city':
                        icon = '📍'
                    elif action_key == 'brand_only_models':
                        icon = '🏷️'

                    # Цветовые схемы для кнопок
                    bg = "linear-gradient(135deg,#ffffff 0%,#f3f4f6 100%)"
                    text_color = "#111827"
                    border_color = "#e5e7eb"
                    if action_key == 'remove_color_filter':
                        bg = "linear-gradient(135deg,#fef3c7 0%,#f59e0b 100%)"  # amber
                        text_color = "#78350f"
                        border_color = "#fcd34d"
                    elif action_key == 'show_similar':
                        bg = "linear-gradient(135deg,#dbeafe 0%,#60a5fa 100%)"  # blue
                        text_color = "#0c4a6e"
                        border_color = "#93c5fd"
                    elif action_key == 'expand_body_type':
                        bg = "linear-gradient(135deg,#ede9fe 0%,#a78bfa 100%)"  # indigo/violet
                        text_color = "#3730a3"
                        border_color = "#c4b5fd"
                    elif action_key == 'increase_price_to':
                        bg = "linear-gradient(135deg,#fef9c3 0%,#fbbf24 100%)"  # yellow
                        text_color = "#713f12"
                        border_color = "#fef08a"
                    elif action_key == 'expand_year_range':
                        bg = "linear-gradient(135deg,#cffafe 0%,#06b6d4 100%)"  # cyan
                        text_color = "#164e63"
                        border_color = "#a5f3fc"
                    elif action_key == 'decrease_power_from':
                        bg = "linear-gradient(135deg,#fee2e2 0%,#f87171 100%)"  # red
                        text_color = "#7f1d1d"
                        border_color = "#fecaca"
                    elif action_key == 'expand_city':
                        bg = "linear-gradient(135deg,#dcfce7 0%,#34d399 100%)"  # green
                        text_color = "#064e3b"
                        border_color = "#bbf7d0"
                    elif action_key == 'brand_only_models':
                        bg = "linear-gradient(135deg,#f3e8ff 0%,#c084fc 100%)"  # purple
                        text_color = "#581c87"
                        border_color = "#e9d5ff"

                    label = s[:1].upper() + s[1:]
                    style = (
                        "display:inline-flex;align-items:center;gap:8px;"
                        "padding:10px 14px;border:1px solid " + border_color + ";border-radius:12px;"
                        "background:" + bg + ";"
                        "cursor:pointer;margin:6px 8px 0 0;box-shadow:0 2px 6px rgba(0,0,0,0.06);"
                        "color:" + text_color + ";font-weight:700;"
                    )
                    actions_html.append(
                        f"<button data-action=\"{action_key}\" style=\"{style}\"><span>{icon}</span><span>{label}</span></button>"
                    )
                return "".join(actions_html)

            reason_html = f"<div style=\"color:#6b7280;margin:6px 0 10px 0;\">Возможная причина: {reason}.</div>" if reason else ""
            buttons_html = render_buttons(suggestions) if suggestions else ""
            html = (
                "<div style=\"background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;margin:8px 0;\">"
                "<div style=\"font-weight:600;color:#111827;\">Нет точных совпадений</div>"
                f"{reason_html}"
                + ("<div style=\"color:#374151;margin-bottom:6px;\">Предлагаю варианты действий:</div>" if buttons_html else "")
                + buttons_html +
                "<div style=\"margin-top:10px;color:#374151;\">Могу выполнить один из вариантов или уточнить критерии (цена/год/цвет/кузов)?</div>"
                "</div>"
            )
            return html
        
        # Формируем описание найденных автомобилей
        found_desc = []
        # Спорткарная логика: скрываем сырые кузова и подставляем «спорткар(ы)»
        is_sportcar = self._is_sportcar_query(query, entities)
        sportcar_label = self._get_sportcar_label(total_found)
        
        if entities.get('brand'):
            brand = entities['brand']
            if isinstance(brand, dict):
                brand_name = brand.get('ru', brand.get('en', ''))
            else:
                brand_name = brand
            found_desc.append(f"марки {brand_name}")
        
        if entities.get('model'):
            found_desc.append(f"модели {entities['model']}")
        
        if entities.get('color'):
            color_val = entities['color']
            if isinstance(color_val, list):
                color_val = color_val[0]
            found_desc.append(self._format_color_phrase(color_val))
        
        if entities.get('body_type') and not is_sportcar:
            found_desc.append(f"{entities['body_type']}")

        if is_sportcar:
            found_desc.append(sportcar_label)
        
        if entities.get('city'):
            found_desc.append(f"в городе {entities['city']}")
        
        if entities.get('price_to'):
            found_desc.append(f"до {entities['price_to']:,} ₽")
        
        # Формируем сообщение
        if found_desc:
            criteria = " ".join(found_desc)
            message = f"🔍 Найдено {total_found} автомобилей по запросу: {criteria}"
        else:
            message = f"🔍 Найдено {total_found} автомобилей"
        
        if total_found > 20:
            message += f"\n\nПоказано первых 20 результатов. Для более точного поиска укажите дополнительные критерии."
        
        return message

    def _describe_filters_brief(self, entities: Dict[str, Any]) -> str:
        """Коротко описывает, какие фильтры могли слишком сузить выбор."""
        applied = []
        if entities.get('brand') and entities.get('model'):
            applied.append("узкая связка марки и модели")
        elif entities.get('brand'):
            applied.append("жесткий фильтр по марке")
        if entities.get('color'):
            applied.append("строгий фильтр по цвету")
        if entities.get('body_type'):
            applied.append("узкий тип кузова")
        if entities.get('city'):
            applied.append("ограничение по городу")
        if entities.get('price_to'):
            applied.append("жесткий верхний предел цены")
        if entities.get('year_from') or entities.get('year_to'):
            applied.append("жесткие границы по году")
        if entities.get('power_from'):
            applied.append("высокий порог по мощности")
        return ", ".join(applied)

    def _zero_result_suggestions(self, entities: Dict[str, Any]) -> list:
        """Формирует практичные шаги при нулевом результате."""
        suggestions = []
        brand = entities.get('brand')
        model = entities.get('model')
        color = entities.get('color')
        body = entities.get('body_type')
        city = entities.get('city')
        price_to = entities.get('price_to')
        year_from = entities.get('year_from')
        year_to = entities.get('year_to')
        power_from = entities.get('power_from')

        if color:
            suggestions.append("показать варианты без фильтра по цвету")
        if body:
            suggestions.append("расширить тип кузова (показать близкие альтернативы)")
        if brand and model:
            suggestions.append("показать все модели марки без жесткой привязки к конкретной модели")
        if brand and not model:
            suggestions.append("показать популярные модели выбранной марки")
        if city:
            suggestions.append("рассмотреть ближайшие города/все города")
        if price_to:
            suggestions.append("увеличить верхний предел цены")
        if year_from or year_to:
            suggestions.append("расширить диапазон годов выпуска")
        if power_from:
            suggestions.append("снизить минимальную мощность для большего выбора")
        # Общая альтернатива
        suggestions.append("показать похожие автомобили без части строгих фильтров")
        return suggestions

    def _generate_fallback_message(self, query: str, entities: Dict[str, Any], total_found: int, criteria_desc: str) -> str:
        """Сообщение без противоречий при ослаблении критериев: сначала честно сообщаем об отсутствии точных совпадений,
        затем — что показаны частично подходящие варианты, и кратко объясняем критерии подбора."""
        # Человеческое название запроса (цвет/спорткары и т.п.)
        parts = []
        if entities.get('color'):
            color_val = entities['color']
            if isinstance(color_val, list):
                color_val = color_val[0]
            parts.append(self._format_color_phrase(color_val))
        if self._is_sportcar_query(query, entities):
            parts.append(self._get_sportcar_label(total_found if total_found else 2))
        base_query = " ".join(parts).strip()
        if not base_query:
            base_query = "указанным критериям"

        # Если критерии пустые — сформируем их из сущностей
        if not criteria_desc:
            # Соберем базовые параметры из сущностей
            draft_params = {}
            for k in ['body_type','power_from','power_to','power_exact','engine_vol_from','engine_vol_to','engine_vol_exact',
                      'year_from','year_to','price_from','price_to','color','fuel_type','drive_type','transmission']:
                if entities.get(k) is not None:
                    draft_params[k] = entities.get(k)
            pretty = self._pretty_params_for_message(draft_params)
            criteria_desc = self._format_filter_description(pretty)

        # Лаконичный HTML-блок (лучше отображается во frontend)
        html = []
        html.append(f"<div>К сожалению, по запросу <b>{base_query}</b> точных совпадений не найдено.</div>")
        html.append(f"<div>Но мы нашли <b>{total_found}</b> вариантов, частично соответствующих запросу.</div>")
        # Показываем критерии только если они содержат полезные пункты
        crit = (criteria_desc or '').strip()
        has_bullets = '•' in crit
        is_empty_criteria = ('не указаны' in crit.lower()) or (not has_bullets)
        if crit and not is_empty_criteria:
            html.append(f"<div style=\"margin-top:6px\">{crit}</div>")
        html.append("<div style=\"margin-top:8px\">Хотите уточнить параметры или посмотреть эти предложения?</div>")
        return "\n".join(html)

    def _is_sportcar_query(self, query: str, entities: Dict[str, Any]) -> bool:
        ql = (query or '').lower()
        if any(w in ql for w in ['спорткар', 'спорткары', 'спорткара', 'спорткаров']):
            return True
        body = entities.get('body_type')
        body_list = [body] if isinstance(body, str) else (body or [])
        sporty_set = {'купе', 'кабриолет', 'родстер'}
        has_sporty_body = any(b in sporty_set for b in body_list)
        power_from = entities.get('power_from')
        return bool(has_sporty_body and (power_from is not None and power_from >= 300))

    def _get_sportcar_label(self, total_found: int) -> str:
        return 'спорткар' if total_found == 1 else 'спорткары'

    def _format_color_phrase(self, color: str) -> str:
        genitive = {
            'желтый': 'желтого', 'красный': 'красного', 'белый': 'белого', 'черный': 'черного',
            'синий': 'синего', 'серый': 'серого', 'зеленый': 'зеленого', 'оранжевый': 'оранжевого',
            'фиолетовый': 'фиолетового', 'розовый': 'розового', 'коричневый': 'коричневого',
            'голубой': 'голубого', 'бежевый': 'бежевого', 'золотой': 'золотого', 'серебристый': 'серебристого'
        }
        base = (color or '').strip().lower()
        word = genitive.get(base, base)
        return f"{word} цвета"

    def _pretty_params_for_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Готовит параметры к выводу: заменяет набор спортивных кузовов на маркер спорткара."""
        pretty = dict(params)
        body = pretty.get('body_type')
        sporty_set = {'купе', 'кабриолет', 'родстер'}
        sportcar = False
        if isinstance(body, list) and body and set(body).issubset(sporty_set):
            sportcar = True
        if isinstance(body, str) and body in sporty_set:
            sportcar = True
        if sportcar:
            pretty.pop('body_type', None)
            pretty['__sportcar__'] = True
        return pretty
    
    def _is_count_query(self, query: str) -> bool:
        """
        Определяет, является ли запрос запросом о количестве
        
        Args:
            query: Текст запроса
            
        Returns:
            bool: True если это запрос о количестве
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.count_keywords)
    
    def _generate_count_response_message(self, query: str, entities: Dict[str, Any], total_found: int) -> str:
        """
        Генерирует ответное сообщение для запросов о количестве
        """
        if total_found == 0:
            return "😔 К сожалению, автомобилей с указанными критериями не найдено."
        
        # Формируем описание критериев
        criteria_desc = []
        
        if entities.get('brand'):
            brand = entities['brand']
            if isinstance(brand, dict):
                brand_name = brand.get('ru', brand.get('en', ''))
            else:
                brand_name = brand
            criteria_desc.append(f"марки {brand_name}")
        
        if entities.get('model'):
            criteria_desc.append(f"модели {entities['model']}")
        
        if entities.get('color'):
            color = entities['color']
            if isinstance(color, list):
                color_names = ", ".join(color)
                criteria_desc.append(f"цветов {color_names}")
            else:
                criteria_desc.append(f"цвета {color}")
        
        if entities.get('body_type'):
            criteria_desc.append(f"типа кузова {entities['body_type']}")
        
        if entities.get('city'):
            criteria_desc.append(f"в городе {entities['city']}")
        
        if entities.get('price_to'):
            price_millions = entities['price_to'] / 1000000
            criteria_desc.append(f"до {price_millions:.1f} млн ₽")
        
        # Формируем сообщение
        if criteria_desc:
            criteria = " ".join(criteria_desc)
            message = f"📊 В наличии {total_found} автомобилей {criteria}"
        else:
            message = f"📊 В наличии {total_found} автомобилей"
        
        return message
    
    def _is_compare_query(self, query: str) -> bool:
        """
        Определяет, является ли запрос запросом сравнения
        
        Args:
            query: Текст запроса
            
        Returns:
            bool: True если это запрос сравнения
        """
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.compare_keywords)
    
    def _process_comparison_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Обрабатывает запрос сравнения автомобилей
        
        Args:
            query: Текст запроса
            user_id: ID пользователя
            
        Returns:
            Dict с результатами сравнения
        """
        try:
            from modules.comparators.car_comparator import CarComparator
            
            comparator = CarComparator()
            
            # Сначала пробуем извлечь пары для сравнения
            comparison_pairs = comparator.extract_comparison_pairs(query)
            
            if len(comparison_pairs) >= 2:
                # Если найдены пары для сравнения, используем compare_by_names
                
                # Выполняем сравнение
                comparison_result = comparator.compare_by_names(comparison_pairs)
                
                # Добавляем информацию о том, что это сравнение по именам
                if comparison_result.get('type') == 'comparison_table':
                    comparison_result['comparison_type'] = 'by_names'
                    comparison_result['comparison_pairs'] = comparison_pairs
                
                if comparison_result.get('type') == 'error':
                    return {
                        "type": "error",
                        "message": comparison_result.get('message', 'Ошибка сравнения'),
                        "cars": [],
                        "entities": {},
                        "total_found": 0
                    }
                
                # Форматируем таблицу сравнения
                comparison_table = comparator.format_comparison_table(comparison_result)
                
                return {
                    "type": "comparison_results",
                    "message": "",  # Оставляем пустым, так как frontend сам форматирует
                    "cars": comparison_result.get('cars', []),
                    "entities": {"comparison_pairs": comparison_pairs},
                    "comparison_result": comparison_result,
                    "total_found": len(comparison_result.get('cars', []))
                }
            else:
                # Если пары не найдены, пробуем извлечь фильтры для сравнения
                filters = comparator.extract_comparison_filters(query)
                
                if filters:
                    # Если найдены фильтры, сравниваем по фильтрам
                    comparison_result = comparator.compare_by_filters(filters)
                    
                    if comparison_result.get('type') == 'error':
                        return {
                            "type": "error",
                            "message": comparison_result.get('message', 'Ошибка сравнения по фильтрам'),
                            "cars": [],
                            "entities": {},
                            "total_found": 0
                        }
                    
                    # Форматируем таблицу сравнения
                    comparison_table = comparator.format_comparison_table(comparison_result)
                    
                    # Формируем описание фильтров
                    filter_desc = self._format_filter_description(filters)
                    
                    return {
                        "type": "comparison_results",
                        "message": f"📊 Сравнение автомобилей\n\n{filter_desc}",  # Убираем markdown-разметку
                        "cars": comparison_result.get('cars', []),
                        "entities": {"filters": filters},
                        "comparison_result": comparison_result,
                        "total_found": len(comparison_result.get('cars', []))
                    }
                else:
                    return {
                        "type": "error",
                        "message": "Для сравнения нужно указать минимум два автомобиля или критерии фильтрации. Примеры: 'сравни BMW X3 и Haval Jolion', 'сравни машины до 3 млн'",
                        "cars": [],
                        "entities": {},
                        "total_found": 0
                    }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Ошибка при сравнении: {str(e)}",
                "cars": [],
                "entities": {},
                "total_found": 0
            }
    
    def _format_filter_description(self, filters: Dict[str, Any]) -> str:
        """
        Форматирует описание фильтров для отображения (лаконично, без markdown).
        Возвращает пустую строку, если нет полезных пунктов.
        """
        descriptions = []
        
        if filters.get('price_from') and filters.get('price_to'):
            price_from_millions = filters['price_from'] / 1000000
            price_to_millions = filters['price_to'] / 1000000
            descriptions.append(f"💰 Цена: от {price_from_millions:.1f} до {price_to_millions:.1f} млн ₽")
        elif filters.get('price_to'):
            price_to_millions = filters['price_to'] / 1000000
            descriptions.append(f"💰 Цена: до {price_to_millions:.1f} млн ₽")
        elif filters.get('price_from'):
            price_from_millions = filters['price_from'] / 1000000
            descriptions.append(f"💰 Цена: от {price_from_millions:.1f} млн ₽")
        
        if filters.get('year_from') and filters.get('year_to'):
            descriptions.append(f"📅 Год выпуска: от {filters['year_from']} до {filters['year_to']}")
        elif filters.get('year_from'):
            descriptions.append(f"📅 Год выпуска: от {filters['year_from']}")
        elif filters.get('year_to'):
            descriptions.append(f"📅 Год выпуска: до {filters['year_to']}")
        
        if filters.get('body_type'):
            descriptions.append(f"🚗 Тип кузова: {filters['body_type']}")
        
        if filters.get('fuel_type'):
            descriptions.append(f"⛽ Тип топлива: {filters['fuel_type']}")
        
        if filters.get('brand'):
            descriptions.append(f"🏷️ Марка: {filters['brand']}")
        
        if filters.get('power_to'):
            descriptions.append(f"⚡ Мощность: до {filters['power_to']} л.с.")
        elif filters.get('power_from') and filters.get('power_to'):
            descriptions.append(f"⚡ Мощность: от {filters['power_from']} до {filters['power_to']} л.с.")
        elif filters.get('power_from'):
            descriptions.append(f"⚡ Мощность: от {filters['power_from']} л.с.")
        elif filters.get('power_exact'):
            descriptions.append(f"⚡ Мощность: {filters['power_exact']} л.с.")
        
        if filters.get('engine_vol_to'):
            descriptions.append(f"🔧 Объем двигателя: до {filters['engine_vol_to']} л")
        elif filters.get('engine_vol_from') and filters.get('engine_vol_to'):
            descriptions.append(f"🔧 Объем двигателя: от {filters['engine_vol_from']} до {filters['engine_vol_to']} л")
        elif filters.get('engine_vol_from'):
            descriptions.append(f"🔧 Объем двигателя: от {filters['engine_vol_from']} л")
        elif filters.get('engine_vol_exact'):
            descriptions.append(f"🔧 Объем двигателя: {filters['engine_vol_exact']} л")
        
        if filters.get('mileage_to'):
            descriptions.append(f"📏 Пробег: до {filters['mileage_to']:,} км")
        elif filters.get('mileage_from') and filters.get('mileage_to'):
            descriptions.append(f"📏 Пробег: от {filters['mileage_from']:,} до {filters['mileage_to']:,} км")
        elif filters.get('mileage_from'):
            descriptions.append(f"📏 Пробег: от {filters['mileage_from']:,} км")
        elif filters.get('mileage_exact'):
            descriptions.append(f"📏 Пробег: {filters['mileage_exact']:,} км")
        
        if filters.get('owners_to') and filters.get('owners_from'):
            descriptions.append(f"👤 Количество владельцев: от {filters['owners_from']} до {filters['owners_to']}")
        elif filters.get('owners_to'):
            descriptions.append(f"👤 Количество владельцев: до {filters['owners_to']}")
        elif filters.get('owners_from'):
            descriptions.append(f"👤 Количество владельцев: от {filters['owners_from']}")
        elif filters.get('owners_count'):
            descriptions.append(f"👤 Количество владельцев: {filters['owners_count']}")
        
        if filters.get('steering_wheel'):
            descriptions.append(f"🎯 Тип руля: {filters['steering_wheel']}")
        
        if filters.get('accident_history'):
            descriptions.append(f"🚨 История аварий: {filters['accident_history']}")
        
        if not descriptions:
            return ""
        # Лаконичный блок с маркерами; без markdown для корректного HTML-рендера во фронтенде
        return "<div><b>Критерии подбора:</b><br>" + "<br>".join(f"• {desc}" for desc in descriptions) + "</div>"
    
    def _is_credit_query(self, query: str) -> bool:
        """
        Проверяет, является ли запрос запросом о кредите
        """
        credit_keywords = [
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
            'платеж', 'платежи', 'ежемесячный', 'рассчитать', 'рассчитай'
        ]
        
        query_lower = query.lower()
        
        # Проверяем точные совпадения
        is_credit = any(keyword in query_lower for keyword in credit_keywords)
        
        # Дополнительная проверка на опечатки и вариации
        if not is_credit:
            # Проверяем наличие слов "кредит", "кридит", "критит" в любом контексте
            credit_variations = ['кредит', 'кридит', 'критит']
            has_credit_word = any(var in query_lower for var in credit_variations)
            
            # Проверяем наличие слов "рассчитать", "рассчитай" вместе с "на"
            has_calculate = any(word in query_lower for word in ['рассчитать', 'рассчитай'])
            has_on = 'на' in query_lower
            
            # Проверяем наличие слов "автомобиль", "авто", "машину"
            has_car = any(word in query_lower for word in ['автомобиль', 'авто', 'машину', 'машина'])
            
            is_credit = has_credit_word or (has_calculate and has_on and has_car)
        
        print(f"[_is_credit_query] Запрос: '{query}' -> {is_credit}")
        return is_credit
    
    def _process_credit_query(self, query: str, entities: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Обрабатывает запросы о кредите
        """
        print(f"[_process_credit_query] Обрабатываем кредитный запрос: '{query}'")
        print(f"[_process_credit_query] Сущности: {entities}")
        
        # Проверяем, есть ли информация об автомобиле в запросе
        has_car_info = any([
            entities.get('brand'),
            entities.get('model'),
            entities.get('car_name'),
            entities.get('price'),
            entities.get('year')
        ])
        
        if has_car_info:
            # Ищем конкретный автомобиль
            search_params = self._build_search_params(entities)
            print(f"[_process_credit_query] Параметры поиска: {search_params}")
            cars = search_all_cars(**search_params)
            
            if cars:
                # Берем первый найденный автомобиль
                car = cars[0]
                car_data = {
                    'id': car.get('id'),
                    'mark': car.get('mark', ''),
                    'model': car.get('model', ''),
                    'year': car.get('manufacture_year', ''),
                    'price': car.get('price', 0),
                    'city': car.get('city', ''),
                    'fuel_type': car.get('fuel_type', ''),
                    'body_type': car.get('body_type', ''),
                    'is_used': car.get('is_used', False)
                }
                
                message = f"Открываю кредитный калькулятор для {car_data['mark']} {car_data['model']} {car_data['year']} года стоимостью {car_data['price']:,.0f} ₽"
                
                print(f"[_process_credit_query] Найден автомобиль: {car_data}")
                return {
                    "type": "credit_calculator",
                    "message": message,
                    "data": car_data
                }
        
        # Если автомобиль не найден или не указан, показываем общий калькулятор
        message = "Открываю универсальный кредитный калькулятор. Вы можете ввести параметры автомобиля и рассчитать кредит на любую машину."
        print(f"[_process_credit_query] Показываем универсальный калькулятор")
        
        return {
            "type": "credit_calculator",
            "message": message,
            "data": None
        } 