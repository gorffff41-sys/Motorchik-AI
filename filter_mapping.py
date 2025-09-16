# coding: utf-8

FUEL_TYPE_MAP = {
    'бензин': 'бензин',
    'дизель': 'дизель',
    'гибрид': 'гибрид',
    'электро': '',  # если появится — добавить
}

GEAR_BOX_TYPE_MAP = {
    'автомат': 'автомат',
    'механика': 'механика',
    'ручная': 'механика',
}

BODY_TYPE_MAP = {
    'внедорожник': 'Внедорожник',
    'кроссовер': 'Кроссовер',
    'купе-кроссовер': 'Купе-кроссовер',
    'лифтбэк': 'Лифтбэк',
    'минивэн': 'Минивэн',
    'пикап': 'Пикап',
    'седан': 'Седан',
    'универсал': 'Универсал',
    'хетчбек': 'Хетчбэк',
    'хетчбек': 'Хетчбэк',
}

DRIVE_TYPE_MAP = {
    'передний': 'передний',
    'полный': 'полный',
    'задний': '',  # если появится — добавить
}

def get_first_deep(val):
    if isinstance(val, (list, tuple)):
        return get_first_deep(val[0]) if val else None
    return val

def map_filter_value(field, value):
    """Преобразует русское значение фильтра к значению в БД"""
    value = get_first_deep(value)
    if value is None:
        return value
    if field == 'fuel_type':
        return FUEL_TYPE_MAP.get(value.lower(), value)
    if field == 'gear_box_type':
        return GEAR_BOX_TYPE_MAP.get(value.lower(), value)
    if field == 'body_type':
        return BODY_TYPE_MAP.get(value.lower(), value)
    if field == 'driving_gear_type':
        return DRIVE_TYPE_MAP.get(value.lower(), value)
    return value 