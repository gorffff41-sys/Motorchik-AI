import json
from typing import Dict, Any, Optional

# --- Модули-обработчики (заглушки, кроме SearchModule) ---
class SearchModule:
    def process(self, query: str, entities: Dict, context: Dict, offset: int = 0, limit: int = 10, show_cars: bool = False) -> Dict:
        from database import search_all_cars
        import difflib
        # --- Расширенный словарь синонимов для цветов ---
        COLOR_SYNONYMS = {
            'белый': [
                'белый', 'Белый', 'white', 'White', 'белая', 'Белая', 'белое', 'Белое', 'белые', 'Белые',
                'белого', 'Белого', 'белой', 'Белой', 'белого', 'Белого', 'белых', 'Белых',
                'перламутровый белый', 'pearlescent white', 'керамический белый', 'ceramic white',
                'белоснежный', 'снежно-белый', 'crystal white', 'alpine white', 'arctic white',
                'ivory white', 'pearl white', 'diamond white', 'platinum white'
            ],
            'черный': [
                'черный', 'Черный', 'black', 'Black', 'чёрный', 'Чёрный',
                'черного', 'Черного', 'черной', 'Черной', 'черного', 'Черного', 'черных', 'Черных',
                'глубокий черный', 'deep black', 'cosmic black', 'midnight black',
                'onyx black', 'ebony black', 'jet black', 'carbon black',
                'obsidian black', 'pitch black', 'void black'
            ],
            'серый': [
                'серый', 'Серый', 'gray', 'Gray', 'grey', 'Grey',
                'серого', 'Серого', 'серой', 'Серой', 'серого', 'Серого', 'серых', 'Серых',
                'серебристый', 'silver', 'silver metallic', 'steel gray',
                'platinum gray', 'titanium gray', 'gunmetal gray', 'charcoal gray',
                'slate gray', 'ash gray', 'pewter gray', 'smoke gray'
            ],
            'синий': [
                'синий', 'Синий', 'blue', 'Blue', 'голубой', 'Голубой',
                'синего', 'Синего', 'синей', 'Синей', 'синего', 'Синего', 'синих', 'Синих',
                'navy blue', 'royal blue', 'sapphire blue', 'cobalt blue',
                'ocean blue', 'sky blue', 'azure blue', 'electric blue',
                'midnight blue', 'steel blue', 'powder blue', 'cornflower blue'
            ],
            'красный': [
                'красный', 'Красный', 'red', 'Red',
                'красного', 'Красного', 'красной', 'Красной', 'красного', 'Красного', 'красных', 'Красных',
                'огненно-красный', 'fire red', 'crimson red', 'scarlet red',
                'ruby red', 'cherry red', 'burgundy red', 'candy red',
                'racing red', 'flame red', 'cardinal red', 'maroon red'
            ],
            'зеленый': [
                'зеленый', 'Зеленый', 'зелёный', 'Зелёный', 'green', 'Green',
                'зеленого', 'Зеленого', 'зеленой', 'Зеленой', 'зеленого', 'Зеленого', 'зеленых', 'Зеленых',
                'изумрудный', 'emerald green', 'forest green', 'olive green',
                'sage green', 'mint green', 'jade green', 'hunter green',
                'kelly green', 'lime green', 'sea green', 'moss green'
            ],
            'желтый': [
                'желтый', 'Желтый', 'yellow', 'Yellow',
                'желтого', 'Желтого', 'желтой', 'Желтой', 'желтого', 'Желтого', 'желтых', 'Желтых',
                'золотистый', 'golden yellow', 'sunny yellow', 'canary yellow',
                'amber yellow', 'honey yellow', 'lemon yellow', 'butter yellow',
                'banana yellow', 'corn yellow', 'wheat yellow'
            ],
            'оранжевый': [
                'оранжевый', 'Оранжевый', 'orange', 'Orange',
                'оранжевого', 'Оранжевого', 'оранжевой', 'Оранжевой', 'оранжевого', 'Оранжевого', 'оранжевых', 'Оранжевых',
                'ярко-оранжевый', 'bright orange', 'tangerine orange', 'pumpkin orange',
                'sunset orange', 'coral orange', 'peach orange', 'apricot orange',
                'carrot orange', 'amber orange', 'copper orange'
            ],
            'фиолетовый': [
                'фиолетовый', 'Фиолетовый', 'purple', 'Purple', 'violet', 'Violet',
                'фиолетового', 'Фиолетового', 'фиолетовой', 'Фиолетовой', 'фиолетового', 'Фиолетового', 'фиолетовых', 'Фиолетовых',
                'пурпурный', 'Пурпурный', 'lavender purple', 'royal purple',
                'plum purple', 'grape purple', 'orchid purple', 'amethyst purple',
                'magenta purple', 'burgundy purple', 'eggplant purple'
            ],
            'розовый': [
                'розовый', 'Розовый', 'pink', 'Pink',
                'розового', 'Розового', 'розовой', 'Розовой', 'розового', 'Розового', 'розовых', 'Розовых',
                'нежно-розовый', 'light pink', 'hot pink', 'rose pink',
                'salmon pink', 'peach pink', 'blush pink', 'fuchsia pink',
                'magenta pink', 'coral pink', 'dusty pink', 'baby pink'
            ],
            'коричневый': [
                'коричневый', 'Коричневый', 'brown', 'Brown',
                'коричневого', 'Коричневого', 'коричневой', 'Коричневой', 'коричневого', 'Коричневого', 'коричневых', 'Коричневых',
                'шоколадный', 'chocolate brown', 'coffee brown', 'caramel brown',
                'tan brown', 'beige brown', 'mocha brown', 'walnut brown',
                'mahogany brown', 'chestnut brown', 'saddle brown', 'taupe brown'
            ],
            'бежевый': [
                'бежевый', 'Бежевый', 'beige', 'Beige',
                'бежевого', 'Бежевого', 'бежевой', 'Бежевой', 'бежевого', 'Бежевого', 'бежевых', 'Бежевых',
                'светло-бежевый', 'light beige', 'cream beige', 'ivory beige',
                'sand beige', 'warm beige', 'cool beige', 'neutral beige',
                'champagne beige', 'pearl beige', 'almond beige'
            ],
            'голубой': [
                'голубой', 'Голубой', 'light blue', 'Light Blue', 'светло-синий', 'Светло-синий',
                'голубого', 'Голубого', 'голубой', 'Голубой', 'голубого', 'Голубого', 'голубых', 'Голубых',
                'baby blue', 'sky blue', 'powder blue', 'periwinkle blue',
                'cornflower blue', 'azure blue', 'robin egg blue', 'steel blue'
            ],
            'темно-синий': [
                'темно-синий', 'Темно-синий', 'dark blue', 'Dark Blue', 'navy', 'Navy',
                'темно-синего', 'Темно-синего', 'темно-синей', 'Темно-синей', 'темно-синего', 'Темно-синего', 'темно-синих', 'Темно-синих',
                'navy blue', 'midnight blue', 'royal blue', 'sapphire blue',
                'cobalt blue', 'indigo blue', 'marine blue', 'ocean blue'
            ],
            'серебристый': [
                'серебристый', 'Серебристый', 'silver', 'Silver',
                'серебристого', 'Серебристого', 'серебристой', 'Серебристой', 'серебристого', 'Серебристого', 'серебристых', 'Серебристых',
                'silver metallic', 'platinum silver', 'titanium silver',
                'chrome silver', 'aluminum silver', 'pewter silver',
                'steel silver', 'nickel silver', 'brushed silver'
            ],
            'золотистый': [
                'золотистый', 'Золотистый', 'gold', 'Gold', 'golden', 'Golden',
                'золотистого', 'Золотистого', 'золотистой', 'Золотистой', 'золотистого', 'Золотистого', 'золотистых', 'Золотистых',
                'golden yellow', 'champagne gold', 'honey gold', 'amber gold',
                'bronze gold', 'copper gold', 'brass gold', 'metallic gold'
            ],
            'бронзовый': [
                'бронзовый', 'Бронзовый', 'bronze', 'Bronze',
                'antique bronze', 'copper bronze', 'golden bronze',
                'metallic bronze', 'aged bronze', 'patina bronze'
            ],
            'медный': [
                'медный', 'Медный', 'copper', 'Copper',
                'copper metallic', 'antique copper', 'rose copper',
                'burnished copper', 'patina copper'
            ]
        }
        BODY_SYNONYMS = {
            'седан': ['седан', 'sedan'],
            'внедорожник': ['внедорожник', 'suv', 'offroad'],
            'кроссовер': ['кроссовер', 'crossover'],
            'универсал': ['универсал', 'wagon'],
            'хетчбэк': ['хетчбэк', 'хэтчбек', 'hatchback'],
            'лифтбэк': ['лифтбэк', 'liftback'],
            'купе': ['купе', 'coupe'],
            'пикап': ['пикап', 'pickup'],
            'минивэн': ['минивэн', 'minivan'],
            'микроавтобус': ['микроавтобус', 'microbus'],
            'кабриолет': ['кабриолет', 'convertible'],
            'фургон': ['фургон', 'van'],
        }
        FUEL_SYNONYMS = {
            'бензин': ['бензин', 'petrol', 'gasoline'],
            'дизель': ['дизель', 'diesel'],
            'электро': ['электро', 'электрический', 'electric', 'ev'],
            'гибрид': ['гибрид', 'hybrid'],
            'газ': ['газ', 'lpg', 'cng'],
        }
        DRIVE_SYNONYMS = {
            'передний': ['передний', 'front', 'fwd'],
            'полный': ['полный', 'awd', '4wd', 'all-wheel', '4x4'],
            'задний': ['задний', 'rwd', 'rear'],
        }
        TRANSMISSION_SYNONYMS = {
            'автомат': ['автомат', 'automatic', 'at'],
            'механика': ['механика', 'manual', 'mt'],
        }
        # --- Универсальная функция для синонимов ---
        def synonym_match(val, target, syn_dict):
            if not val or not target:
                return False
            val, target = str(val).lower(), str(target).lower()
            for base, syns in syn_dict.items():
                if val == base or val in syns:
                    if target == base or target in syns:
                        return True
            return False
        # --- Динамические синонимы для городов и дилеров ---
        from database import get_all_cities, get_all_dealer_centers
        import unidecode
        def build_synonyms_dict(values):
            syns = {}
            for v in values:
                v_norm = str(v).strip().lower()
                variants = set()
                variants.add(v_norm)
                variants.add(v_norm.replace('ё', 'е'))
                variants.add(v_norm.replace(' ', ''))
                variants.add(unidecode.unidecode(v_norm))
                if ' ' in v_norm:
                    parts = v_norm.split()
                    for p in parts:
                        variants.add(p)
                syns[v_norm] = list(variants)
            return syns
        # Получаем все города и дилеры из БД
        all_cities = get_all_cities()
        all_dealers = [d['name'] for d in get_all_dealer_centers()] if get_all_dealer_centers() else []
        DYNAMIC_CITY_SYNONYMS = build_synonyms_dict(all_cities)
        DYNAMIC_DEALER_SYNONYMS = build_synonyms_dict(all_dealers)
        # --- Динамические синонимы для цвета салона и ПТС ---
        def get_all_unique_field_values(field):
            from database import search_all_cars
            values = set()
            for car in search_all_cars():
                v = car.get(field, '')
                if v:
                    values.add(str(v).strip().lower())
            return values
        all_salon_colors = get_all_unique_field_values('salon_color')
        all_pts_colors = get_all_unique_field_values('pts_color')
        DYNAMIC_SALON_COLOR_SYNONYMS = build_synonyms_dict(all_salon_colors)
        DYNAMIC_PTS_COLOR_SYNONYMS = build_synonyms_dict(all_pts_colors)
        
        # --- Новые синонимы для расширенных фильтров ---
        CAR_STATE_SYNONYMS = {
            'new': ['новый', 'новый автомобиль', 'new'],
            'used': ['с пробегом', 'б/у', 'подержанный', 'автомобиль с пробегом', 'used']
        }
        
        POPULAR_OPTIONS_SYNONYMS = {
            'S403A': ['люк', 'sunroof', 'открывающаяся крыша'],
            'S423A': ['панорамная крыша', 'panoramic roof', 'панорамная'],
            'S430A': ['климат-контроль', 'climate control', 'кондиционер'],
            'S431A': ['подогрев сидений', 'heated seats', 'подогрев'],
            'S459A': ['электрорегулировка сидений', 'power seats'],
            'S494A': ['система парковки', 'parking system'],
            'S502A': ['навигация', 'navigation', 'gps'],
            'S508A': ['парктроник', 'parking sensors'],
            'S521A': ['датчик дождя', 'rain sensor'],
            'S522A': ['ксенон', 'xenon'],
            'S524A': ['адаптивные фары', 'adaptive headlights'],
            'S534A': ['система комфортного доступа', 'comfort access'],
            'LUXURY': ['люкс-комплектация', 'люкс', 'luxury'],
            'COMFORT': ['комфорт-комплектация', 'комфорт', 'comfort'],
            'SPORT': ['спорт-комплектация', 'спорт', 'sport'],
            'FAMILY': ['семейная комплектация', 'семейная', 'family'],
            'BUSINESS': ['бизнес-комплектация', 'бизнес', 'business']
        }
        
        MILEAGE_RANGE_SYNONYMS = {
            'до 20 тыс': ['до 20 тыс км', 'до 20 тысяч', 'маленький пробег'],
            'до 50 тыс': ['до 50 тыс км', 'до 50 тысяч'],
            'до 100 тыс': ['до 100 тыс км', 'до 100 тысяч'],
            'до 200 тыс': ['до 200 тыс км', 'до 200 тысяч'],
            '20-50 тыс': ['20-50 тыс км', '20-50 тысяч'],
            '50-100 тыс': ['50-100 тыс км', '50-100 тысяч'],
            '100-200 тыс': ['100-200 тыс км', '100-200 тысяч'],
            'более 200 тыс': ['более 200 тыс км', 'более 200 тысяч', 'большой пробег']
        }
        
        SCENARIO_SYNONYMS = {
            'семейный': ['семейный', 'семья', 'family', 'для семьи', 'с детьми'],
            'для города': ['городской', 'город', 'city', 'компактный', 'маневренный'],
            'для путешествий': ['путешествия', 'поездки', 'travel', 'внедорожник', 'кроссовер'],
            'для работы': ['работа', 'бизнес', 'work', 'business', 'солидный'],
            'для дачи': ['дача', 'загородный', 'проходимость', 'вместительность'],
            'для молодежи': ['молодежный', 'молодежь', 'youth', 'спортивный', 'динамичный'],
            'для бизнеса': ['бизнес', 'престижный', 'люкс', 'premium'],
            'экономичный': ['экономичный', 'экономия', 'дешевый', 'бюджетный']
        }
        # --- Динамические синонимы для опций (комплектаций) ---
        def get_all_unique_options():
            from database import get_all_options
            options = set()
            for opt in get_all_options():
                name = opt.get('description') or opt.get('code')
                if name:
                    options.add(str(name).strip().lower())
            return options
        all_options = get_all_unique_options()
        DYNAMIC_OPTION_SYNONYMS = build_synonyms_dict(all_options)
        OPTION_SYNONYMS = DYNAMIC_OPTION_SYNONYMS  # Можно добавить статические, если есть
        # --- Сбор фильтров для search_all_cars ---
        filters = {}
        
        # --- ДОБАВЛЕНО: извлекаем все цвета из текста запроса независимо от NER ---
        try:
            ql_text = (query or '').lower()
            found_color_bases = []
            for base_color, synonyms in COLOR_SYNONYMS.items():
                # если в тексте встречается базовое название или любой синоним
                if base_color in ql_text or any(s.lower() in ql_text for s in synonyms):
                    found_color_bases.append(base_color)
            # убираем дубликаты, сохраняем порядок появления
            seen = set()
            unique_colors = []
            for c in found_color_bases:
                if c not in seen:
                    seen.add(c)
                    unique_colors.append(c)
            if unique_colors:
                # если несколько цветов — используем список, если один — оставим как список (поддержка И/ИЛИ на постфильтрации)
                entities.setdefault('colors', unique_colors)
        except Exception:
            pass

        # --- Приведение brand к строке (en) перед формированием filters ---
        brand_entity = entities.get('brand') or entities.get('mark')
        if brand_entity and isinstance(brand_entity, dict):
            filters['brand'] = brand_entity.get('en') or list(brand_entity.values())[0]
        else:
            filters['brand'] = brand_entity
            
        filters['model'] = entities.get('model')
        filters['year_from'] = entities.get('year_from')
        filters['year_to'] = entities.get('year_to')
        filters['price_from'] = entities.get('price_from')
        filters['price_to'] = entities.get('price_to')
        filters['fuel_type'] = entities.get('fuel_type')
        filters['transmission'] = entities.get('transmission') or entities.get('gear_box_type')
        filters['body_type'] = entities.get('body_type')
        filters['drive_type'] = entities.get('drive_type') or entities.get('driving_gear_type')
        filters['city'] = entities.get('city')
        filters['seats'] = entities.get('seats')
        # Новые числовые фильтры производительности
        if entities.get('power_from') is not None:
            filters['power_from'] = entities.get('power_from')
        if entities.get('power_to') is not None:
            filters['power_to'] = entities.get('power_to')
        # Обработка цвета: поддержка списка цветов и ключа 'colors'
        color_entity = entities.get('color')
        colors_list = entities.get('colors')
        if colors_list and isinstance(colors_list, list) and len(colors_list) > 0:
            filters['color'] = colors_list
        else:
            filters['color'] = color_entity  # строка или None
        # --- ДОБАВЛЕНО: фильтр по опциям ---
        if entities.get('options'):
            opts = entities['options']
            if not isinstance(opts, list):
                opts = [opts]
            filters['option_description'] = opts
        print(f"[SearchModule] entities: {entities}")
        print(f"[SearchModule] filters: {filters}")
        # --- Поиск по БД ---
        cars = search_all_cars(**{k: v for k, v in filters.items() if v is not None})
        # --- ЛОГИ ДЛЯ ДИАГНОСТИКИ body_type ---
        if filters.get('body_type'):
            unique_body_types = set((car.get('body_type') or '').lower() for car in cars)
            print(f"[DEBUG] Фильтр body_type: {filters['body_type']}, уникальные body_type в cars: {unique_body_types}")
        # --- Fuzzy/синонимы для цвета, дилера, VIN, опций, мощности, объема, салона, ПТС, модельного года, крутящего момента, разгона, габаритов, массы, багажника ---
        import difflib
        def fuzzy_match(val, target, cutoff=0.7):
            if not val or not target:
                return False
            if isinstance(val, (int, float)):
                return val == target
            val, target = str(val).lower(), str(target).lower()
            return val == target or difflib.SequenceMatcher(None, val, target).ratio() >= cutoff
        # --- Словари синонимов ---
        # --- Словари синонимов ---
        CITY_SYNONYMS = {
            'москва': ['москва', 'moscow', 'msk'],
            'санкт-петербург': ['санкт-петербург', 'питер', 'spb', 'saint petersburg', 'st. petersburg'],
            'казань': ['казань', 'kazan'],
            'краснодар': ['краснодар', 'krasnodar'],
            'екатеринбург': ['екатеринбург', 'екб', 'ekaterinburg'],
            'новосибирск': ['новосибирск', 'novosibirsk'],
            # ... можно расширить
        }
        DEALER_SYNONYMS = {
            'ultrand_krd': ['ultrand_krd', 'ultrand', 'ультранд', 'ультранд краснодар'],
            'aaa_motors': ['aaa_motors', 'aaa motors', 'ааа моторс', 'aaa'],
            # ... можно расширить
        }
        SALON_COLOR_SYNONYMS = {
            'черный': ['черный', 'чёрный', 'black', 'dark'],
            'бежевый': ['бежевый', 'beige', 'ivory'],
            'коричневый': ['коричневый', 'brown', 'coffee'],
            'серый': ['серый', 'gray', 'grey'],
            # ... можно расширить
        }
        PTS_COLOR_SYNONYMS = COLOR_SYNONYMS  # Цвет по ПТС совпадает с основными цветами
        # Объединяем статические и динамические синонимы
        def merge_synonyms(static, dynamic):
            merged = dict(static)
            for k, v in dynamic.items():
                if k in merged:
                    merged[k] = list(set(merged[k] + v))
                else:
                    merged[k] = v
            return merged
        CITY_SYNONYMS = merge_synonyms(CITY_SYNONYMS, DYNAMIC_CITY_SYNONYMS)
        DEALER_SYNONYMS = merge_synonyms(DEALER_SYNONYMS, DYNAMIC_DEALER_SYNONYMS)
        SALON_COLOR_SYNONYMS = merge_synonyms(SALON_COLOR_SYNONYMS, DYNAMIC_SALON_COLOR_SYNONYMS)
        PTS_COLOR_SYNONYMS = merge_synonyms(PTS_COLOR_SYNONYMS, DYNAMIC_PTS_COLOR_SYNONYMS)
        # --- Сортировка и ранжирование ---
        sort_by = entities.get('sort_by') or 'price'
        sort_order = entities.get('sort_order') or 'asc'
        # --- Post-фильтрация по остальным полям с fuzzy/синонимами ---
        color = entities.get('color')
        options = entities.get('options')
        dealer = entities.get('dealer')
        salon_color = entities.get('salon_color')
        pts_color = entities.get('pts_color')
        vin = entities.get('vin')
        engine_volume = entities.get('engine_volume')
        engine_volume_from = entities.get('engine_volume_from')
        engine_volume_to = entities.get('engine_volume_to')
        torque = entities.get('torque')
        torque_from = entities.get('torque_from')
        torque_to = entities.get('torque_to')
        acceleration = entities.get('acceleration')
        acceleration_from = entities.get('acceleration_from')
        acceleration_to = entities.get('acceleration_to')
        mass = entities.get('mass')
        mass_from = entities.get('mass_from')
        mass_to = entities.get('mass_to')
        trunk_volume = entities.get('trunk_volume')
        trunk_volume_from = entities.get('trunk_volume_from')
        trunk_volume_to = entities.get('trunk_volume_to')
        model_year = entities.get('model_year')
        model_year_from = entities.get('model_year_from')
        model_year_to = entities.get('model_year_to')
        salon_color_from = entities.get('salon_color_from')
        salon_color_to = entities.get('salon_color_to')
        pts_color_from = entities.get('pts_color_from')
        pts_color_to = entities.get('pts_color_to')
        dimensions = entities.get('dimensions')
        # ... остальные переменные по необходимости ...
        filtered = []
        for car in cars:
            # --- Множественные цвета (OR и комбинации) ---
            if color:
                car_color = (car.get('color') or '').lower()
                if isinstance(color, list):
                    # Ищем если хотя бы один цвет совпадает или если все цвета входят в строку цвета (комбинация)
                    if not (
                        any(fuzzy_match(c, car_color) or synonym_match(c, car_color, COLOR_SYNONYMS) for c in color)
                        or all(c in car_color for c in color)
                    ):
                        continue
                else:
                    if not (fuzzy_match(color, car_color) or synonym_match(color, car_color, COLOR_SYNONYMS)):
                        continue
            # --- Количество мест уже обработано на уровне БД ---
            # --- Размер (если есть поле size) ---
            size = entities.get('size')
            car_size = car.get('size')
            if size:
                if car_size:
                    if size.lower() not in str(car_size).lower():
                        continue
                else:
                    # Если нет size, анализируем тип кузова, модель, марку
                    body_type = (car.get('body_type') or '').lower()
                    model = (car.get('model') or '').lower()
                    mark = (car.get('mark') or '').lower()
                    # Маленькие: хэтчбек, компакт, мини, smart, fiat 500, peugeot 107 и т.д.
                    if size == 'маленькая':
                        if not (body_type in ['хэтчбек', 'компакт', 'мини'] or 'smart' in model or 'fiat' in model or 'peugeot 107' in model or 'mini' in model or 'a1' in model or 'picanto' in model or 'matiz' in model):
                            continue
                    if size == 'большая':
                        if not (body_type in ['внедорожник', 'минивэн', 'микроавтобус', 'седан', 'универсал'] or 'land cruiser' in model or 'escalade' in model or 'gls' in model or 's-class' in model):
                            continue
            if filters.get('body_type') and not (fuzzy_match(filters['body_type'], car.get('body_type')) or synonym_match(filters['body_type'], car.get('body_type'), BODY_SYNONYMS)):
                continue
            if filters.get('fuel_type') and not (fuzzy_match(filters['fuel_type'], car.get('fuel_type')) or synonym_match(filters['fuel_type'], car.get('fuel_type'), FUEL_SYNONYMS)):
                continue
            if filters.get('drive_type') and not (fuzzy_match(filters['drive_type'], car.get('driving_gear_type')) or synonym_match(filters['drive_type'], car.get('driving_gear_type'), DRIVE_SYNONYMS)):
                continue
            if filters.get('transmission') and not (fuzzy_match(filters['transmission'], car.get('gear_box_type')) or synonym_match(filters['transmission'], car.get('gear_box_type'), TRANSMISSION_SYNONYMS)):
                continue
            if filters.get('city') and not (fuzzy_match(filters['city'], car.get('city')) or synonym_match(filters['city'], car.get('city'), CITY_SYNONYMS)):
                continue
            if dealer and not (fuzzy_match(dealer, car.get('dealer_center')) or synonym_match(dealer, car.get('dealer_center'), DEALER_SYNONYMS)):
                continue
            if vin and car.get('vin') != vin:
                continue
            if engine_volume and car.get('engine_vol') != engine_volume:
                continue
            if engine_volume_from and car.get('engine_vol') and car.get('engine_vol') < engine_volume_from:
                continue
            if engine_volume_to and car.get('engine_vol') and car.get('engine_vol') > engine_volume_to:
                continue
            if salon_color and not (fuzzy_match(salon_color, car.get('salon_color')) or synonym_match(salon_color, car.get('salon_color'), SALON_COLOR_SYNONYMS)):
                continue
            if pts_color and not (fuzzy_match(pts_color, car.get('pts_color')) or synonym_match(pts_color, car.get('pts_color'), PTS_COLOR_SYNONYMS)):
                continue
            if model_year and car.get('model_year') != model_year:
                continue
            if torque and car.get('power') != torque:
                continue
            if torque_from and car.get('power') and car.get('power') < torque_from:
                continue
            if torque_to and car.get('power') and car.get('power') > torque_to:
                continue
            if acceleration and car.get('acceleration') != acceleration:
                continue
            if acceleration_from and car.get('acceleration') and car.get('acceleration') < acceleration_from:
                continue
            if acceleration_to and car.get('acceleration') and car.get('acceleration') > acceleration_to:
                continue
            if dimensions and car.get('dimensions') != dimensions:
                continue
            if mass and car.get('mass') != mass:
                continue
            if mass_from and car.get('mass') and car.get('mass') < mass_from:
                continue
            if mass_to and car.get('mass') and car.get('mass') > mass_to:
                continue
            if trunk_volume and car.get('trunk_volume') != trunk_volume:
                continue
            if trunk_volume_from and car.get('trunk_volume') and car.get('trunk_volume') < trunk_volume_from:
                continue
            if trunk_volume_to and car.get('trunk_volume') and car.get('trunk_volume') > trunk_volume_to:
                continue
            if options:
                car_options = set(car.get('options', []))
                # Сравниваем каждую опцию с синонимами
                if not all(any(synonym_match(opt, car_opt, OPTION_SYNONYMS) for car_opt in car_options) for opt in options):
                    continue
            
            # --- Новые фильтры ---
            
            # Состояние автомобиля (новый/б/у)
            state = entities.get('state')
            if state:
                # Определяем состояние по таблице (car = новый, used_car = б/у)
                car_state = 'new' if 'car' in str(car.get('source', '')) else 'used'
                if not synonym_match(state, car_state, CAR_STATE_SYNONYMS):
                    continue
            
            # Популярные опции по кодам
            option_codes = entities.get('option_codes')
            if option_codes:
                car_options = set(car.get('options', []))
                # Проверяем наличие хотя бы одной из запрошенных опций
                found_options = []
                for option_code in option_codes:
                    if any(synonym_match(option_code, car_opt, POPULAR_OPTIONS_SYNONYMS) for car_opt in car_options):
                        found_options.append(option_code)
                if not found_options:
                    continue
            
            # Диапазоны пробега (для подержанных авто)
            mileage_from = entities.get('mileage_from')
            mileage_to = entities.get('mileage_to')
            if mileage_from or mileage_to:
                car_mileage = car.get('mileage')
                if car_mileage:
                    if mileage_from and car_mileage < mileage_from:
                        continue
                    if mileage_to and car_mileage > mileage_to:
                        continue
                else:
                    # Если нет пробега, это новый автомобиль
                    if mileage_from or mileage_to:
                        continue
            
            # Сценарии использования
            scenario = entities.get('scenario')
            if scenario:
                # Примитивная логика для сценариев
                body_type = (car.get('body_type') or '').lower()
                model = (car.get('model') or '').lower()
                mark = (car.get('mark') or '').lower()
                price = car.get('price', 0)
                
                if scenario == 'семейный':
                    # Семейные: универсал, минивэн, внедорожник, седан
                    if not (body_type in ['универсал', 'минивэн', 'внедорожник', 'седан'] or 
                           'wagon' in model or 'minivan' in model or 'suv' in model):
                        continue
                elif scenario == 'для города':
                    # Городские: хэтчбек, компакт, седан
                    if not (body_type in ['хэтчбек', 'компакт', 'седан'] or 
                           'hatchback' in model or 'compact' in model or 'a1' in model or 'smart' in model):
                        continue
                elif scenario == 'для путешествий':
                    # Путешествия: внедорожник, кроссовер, универсал
                    if not (body_type in ['внедорожник', 'кроссовер', 'универсал'] or 
                           'suv' in model or 'crossover' in model or 'wagon' in model):
                        continue
                elif scenario == 'для работы':
                    # Работа: седан, универсал, бизнес-класс
                    if not (body_type in ['седан', 'универсал'] or 
                           'sedan' in model or 'wagon' in model or 'e-class' in model or '5-series' in model):
                        continue
                elif scenario == 'для дачи':
                    # Дача: внедорожник, пикап, высокий клиренс
                    if not (body_type in ['внедорожник', 'пикап'] or 
                           'suv' in model or 'pickup' in model or 'land cruiser' in model):
                        continue
                elif scenario == 'для молодежи':
                    # Молодежь: спортивные, динамичные, хэтчбек, купе
                    if not (body_type in ['хэтчбек', 'купе', 'спортивный'] or 
                           'hatchback' in model or 'coupe' in model or 'gti' in model or 'rs' in model):
                        continue
                elif scenario == 'для бизнеса':
                    # Бизнес: люкс-седан, премиум
                    if not (body_type in ['седан'] or 
                           's-class' in model or '7-series' in model or 'a8' in model or price > 3000000):
                        continue
                elif scenario == 'экономичный':
                    # Экономичные: дешевые, малолитражные
                    if price > 1500000:  # Бюджет до 1.5 млн
                        continue
            
            filtered.append(car)
        # --- Снятие ограничения на количество авто по запросу пользователя ---
        show_all = False
        if 'покажи все' in query.lower() or 'выведи все' in query.lower() or 'все автомобили' in query.lower():
            show_all = True
        # --- Сортировка ---
        def get_sort_key(car):
            if sort_by in ['price', 'manufacture_year', 'power', 'acceleration', 'engine_vol', 'mass', 'trunk_volume']:
                return car.get(sort_by) or 0
            return str(car.get(sort_by, '')).lower()
        reverse = sort_order == 'desc'
        filtered = sorted(filtered, key=get_sort_key, reverse=reverse)
        applied_filters = {k: v for k, v in entities.items() if v is not None}
        # --- Проверка наличия цвета в базе ---
        if color and len(filtered) == 0:
            if isinstance(color, list):
                # Удалён блок с not_found
                pass
            else:
                # Удалён блок с not_found
                pass
        # --- Проверка наличия по размеру/местам ---
        # Убираем дублирующую проверку seats, так как она уже применена на уровне БД
        size = entities.get('size')
        if size and len(filtered) == 0:
            return {
                'type': 'no_results',
                'message': 'К сожалению, не найдено автомобилей с такими параметрами размера. Попробуйте изменить критерии поиска.',
                'entities': entities,
                'applied_filters': applied_filters,
                'count': 0,
                'suggestions': [
                    'Попробуйте поискать без указания размера',
                    'Попробуйте другие параметры поиска'
                ]
            }
        # --- Если вообще ничего не найдено ---
        if len(filtered) == 0:
            return {
                'type': 'no_results',
                'message': 'К сожалению, не найдено автомобилей по вашему запросу. Попробуйте изменить параметры поиска.',
                'entities': entities,
                'applied_filters': applied_filters,
                'count': 0,
                'suggestions': [
                    'Попробуйте поискать только по бренду',
                    'Попробуйте поискать только по цвету', 
                    'Попробуйте другие цвета или бренды'
                ]
            }
        # --- Fallback на LLM для уточнений ---
        def llm_clarification(entities, count):
            if count == 0:
                return {
                    'need_clarification': True,
                    'clarification': 'Не найдено ни одного автомобиля. Пожалуйста, уточните параметры поиска или попробуйте изменить фильтры.'
                }
            
            # Убираем ограничения по количеству сущностей - поиск работает с любым количеством критериев
            # Показываем все результаты независимо от количества сущностей
                return None
                
        # Проверяем, есть ли результаты
        if len(filtered) == 0:
            # Если нет результатов, показываем сообщение с предложением альтернатив
                return {
                'type': 'no_results',
                'message': f'К сожалению, не найдено автомобилей по вашему запросу. Попробуйте изменить параметры поиска.',
                'entities': entities,
                'applied_filters': applied_filters,
                'count': 0,
                'suggestions': [
                    'Попробуйте поискать только по бренду',
                    'Попробуйте поискать только по цвету', 
                    'Попробуйте другие цвета или бренды'
                ]
            }
        # --- ПАГИНАЦИЯ ---
        total_count = len(filtered)
        has_more = total_count > offset + limit
        # Возвращаем все найденные машины без ограничения
        cars_page = filtered
        # Если есть llm_answer и show_cars=False, сначала только сообщение и флаг
        if context.get('llm_answer') and not show_cars:
            return {
                'type': 'llm_answer_with_cars',
                'message': context['llm_answer'] + '\n\nПоказать найденные автомобили?',
                'show_cars_required': True,
                'total_count': total_count,
                'has_more': has_more,
                'show_more_instruction': 'Показать еще',
                'cars': [],
            }
        return {
            'type': 'car_list',
            'message': f'Найдено {total_count} автомобилей по фильтрам.',
            'cars': cars_page,
            'has_more': has_more,
            'total_count': total_count,
            'show_more_instruction': 'Показать еще' if has_more else ''
        }

class CompareModule:
    def process(self, query: str, entities: Dict, context: Dict, offset: int = 0, limit: int = 10, show_cars: bool = False) -> Dict:
        from database import search_all_cars, get_full_car_info
        import difflib
        # Ожидаем либо список id, либо список (марка, модель)
        car_ids = entities.get('car_ids')
        pairs = entities.get('compare_pairs')  # [{'mark':..., 'model':...}, ...]
        cars = []
        if car_ids:
            for cid in car_ids:
                car = get_full_car_info(car_id=cid)
                if car:
                    cars.append(car)
        elif pairs:
            for pair in pairs:
                mark = pair.get('mark') or pair.get('brand')
                model = pair.get('model')
                found = [c for c in search_all_cars(brand=mark, model=model)]
                if found:
                    cars.append(found[0])
            if not cars:
                from llama_service import generate_with_llama
                llm_answer = generate_with_llama(f'Пользователь хочет сравнить автомобили по запросу: "{query}". В базе не найдено ни одной подходящей машины для сравнения. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
                return {
                    'type': 'clarification',
                    'message': 'В базе не найдено ни одной подходящей машины для сравнения.',
                    'llm_answer': llm_answer,
                    'entities': entities
                }
        else:
            # Попробуем извлечь марки/модели из текста (fuzzy)
            text = query.lower()
            all_cars = search_all_cars()
            all_marks = set(c['mark'].lower() for c in all_cars if c.get('mark'))
            all_models = set(c['model'].lower() for c in all_cars if c.get('model'))
            found_marks = [m for m in all_marks if m in text]
            found_models = [m for m in all_models if m in text]
            for mark in found_marks:
                for model in found_models:
                    found = [c for c in all_cars if c['mark'].lower() == mark and c['model'].lower() == model]
                    if found:
                        cars.append(found[0])
            # Если не нашли — уточнение
            if not cars:
                return {
                    'type': 'clarification',
                    'need_clarification': True,
                    'clarification': 'Пожалуйста, укажите хотя бы две машины для сравнения (по id или марке и модели).',
                    'entities': entities
                }
        if len(cars) < 2:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет сравнить автомобили по запросу: "{query}". В базе найдено менее двух подходящих машин. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Для сравнения нужно минимум 2 автомобиля.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        # Формируем таблицу сравнения по ключевым характеристикам
        fields = [
            ('mark', 'Марка'),
            ('model', 'Модель'),
            ('manufacture_year', 'Год'),
            ('price', 'Цена'),
            ('power', 'Мощность'),
            ('fuel_type', 'Топливо'),
            ('driving_gear_type', 'Привод'),
            ('acceleration', 'Разгон 0-100'),
            ('mass', 'Масса'),
            ('trunk_volume', 'Багажник'),
        ]
        table = []
        for field, label in fields:
            row = [label]
            for car in cars:
                val = car.get(field, '-')
                row.append(val)
            table.append(row)
        # Формируем текстовую таблицу
        table_str = '\n'.join([' | '.join(map(str, row)) for row in table])
        message = f'Сравнение автомобилей:\n\n{table_str}'
        # --- Интеграция с LLM для объяснения различий ---
        llm_explanation = None
        try:
            from llama_service import generate_with_llama
            explain_prompt = f"Сравни автомобили по этим данным и объясни основные различия:\n{table_str}"
            llm_explanation = generate_with_llama(explain_prompt)
        except Exception:
            llm_explanation = None
        total_count = len(cars)
        has_more = total_count > offset + limit
        cars_page = cars[offset:offset+limit] if show_cars or not context.get('llm_answer') else []
        # Если есть llm_answer и show_cars=False, сначала только сообщение и флаг
        if context.get('llm_answer') and not show_cars:
            return {
                'type': 'llm_answer_with_cars',
                'message': context['llm_answer'] + '\n\nПоказать найденные автомобили?',
                'show_cars_required': True,
                'total_count': total_count,
                'has_more': has_more,
                'show_more_instruction': 'Показать еще',
                'cars': [],
            }
        return {
            'type': 'comparison',
            'cars': cars_page,
            'count': len(cars_page),
            'fields': [f[0] for f in fields],
            'table': table,
            'message': message,
            'llm_explanation': llm_explanation,
            'total_count': total_count,
            'has_more': has_more,
            'show_more_instruction': 'Показать еще' if has_more else '',
        }
class LoanModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        # Ожидаемые параметры: price, down_payment, term_months, interest_rate
        price = entities.get('price')
        down_payment = entities.get('down_payment', 0)
        term = entities.get('term_months', 36)
        rate = entities.get('interest_rate', 0.15)  # 15% годовых по умолчанию
        try:
            price = float(price)
            down_payment = float(down_payment)
            term = int(term)
            rate = float(rate)
        except Exception:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет рассчитать кредит по запросу: "{query}". Введены некорректные параметры. Всегда отвечай только на русском языке. Объясни, какие параметры нужны и предложи пример.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Пожалуйста, укажите корректные параметры: цену, первоначальный взнос, срок (мес), ставку (%).',
                'llm_answer': llm_answer,
                'entities': entities
            }
        loan_amount = price - down_payment
        if loan_amount <= 0 or term <= 0 or rate < 0:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет рассчитать кредит по запросу: "{query}". Введены некорректные параметры (отрицательная сумма, срок или ставка). Всегда отвечай только на русском языке. Объясни, какие параметры нужны и предложи пример.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Проверьте параметры: сумма кредита, срок и ставка должны быть положительными.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        # Аннуитетная формула
        monthly_rate = rate / 12
        if monthly_rate > 0:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
        else:
            monthly_payment = loan_amount / term
        overpayment = monthly_payment * term - loan_amount
        return {
            'type': 'loan_calc',
            'price': price,
            'down_payment': down_payment,
            'loan_amount': loan_amount,
            'term_months': term,
            'interest_rate': rate,
            'monthly_payment': round(monthly_payment, 2),
            'overpayment': round(overpayment, 2),
            'message': f'Ежемесячный платёж: {round(monthly_payment,2)} ₽. Переплата: {round(overpayment,2)} ₽.'
        }
class DetailsModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        from database import get_full_car_info, search_all_cars
        car_id = entities.get('car_id')
        vin = entities.get('vin')
        mark = entities.get('mark') or entities.get('brand')
        model = entities.get('model')
        car = None
        if car_id:
            car = get_full_car_info(car_id=car_id)
        elif vin:
            found = [c for c in search_all_cars() if c.get('vin') == vin]
            if found:
                car = found[0]
        elif mark and model:
            found = [c for c in search_all_cars(brand=mark, model=model)]
            if found:
                car = found[0]
        if not car:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет получить подробную информацию по запросу: "{query}". В базе не найдено ни одной подходящей машины. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Пожалуйста, уточните id, VIN или марку и модель автомобиля для получения подробной информации.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        # Формируем подробное описание
        details = {k: v for k, v in car.items() if v not in (None, '', [])}
        message = '\n'.join([f'{k}: {v}' for k, v in details.items()])
        return {
            'type': 'car_details',
            'car': car,
            'details': details,
            'message': message
        }
class DealerModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        # Заготовка: поиск информации о дилере по названию, городу или id
        dealer = entities.get('dealer')
        city = entities.get('city')
        dealer_id = entities.get('dealer_id')
        # TODO: реализовать поиск дилера через database.get_all_dealer_centers()
        from llama_service import generate_with_llama
        llm_answer = generate_with_llama(f'Пользователь ищет информацию о дилере по запросу: "{query}". В базе нет информации о таком дилере. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
        return {
            'type': 'dealer_info',
            'message': 'Информация о дилере в разработке.',
            'llm_answer': llm_answer,
            'entities': entities
        }
class RecommendationModule:
    def process(self, query: str, entities: Dict, context: Dict, offset: int = 0, limit: int = 10, show_cars: bool = False) -> Dict:
        from database import search_all_cars
        # Используем предпочтения: бюджет, тип кузова, топливо, город и др.
        price_to = entities.get('price_to')
        body_type = entities.get('body_type')
        fuel_type = entities.get('fuel_type')
        city = entities.get('city')
        # Можно добавить больше фильтров по entities
        filters = {}
        if price_to:
            filters['price_to'] = price_to
        if body_type:
            filters['body_type'] = body_type
        if fuel_type:
            filters['fuel_type'] = fuel_type
        if city:
            filters['city'] = city
        if not filters:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет получить рекомендации по запросу: "{query}". Не указаны предпочтения. Всегда отвечай только на русском языке. Объясни, какие параметры нужны и предложи пример.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Пожалуйста, укажите ваши предпочтения: бюджет, тип кузова, топливо, город и т.д. для рекомендации.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        cars = search_all_cars(**filters)
        if not cars:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет получить рекомендации по запросу: "{query}". В базе нет подходящих автомобилей. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Не найдено подходящих автомобилей. Попробуйте изменить предпочтения.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        # Сортируем по цене по возрастанию
        cars = sorted(cars, key=lambda c: c.get('price', 0))
        top_cars = cars[:5]
        message = 'Рекомендуемые автомобили:\n' + '\n'.join([f"{c.get('mark', '')} {c.get('model', '')}, {c.get('price', '')} ₽" for c in top_cars])
        total_count = len(cars)
        has_more = total_count > offset + limit
        cars_page = cars[offset:offset+limit] if show_cars or not context.get('llm_answer') else []
        # Если есть llm_answer и show_cars=False, сначала только сообщение и флаг
        if context.get('llm_answer') and not show_cars:
            return {
                'type': 'llm_answer_with_cars',
                'message': context['llm_answer'] + '\n\nПоказать найденные автомобили?',
                'show_cars_required': True,
                'total_count': total_count,
                'has_more': has_more,
                'show_more_instruction': 'Показать еще',
                'cars': [],
            }
        return {
            'type': 'recommendation',
            'cars': cars_page,
            'count': len(cars_page),
            'message': message,
            'total_count': total_count,
            'has_more': has_more,
            'show_more_instruction': 'Показать еще' if has_more else '',
        }
class VINModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        vin = entities.get('vin')
        # TODO: реализовать проверку VIN через базу или внешний сервис
        if not vin:
            from llama_service import generate_with_llama
            llm_answer = generate_with_llama(f'Пользователь хочет проверить VIN по запросу: "{query}". VIN не указан. Всегда отвечай только на русском языке. Объясни, зачем нужен VIN и предложи пример.')
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': 'Пожалуйста, укажите VIN для проверки.',
                'llm_answer': llm_answer,
                'entities': entities
            }
        # Заглушка: просто возвращаем VIN
        return {
            'type': 'vin_check',
            'vin': vin,
            'message': f'Проверка VIN {vin} в разработке.'
        }
class StatisticsModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        from database import search_all_cars, get_all_cities, get_all_dealer_centers
        try:
            cars = search_all_cars()
            total = len(cars)
            if total == 0:
                from llama_service import generate_with_llama
                llm_answer = generate_with_llama(f'Пользователь хочет получить статистику по базе по запросу: "{query}". В базе нет автомобилей. Всегда отвечай только на русском языке. Объясни ситуацию или предложи альтернативу.')
                return {
                    'type': 'clarification',
                    'need_clarification': True,
                    'clarification': 'В базе нет автомобилей для статистики.',
                    'llm_answer': llm_answer,
                    'entities': entities
                }
            avg_price = sum(c.get('price', 0) or 0 for c in cars) / total if total else 0
            from collections import Counter
            marks = Counter(c.get('mark') for c in cars if c.get('mark'))
            cities = Counter(c.get('city') for c in cars if c.get('city'))
            body_types = Counter(c.get('body_type') for c in cars if c.get('body_type'))
            stats = {
                'total_cars': total,
                'average_price': round(avg_price, 2),
                'top_marks': marks.most_common(5),
                'top_cities': cities.most_common(5),
                'top_body_types': body_types.most_common(5),
            }
            message = f"Всего авто: {total}\nСредняя цена: {round(avg_price,2)} ₽\nТоп-5 марок: {stats['top_marks']}\nТоп-5 городов: {stats['top_cities']}\nТоп-5 типов кузова: {stats['top_body_types']}"
            return {
                'type': 'statistics',
                'stats': stats,
                'message': message
            }
        except Exception as e:
            return {
                'type': 'clarification',
                'need_clarification': True,
                'clarification': f'Ошибка при получении статистики: {e}',
                'entities': entities
            }
class ClarificationModule:
    def process(self, query: str, entities: Dict, context: Dict) -> Dict:
        # Примитивная заглушка — всегда fallback на LLM
        from llama_service import generate_with_llama
        llm_answer = generate_with_llama(f'Пользователь задал уточняющий вопрос: "{query}". Система не смогла дать ответ. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
        return {
            'type': 'clarification',
            'message': 'Система не смогла дать уточняющий ответ.',
            'llm_answer': llm_answer,
            'entities': entities
        }

# --- Классификатор типа запроса ---
class QueryClassifier:
    def classify(self, query: str, entities: dict, context: dict = None) -> str:
        # Улучшенная эвристика: если нет автомобильных ключей — general
        AUTO_KEYWORDS = [
            'машин', 'авто', 'car', 'mark', 'model', 'модель', 'марка', 'цена', 'год', 'кузов', 'двигатель',
            'лошад', 'сил', 'разгон', 'багажник', 'привод', 'коробка', 'топливо', 'hybrid', 'электро',
            'внедорожник', 'седан', 'купе', 'кабриолет', 'универсал', 'хэтчбек', 'минивэн', 'микроавтобус',
            'vin', 'дилер', 'салон', 'цвет', 'power', 'engine', 'fuel', 'dealer', 'option', 'комплектация',
            'полнопривод', 'передний привод', 'задний привод', 'мощность', 'объем', 'torque', 'acceleration',
            'размер', 'мест', 'маленьк', 'больш', 'электромобиль', 'hybrid', 'plug-in', 'turbo', 'turbocharged',
            'turbo', 'turbocharged', 'turbo', 'turbocharged', 'turbo', 'turbocharged', 'turbo', 'turbocharged',
        ]
        ql = query.lower()
        if not any(k in ql for k in AUTO_KEYWORDS):
            return 'general'
        # Примитивные правила (можно заменить на ML/LLM)
        q = query.lower()
        if any(w in q for w in ['сравни', 'vs', 'отличия', 'разница', 'чем лучше', 'чем отличается']):
            return 'compare'
        if any(w in q for w in ['кредит', 'рассрочка', 'платеж', 'ипотека', 'сколько в месяц']):
            return 'loan'
        if any(w in q for w in ['vin', 'вин', 'проверь', 'история', 'номер кузова']):
            return 'vin'
        if any(w in q for w in ['дилер', 'салон', 'где купить', 'адрес', 'центр']):
            return 'dealer'
        if any(w in q for w in ['рекоменд', 'подбери', 'совет', 'лучший', 'выбери']):
            return 'recommendation'
        if any(w in q for w in ['статистик', 'сколько всего', 'топ', 'самый популярный']):
            return 'statistics'
        if any(w in q for w in ['подробнее', 'характеристик', 'опция', 'комплектация', 'деталь', 'что такое']):
            return 'details'
        if any(w in q for w in ['уточни', 'какой', 'какая', 'какие', 'что еще', 'ещё', 'другой', 'альтернатива']):
            return 'clarification'
        # По умолчанию — поиск
        return 'search'

# --- Диалоговый менеджер (контекст, история) ---
class DialogManager:
    def __init__(self):
        self.user_contexts = {}
    def get_context(self, user_id: str) -> dict:
        return self.user_contexts.get(user_id, {'history': []})
    def update_context(self, user_id: str, context: dict):
        self.user_contexts[user_id] = context
    def append_message(self, user_id: str, role: str, message: str):
        ctx = self.get_context(user_id)
        ctx.setdefault('history', []).append({'role': role, 'message': message})
        self.update_context(user_id, ctx)
    def clear_context(self, user_id: str):
        self.user_contexts[user_id] = {'history': []}

# --- UniversalQueryProcessor ---
from modules.classifiers.ner_intent_classifier import NERIntentClassifier

class UniversalQueryProcessor:
    def __init__(self):
        self.ner_intent = NERIntentClassifier()
        self.search = SearchModule()
        self.compare = CompareModule()
        self.loan = LoanModule()
        self.details = DetailsModule()
        self.dealer = DealerModule()
        self.recommend = RecommendationModule()
        self.vin = VINModule()
        self.stats = StatisticsModule()
        self.clarification = ClarificationModule()
        self.dialog_manager = DialogManager()
    def extract_entities_from_text(self, query: str) -> dict:
        import re
        entities = {}
        # Цвета
        COLORS = ['красный', 'синий', 'белый', 'бежевый', 'черный', 'серый', 'зеленый', 'желтый', 'оранжевый', 'фиолетовый', 'коричневый']
        # Ищем все цвета в строке, даже если их несколько (с учетом падежей и форм)
        color_patterns = [c[:-2] for c in COLORS]  # корень цвета
        found_colors = set()
        for root, base in zip(color_patterns, COLORS):
            # ищем все слова, начинающиеся с корня цвета
            matches = re.findall(rf'{root}[а-я]*', query.lower())
            if matches:
                found_colors.add(base)
        if found_colors:
            entities['color'] = list(found_colors) if len(found_colors) > 1 else list(found_colors)[0]
        # Марки
        MARKS = ['мерседес', 'bmw', 'лада', 'тойота', 'audi', 'volkswagen', 'nissan', 'mazda', 'honda', 'hyundai', 'kia', 'renault', 'ford', 'skoda', 'chery', 'geely', 'haval', 'lexus', 'porsche', 'subaru', 'suzuki', 'mitsubishi', 'peugeot', 'citroen', 'fiat', 'opel', 'chevrolet', 'uaz', 'ваз', 'volvo', 'infiniti', 'acura', 'tesla', 'bentley', 'bugatti', 'rolls-royce', 'mini', 'smart', 'jac', 'exeed', 'dongfeng', 'byd', 'li', 'xpeng', 'zeekr', 'tank', 'jetour', 'gac', 'aiways', 'nio', 'voyah', 'moskvich', 'evolute', 'genesis', 'ravon', 'datsun', 'daewoo', 'great wall', 'ssangyong', 'proton', 'saab', 'seat', 'changan', 'dongfeng', 'faw', 'gac', 'jac', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 'haima', 'hafei', 'geely', 'chery', 'foton', 'dfm', 'dongfeng', 'gac', 'jac', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 'haima', 'hafei', 'geely', 'chery', 'foton', 'dfm']
        for m in MARKS:
            if m in query.lower():
                entities['brand'] = m
                break
        # Тип кузова
        BODY_TYPES = {'кабриолет': 'кабриолет', 'открытой крышей': 'кабриолет', 'универсал': 'универсал', 'седан': 'седан', 'хэтчбек': 'хэтчбек', 'купе': 'купе', 'внедорожник': 'внедорожник', 'джип': 'внедорожник', 'пикап': 'пикап', 'минивэн': 'минивэн', 'микроавтобус': 'микроавтобус', 'фургон': 'фургон', 'лимузин': 'лимузин', 'родстер': 'родстер', 'тарга': 'тарга', 'лифтбек': 'лифтбек', 'фастбек': 'фастбек', 'комби': 'универсал'}
        for k, v in BODY_TYPES.items():
            if k in query.lower():
                entities['body_type'] = v
                break
        # Размер/маленькая машина
        if 'маленьк' in query.lower():
            entities['size'] = 'маленькая'
        # Количество мест
        match = re.search(r'(\d+)\s*мест', query.lower())
        if match:
            entities['seats'] = int(match.group(1))
        # Для "машина для одного человека"
        if 'одного человек' in query.lower():
            entities['seats'] = 1
        # --- Преобразование brand к строке (en) ---
        # --- Гибкая фильтрация по бренду ---
        if 'brand' in entities and isinstance(entities['brand'], dict):
           entities['brand'] = entities['brand'].get('en') or list(entities['brand'].values())[0]
        brand = entities.get('brand')
        if brand:
            brand_query = str(brand).lower().replace('-', '').replace(' ', '')
            all_marks = [
        'audi', 'alfaromeo', 'bmw', 'byd', 'chery', 'chevrolet', 'citroen', 'dongfeng', 'dodge', 'exeed', 'fiat', 'ford', 'gac', 'geely', 'gmc', 'haval', 'honda', 'hyundai', 'jeep', 'jishi', 'kia', 'lada', 'landrover', 'lexus', 'liauto', 'lixiang', 'mazda', 'mercedesbenz', 'mitsubishi', 'nissan', 'omoda', 'opel', 'peugeot', 'porsche', 'ram', 'renault', 'skoda', 'ssangyong', 'subaru', 'suzuki', 'tank', 'tesla', 'toyota', 'volkswagen', 'volvo', 'voyah', 'zeekr'
    ]
            all_marks_norm = [m.lower().replace('-', '').replace(' ', '') for m in all_marks] 
            brand_syns = [m for m in all_marks_norm if brand_query in m]
            if not brand_syns:
                brand_syns = [brand_query]
            brand_clauses = ["LOWER(REPLACE(REPLACE(mark, '-', ''), ' ', '')) LIKE ?" for _ in brand_syns]
        if 'filters_sql' not in locals():
            filters_sql = []
        if 'params_sql' not in locals():
            params_sql = []
            filters_sql.append(f"({' OR '.join(brand_clauses)})")
            params_sql.extend([f"%{b}%" for b in brand_syns])
            if 'model' in entities and isinstance(entities['model'], dict):
                entities['model'] = entities['model'].get('en') or list(entities['model'].values())[0]
        # --- Исправление color_in_db ---
        # Найти и заменить все color_in_db на color (или удалить, если не используется)
        return entities
    def process(self, query: str, entities: dict, user_id: str = 'default', offset: int = 0, limit: int = 10, show_cars: bool = False) -> dict:
        from llama_service import generate_with_llama
        print(f"[DEBUG] process() called with query: {query}, type: {type(query)}")
        context = self.dialog_manager.get_context(user_id)
        self.dialog_manager.append_message(user_id, 'user', query)
        # Новый способ: извлекаем сущности и интент через NERIntentClassifier
        # Убеждаемся, что query - это строка
        if not isinstance(query, str):
            query = str(query)
        print(f"[DEBUG] Before extract_entities: query = {query}, type = {type(query)}")
        auto_entities = self.ner_intent.extract_entities(query)
        # Локальная обработка качественных характеристик (быстрый/медленный/дорогой/дешевый/спорткар)
        ql = query.lower()
        fast_words = ['быстрый', 'быстрая', 'быстрые', 'скоростной', 'скоростная', 'динамичный', 'динамичная', 'шустрый', 'шустрая']
        slow_words = ['медленный', 'медленная', 'медленные', 'не быстрый', 'неспешный', 'спокойный']
        expensive_words = ['дорогой', 'дорогая', 'дорогие', 'премиум', 'люксовый', 'люксовая', 'люксовые']
        cheap_words = ['дешевый', 'дешевая', 'дешевые', 'бюджетный', 'бюджетная', 'недорогой', 'недорогая', 'недорогие']
        sport_words = ['спорткар', 'спорткары', 'спортивный автомобиль', 'спортивная машина', 'спортивная', 'спортивный']
        # Спорткар: кузов и мощность
        if any(w in ql for w in sport_words):
            auto_entities.setdefault('body_type', ['купе', 'кабриолет'])
            auto_entities.setdefault('power_from', 200)
        # Быстрый: мощнее
        if any(w in ql for w in fast_words):
            auto_entities.setdefault('power_from', 180)
        # Медленный: менее мощный
        if any(w in ql for w in slow_words):
            auto_entities.setdefault('power_to', 130)
        # Дорогой: высокий бюджет
        if any(w in ql for w in expensive_words):
            auto_entities.setdefault('price_from', 3000000)
        # Дешевый: низкий бюджет
        if any(w in ql for w in cheap_words):
            auto_entities.setdefault('price_to', 1500000)
        entities = {**auto_entities, **entities}
        intent = self.ner_intent.classify_intent(query)
        
        # --- ПРОВЕРКА НА ЗАПРОСЫ СРАВНЕНИЯ ---
        query_lower = query.lower()
        compare_keywords = ['сравни', 'сравнить', 'сравнение', 'сравнивать', 'сопоставь', 'сопоставить']
        is_compare_query = any(keyword in query_lower for keyword in compare_keywords)
        
        if is_compare_query:
            print(f"[DEBUG] Обнаружен запрос сравнения: {query}")
            # Обрабатываем через CompareModule
            compare_result = self.compare.process(query, entities, context, offset=offset, limit=limit, show_cars=show_cars)
            if compare_result.get('type') in ['comparison_table', 'comparison_results']:
                print(f"[DEBUG] Сравнение выполнено успешно")
                return compare_result
            elif compare_result.get('type') == 'error':
                print(f"[DEBUG] Ошибка сравнения: {compare_result.get('message')}")
                return compare_result
        
        # --- СНАЧАЛА ЛОКАЛЬНЫЙ ПОИСК ---
        local_result = self.search.process(query, entities, context, offset=offset, limit=limit, show_cars=show_cars)
        print(f"[DEBUG] Local result type: {type(local_result)}")
        print(f"[DEBUG] Local result keys: {local_result.keys() if isinstance(local_result, dict) else 'Not a dict'}")
        print(f"[DEBUG] Local result cars: {local_result.get('cars', 'No cars key')}")
        print(f"[DEBUG] Local result cars length: {len(local_result.get('cars', [])) if local_result.get('cars') else 0}")
        
        if local_result.get('cars') and len(local_result['cars']) > 0:
            local_result['message'] = 'Результат найден локально (без LLAMA).'
            return local_result
        
        # Если машины не найдены локально, возвращаем результат без LLAMA
        if local_result.get('type') in ['no_results', 'partial_results']:
            return local_result
        
        # --- ПРОВЕРКА НА СТАТИСТИЧЕСКИЕ ЗАПРОСЫ ---
        query_lower = query.lower()
        statistics_keywords = ['статистика', 'статистику', 'сколько', 'количество', 'общее количество', 'всего', 'анализ', 'аналитика']
        
        if any(keyword in query_lower for keyword in statistics_keywords):
            # Обрабатываем статистический запрос
            try:
                from database import search_all_cars
                all_cars = search_all_cars()
                total_cars = len(all_cars)
                
                # Подсчитываем статистику
                cities = set()
                brands = set()
                models = set()
                fuel_types = set()
                
                for car in all_cars:
                    if car.get('city'):
                        cities.add(car['city'])
                    if car.get('mark'):
                        brands.add(car['mark'])
                    if car.get('model'):
                        models.add(car['model'])
                    if car.get('fuel_type'):
                        fuel_types.add(car['fuel_type'])
                
                message = f"📊 **Статистика базы данных автомобилей:**\n\n"
                message += f"🚗 **Всего автомобилей:** {total_cars:,}\n"
                message += f"📍 **Городов:** {len(cities)}\n"
                message += f"🏭 **Марок:** {len(brands)}\n"
                message += f"🏎️ **Моделей:** {len(models)}\n"
                message += f"⛽ **Типов топлива:** {len(fuel_types)}\n\n"
                
                if cities:
                    message += f"📍 **Города:** {', '.join(sorted(list(cities))[:10])}{'...' if len(cities) > 10 else ''}\n\n"
                if brands:
                    message += f"🚗 **Марки:** {', '.join(sorted(list(brands))[:10])}{'...' if len(brands) > 10 else ''}\n\n"
                
                return {
                    'type': 'statistics_response',
                    'message': message,
                    'statistics': {
                        'total_cars': total_cars,
                        'cities_count': len(cities),
                        'brands_count': len(brands),
                        'models_count': len(models),
                        'fuel_types_count': len(fuel_types)
                    }
                }
            except Exception as e:
                print(f"[ERROR] Ошибка при обработке статистического запроса: {e}")
                # Продолжаем с обычной обработкой
        
        # --- ЕСЛИ ЛОКАЛЬНО НИЧЕГО НЕ НАЙДЕНО — LLAMA/DeepSeek ---
        filter_prompt = (
                "Пользователь задал вопрос: '" + query + "'. "
                "В базе данных автомобиля есть следующие поля: "
                "mark: марка автомобиля (например, BMW, Toyota); "
                "model: модель автомобиля (например, X5, Camry); "
                "manufacture_year: год выпуска; "
                "price: цена в рублях; "
                "city: город продажи; "
                "color: цвет кузова; "
                "body_type: тип кузова (седан, кроссовер и т.д.); "
                "gear_box_type: тип коробки передач (автомат, механика и т.д.); "
                "driving_gear_type: тип привода (передний, задний, полный); "
                "engine_vol: объём двигателя; "
                "power: мощность двигателя; "
                "fuel_type: тип топлива; "
                "dealer_center: дилерский центр; "
                "option_description: опции автомобиля (например, люк, панорамная крыша, кабриолет). "
                "Используй только эти поля. Если речь о люке, панорамной крыше или кабриолете — используй поле option_description со значением ['люк', 'панорамная крыша', 'открывающаяся крыша']. Не используй поля, которых нет в списке. "
                "Сформируй фильтры для поиска в базе данных автомобилей. Верни только JSON, например: "
                '{"body_type": "кроссовер", "option_description": ["люк", "панорамная крыша"]}. '
                "Если фильтры не извлечены — верни пустой JSON {}."
            )
        # Убираем LLAMA для автомобильных запросов
        # print(f"[LLAMA FILTERS] Prompt: {filter_prompt}")
        # try:
        #     llama_filters = generate_with_llama(filter_prompt)
        #     print(f"[LLAMA FILTERS] Response: {llama_filters}")
        #     import json as _json
        #     filters = _json.loads(llama_filters.strip().split('```')[-1] if '```' in llama_filters else llama_filters)
        # except Exception:
        #     filters = {}
        filters = {}
        # --- Пост-обработка нестандартных фильтров ---
        if isinstance(filters, dict):
            for key in list(filters.keys()):
                if key.lower() in ["open_roof", "roof_type", "roof_open"] or (
                    isinstance(filters[key], str) and "открыт" in filters[key].lower()
                ):
                    filters["option_description"] = ['люк', 'панорамная крыша', 'открывающаяся крыша']
                    del filters[key]
        if filters and isinstance(filters, dict):
            from database import search_all_cars
            mapping = {
                'brand': 'brand', 'mark': 'brand', 'model': 'model', 'body_type': 'body_type',
                'year_from': 'year_from', 'year_to': 'year_to', 'price_from': 'price_from', 'price_to': 'price_to',
                'fuel_type': 'fuel_type', 'transmission': 'transmission', 'gear_box_type': 'transmission',
                'drive_type': 'drive_type', 'city': 'city', 'option': 'option_description', 'options': 'option_description'
            }
            search_kwargs = {}
            for k, v in filters.items():
                mapped = mapping.get(k)
                if mapped:
                    search_kwargs[mapped] = v
            # Ограничиваем выборку для LLAMA
            cars = search_all_cars(**search_kwargs, limit=50)
            # Передаем LLAMA только 5 машин
            cars_str = '\n'.join([
                f"{c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')} {c.get('body_type','')} {c.get('price','')} {c.get('city','')}"
                for c in cars[:5]
            ])
            # Убираем LLAMA для автомобильных запросов
            # prompt = (
            #     "Пользователь задал вопрос: '" + query + "'. Вот список машин из базы данных по найденным фильтрам:\n"
            #     f"{cars_str}\n"
            #     "Ответь только на русском языке и только по этим данным. "
            #     "Если ни одна не подходит — скажи, что ничего не найдено. "
            #     "Если подходят только некоторые — выведи их марку, модель, год, тип кузова, цену и город."
            # )
            # llama_answer = generate_with_llama(prompt)
            # return {'type': 'llama_response', 'message': llama_answer, 'llama': True}
            return {'type': 'no_results', 'message': 'К сожалению, не найдено автомобилей по вашему запросу.'}
        # Если ничего не найдено — fallback на обычный Llama-ответ по базе
        from database import search_all_cars
        cars = search_all_cars()
        if not cars:
            return {'type': 'no_results', 'message': 'В базе нет ни одного автомобиля.'}
        cars_str = '\n'.join([
            f"{c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')} {c.get('body_type','')} {c.get('price','')} {c.get('city','')}"
            for c in cars[:100]
        ])
        # Убираем LLAMA для автомобильных запросов
        # prompt = (
        #     "Пользователь задал вопрос: '" + query + "'. Вот список машин из базы данных:\n"
        #     f"{cars_str}\n"
        #     "Ответь только на русском языке и только по этим данным. "
        #     "Если ни одна не подходит — скажи, что ничего не найдено. "
        #     "Если подходят только некоторые — выведи их марку, модель, год, тип кузова, цену и город."
        # )
        # llama_answer = generate_with_llama(prompt)
        # return {'type': 'llama_response', 'message': llama_answer, 'llama': True}
        return {'type': 'no_results', 'message': 'К сожалению, не найдено автомобилей по вашему запросу.'}
        # --- Спецлогика для "открытая крыша", "кабриолет", "люк" ---
        ql = query.lower()
        if any(w in ql for w in ['открытая крыша', 'кабриолет', 'открытым верхом', 'открытым кузовом', 'открывающаяся крыша', 'люк', 'панорамная крыша']):
            # 1. Сначала ищем кабриолеты
            cabrio_entities = dict(entities)
            cabrio_entities['body_type'] = 'кабриолет'
            print(f"[UniversalQueryProcessor] cabrio_entities: {cabrio_entities}")
            cabrio_result = self.search.process(query, cabrio_entities, context, offset=offset, limit=limit, show_cars=show_cars)
            if cabrio_result.get('cars') and len(cabrio_result['cars']) > 0:
                return cabrio_result
            # 2. Если нет — ищем по опциям
            option_entities = dict(entities)
            option_entities.pop('body_type', None)
            option_entities['options'] = ['люк', 'панорамная крыша', 'открывающаяся крыша']
            print(f"[UniversalQueryProcessor] option_entities: {option_entities}")
            option_result = self.search.process(query, option_entities, context, offset=0, limit=1000, show_cars=True)
            cars = option_result.get('cars', [])
            if len(cars) > 100:
                # Убираем LLAMA для автомобильных запросов
                # from llama_service import generate_with_llama
                # # Формируем краткое описание фильтров и машин
                # filters_str = f"Фильтры: {option_entities}"
                # cars_str = '\n'.join([f"{c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')} {c.get('body_type','')} {c.get('price','')} {c.get('city','')}" for c in cars[:100]])
                # prompt = (
                #     f"Пользователь ищет машины с открытой крышей (люк, панорамная крыша и т.д.). "
                #     f"Вот фильтры: {filters_str}. Вот первые 100 найденных машин:\n{cars_str}\n"
                #     "Проверь, соответствуют ли эти машины запросу пользователя. "
                #     "Если все соответствуют — ответь 'ok'. "
                #     "Если не соответствуют — ответь 'none'. "
                #     "Если только часть — выведи список марок и моделей, которые подходят. "
                #     "Отвечай только на русском, без лишних пояснений."
                # )
                # llama_answer = generate_with_llama(prompt)
                # if llama_answer.strip().lower() == 'ok':
                #     option_result['message'] = 'Показаны все найденные автомобили с люком или панорамной крышей.'
                #     return option_result
                # elif llama_answer.strip().lower() == 'none':
                #     return {'type': 'no_results', 'message': 'Не найдено ни одного автомобиля с открытой крышей, соответствующего вашему запросу.'}
                # else:
                #     # Парсим список одобренных машин (марка+модель)
                #     approved = set()
                #     for line in llama_answer.splitlines():
                #         parts = line.strip().split()
                #         if len(parts) >= 2:
                #         approved.add((parts[0].lower(), parts[1].lower()))
                #     filtered_cars = [c for c in cars if (str(c.get('mark','')).lower(), str(c.get('model','')).lower()) in approved]
                #     if filtered_cars:
                #         option_result['cars'] = filtered_cars
                #         option_result['message'] = 'Показаны только автомобили, которые одобрила Llama как соответствующие запросу.'
                #         option_result['total_count'] = len(filtered_cars)
                #         return option_result
                #     else:
                #         return {'type': 'no_results', 'message': 'Не найдено ни одного автомобиля с открытой крышей, соответствующего вашему запросу.'}
                    option_result['message'] = 'Показаны все найденные автомобили с люком или панорамной крышей.'
                    return option_result
            if cars and len(cars) > 0:
                option_result['message'] = 'Нет кабриолетов, но есть автомобили с люком или панорамной крышей.'
                return option_result
            # 3. Если и таких нет — явное сообщение
            # Вместо простого no_results — универсальный Llama fallback по базе
            from database import search_all_cars
            all_cars = search_all_cars()
            if not all_cars:
                return {'type': 'no_results', 'message': 'В базе нет ни одного автомобиля.'}
            cars_str = '\n'.join([
                f"{c.get('mark','')} {c.get('model','')} {c.get('manufacture_year','')} {c.get('body_type','')} {c.get('price','')} {c.get('city','')}"
                for c in all_cars[:100]
            ])
            # Убираем LLAMA для автомобильных запросов
            # prompt = (
            #     "Пользователь задал вопрос: '" + query + "'. Вот список машин из базы данных:\n"
            #     f"{cars_str}\n"
            #     "Ответь только на русском языке и только по этим данным. "
            #     "Если ни одна не подходит — скажи, что ничего не найдено. "
            #     "Если подходят только некоторые — выведи их марку, модель, год, тип кузова, цену и город."
            # )
            # from llama_service import generate_with_llama
            # llama_answer = generate_with_llama(prompt)
            # return {'type': 'llama_response', 'message': llama_answer, 'llama': True}
            return {'type': 'no_results', 'message': 'К сожалению, не найдено автомобилей с открытой крышей по вашему запросу.'}
        # --- Обычная маршрутизация ---
        def clarify_with_llm(module_result, query, context):
            if module_result.get('need_clarification'):
                # Убираем LLAMA для автомобильных запросов
                # try:
                #     from llama_service import generate_with_llama
                #     history = context.get('history', [])
                #     clarification_text = module_result.get('clarification') or ''
                #     clarification_prompt = (
                #         "Ты — виртуальный автоассистент. Пользователь задал вопрос: '" + query + "'. "
                #         "Система не смогла однозначно ответить. " + clarification_text + "\n"
                #         "Твоя задача — задать КОРОТКИЙ, конкретный и дружелюбный уточняющий вопрос, чтобы получить недостающую информацию. "
                #         "Не повторяй исходный вопрос пользователя. Пример: 'Уточните, пожалуйста, марку автомобиля?' или 'Какой город вас интересует?'. "
                #         "Если нужно, предложи варианты. Не используй длинные вступления. "
                #         "Всегда отвечай только на русском языке."
                #     )
                #     llm_question = generate_with_llama(clarification_prompt)
                #     module_result['llm_clarification'] = llm_question
                #     module_result['message'] = llm_question
                # except Exception as e:
                #     module_result['llm_clarification'] = f'LLM недоступен: {e}'
                #     module_result['message'] = module_result.get('clarification', f'LLM недоступен: {e}')
                module_result['message'] = module_result.get('clarification', 'Пожалуйста, уточните ваш запрос.')
            return module_result
        def call_llm_dialog(prompt, context):
            # Убираем LLAMA для автомобильных запросов
            # try:
            #     from llama_service import generate_with_llama
            #     history = context.get('history', [])
            #     system_prompt = (
            #         "Ты — виртуальный автоассистент. Отвечай максимально полезно, по теме автомобилей, кратко и по делу. "
            #         "Если вопрос не по теме авто — вежливо сообщи об этом. "
            #         "Всегда отвечай только на русском языке."
            #     )
            #     full_prompt = f"{system_prompt}\n\n{prompt}"
            #     answer = generate_with_llama(full_prompt)
            #     return {'type': 'llm_answer', 'message': answer}
            return {'type': 'no_results', 'message': 'К сожалению, не найдено информации по вашему запросу.'}
        # --- Маршрутизация ---
        if intent == 'search':
            result = self.search.process(query, entities, context, offset=offset, limit=limit, show_cars=show_cars)
            # Не дублируем уточняющие сообщения, если show_cars_required
            if result.get('type') == 'clarification' and result.get('show_cars_required'):
                return result
            result = clarify_with_llm(result, query, context)
        elif intent == 'compare':
            result = self.compare.process(query, entities, context, offset=offset, limit=limit, show_cars=show_cars)
            result = clarify_with_llm(result, query, context)
        elif intent == 'loan':
            result = self.loan.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'details':
            result = self.details.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'dealer':
            result = self.dealer.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'recommendation':
            result = self.recommend.process(query, entities, context, offset=offset, limit=limit, show_cars=show_cars)
            result = clarify_with_llm(result, query, context)
        elif intent == 'vin':
            result = self.vin.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'statistics':
            result = self.stats.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'clarification':
            result = self.clarification.process(query, entities, context)
            result = clarify_with_llm(result, query, context)
        elif intent == 'general':
            result = call_llm_dialog(query, context)
        else:
            result = call_llm_dialog(query, context)
        # --- LLM fallback если нет результата ---
        # Убираем LLAMA для автомобильных запросов
        # if (result.get('type') == 'clarification' or result.get('need_clarification')) and 'llm_answer' not in result:
        #     from llama_service import generate_with_llama
        #     llm_answer = generate_with_llama(f'Пользователь задал запрос: "{query}". Система не смогла найти результат. Всегда отвечай только на русском языке. Предложи альтернативу или объясни ситуацию.')
        #     result['llm_answer'] = llm_answer
        # После обычной маршрутизации: если entities пустой (нет ни одного фильтра), не возвращать clarification/show_cars_required вообще
        if result.get('type') == 'clarification' and result.get('show_cars_required'):
            if not any([entities.get('brand'), entities.get('model'), entities.get('year_from'), entities.get('year_to'), entities.get('price_from'), entities.get('price_to'), entities.get('fuel_type'), entities.get('transmission'), entities.get('body_type'), entities.get('drive_type'), entities.get('city'), entities.get('options')]):
                return {'type': 'no_results', 'message': 'Не найдено ни одного автомобиля по вашему запросу.'}
        self.dialog_manager.append_message(user_id, 'system', result.get('message', ''))
        self.dialog_manager.update_context(user_id, context)
        result['context'] = context
        # --- Если entities пустой (нет ни одного фильтра), отправлять запрос в Llama ---
        # Убираем LLAMA для автомобильных запросов
        # if not entities:
        #     from llama_service import generate_with_llama
        #     llama_answer = generate_with_llama(query)
        #     return {'type': 'llama_response', 'message': llama_answer, 'llama': True}
        # --- Fallback-логика ---
        # Если не извлечено ни одной фильтрующей сущности (brand, model, color, year, price и т.д.)
        filter_keys = ['brand', 'model', 'color', 'body_type', 'year_from', 'year_to', 'price_from', 'price_to', 'fuel_type', 'transmission', 'gear_box_type', 'drive_type', 'city', 'options', 'mileage_from', 'mileage_to']
        has_filters = any(entities.get(k) for k in filter_keys)
        if intent == 'car_search' and not has_filters:
            # Вместо выборки всех машин и передачи их в Llama — уточняющий вопрос
            clarification = "Пожалуйста, уточните марку, модель, цвет, год или другие параметры автомобиля, чтобы я мог подобрать подходящие варианты."
            # Убираем LLAMA для автомобильных запросов
            # try:
            #     from llama_service import generate_with_llama
            #     clarification = generate_with_llama(
            #         "Пользователь задал вопрос: '" + query + "'. Система не смогла извлечь фильтры. Сформулируй короткий, дружелюбный уточняющий вопрос на русском, чтобы узнать марку, модель, цвет, год или другие параметры автомобиля. Не повторяй исходный вопрос пользователя."
            #     )
            # except Exception:
            #     pass
            return {'type': 'clarification', 'need_clarification': True, 'clarification': clarification, 'entities': entities}
        return result 

def classify_intent(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ['машин', 'авто', 'купить', 'продать', 'найди', 'сравни', 'цена', 'год', 'пробег']):
        return 'car_search'
    if any(w in q for w in ['опция', 'комплектация', 'что входит', 'доступно']):
        return 'car_option'
    if any(w in q for w in ['как дела', 'привет', 'расскажи', 'шутка', 'анекдот']):
        return 'chitchat'
    if any(w in q for w in ['справка', 'что ты умеешь', 'инструкция', 'help', 'помощь']):
        return 'help'
    return 'general'