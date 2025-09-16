import requests
import json
import logging
import time
from typing import Dict, Any, Optional
import sqlite3
import re

logger = logging.getLogger("deepseek_service")

class DeepSeekService:
    def __init__(self):
        self.api_url = self._find_working_api_url()
        self.available = self._check_availability()
        self.db_path = "instance/cars.db"
        
    def _find_working_api_url(self) -> str:
        """Пробует несколько адресов DeepSeek и возвращает первый рабочий"""
        urls = [
            "http://host.docker.internal:11888/v1/chat/completions",
            "http://localhost:11888/v1/chat/completions",
            "http://127.0.0.1:11888/v1/chat/completions"
        ]
        for url in urls:
            try:
                # Используем правильный формат запроса для API
                resp = requests.post(url, json={
                    "model": "deepseek-r1:latest",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1
                }, timeout=60)
                if resp.status_code in (200, 400):  # 400 если модель не указана, 200 если есть ответ
                    logger.info(f"DeepSeek API доступен по адресу: {url}")
                    return url
            except Exception as e:
                logger.info(f"DeepSeek API не доступен по адресу {url}: {e}")
        logger.warning("DeepSeek API не найден, используется адрес по умолчанию localhost")
        return "http://localhost:11888/v1/chat/completions"
        
    def _check_availability(self) -> bool:
        """Проверяет доступность DeepSeek API"""
        try:
            response = requests.get("http://host.docker.internal:11888/v1/models", timeout=60)
            if response.status_code == 200:
                logger.info("DeepSeek API доступен")
                return True
        except Exception as e:
            logger.info(f"DeepSeek API не доступен по адресу http://host.docker.internal:11888/v1/models: {e}")
        try:
            response = requests.get("http://localhost:11888/v1/models", timeout=60)
            if response.status_code == 200:
                logger.info("DeepSeek API доступен")
                return True
        except Exception as e:
            logger.info(f"DeepSeek API не доступен по адресу http://localhost:11888/v1/models: {e}")
        try:
            response = requests.get("http://127.0.0.1:11888/v1/models", timeout=60)
            if response.status_code == 200:
                logger.info("DeepSeek API доступен")
                return True
        except Exception as e:
            logger.info(f"DeepSeek API не доступен по адресу http://127.0.0.1:11888/v1/models: {e}")
        # Если ни один из адресов не доступен, возвращаем False
        return False
    
    def _generate_search_conditions(self, query: str) -> str:
        """Генерирует условия поиска на основе запроса пользователя"""
        query_lower = query.lower()
        conditions = []
        
        # Поиск по брендам
        brand_patterns = {
            'bmw': ['bmw', 'бмв'],
            'mercedes': ['mercedes', 'мерседес', 'бенц', 'benz'],
            'audi': ['audi', 'ауди'],
            'volkswagen': ['volkswagen', 'vw', 'фольксваген'],
            'toyota': ['toyota', 'тойота'],
            'honda': ['honda', 'хонда'],
            'nissan': ['nissan', 'ниссан'],
            'ford': ['ford', 'форд'],
            'chevrolet': ['chevrolet', 'chev', 'шевроле'],
            'hyundai': ['hyundai', 'хендай'],
            'kia': ['kia', 'киа'],
            'mazda': ['mazda', 'мазда'],
            'subaru': ['subaru', 'субару'],
            'lexus': ['lexus', 'лексус'],
            'infiniti': ['infiniti', 'инфинити'],
            'volvo': ['volvo', 'вольво'],
            'skoda': ['skoda', 'шкода'],
            'seat': ['seat', 'сеат'],
            'renault': ['renault', 'рено'],
            'peugeot': ['peugeot', 'пежо'],
            'citroen': ['citroen', 'ситроен'],
            'opel': ['opel', 'опель'],
            'fiat': ['fiat', 'фиат'],
            'alfa romeo': ['alfa romeo', 'альфа ромео'],
            'jaguar': ['jaguar', 'ягуар'],
            'land rover': ['land rover', 'ленд ровер'],
            'range rover': ['range rover', 'рейндж ровер'],
            'porsche': ['porsche', 'порше'],
            'ferrari': ['ferrari', 'феррари'],
            'lamborghini': ['lamborghini', 'ламборгини'],
            'maserati': ['maserati', 'мазерати'],
            'bentley': ['bentley', 'бентли'],
            'rolls royce': ['rolls royce', 'роллс ройс'],
            'aston martin': ['aston martin', 'астон мартин'],
            'mclaren': ['mclaren', 'макларен'],
            'bugatti': ['bugatti', 'бугатти'],
            'koenigsegg': ['koenigsegg', 'кенигсегг'],
            'pagani': ['pagani', 'пагани'],
            'lotus': ['lotus', 'лотос'],
            'mini': ['mini', 'мини'],
            'smart': ['smart', 'смарт'],
            'fiat': ['fiat', 'фиат'],
            'lancia': ['lancia', 'ланча'],
            'saab': ['saab', 'сааб'],
            'rover': ['rover', 'ровер'],
            'mg': ['mg', 'мг'],
            'triumph': ['triumph', 'триумф'],
            'jensen': ['jensen', 'дженсен'],
            'bristol': ['bristol', 'бристоль'],
            'morgan': ['morgan', 'морган'],
            'caterham': ['caterham', 'катерхам'],
            'ariel': ['ariel', 'ариэль'],
            'noble': ['noble', 'нобл'],
            'gumpert': ['gumpert', 'гумперт'],
            'wiesmann': ['wiesmann', 'висман'],
            'russian': ['москвич', 'лада', 'ваз', 'автоваз', 'газ', 'уаз', 'камаз', 'зил', 'иж', 'тагaz', 'волга']
        }
        
        for brand, patterns in brand_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                # Создаем условие поиска для всех вариантов написания
                brand_conditions = []
                for pattern in patterns:
                    brand_conditions.append(f"mark LIKE '%{pattern}%'")
                conditions.append(f"({' OR '.join(brand_conditions)})")
                break
        
        # Поиск по типу топлива
        fuel_types = {
            'бензин': ['бензин', 'бензиновый', 'gasoline', 'petrol'],
            'дизель': ['дизель', 'дизельный', 'diesel'],
            'электро': ['электро', 'электрический', 'electric', 'электромобиль'],
            'гибрид': ['гибрид', 'гибридный', 'hybrid'],
            'газ': ['газ', 'газовый', 'lpg', 'cng']
        }
        
        for fuel_type, keywords in fuel_types.items():
            if any(keyword in query_lower for keyword in keywords):
                conditions.append(f"fuel_type LIKE '%{fuel_type}%'")
                break
        
        # Поиск по типу кузова
        body_types = {
            'седан': ['седан', 'sedan'],
            'хэтчбек': ['хэтчбек', 'hatchback', 'хетчбек'],
            'универсал': ['универсал', 'wagon', 'station wagon'],
            'внедорожник': ['внедорожник', 'suv', 'кроссовер', 'crossover'],
            'купе': ['купе', 'coupe'],
            'кабриолет': ['кабриолет', 'cabriolet', 'convertible'],
            'пикап': ['пикап', 'pickup'],
            'микроавтобус': ['микроавтобус', 'minivan', 'минивэн']
        }
        
        for body_type, keywords in body_types.items():
            if any(keyword in query_lower for keyword in keywords):
                conditions.append(f"body_type LIKE '%{body_type}%'")
                break
        
        # Поиск по цене
        price_patterns = [
            (r'до (\d+)', 'price <= {}'),
            (r'от (\d+)', 'price >= {}'),
            (r'(\d+)-(\d+)', 'price BETWEEN {} AND {}')
        ]
        
        for pattern, condition_template in price_patterns:
            matches = re.findall(pattern, query)
            if matches:
                if len(matches[0]) == 1:  # до X или от X
                    value = int(matches[0][0]) * 1000  # предполагаем, что числа в тысячах
                    conditions.append(condition_template.format(value))
                elif len(matches[0]) == 2:  # X-Y
                    min_price = int(matches[0][0]) * 1000
                    max_price = int(matches[0][1]) * 1000
                    conditions.append(condition_template.format(min_price, max_price))
                break
        
        # Поиск по году
        year_patterns = [
            (r'(\d{4}) года?', 'manufacture_year = {}'),
            (r'от (\d{4})', 'manufacture_year >= {}'),
            (r'до (\d{4})', 'manufacture_year <= {}'),
            (r'(\d{4})-(\d{4})', 'manufacture_year BETWEEN {} AND {}')
        ]
        
        for pattern, condition_template in year_patterns:
            matches = re.findall(pattern, query)
            if matches:
                if len(matches[0]) == 1:
                    year = int(matches[0][0])
                    conditions.append(condition_template.format(year))
                elif len(matches[0]) == 2:
                    min_year = int(matches[0][0])
                    max_year = int(matches[0][1])
                    conditions.append(condition_template.format(min_year, max_year))
                break
        
        return ' AND '.join(conditions) if conditions else "1=1"
    
    def _get_db_context(self) -> str:
        """Получает базовый контекст из БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем общую статистику
            cursor.execute("SELECT COUNT(*) FROM car")
            total_cars = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT mark) FROM car")
            unique_brands = cursor.fetchone()[0]
            
            cursor.execute("SELECT mark, COUNT(*) as count FROM car GROUP BY mark ORDER BY count DESC")
            top_brands = cursor.fetchall()
            
            cursor.execute("SELECT model, COUNT(*) as count FROM car GROUP BY model ORDER BY count DESC")
            top_models = cursor.fetchall()
            
            # Получаем статистику по подержанным автомобилям
            cursor.execute("SELECT COUNT(*) FROM used_car")
            total_used_cars = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT mark) FROM used_car")
            unique_used_brands = cursor.fetchone()[0]
            
            conn.close()
            
            context = f"""Общая статистика базы данных:
- Всего новых автомобилей: {total_cars}
- Всего подержанных автомобилей: {total_used_cars}
- Уникальных брендов (новые): {unique_brands}
- Уникальных брендов (подержанные): {unique_used_brands}
- Топ брендов (новые): {', '.join([f'{brand} ({count})' for brand, count in top_brands])}
- Топ моделей (новые): {', '.join([f'{model} ({count})' for model, count in top_models])}

Структура таблиц:
1. Таблица 'car' (новые автомобили):
   - mark: бренд автомобиля
   - model: модель автомобиля
   - manufacture_year: год выпуска
   - price: цена
   - fuel_type: тип топлива
   - body_type: тип кузова
   - gear_box_type: коробка передач
   - engine_vol: объем двигателя
   - color: цвет
   - city: город
   - dealer_center: дилерский центр
   - power: мощность двигателя
   - driving_gear_type: тип привода

2. Таблица 'used_car' (подержанные автомобили):
   - mark: бренд автомобиля
   - model: модель автомобиля
   - manufacture_year: год выпуска
   - price: цена
   - mileage: пробег
   - fuel_type: тип топлива
   - body_type: тип кузова
   - gear_box_type: коробка передач
   - engine_vol: объем двигателя
   - color: цвет
   - city: город
   - power: мощность двигателя
   - driving_gear_type: тип привода
   - accident: аварийность
   - owners: количество владельцев

3. Таблица 'option' (опции автомобилей)
4. Таблица 'picture' (фотографии новых автомобилей)
5. Таблица 'used_car_picture' (фотографии подержанных автомобилей)

ВАЖНО: При поиске учитывай различные варианты написания брендов:
- BMW может быть записан как 'BMW', 'bmw', 'БМВ', 'бмв'
- Mercedes может быть записан как 'Mercedes', 'MERCEDES', 'Mercedes-Benz', 'Бенц'
- Audi может быть записан как 'Audi', 'AUDI', 'Ауди'
- И так далее для всех брендов
"""
            return context
            
        except Exception as e:
            logger.error(f"Ошибка получения контекста БД: {str(e)}")
            return "Ошибка доступа к базе данных"
    
    def _execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Выполняет SQL запрос и возвращает результаты"""
        try:
            # Проверяем безопасность запроса (только SELECT)
            if not sql_query.strip().upper().startswith('SELECT'):
                return {"error": "Разрешены только SELECT запросы"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            # Получаем названия колонок
            column_names = [description[0] for description in cursor.description]
            
            conn.close()
            
            return {
                "success": True,
                "columns": column_names,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Ошибка выполнения SQL запроса: {str(e)}")
            return {"error": str(e)}
    
    def generate_response(self, query: str, user_id: str) -> Dict[str, Any]:
        """Генерирует ответ с автоматическим выполнением SQL запросов"""
        if not self.available:
            return {"success": False, "message": "DeepSeek недоступен"}
        
        try:
            logger.info("🧠 DeepSeek: Начало обработки запроса")
            logger.info(f"🧠 DeepSeek: Запрос: {query}")
            logger.info(f"🧠 DeepSeek: User ID: {user_id}")
            
            # Получаем базовый контекст
            db_context = self._get_db_context()
            logger.info(f"🧠 DeepSeek: Контекст получен, длина: {len(db_context)} символов")
            
            # Генерируем условия поиска
            search_conditions = self._generate_search_conditions(query)
            logger.info(f"🧠 DeepSeek: Сгенерированы условия поиска: {search_conditions}")
            
            # Автоматически выполняем SQL запросы для поиска данных
            sql_results = {}
            
            # Поиск в новых автомобилях
            if search_conditions != "1=1":
                car_sql = f"SELECT mark, model, manufacture_year, price, fuel_type, body_type, gear_box_type, engine_vol, power, color, city, dealer_center FROM car WHERE {search_conditions} ORDER BY price DESC"
                logger.info(f"🧠 DeepSeek: Выполняем SQL для новых авто: {car_sql}")
                car_result = self._execute_sql_query(car_sql)
                if car_result.get("success"):
                    sql_results["new_cars"] = car_result
                    logger.info(f"🧠 DeepSeek: Найдено новых авто: {car_result['count']}")
                else:
                    logger.warning(f"🧠 DeepSeek: Ошибка SQL для новых авто: {car_result.get('error')}")
            
            # Поиск в подержанных автомобилях
            if search_conditions != "1=1":
                used_car_sql = f"SELECT mark, model, manufacture_year, price, mileage, fuel_type, body_type, gear_box_type, engine_vol, power, color, city, accident, owners FROM used_car WHERE {search_conditions} ORDER BY price DESC"
                logger.info(f"🧠 DeepSeek: Выполняем SQL для подержанных авто: {used_car_sql}")
                used_car_result = self._execute_sql_query(used_car_sql)
                if used_car_result.get("success"):
                    sql_results["used_cars"] = used_car_result
                    logger.info(f"🧠 DeepSeek: Найдено подержанных авто: {used_car_result['count']}")
                else:
                    logger.warning(f"🧠 DeepSeek: Ошибка SQL для подержанных авто: {used_car_result.get('error')}")
            
            # Если нет результатов с условиями поиска, пробуем общий поиск
            if not sql_results:
                logger.info("🧠 DeepSeek: Нет результатов с условиями поиска, выполняем общий поиск")
                
                # Общий поиск BMW в обеих таблицах
                general_car_sql = "SELECT mark, model, manufacture_year, price, fuel_type, body_type, gear_box_type, engine_vol, power, color, city, dealer_center FROM car WHERE (mark LIKE '%BMW%' OR mark LIKE '%bmw%' OR mark LIKE '%БМВ%' OR mark LIKE '%бмв%') ORDER BY price DESC"
                general_used_sql = "SELECT mark, model, manufacture_year, price, mileage, fuel_type, body_type, gear_box_type, engine_vol, power, color, city, accident, owners FROM used_car WHERE (mark LIKE '%BMW%' OR mark LIKE '%bmw%' OR mark LIKE '%БМВ%' OR mark LIKE '%бмв%') ORDER BY price DESC"
                
                car_result = self._execute_sql_query(general_car_sql)
                used_car_result = self._execute_sql_query(general_used_sql)
                
                if car_result.get("success") and car_result["count"] > 0:
                    sql_results["new_cars"] = car_result
                if used_car_result.get("success") and used_car_result["count"] > 0:
                    sql_results["used_cars"] = used_car_result
            
            # Формируем промпт для анализа результатов
            if sql_results:
                analysis_prompt = f"""Ты - эксперт по анализу данных об автомобилях. Пользователь задал вопрос: "{query}"

Вот результаты поиска в базе данных:

"""

                for table_name, result in sql_results.items():
                    analysis_prompt += f"""
{table_name.upper()} (найдено {result['count']} записей):
Колонки: {result['columns']}
Данные: {result['results'][:10]}  # Показываем первые 10 результатов"""

                analysis_prompt += f"""

ВАЖНО: Дай ТОЛЬКО финальный, хорошо структурированный ответ на русском языке. НЕ используй теги <think>, НЕ пиши размышления, НЕ объясняй процесс анализа.

Структурируй ответ следующим образом:

# 📊 Анализ данных по запросу "{query}"

## 🎯 Что найдено в базе данных
[Краткое описание найденных данных с конкретными цифрами]

## 📈 Статистика и характеристики
- **Годы выпуска:** [диапазон и особенности с конкретными годами]
- **Типы кузовов:** [основные типы с примерами моделей]
- **Двигатели:** [типы топлива, объемы, мощность с конкретными данными]
- **Цвета:** [основные цвета с процентами]
- **Города:** [география продаж с конкретными городами]

## 💰 Ценовые диапазоны
- **Самые дорогие:** [модели и цены с конкретными суммами]
- **Средний сегмент:** [модели и цены с диапазонами]
- **Доступные варианты:** [модели и цены для бюджетного сегмента]

## 💡 Практические рекомендации
[Конкретные советы по выбору с учетом найденных данных]

## 🔍 Альтернативы
[Если данных мало или нет, предложи альтернативы]

Отвечай кратко, информативно и структурированно. Используй конкретные данные из результатов запросов."""

                logger.info("🧠 DeepSeek: Анализируем результаты SQL запросов...")
                
                # Отправляем запрос на анализ результатов
                system_prompt = "Ты - эксперт по анализу данных об автомобилях. Отвечай на русском языке."
                full_prompt = f"{system_prompt}\n\n{analysis_prompt}"
                
                analysis_payload = {
                    "model": "deepseek-r1:latest",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                start_time = time.time()
                analysis_response = requests.post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json=analysis_payload,
                    timeout=600
                )
                execution_time = time.time() - start_time
                
                if analysis_response.status_code == 200:
                    analysis_result = analysis_response.json()
                    if "choices" in analysis_result and len(analysis_result["choices"]) > 0:
                        final_content = analysis_result["choices"][0]["message"]["content"]
                        
                        # Очищаем ответ
                        final_content = re.sub(r'<think>.*?</think>', '', final_content, flags=re.IGNORECASE | re.DOTALL)
                        final_content = re.sub(r'<think>|</think>', '', final_content, flags=re.IGNORECASE)
                        # Удаляем размышления в начале ответа до первого заголовка
                        final_content = re.sub(r'^.*?(?=# |## |📊|🎯|🔍)', '', final_content, flags=re.DOTALL)
                        final_content = re.sub(r'\n\s*\n', '\n\n', final_content)
                        final_content = final_content.strip()
                        
                        logger.info(f"🧠 DeepSeek: Финальный ответ, длина: {len(final_content)} символов")
                        
                        return {
                            "success": True,
                            "message": final_content,
                            "type": "deepseek_response",
                            "model": "deepseek-r1:latest",
                            "query": query,
                            "execution_time": execution_time,
                            "sql_used": True,
                            "sql_results": sql_results,
                            "total_results": sum(result["count"] for result in sql_results.values())
                        }
                    else:
                        logger.error("🧠 DeepSeek: Неожиданный формат ответа анализа")
                        return {
                            "success": False,
                            "message": "Ошибка анализа результатов SQL запроса",
                            "type": "analysis_error"
                        }
                else:
                    logger.error(f"🧠 DeepSeek: Ошибка API анализа, статус: {analysis_response.status_code}")
                    return {
                        "success": False,
                        "message": f"Ошибка API анализа: {analysis_response.status_code}",
                        "type": "analysis_error"
                    }
            else:
                # Нет данных в базе, даем общий ответ
                logger.info("🧠 DeepSeek: Данные не найдены, даем общий ответ")
                
                general_prompt = f"""Ты - эксперт по автомобилям. Пользователь задал вопрос: "{query}"

К сожалению, в базе данных не найдено информации по этому запросу.

ВАЖНО: Дай ТОЛЬКО финальный, краткий ответ на русском языке. НЕ используй теги <think>, НЕ пиши размышления.

Структурируй ответ так:

# 🔍 Результат поиска

По запросу "{query}" в базе данных ничего не найдено.

## 💡 Рекомендации

- Попробуйте изменить параметры поиска
- Обратитесь к официальным дилерским центрам
- Рассмотрите альтернативные марки автомобилей

Отвечай кратко и по делу."""

                system_prompt = "Ты - эксперт по автомобилям. Отвечай на русском языке."
                full_general_prompt = f"{system_prompt}\n\n{general_prompt}"
                
                general_payload = {
                    "model": "deepseek-r1:latest",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": general_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                start_time = time.time()
                general_response = requests.post(
                    self.api_url,
                    headers={"Content-Type": "application/json"},
                    json=general_payload,
                    timeout=600
                )
                execution_time = time.time() - start_time
                
                if general_response.status_code == 200:
                    general_result = general_response.json()
                    if "choices" in general_result and len(general_result["choices"]) > 0:
                        content = general_result["choices"][0]["message"]["content"]
                        
                        # Очищаем ответ
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.IGNORECASE | re.DOTALL)
                        content = re.sub(r'<think>|</think>', '', content, flags=re.IGNORECASE)
                        # Удаляем размышления в начале ответа до первого заголовка
                        content = re.sub(r'^.*?(?=# |## |🔍|💡)', '', content, flags=re.DOTALL)
                        content = re.sub(r'\n\s*\n', '\n\n', content)
                        content = content.strip()
                        
                        logger.info(f"🧠 DeepSeek: Общий ответ, длина: {len(content)} символов")
                        
                        return {
                            "success": True,
                            "message": content,
                            "type": "deepseek_response",
                            "model": "deepseek-r1:latest",
                            "query": query,
                            "execution_time": execution_time,
                            "sql_used": False,
                            "data_found": False
                        }
                    else:
                        logger.error("🧠 DeepSeek: Неожиданный формат общего ответа")
                        return {
                            "success": False,
                            "message": "По вашему запросу ничего не найдено. Попробуйте изменить параметры поиска.",
                            "type": "no_data_found"
                        }
                else:
                    logger.error(f"🧠 DeepSeek: Ошибка API общего ответа, статус: {general_response.status_code}")
                    return {
                        "success": False,
                        "message": "По вашему запросу ничего не найдено. Попробуйте изменить параметры поиска.",
                        "type": "no_data_found"
                    }
                
        except requests.exceptions.Timeout:
            logger.error("🧠 DeepSeek: Таймаут запроса (более 10 минут)")
            return {
                "success": False, 
                "message": "Запрос к DeepSeek занял более 10 минут. Попробуйте переформулировать вопрос или обратитесь позже.",
                "type": "timeout_error"
            }
        except Exception as e:
            logger.error(f"🧠 DeepSeek: Ошибка: {str(e)}")
            return {"success": False, "message": f"Ошибка DeepSeek: {str(e)}"}

# Создаем глобальный экземпляр сервиса
deepseek_service = DeepSeekService() 