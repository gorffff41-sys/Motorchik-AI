# ВАЖНО: Не импортировать ничего из app.py, чтобы не было циклических зависимостей!
import json
from database import CacheManager, get_car_options, get_full_car_info, compare_cars, filter_cars, get_all_brands, get_all_models, get_dealer_centers_for_car, get_dealer_center_info_by_code, smart_filter_cars, get_all_dealer_centers
from nlp_processor import NLPProcessor, extract_down_payment, extract_term, extract_price, extract_year, extract_mileage, extract_contact, extract_date, extract_price_range, extract_year_range, extract_city
import sqlite3
from user_history import UserHistory

# --- Универсальный словарь синонимов моделей для нечеткого поиска ---
MODEL_SYNONYMS = {
    # BMW
    'x5': ['x5', '5 серии', '5 серия', '5 series'],
    '5 серии': ['5 серии', '5 серия', 'x5', '5 series'],
    '5 серия': ['5 серия', '5 серии', 'x5', '5 series'],
    'x3': ['x3', '3 серии', '3 серия', '3 series'],
    'x6': ['x6', '6 серии', '6 серия', '6 series'],
    'x4': ['x4', '4 серии', '4 серия', '4 series'],
    'x7': ['x7', '7 серии', '7 серия', '7 series'],
    # Mercedes
    'e-class': ['e-class', 'e класс', 'eкласс', 'e class', 'e200', 'e220', 'e300', 'e350', 'e400', 'e450', 'e500'],
    'c-class': ['c-class', 'c класс', 'cкласс', 'c class', 'c180', 'c200', 'c220', 'c250', 'c300', 'c350'],
    # Audi
    'a4': ['a4', 'а4', 'a 4', 'а 4'],
    'a6': ['a6', 'а6', 'a 6', 'а 6'],
    'q5': ['q5', 'к5', 'q 5', 'к 5'],
    # ... можно расширять для других брендов и моделей
}

def get_model_synonyms_universal(model):
    if not model:
        return []
    key = str(model).lower().replace(' ', '')
    for canon, syns in MODEL_SYNONYMS.items():
        if key in [s.replace(' ', '') for s in syns]:
            return syns
    return [model]

class DialogManager:
    def __init__(self):
        self.cache = CacheManager()
        self.nlp = NLPProcessor()

    def handle_query(self, user_id: str, query: str) -> str:
        try:
            cached = self.cache.get_simple_cache(query)
            if cached:
                return cached

            # Получение текущего контекста
            context = self.cache.get_context(user_id)

            # NLP обработка
            nlp_result = self.nlp.process_query(query)
            intent = nlp_result.get("intent")
            entities = {**context.get("entities", {}), **nlp_result.get("entities", {})}
            context.update({
                "intent": intent,
                "entities": entities,
                "step": context.get("step", 0) + 1
            })

            # Сохраняем контекст для отладки
            self.cache.save_context(user_id, context)

            # Обработка intent-ов
            if intent in ("car_info", "options", "photo", "info"):
                brand = entities.get("brand")
                model = entities.get("model")
                used = entities.get("state") == "used"
                
                if not brand and not model:
                    return "Пожалуйста, укажите марку и модель автомобиля, который вас интересует."
                
                car = get_full_car_info(brand, model, used=used)
                if not car:
                    return f"К сожалению, не найдено информации о {brand or ''} {model or ''}. Попробуйте уточнить марку и модель."
                
                # Формируем подробный ответ
                info = f"Марка: {car.get('mark')}, Модель: {car.get('model')}, Год: {car.get('manufacture_year')}, Цена: {car.get('price')} руб, Топливо: {car.get('fuel_type')}, Мощность: {car.get('power')} л.с., Коробка: {car.get('gear_box_type')}, Кузов: {car.get('body_type')}, Город: {car.get('city')}"
                options = car.get('options', [])
                pics = car.get('pictures', [])
                result = [info]
                if options:
                    result.append("\nОпции:")
                    for opt in options:
                        result.append(f"- {opt['description']}")
                if pics:
                    result.append("\nФото:")
                    for pic in pics[:3]:
                        result.append(f"{pic['url']}")
                return "\n".join(result)

            # COMPARE
            if intent == "compare":
                # Ожидаем entities["cars"] = список словарей {brand, model, used}
                cars_to_compare = entities.get("cars")
                if not cars_to_compare:
                    return "🔍 Уточните, какие автомобили сравнить (марка и модель). Например: 'сравни BMW X5 и Mercedes GLE'"
                infos = compare_cars(cars_to_compare)
                if not infos:
                    return "❌ Нет данных для сравнения."
                result = ["📊 Сравнение автомобилей:"]
                for car in infos:
                    info = f"🚗 {car.get('mark')} {car.get('model')} ({car.get('manufacture_year')}), 💰 {car.get('price')} руб, ⛽ {car.get('fuel_type')}, 🏎️ {car.get('power')} л.с., 🚙 {car.get('body_type')}"
                    result.append(info)
                return "\n".join(result)

            # RECOMMENDATIONS
            if intent == "recommendations":
                # Получаем рекомендации на основе истории пользователя
                try:
                    with sqlite3.connect('instance/cars.db') as conn:
                        cursor = conn.cursor()
                        
                        # Простая логика рекомендаций
                        cursor.execute("""
                            SELECT * FROM car 
                            ORDER BY RANDOM() 
                    
                        """)
                        
                        cars = cursor.fetchall()
                        if cars:
                            result = ["🎯 Рекомендуемые автомобили:"]
                            for car in cars:
                                info = f"🚗 {car[1]} {car[2]} ({car[3]}), 💰 {car[4]} руб"
                                result.append(info)
                            return "\n".join(result)
                        else:
                            return "❌ К сожалению, не удалось найти рекомендации."
                except Exception as e:
                    return "❌ Ошибка получения рекомендаций. Попробуйте позже."

            # FILTER
            if intent == "filter":
                # Попробовать извлечь диапазоны и город
                text = query
                price_min, price_max = extract_price_range(text)
                year_min, year_max = extract_year_range(text)
                # Получить список городов из БД (или захардкодить для примера)
                city_list = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск"]
                city = extract_city(text, city_list)
                filtered = filter_cars(
                    brand=entities.get("brand"),
                    model=entities.get("model"),
                    year=year_min if year_min else entities.get("year"),
                    price_min=price_min,
                    price_max=price_max,
                    city=city if city else entities.get("city"),
                    body_type=entities.get("body_type"),
                    used=entities.get("state") == "used"
                )
                if not filtered:
                    return "🔍 Нет подходящих автомобилей по вашему запросу. Попробуйте изменить фильтры."
                result = [f"📋 Найдено автомобилей: {len(filtered)}"]
                for car in filtered[:5]:
                    info = f"🚗 {car.get('mark')} {car.get('model')} ({car.get('manufacture_year')}), 💰 {car.get('price')} руб, ⛽ {car.get('fuel_type')}, 🏎️ {car.get('power')} л.с., 🚙 {car.get('body_type')}"
                    result.append(info)
                if len(filtered) > 5:
                    result.append("...и другие")
                return "\n".join(result)

            # LIST_BRANDS
            if intent == "list_brands":
                brands = get_all_brands()
                return "🏷️ Доступные бренды:\n" + ", ".join(brands)

            # LIST_MODELS
            if intent == "list_models":
                models = get_all_models()
                return "🚗 Доступные модели:\n" + ", ".join(models)

            # LOAN
            if intent == "loan":
                required = ["price", "down_payment", "term"]
                missing = [p for p in required if not entities.get(p)]
                # Попробовать извлечь недостающие параметры из текста
                if missing:
                    text = query
                    if "price" in missing:
                        price = extract_price(text)
                        if price:
                            entities["price"] = price
                    if "down_payment" in missing:
                        down = extract_down_payment(text)
                        if down:
                            entities["down_payment"] = down
                    if "term" in missing:
                        term = extract_term(text)
                        if term:
                            entities["term"] = term
                    # Перепроверить
                    missing = [p for p in required if not entities.get(p)]
                    if missing:
                        context["entities"] = entities
                        self.cache.save_context(user_id, context)
                        return f"💰 Для расчёта кредита укажите: {', '.join(missing)}"
                price = float(entities["price"])
                down = float(entities["down_payment"])
                term = int(entities["term"])
                rate = 0.12
                loan_sum = price - down
                monthly = int((loan_sum * (rate/12) * (1 + rate/12)**(term*12)) / ((1 + rate/12)**(term*12) - 1))
                return f"💰 Ваш платёж: {monthly:,} руб/мес. Оформляем заявку? 📝"

            # TEST_DRIVE
            if intent == "test_drive":
                required = ["brand", "model", "date", "contact"]
                missing = [p for p in required if not entities.get(p)]
                if missing:
                    text = query
                    if "date" in missing:
                        date = extract_date(text)
                        if date:
                            entities["date"] = date
                    if "contact" in missing:
                        contact = extract_contact(text)
                        if contact:
                            entities["contact"] = contact
                    missing = [p for p in required if not entities.get(p)]
                    if missing:
                        context["entities"] = entities
                        self.cache.save_context(user_id, context)
                        return f"🎯 Для записи на тест-драйв укажите: {', '.join(missing)}"
                return f"✅ Вы записаны на тест-драйв {entities['brand']} {entities['model']} на {entities['date']}. Наш менеджер свяжется с вами по {entities['contact']}! 📞"

            # TRADE_IN
            if intent == "trade_in":
                required = ["brand", "model", "year", "mileage"]
                missing = [p for p in required if not entities.get(p)]
                if missing:
                    text = query
                    if "year" in missing:
                        year = extract_year(text)
                        if year:
                            entities["year"] = year
                    if "mileage" in missing:
                        mileage = extract_mileage(text)
                        if mileage:
                            entities["mileage"] = mileage
                    missing = [p for p in required if not entities.get(p)]
                    if missing:
                        context["entities"] = entities
                        self.cache.save_context(user_id, context)
                        return f"🔄 Для оценки trade-in укажите: {', '.join(missing)}"
                price = 500_000  # Здесь можно добавить реальный расчёт
                return f"💰 Предварительная оценка вашего {entities['brand']} {entities['model']} {entities['year']} — {price:,} руб. Ждём вас на осмотр! 🔍"

            # DEALER_CENTER
            if intent == "dealer_center":
                brand = entities.get("brand")
                model = entities.get("model")
                city = entities.get("city")
                used = entities.get("state") == "used"
                # --- Новая логика: если есть только бренд, ищем дилеров по бренду и городу ---
                if brand and not model:
                    # 1. Определяем город: из запроса, из истории, иначе спрашиваем
                    user_city = city or context.get('entities', {}).get('city')
                    if not user_city:
                        return "В каком городе вы находитесь? Укажите город, чтобы найти ближайший дилерский центр."
                    from database import get_all_dealer_centers
                    all_dealers = get_all_dealer_centers(user_city)
                    filtered = [d for d in all_dealers if d.get('brands') and brand.lower() in d['brands'].lower()]
                    if not filtered:
                        return f"❌ Нет дилеров {brand} в городе {user_city}."
                    # Если есть координаты — ищем ближайшего, иначе берём первого
                    best = filtered[0]
                    msg = [f"🏢 Ближайший дилер {brand} в {user_city}:"]
                    website_str = f"\n🌐 {best['website']}" if best.get('website') else ""
                    hours_str = f"\n🕒 {best['working_hours']}" if best.get('working_hours') else ""
                    msg.append(f"{best['name']}\n📍 {best['address']}\n📞 {best['phone'] or '-'}{website_str}{hours_str}")
                    if len(filtered) > 1:
                        msg.append(f"...и ещё {len(filtered)-1} дилеров в этом городе")
                    return "\n\n".join(msg)
                # --- Старая логика: если есть бренд и модель ---
                if not brand or not model:
                    return "🏢 Пожалуйста, уточните марку и модель автомобиля, чтобы я мог подсказать дилерский центр."
                city_param = city if isinstance(city, str) and city else None
                dealer_centers = get_dealer_centers_for_car(brand, model, city_param)
                if not dealer_centers:
                    return f"❌ К сожалению, информация о дилерских центрах для {brand} {model} отсутствует в базе данных."
                if len(dealer_centers) == 1:
                    dealer = dealer_centers[0]
                    if isinstance(dealer, dict) and dealer.get('address') and dealer.get('phone'):
                        return f"🏢 Дилерский центр {brand} {model}: {dealer['address']}, 📞 тел: {dealer['phone']}"
                    else:
                        return f"🏢 Дилерский центр {brand} {model}: {dealer}"
                else:
                    result = [f"🏢 Дилерские центры {brand} {model}:"]
                    for dealer in dealer_centers[:3]:
                        if isinstance(dealer, dict) and dealer.get('address'):
                            result.append(f"📍 {dealer['address']}")
                        else:
                            result.append(f"📍 {dealer}")
                    if len(dealer_centers) > 3:
                        result.append("...и другие")
                    return "\n".join(result)

            # NEW: OWNERSHIP_COST
            if intent == "ownership_cost":
                brand = entities.get("brand")
                model = entities.get("model")
                if not brand or not model:
                    return "💰 Для расчета стоимости владения укажите марку и модель автомобиля."
                
                # Простой расчет стоимости владения
                try:
                    with sqlite3.connect('instance/cars.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT price FROM car WHERE mark LIKE ? AND model LIKE ?", 
                                     [f"%{brand}%", f"%{model}%"])
                        result = cursor.fetchone()
                        
                        if result:
                            price = result[0]
                            # Расчет стоимости владения (упрощенный)
                            insurance = price * 0.05  # 5% от стоимости
                            maintenance = price * 0.02  # 2% от стоимости
                            fuel = 15000  # Примерно в год
                            total_yearly = insurance + maintenance + fuel
                            
                            return f"💰 Стоимость владения {brand} {model} в год:\n" \
                                   f"🚗 Страховка: {insurance:,.0f} руб\n" \
                                   f"🔧 ТО: {maintenance:,.0f} руб\n" \
                                   f"⛽ Топливо: {fuel:,.0f} руб\n" \
                                   f"📊 Итого: {total_yearly:,.0f} руб/год"
                        else:
                            return f"❌ Не найдена информация о {brand} {model}"
                except Exception as e:
                    return "❌ Ошибка расчета стоимости владения."

            # NEW: DISCOUNTS
            if intent == "discounts":
                return "🎉 Текущие акции и скидки:\n" \
                       "🏷️ Скидка 10% на все BMW до конца месяца\n" \
                       "🎯 Mercedes - бесплатный первый ТО\n" \
                       "💰 Кредит от 0.1% на Audi\n" \
                       "🎁 Подарок при покупке любого автомобиля"

            # NEW: WARRANTY
            if intent == "warranty":
                return "🛡️ Информация о гарантии:\n" \
                       "📅 Стандартная гарантия: 3 года или 100,000 км\n" \
                       "🔧 Расширенная гарантия: до 5 лет\n" \
                       "🚗 Гарантия на подержанные: 1 год\n" \
                       "📞 Подробности у менеджера"

            # SEARCH
            if intent == "search" or intent == "filter":
                brand = get_first(entities.get("brand"))
                model = get_first(entities.get("model"))
                year = get_first(entities.get("year"))
                price_min = get_first(entities.get("price_min"))
                price_max = get_first(entities.get("price_max"))
                fuel_type = get_first(entities.get("fuel_type"))
                body_type = get_first(entities.get("body_type"))
                transmission = get_first(entities.get("transmission"))
                drive_type = get_first(entities.get("drive_type"))
                used = get_first(entities.get("state")) == "used"

                cars, explanation = smart_filter_cars(
                    brand=brand,
                    model=model,
                    year=year,
                    price_min=price_min,
                    price_max=price_max,
                    body_type=body_type,
                    used=used
                )
                if cars:
                    msg = f"{explanation}\n"
                    for car in cars[:5]:
                        msg += f"🚗 {car.get('mark','')} {car.get('model','')} {car.get('manufacture_year','')} — {car.get('price','')} ₽\n"
                    if len(cars) > 5:
                        msg += f"... и ещё {len(cars)-5} автомобилей"
                    return msg
                else:
                    return f"{explanation}"

            # Если intent не распознан, возвращаем общий ответ
            if not intent or intent == "unknown":
                return "🤔 Извините, я не совсем понял ваш запрос. Попробуйте:\n" \
                       "🔍 'найти BMW X5'\n" \
                       "💰 'рассчитать кредит'\n" \
                       "🎯 'записаться на тест-драйв'\n" \
                       "🔄 'оценить trade-in'\n" \
                       "📊 'сравнить автомобили'\n" \
                       "🎉 'акции и скидки'"

            # Если дошли до сюда, значит intent не обработан
            return f"🚧 Функция '{intent}' пока в разработке. Попробуйте другой запрос."

        except Exception as e:
            # Логируем ошибку для отладки
            import logging
            logging.error(f"Ошибка в DialogManager: {str(e)}")
            
            # Возвращаем понятное сообщение пользователю
            return "Извините, произошла техническая ошибка. Попробуйте переформулировать ваш запрос или обратитесь к администратору."

def get_first(val):
    if isinstance(val, list):
        return val[0] if val else None
    if isinstance(val, tuple):
        return val[0] if val else None
    return val

class ContextAwareDialogManager(DialogManager):
    """
    Менеджер диалога с расширенным учётом контекста пользователя:
    - анализирует историю запросов
    - учитывает предпочтения пользователя
    - может персонализировать ответы и рекомендации
    """
    def __init__(self):
        super().__init__()
        self.user_history = UserHistory()

    def handle_query(self, user_id: str, query: str) -> str:
        history = self.user_history.get_user_history(user_id, limit=10)
        preferences = self.user_history.get_preferences(user_id)
        base_response = super().handle_query(user_id, query)
        nlp_result = self.nlp.process_query(query)
        intent = nlp_result.get("intent")
        def get_first_deep(val):
            if isinstance(val, (list, tuple)):
                return get_first_deep(val[0]) if val else None
            return val
        # Новый сценарий: показать последние просмотренные авто
        if intent == "recent_cars":
            from database import get_recent_cars_from_db
            cars = get_recent_cars_from_db(limit=5)
            if cars:
                result = ["🕓 Последние просмотренные автомобили:"]
                for car in cars:
                    info = f"🚗 {car['brand']} {car['model']} {car['year']} — {car['price']} ₽"
                    result.append(info)
                return "\n".join(result)
            else:
                return "Нет недавних автомобилей."
        # Новый сценарий: показать избранное
        if intent == "favorites":
            favorites = self.user_history.get_favorites(user_id)
            if favorites:
                result = ["⭐ Ваши избранные автомобили:"]
                for car in favorites:
                    info = f"🚗 {car['brand']} {car['model']} {car['year']} — {car['price']} ₽"
                    result.append(info)
                return "\n".join(result)
            else:
                return "У вас нет избранных автомобилей."
        # Новый сценарий: показать аналитику интересов
        if intent == "interests":
            stats = self.user_history.get_user_statistics(user_id)
            if stats:
                brands = stats.get('brands', [])
                result = ["📊 Ваша аналитика интересов:"]
                for b in brands:
                    result.append(f"{b['brand']}: {b['count']} запросов, средняя цена: {b['avg_price']} ₽")
                return "\n".join(result)
            else:
                return "Нет аналитики по интересам."
        # Новый сценарий: вернуться к предыдущему вопросу
        if intent == "previous_question":
            if history and len(history) > 1:
                prev = history[1]
                return f"Ваш предыдущий вопрос: '{prev['query']}'\nОтвет: {prev['response']}"
            else:
                return "Нет предыдущих вопросов."
        # Персональные рекомендации (с учётом get_first_deep)
        if intent == "recommendations":
            preferred_brands = preferences.get("preferred_brands")
            preferred_price_range = preferences.get("preferred_price_range")
            brand = get_first_deep(preferred_brands) if preferred_brands else None
            price_min = get_first_deep(preferred_price_range[0]) if preferred_price_range and isinstance(preferred_price_range, list) and len(preferred_price_range) > 0 else None
            price_max = get_first_deep(preferred_price_range[1]) if preferred_price_range and isinstance(preferred_price_range, list) and len(preferred_price_range) > 1 else None
            if brand or price_min or price_max:
                from database import smart_filter_cars
                filtered, explanation = smart_filter_cars(
                    brand=brand,
                    price_min=price_min,
                    price_max=price_max
                )
                if filtered:
                    result = ["🎯 Персональные рекомендации:"]
                    for car in filtered[:3]:
                        info = f"🚗 {car.get('mark')} {car.get('model')} ({car.get('manufacture_year')}), 💰 {car.get('price')} руб"
                        result.append(info)
                    if explanation:
                        result.append(f"\n{explanation}")
                    return "\n".join(result)
                else:
                    return base_response + "\n(Нет персональных рекомендаций по вашим предпочтениям)"
        return base_response

# Пример использования
if __name__ == "__main__":
    dm = DialogManager()
    user_id = "test_user"
    while True:
        query = input("Пользователь: ")
        if query.strip().lower() in ("выход", "exit", "quit"): break
        response = dm.handle_query(user_id, query)
        print("Ассистент:", response) 
 
 