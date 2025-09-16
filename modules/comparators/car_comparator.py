import sqlite3
import re
from typing import List, Dict, Any, Optional
from database import search_all_cars

DB_PATH = r'E:\Users\diman\OneDrive\Документы\Рабочий стол\2\хрень — копия\instance\cars.db'

class CarComparator:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def compare(self, car_ids: list):
        """
        Сравнивает автомобили по их ID (ищет и среди новых, и среди б/у).
        """
        if not car_ids or len(car_ids) < 2:
            return {
                "type": "error",
                "message": "Для сравнения нужно как минимум два автомобиля."
            }
        cars = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Поиск среди новых авто
            q_marks = ','.join(['?']*len(car_ids))
            cursor.execute(f"SELECT id, mark, model, manufacture_year, price, color, body_type, fuel_type, power, engine_vol FROM car WHERE id IN ({q_marks})", car_ids)
            for row in cursor.fetchall():
                cars.append({
                    "id": row[0], "mark": row[1], "model": row[2], "year": row[3], "price": row[4], "color": row[5], "body_type": row[6], "fuel_type": row[7], "power": row[8], "engine_vol": row[9], "used": False
                })
            # Поиск среди б/у авто
            cursor.execute(f"SELECT id, mark, model, manufacture_year, price, color, body_type, fuel_type, power, engine_vol, mileage FROM used_car WHERE id IN ({q_marks})", car_ids)
            for row in cursor.fetchall():
                cars.append({
                    "id": row[0], "mark": row[1], "model": row[2], "year": row[3], "price": row[4], "color": row[5], "body_type": row[6], "fuel_type": row[7], "power": row[8], "engine_vol": row[9], "mileage": row[10], "used": True
                })
            conn.close()
        except Exception as e:
            return {"type": "error", "message": str(e)}
        if len(cars) < 2:
            return {"type": "error", "message": "Не удалось найти все автомобили для сравнения."}
        features = ["price", "year", "color", "body_type", "fuel_type", "power", "engine_vol"]
        return {
            "type": "comparison_table",
            "cars": cars,
            "features": features
        } 

    def compare_by_names(self, comparison_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Сравнивает автомобили по названиям марок и моделей.
        
        Args:
            comparison_pairs: Список словарей с ключами 'brand' и 'model'
                             Пример: [{'brand': 'BMW', 'model': 'X3'}, {'brand': 'Haval', 'model': 'Jolion'}]
        """
        if not comparison_pairs or len(comparison_pairs) < 2:
            return {
                "type": "error",
                "message": "Для сравнения нужно как минимум два автомобиля."
            }
        
        found_cars = []
        
        for pair in comparison_pairs:
            brand = pair.get('brand', '').strip()
            model = pair.get('model', '').strip()
            
            if not brand:
                continue
                
            # Ищем автомобили по марке и модели с более точным поиском
            search_params = {'brand': brand}
            if model:
                search_params['model'] = model
            
            # Получаем все автомобили и фильтруем более точно
            all_cars = search_all_cars(**search_params)
            
            # Точная фильтрация по марке и модели
            filtered_cars = []
            for car in all_cars:
                car_brand = car.get('mark', '').strip().upper()
                car_model = car.get('model', '').strip().upper()
                
                # Проверяем точное совпадение марки
                if car_brand != brand.upper():
                    continue
                
                # Если модель указана, проверяем точное совпадение модели
                if model and car_model != model.upper():
                    continue
                
                filtered_cars.append(car)
            
            if filtered_cars:
                # Берем несколько автомобилей для каждой пары (не только первый)
                for i, car in enumerate(filtered_cars[:5]):  # Ограничиваем до 5 машин на пару
                    # Добавляем информацию о том, что это для сравнения
                    car['comparison_name'] = f"{brand} {model}".strip()
                    found_cars.append(car)
            else:
                # Если не найдено, добавляем пустую запись
                found_cars.append({
                    'comparison_name': f"{brand} {model}".strip(),
                    'mark': brand,
                    'model': model,
                    'price': None,
                    'manufacture_year': None,
                    'color': None,
                    'body_type': None,
                    'fuel_type': None,
                    'power': None,
                    'engine_vol': None,
                    'not_found': True
                })
        
        if len(found_cars) < 2:
            return {
                "type": "error", 
                "message": "Не удалось найти достаточно автомобилей для сравнения."
            }
        
        # Определяем основные характеристики для сравнения
        features = ["price", "manufacture_year", "color", "body_type", "fuel_type", "power", "engine_vol"]
        
        return {
            "type": "comparison_table",
            "cars": found_cars,
            "features": features,
            "comparison_pairs": comparison_pairs
        }

    def extract_comparison_pairs(self, query: str) -> List[Dict[str, str]]:
        """
        Извлекает пары марка-модель из запроса на сравнение.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            Список словарей с парами brand-model
        """
        query_lower = query.lower()
        
        # Удаляем слово "сравни" из начала
        if query_lower.startswith('сравни'):
            query_lower = query_lower[7:].strip()
        
        pairs = []
        
        # Разделяем по запятым и "и"
        # Используем более точное разделение для "и"
        parts = []
        
        # Сначала разделяем по запятым
        comma_parts = query_lower.split(',')
        for part in comma_parts:
            part = part.strip()
            if not part:
                continue
            
            # Разделяем каждую часть по "и"
            and_parts = part.split(' и ')
            for and_part in and_parts:
                and_part = and_part.strip()
                if and_part:
                    parts.append(and_part)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # Разделяем на марку и модель
            words = part.split()
            if len(words) >= 2:
                brand = words[0].upper()
                model = ' '.join(words[1:]).upper()
                pairs.append({'brand': brand, 'model': model})
            elif len(words) == 1:
                brand = words[0].upper()
                pairs.append({'brand': brand, 'model': ''})
        
        # Удаляем дубликаты
        unique_pairs = []
        seen = set()
        for pair in pairs:
            pair_key = f"{pair['brand']}_{pair['model']}"
            if pair_key not in seen:
                seen.add(pair_key)
                unique_pairs.append(pair)
        
        return unique_pairs

    def compare_by_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сравнивает автомобили по заданным фильтрам.
        
        Args:
            filters: Словарь с фильтрами (price_from, price_to, year_from, year_to, 
                     body_type, fuel_type, brand, etc.)
            
        Returns:
            Dict с результатами сравнения
        """
        try:
            # Выполняем поиск по фильтрам
            cars = search_all_cars(**filters, limit=10)
            
            if len(cars) < 2:
                return {
                    "type": "error",
                    "message": f"Не найдено достаточно автомобилей для сравнения по заданным критериям."
                }
            
            # Добавляем информацию для сравнения
            for car in cars:
                car['comparison_name'] = f"{car.get('mark', '')} {car.get('model', '')}".strip()
            
            # Определяем основные характеристики для сравнения
            features = ["price", "manufacture_year", "color", "body_type", "fuel_type", "power", "engine_vol"]
            
            return {
                "type": "comparison_table",
                "cars": cars,
                "features": features,
                "filters": filters
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Ошибка при сравнении по фильтрам: {str(e)}"
            }

    def extract_comparison_filters(self, query: str) -> Dict[str, Any]:
        """
        Извлекает фильтры для сравнения из запроса.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            Словарь с фильтрами
        """
        query_lower = query.lower()
        filters = {}
        
        # Фильтры по цене
        price_patterns = [
            (r'от\s+(\d+(?:\.\d+)?)\s*до\s+(\d+(?:\.\d+)?)\s*млн', 'price_range', lambda x, y: (float(x) * 1000000, float(y) * 1000000)),
            (r'от\s+(\d+(?:\.\d+)?)\s*млн', 'price_from', lambda x: float(x) * 1000000),
            (r'до\s+(\d+(?:\.\d+)?)\s*млн', 'price_to', lambda x: float(x) * 1000000),
            (r'от\s+(\d+)\s*до\s+(\d+)\s*тыс', 'price_range', lambda x, y: (float(x) * 1000, float(y) * 1000)),
            (r'до\s+(\d+)\s*тыс', 'price_to', lambda x: float(x) * 1000),
        ]
        
        for pattern, filter_type, converter in price_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if filter_type == 'price_range':
                    for match in matches:
                        if len(match) == 2:
                            price_from, price_to = converter(match[0], match[1])
                            filters['price_from'] = price_from
                            filters['price_to'] = price_to
                else:
                    for match in matches:
                        if filter_type == 'price_to':
                            filters['price_to'] = converter(match)
                        elif filter_type == 'price_from':
                            filters['price_from'] = converter(match)
                break
        
        # Фильтры по году
        year_patterns = [
            (r'от\s+(\d{4})\s*года', 'year_from', int),
            (r'до\s+(\d{4})\s*года', 'year_to', int),
            (r'(\d{4})\s*года', 'year_from', int),
        ]
        
        for pattern, filter_type, converter in year_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                for match in matches:
                    if filter_type == 'year_from':
                        filters['year_from'] = converter(match)
                    elif filter_type == 'year_to':
                        filters['year_to'] = converter(match)
                break
        
        # Фильтры по типу кузова
        body_type_patterns = [
            (r'внедорожник', 'body_type', 'Внедорожник'),
            (r'седан', 'body_type', 'Седан'),
            (r'хэтчбек', 'body_type', 'Хэтчбек'),
            (r'универсал', 'body_type', 'Универсал'),
            (r'купе', 'body_type', 'Купе'),
            (r'кабриолет', 'body_type', 'Кабриолет'),
            (r'пикап', 'body_type', 'Пикап'),
            (r'микроавтобус', 'body_type', 'Микроавтобус'),
        ]
        
        for pattern, filter_type, value in body_type_patterns:
            if re.search(pattern, query_lower):
                filters[filter_type] = value
                break
        
        # Фильтры по типу топлива
        fuel_patterns = [
            (r'бензин', 'fuel_type', 'Бензин'),
            (r'дизель', 'fuel_type', 'Дизель'),
            (r'электро', 'fuel_type', 'Электро'),
            (r'гибрид', 'fuel_type', 'Гибрид'),
        ]
        
        for pattern, filter_type, value in fuel_patterns:
            if re.search(pattern, query_lower):
                filters[filter_type] = value
                break
        
        # Фильтры по марке
        brand_patterns = [
            (r'bmw|бмв', 'brand', 'BMW'),
            (r'audi|ауди', 'brand', 'AUDI'),
            (r'mercedes|мерседес', 'brand', 'MERCEDES'),
            (r'ford|форд', 'brand', 'FORD'),
            (r'toyota|тойота', 'brand', 'TOYOTA'),
            (r'honda|хонда', 'brand', 'HONDA'),
            (r'nissan|ниссан', 'brand', 'NISSAN'),
            (r'volkswagen|фольксваген', 'brand', 'VOLKSWAGEN'),
            (r'haval|хавал', 'brand', 'HAVAL'),
            (r'omoda|омода', 'brand', 'OMODA'),
        ]
        
        # Фильтры по мощности
        power_patterns = [
            (r'до\s+(\d+)\s*л\.с\.', 'power_to', int),
            (r'от\s+(\d+)\s*до\s+(\d+)\s*л\.с\.', 'power_range', lambda x, y: (int(x), int(y))),
            (r'(\d+)\s*л\.с\.', 'power_exact', int),
        ]
        
        # Фильтры по объему двигателя
        engine_vol_patterns = [
            (r'до\s+(\d+(?:\.\d+)?)\s*л', 'engine_vol_to', float),
            (r'от\s+(\d+(?:\.\d+)?)\s*до\s+(\d+(?:\.\d+)?)\s*л', 'engine_vol_range', lambda x, y: (float(x), float(y))),
            (r'(\d+(?:\.\d+)?)\s*л', 'engine_vol_exact', float),
        ]
        
        # Фильтры по пробегу
        mileage_patterns = [
            (r'до\s+(\d+(?:\s*\d+)*)\s*км', 'mileage_to', lambda x: int(x.replace(' ', ''))),
            (r'от\s+(\d+(?:\s*\d+)*)\s*до\s+(\d+(?:\s*\d+)*)\s*км', 'mileage_range', lambda x, y: (int(x.replace(' ', '')), int(y.replace(' ', '')))),
            (r'(\d+(?:\s*\d+)*)\s*км', 'mileage_exact', lambda x: int(x.replace(' ', ''))),
        ]
        
        # Фильтры по количеству владельцев
        owners_patterns = [
            (r'от\s+(\d+)\s*до\s+(\d+)\s*владелец', 'owners_range', lambda x, y: (int(x), int(y))),
            (r'от\s+(\d+)\s*до\s+(\d+)\s*владельца', 'owners_range', lambda x, y: (int(x), int(y))),
            (r'от\s+(\d+)\s*до\s+(\d+)\s*владельцев', 'owners_range', lambda x, y: (int(x), int(y))),
            (r'от\s+(\d+)\s*до\s+(\d+)\s*владельцов', 'owners_range', lambda x, y: (int(x), int(y))),
            (r'до\s+(\d+)\s*владелец', 'owners_to', int),
            (r'до\s+(\d+)\s*владельца', 'owners_to', int),
            (r'до\s+(\d+)\s*владельцев', 'owners_to', int),
            (r'до\s+(\d+)\s*владельцов', 'owners_to', int),
            (r'от\s+(\d+)\s*владелец', 'owners_from', int),
            (r'от\s+(\d+)\s*владельца', 'owners_from', int),
            (r'от\s+(\d+)\s*владельцев', 'owners_from', int),
            (r'от\s+(\d+)\s*владельцов', 'owners_from', int),
            (r'(\d+)\s*владелец', 'owners_count', int),
            (r'(\d+)\s*владельца', 'owners_count', int),
            (r'(\d+)\s*владельцев', 'owners_count', int),
            (r'(\d+)\s*владельцов', 'owners_count', int),
        ]
        
        # Фильтры по типу руля
        steering_patterns = [
            (r'левый\s*руль', 'steering_wheel', 'левый'),
            (r'правый\s*руль', 'steering_wheel', 'правый'),
        ]
        
        # Фильтры по истории аварий
        accident_patterns = [
            (r'без\s+аварий', 'accident_history', 'без аварий'),
            (r'с\s+авариями', 'accident_history', 'с авариями'),
            (r'не\s+битый', 'accident_history', 'без аварий'),
            (r'битый', 'accident_history', 'с авариями'),
        ]
        
        for pattern, filter_type, value in brand_patterns:
            if re.search(pattern, query_lower):
                filters[filter_type] = value
                break
        
        # Обработка фильтров по мощности
        for pattern, filter_type, converter in power_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if filter_type == 'power_range':
                    for match in matches:
                        if len(match) == 2:
                            power_from, power_to = converter(match[0], match[1])
                            filters['power_from'] = power_from
                            filters['power_to'] = power_to
                else:
                    for match in matches:
                        if filter_type == 'power_to':
                            filters['power_to'] = converter(match)
                        elif filter_type == 'power_exact':
                            filters['power_exact'] = converter(match)
                break
        
        # Обработка фильтров по объему двигателя
        for pattern, filter_type, converter in engine_vol_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if filter_type == 'engine_vol_range':
                    for match in matches:
                        if len(match) == 2:
                            vol_from, vol_to = converter(match[0], match[1])
                            filters['engine_vol_from'] = vol_from
                            filters['engine_vol_to'] = vol_to
                else:
                    for match in matches:
                        if filter_type == 'engine_vol_to':
                            filters['engine_vol_to'] = converter(match)
                        elif filter_type == 'engine_vol_exact':
                            filters['engine_vol_exact'] = converter(match)
                break
        
        # Обработка фильтров по пробегу
        for pattern, filter_type, converter in mileage_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if filter_type == 'mileage_range':
                    for match in matches:
                        if len(match) == 2:
                            mileage_from, mileage_to = converter(match[0], match[1])
                            filters['mileage_from'] = mileage_from
                            filters['mileage_to'] = mileage_to
                else:
                    for match in matches:
                        if filter_type == 'mileage_to':
                            filters['mileage_to'] = converter(match)
                        elif filter_type == 'mileage_exact':
                            filters['mileage_exact'] = converter(match)
                break
        
        # Обработка фильтров по количеству владельцев
        for pattern, filter_type, converter in owners_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if filter_type == 'owners_range':
                    for match in matches:
                        if len(match) == 2:
                            owners_from, owners_to = converter(match[0], match[1])
                            filters['owners_from'] = owners_from
                            filters['owners_to'] = owners_to
                else:
                    for match in matches:
                        if filter_type == 'owners_to':
                            filters['owners_to'] = converter(match)
                        elif filter_type == 'owners_from':
                            filters['owners_from'] = converter(match)
                        elif filter_type == 'owners_count':
                            filters['owners_count'] = converter(match)
                break
        
        # Обработка фильтров по типу руля
        for pattern, filter_type, value in steering_patterns:
            if re.search(pattern, query_lower):
                filters[filter_type] = value
                break
        
        # Обработка фильтров по истории аварий
        for pattern, filter_type, value in accident_patterns:
            if re.search(pattern, query_lower):
                filters[filter_type] = value
                break
        
        return filters

    def format_comparison_table(self, comparison_result: Dict[str, Any]) -> str:
        """
        Форматирует результат сравнения в виде таблицы.
        
        Args:
            comparison_result: Результат сравнения от compare_by_names
            
        Returns:
            Отформатированная строка с таблицей сравнения
        """
        if comparison_result.get('type') != 'comparison_table':
            return comparison_result.get('message', 'Ошибка сравнения')
        
        cars = comparison_result.get('cars', [])
        features = comparison_result.get('features', [])
        
        if not cars:
            return "Не найдено автомобилей для сравнения"
        
        # Заголовок таблицы
        table = "📊 **СРАВНЕНИЕ АВТОМОБИЛЕЙ**\n\n"
        
        # Заголовки колонок
        headers = ["Характеристика"]
        for car in cars:
            name = car.get('comparison_name', f"{car.get('mark', '')} {car.get('model', '')}").strip()
            headers.append(name)
        
        table += "| " + " | ".join(headers) + " |\n"
        table += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # Строки с характеристиками
        for feature in features:
            row = [self._get_feature_display_name(feature)]
            
            for car in cars:
                value = car.get(feature)
                if value is None:
                    row.append("—")
                else:
                    row.append(self._format_feature_value(feature, value))
            
            table += "| " + " | ".join(row) + " |\n"
        
        return table

    def _get_feature_display_name(self, feature: str) -> str:
        """Возвращает отображаемое название характеристики"""
        display_names = {
            'price': '💰 Цена',
            'manufacture_year': '📅 Год выпуска',
            'color': '🎨 Цвет',
            'body_type': '🚗 Тип кузова',
            'fuel_type': '⛽ Тип топлива',
            'power': '⚡ Мощность',
            'engine_vol': '🔧 Объем двигателя'
        }
        return display_names.get(feature, feature.title())

    def _format_feature_value(self, feature: str, value: Any) -> str:
        """Форматирует значение характеристики для отображения"""
        if value is None:
            return "—"
        
        if feature == 'price':
            return f"{value:,} ₽"
        elif feature == 'power':
            return f"{value} л.с."
        elif feature == 'engine_vol':
            return f"{value} л"
        else:
            return str(value) 