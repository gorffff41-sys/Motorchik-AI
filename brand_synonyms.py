# Единый словарь синонимов для всех модулей
import sqlite3
import os
from difflib import get_close_matches
from functools import lru_cache
import re

def generate_case_variations(word):
    """Генерирует падежные вариации для русского слова"""
    if not word or len(word) < 2:
        return [word]
    
    # Базовые падежные окончания для существительных женского рода (оканчивающихся на -а)
    if word.endswith('а'):
        base = word[:-1]
        variations = [
            word,  # именительный падеж (лада)
            base + 'у',  # винительный падеж (ладу)
            base + 'ы',  # родительный падеж (лады)
            base + 'е',  # дательный падеж (ладе)
            base + 'ой',  # творительный падеж (ладой)
            base + 'ою',  # творительный падеж (ладою)
            base + 'ах',  # предложный падеж (ладах)
        ]
    # Для существительных мужского рода (оканчивающихся на согласную)
    elif not word.endswith(('ь', 'й', 'я', 'е', 'о', 'и', 'ы')):
        variations = [
            word,  # именительный падеж (бмв)
            word + 'а',  # родительный падеж (бмва)
            word + 'у',  # дательный падеж (бмву)
            word + 'ом',  # творительный падеж (бмвом)
            word + 'е',  # предложный падеж (бмве)
        ]
    # Для существительных на -ь
    elif word.endswith('ь'):
        base = word[:-1]
        variations = [
            word,  # именительный падеж
            base + 'и',  # родительный падеж
            base + 'и',  # дательный падеж
            base + 'ью',  # творительный падеж
            base + 'и',  # предложный падеж
        ]
    # Для существительных на -й
    elif word.endswith('й'):
        base = word[:-1]
        variations = [
            word,  # именительный падеж
            base + 'я',  # родительный падеж
            base + 'ю',  # дательный падеж
            base + 'ем',  # творительный падеж
            base + 'е',  # предложный падеж
        ]
    else:
        variations = [word]
    
    return list(set(variations))  # Убираем дубликаты

def expand_brand_synonyms(brand_dict):
    """Расширяет словарь брендов падежными вариациями"""
    expanded_dict = {}
    
    for canonical, synonyms in brand_dict.items():
        expanded_synonyms = []
        
        for synonym in synonyms:
            # Добавляем оригинальный синоним
            expanded_synonyms.append(synonym)
            
            # Генерируем падежные вариации только для русских слов
            if any(ord(c) > 127 for c in synonym):  # Проверяем наличие русских букв
                case_variations = generate_case_variations(synonym)
                expanded_synonyms.extend(case_variations)
        
        # Убираем дубликаты и пустые значения
        expanded_synonyms = list(set([s for s in expanded_synonyms if s]))
        expanded_dict[canonical] = expanded_synonyms
    
    return expanded_dict

# --- Китайские бренды ---
CHINESE_BRAND_SYNONYMS = {
    'chery': ['чери', 'чері', 'chery', 'черри'],
    'exeed': ['эксид', 'эксиид', 'exeed', 'ексид'],
    'omoda': ['омода', 'omoda'],
    'jaecoo': ['джейку', 'джеку', 'jaecoo'],
    'haval': ['хавейл', 'хавал', 'haval'],
    'geely': ['джили', 'geely', 'гели'],
    'changan': ['чанган', 'changan'],
    'faw': ['фав', 'faw'],
    'dongfeng': ['донгфенг', 'dongfeng'],
    'jac': ['джак', 'jac'],
    'gac': ['гак', 'gac'],
    'byd': ['бивиди', 'byd', 'бивайди'],
    'tank': ['танк', 'tank'],
    'jetour': ['жетур', 'jetour'],
    'kaiyi': ['каи', 'kaiyi'],
    'baic': ['баик', 'baic'],
    'swm': ['свм', 'swm'],
    'hongqi': ['хонгчи', 'hongqi', 'хунцы', 'хонгци'],
    'li auto': ['ли авто', 'li auto', 'ликсианг', 'lixiang'],
    'lynk & co': ['линк энд ко', 'lynk & co'],
    'mg': ['эмджи', 'mg'],
    'neta': ['нета', 'neta'],
    'nio': ['нио', 'nio'],
    'voyah': ['воях', 'voyah'],
    'xev': ['ксев', 'xev'],
    'xpeng': ['кспенг', 'xpeng'],
    'zeekr': ['зикр', 'zeekr'],
    'aion': ['айон', 'aion'],
    'ora': ['орой', 'ora'],
    'wey': ['вэйл', 'wey'],
    'aito': ['айто', 'aito'],
    'belgee': ['белджи', 'belgee'],
    'jishi': ['джиши', 'jishi'],
    'knewstar': ['ньюстар', 'knewstar'],
    'seres': ['серес', 'seres'],
    'solaris': ['соларис', 'solaris'],
    'gmc': ['джимси', 'gmc'],
    'ram': ['рам', 'ram'],
    'tesla': ['тесла', 'tesla'],
    'lixiang': ['лисян', 'lixiang'],
    'lixiang': ['лисян', 'lixiang'],
    'moskvich': ['москвич', 'moskvich'],
}

# --- Европейские бренды (пример, можно расширять) ---
EUROPEAN_BRAND_SYNONYMS = {
    'bmw': ['бмв', 'bmw', 'беэмвэ'],
    'mercedes-benz': ['мерседес', 'mercedes-benz', 'мерс'],
    'audi': ['ауди', 'audi', 'ауды'],
    'volkswagen': ['фольксваген', 'volkswagen', 'вв', 'vw'],
    'skoda': ['шкода', 'skoda'],
    'opel': ['опель', 'opel'],
    'porsche': ['порше', 'porsche'],
    'mini': ['мини', 'mini'],
    'maybach': ['майбах', 'maybach'],
    'smart': ['смарт', 'smart'],
    'alpina': ['альпина', 'alpina'],
    'seat': ['сеат', 'seat', 'сит'],
    'renault': ['рено', 'renault'],
    'peugeot': ['пежо', 'peugeot'],
    'citroen': ['ситроен', 'citroen'],
    'dacia': ['дачия', 'dacia'],
    'alpine': ['альпин', 'alpine'],
    'ds': ['дс', 'ds'],
    'fiat': ['фиат', 'fiat'],
    'alfa romeo': ['альфа ромео', 'alfa romeo'],
    'lancia': ['ланча', 'lancia'],
    'maserati': ['мазерати', 'maserati'],
    'ferrari': ['феррари', 'ferrari'],
    'lamborghini': ['ламборгини', 'lamborghini'],
    'pagani': ['пагани', 'pagani'],
}
    
    # --- Корейские бренды ---
KOREAN_BRAND_SYNONYMS = {
    'kia': ['киа', 'kia', 'кия'],
    'hyundai': ['хендай', 'hyundai', 'хундай', 'хендэ'],
    'ssangyong': ['ссангйонг', 'ssangyong'],
    'genesis': ['генесис', 'genesis'],
}
    
    # --- Японские бренды ---
JAPANESE_BRAND_SYNONYMS = {
    'toyota': ['тойота', 'toyota', 'тоёта', 'тойотта'],
    'nissan': ['ниссан', 'nissan', 'нисан'],
    'honda': ['хонда', 'honda'],
    'mazda': ['мазда', 'mazda'],
    'lexus': ['лексус', 'lexus'],
    'mitsubishi': ['мицубиси', 'mitsubishi', 'мицубиши'],
    'subaru': ['субару', 'subaru'],
    'suzuki': ['сузуки', 'suzuki'],
    'infiniti': ['инфинити', 'infiniti'],
    'daihatsu': ['дайхатсу', 'daihatsu'],
    'acura': ['акура', 'acura'],
}
    
    # --- Американские бренды ---
AMERICAN_BRAND_SYNONYMS = {
    'ford': ['форд', 'ford'],
    'chevrolet': ['шевроле', 'chevrolet'],
    'jeep': ['джип', 'jeep'],
    'dodge': ['додж', 'dodge'],
    'chrysler': ['крайслер', 'chrysler'],
    'cadillac': ['кадиллак', 'cadillac'],
    'lincoln': ['линкольн', 'lincoln'],
    'buick': ['бьюик', 'buick'],
    'pontiac': ['понтиак', 'pontiac'],
    'saturn': ['сатурн', 'saturn'],
    'hummer': ['хаммер', 'hummer'],
    'gmc': ['джиэмси', 'gmc'],
    'ram': ['рам', 'ram'],
    'tesla': ['тесла', 'tesla'],
    'rivian': ['ривиан', 'rivian'],
    'lucid': ['люсид', 'lucid'],
}
    
    # --- Шведские бренды ---
SWEDISH_BRAND_SYNONYMS = {
    'volvo': ['вольво', 'volvo'],
    'saab': ['сааб', 'saab'],
    'polestar': ['полестар', 'polestar'],
}
    
    # --- Британские бренды ---
BRITISH_BRAND_SYNONYMS = {
    'jaguar': ['ягуар', 'jaguar'],
    'land rover': ['ленд ровер', 'land rover'],
    'rolls-royce': ['роллс ройс', 'rolls-royce'],
    'bentley': ['бентли', 'bentley'],
    'aston martin': ['астон мартин', 'aston martin'],
    'mclaren': ['макларен', 'mclaren', 'маклерен'],
    'lotus': ['лотос', 'lotus'],
    'canoo': ['кану', 'canoo'],
}
    
# --- Российские бренды ---
RUSSIAN_BRAND_SYNONYMS = {
    'lada': ['лада', 'lada', 'ваз', 'жигули', 'лада (ваз)'],
    'москвич': ['москвич', 'moskvich', 'moscvich'],
    'уаз': ['уаз'],
    'газ': ['газ'],
    'камаз': ['камаз'],
}
    
    # --- Другие популярные бренды ---
OTHER_BRAND_SYNONYMS = {
    'faraday future': ['фарадей фьючер', 'faraday future'],
    'fisker': ['фискер', 'fisker'],
    'nikola': ['никола', 'nikola'],
    'lordstown': ['лордстаун', 'lordstown'],
    'koenigsegg': ['коенигсегг', 'koenigsegg'],
    'bugatti': ['бугатти', 'bugatti'],
}

# --- Расширяем словари с падежными вариациями ---
EUROPEAN_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(EUROPEAN_BRAND_SYNONYMS)
CHINESE_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(CHINESE_BRAND_SYNONYMS)
KOREAN_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(KOREAN_BRAND_SYNONYMS)
JAPANESE_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(JAPANESE_BRAND_SYNONYMS)
AMERICAN_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(AMERICAN_BRAND_SYNONYMS)
SWEDISH_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(SWEDISH_BRAND_SYNONYMS)
BRITISH_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(BRITISH_BRAND_SYNONYMS)
RUSSIAN_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(RUSSIAN_BRAND_SYNONYMS)
OTHER_BRAND_SYNONYMS_EXPANDED = expand_brand_synonyms(OTHER_BRAND_SYNONYMS)

# --- Объединённый словарь для использования в коде ---
BRAND_SYNONYMS = {}
for d in (
    EUROPEAN_BRAND_SYNONYMS_EXPANDED,
    CHINESE_BRAND_SYNONYMS_EXPANDED,
    KOREAN_BRAND_SYNONYMS_EXPANDED,
    JAPANESE_BRAND_SYNONYMS_EXPANDED,
    AMERICAN_BRAND_SYNONYMS_EXPANDED,
    SWEDISH_BRAND_SYNONYMS_EXPANDED,
    BRITISH_BRAND_SYNONYMS_EXPANDED,
    RUSSIAN_BRAND_SYNONYMS_EXPANDED,
    OTHER_BRAND_SYNONYMS_EXPANDED
):
    for canon, syns in d.items():
        for s in syns:
            BRAND_SYNONYMS[s.lower()] = canon.title()
        BRAND_SYNONYMS[canon.lower()] = canon.title()

# --- ДОБАВЛЯЕМ СИНОНИМЫ ДЛЯ ЛАДА ---
RUSSIAN_BRAND_SYNONYMS["Lada"] = [
    "лада", "ладу", "лады", "ладе", "ладой", "ладою", "ладах", "лад", "лады", "ладам", "ладами", "ладах",
    "Lada", "LADA", "ЛАДА", "lad", "ladа", "лада", "ладу", "лады", "ладе", "ладой", "ладою", "ладах"
]

# --- ДОБАВЛЯЕМ СИНОНИМЫ ДЛЯ ГОРОДОВ ---
CITY_SYNONYMS = {
    "Ростов-на-Дону": [
        "ростов-на-дону", "ростов", "ростове", "ростове-на-дону", "ростов на дону", "ростов-на-дону", "rostov", "rostov-on-don", "rostov na donu", "rostove", "rostove-na-donu"
    ],
    "Воронеж": [
        "воронеж", "воронеже", "voronezh", "voroneje", "voronezhe", "воронежа", "воронежу", "воронежем"
    ],
    "Краснодар": [
        "краснодар", "краснодаре", "krasnodar", "krasnodare", "краснодара", "краснодару", "краснодаром"
    ],
}

# Словарь синонимов китайских моделей
CHINESE_MODEL_SYNONYMS = {
    # Chery
    'тигго': 'Tiggo', 'тиго': 'Tiggo', 'тигго': 'Tiggo',
    'тигго 4': 'Tiggo 4', 'тигго 4 про': 'Tiggo 4 Pro', 'тигго 4 про': 'Tiggo 4 Pro',
    'тигго 7': 'Tiggo 7', 'тигго 7 про': 'Tiggo 7 Pro', 'тигго 7 про макс': 'Tiggo 7 Pro Max',
    'тиго 7': 'Tiggo 7', 'тиго 7 про': 'Tiggo 7 Pro', 'тиго 7 про макс': 'Tiggo 7 Pro Max',
    'тиго макс 7 про': 'Tiggo 7 Pro Max', 'тиго макс 7': 'Tiggo 7 Pro Max',
    'тигго макс 7 про': 'Tiggo 7 Pro Max', 'тигго макс 7': 'Tiggo 7 Pro Max',
    'тигго 8': 'Tiggo 8', 'тигго 8 про': 'Tiggo 8 Pro', 'тигго 8 про макс': 'Tiggo 8 Pro Max', 'тигго 8 про е+': 'Tiggo 8 Pro e+',
    'аризо': 'Arrizo', 'arrizo 8': 'Arrizo 8', 'аризо': 'Arrizo',
    'омода': 'Omoda', 'омода с5': 'Omoda C5', 'омода s5': 'Omoda S5',
    
    # Exeed
    'lx': 'LX', 'лх': 'LX',
    'txl': 'TXL', 'тхл': 'TXL',
    'vx': 'VX', 'вх': 'VX',
    'rx': 'RX', 'рх': 'RX',

    # Omoda
    'с5': 'C5', 'c5': 'C5', 'с5': 'C5',
    's5': 'S5', 'с5 седан': 'S5', 'с5': 'S5',
    'crossover': 'C5', 'кроссовер': 'C5',

    # Jaecoo
    'j7': 'J7', 'джей 7': 'J7', 'дж7': 'J7',
    'j8': 'J8', 'джей 8': 'J8', 'дж8': 'J8',

    # Haval
    'jolion': 'Jolion', 'джулион': 'Jolion', 'джолион': 'Jolion',
    'ф7': 'F7', 'f7': 'F7', 'ф7': 'F7',
    'ф7х': 'F7x', 'f7x': 'F7x', 'ф7х': 'F7x',
    'дарго': 'Dargo', 'дарго икс': 'Dargo X', 'дарго': 'Dargo',
    'н9': 'H9', 'h9': 'H9', 'н9': 'H9',
    
    # Geely
    'coolray': 'Coolray', 'кулрей': 'Coolray', 'кулрей': 'Coolray',
    'atlas pro': 'Atlas Pro', 'атлас про': 'Atlas Pro', 'атлас про': 'Atlas Pro',
    'tugella': 'Tugella', 'тугела': 'Tugella', 'тугела': 'Tugella',
    'monjaro': 'Monjaro', 'монджаро': 'Monjaro', 'монджаро': 'Monjaro',

    # Changan
    'cs35plus': 'CS35PLUS', 'кс35плюс': 'CS35PLUS',
    'cs55plus': 'CS55PLUS', 'кс55плюс': 'CS55PLUS',
    'cs75plus': 'CS75FL', 'кс75плюс': 'CS75FL',
    'uni-k': 'UNI-K', 'юни-к': 'UNI-K', 'юни-к': 'UNI-K',
    'uni-v': 'UNI-V', 'юни-в': 'UNI-V', 'юни-в': 'UNI-V',
    
    # BYD
    'атто': 'Atto', 'атто 3': 'Atto 3', 'атто': 'Atto',
    'хан': 'Han', 'хан': 'Han',
    'тан': 'Song', 'сун': 'Song',
    
    # Другие
    'Москвич 3': '3', 'москвич 3': '3',
    'Москвич 6': '6', 'москвич 6': '6',

    # Chery Tiggo 7 Pro Max и все варианты
    'тиго макс 7 про': 'Tiggo 7 Pro Max',
    'тиго 7 про макс': 'Tiggo 7 Pro Max',
    'тиго 7 макс про': 'Tiggo 7 Pro Max',
    'тиго 7 про max': 'Tiggo 7 Pro Max',
    'тиго 7 pro max': 'Tiggo 7 Pro Max',
    'тиго7 про макс': 'Tiggo 7 Pro Max',
    'тиго7 про max': 'Tiggo 7 Pro Max',
    'тиго7 pro max': 'Tiggo 7 Pro Max',
    'тиго7 макс про': 'Tiggo 7 Pro Max',
    'тиго7 max pro': 'Tiggo 7 Pro Max',
    'тиго7 pro': 'Tiggo 7 Pro',
    'тиго7': 'Tiggo 7',
    'тиго 7 про': 'Tiggo 7 Pro',
    'тиго 7pro': 'Tiggo 7 Pro',
    'тиго 7': 'Tiggo 7',
    'tiggo 7 pro max': 'Tiggo 7 Pro Max',
    'tiggo7 pro max': 'Tiggo 7 Pro Max',
    'tiggo7 pro': 'Tiggo 7 Pro',
    'tiggo7': 'Tiggo 7',
    'tiggo 7 pro': 'Tiggo 7 Pro',
    'tiggo 7': 'Tiggo 7',
    'tiggo7pro': 'Tiggo 7 Pro',
    'tiggo7promax': 'Tiggo 7 Pro Max',
    'tiggo7maxpro': 'Tiggo 7 Pro Max',
    'tiggo7max': 'Tiggo 7 Max',
    'tiggo 7 max': 'Tiggo 7 Max',
    'тиго 7 макс': 'Tiggo 7 Max',
    'тиго7 макс': 'Tiggo 7 Max',
    # Дополнительные варианты для "тиго макс 7 про"
    'тиго макс 7 про макс': 'Tiggo 7 Pro Max',
    'тиго макс 7 про max': 'Tiggo 7 Pro Max',
    'тиго макс 7 pro max': 'Tiggo 7 Pro Max',
    'тиго макс 7 pro': 'Tiggo 7 Pro Max',
    'тиго макс 7 max pro': 'Tiggo 7 Pro Max',
    'тиго макс 7 max': 'Tiggo 7 Pro Max',
    'тигго макс 7 про макс': 'Tiggo 7 Pro Max',
    'тигго макс 7 про max': 'Tiggo 7 Pro Max',
    'тигго макс 7 pro max': 'Tiggo 7 Pro Max',
    'тигго макс 7 pro': 'Tiggo 7 Pro Max',
    'тигго макс 7 max pro': 'Tiggo 7 Pro Max',
    'тигго макс 7 max': 'Tiggo 7 Pro Max',
    # Tiggo/Tigo 3-8
    'тиго 3': 'Tiggo 3', 'тигго 3': 'Tiggo 3', 'tiggo 3': 'Tiggo 3',
    'тиго 4': 'Tiggo 4', 'тигго 4': 'Tiggo 4', 'tiggo 4': 'Tiggo 4',
    'тиго 5': 'Tiggo 5', 'тигго 5': 'Tiggo 5', 'tiggo 5': 'Tiggo 5',
    'тиго 6': 'Tiggo 6', 'тигго 6': 'Tiggo 6', 'tiggo 6': 'Tiggo 6',
    'тиго 7': 'Tiggo 7', 'тигго 7': 'Tiggo 7', 'tiggo 7': 'Tiggo 7',
    'тиго 8': 'Tiggo 8', 'тигго 8': 'Tiggo 8', 'tiggo 8': 'Tiggo 8',
    # Падежные формы для "нива"
    'нива': 'Niva', 'ниву': 'Niva', 'нивы': 'Niva', 'ниве': 'Niva', 'нивой': 'Niva', 'нивою': 'Niva', 'нивах': 'Niva',
    
    # Падежные формы для моделей Lada
    # Ларгус
    'ларгус': 'Largus', 'ларгуса': 'Largus', 'ларгусу': 'Largus', 'ларгусом': 'Largus', 'ларгусе': 'Largus',
    'иксрей': 'XRAY', 'иксрея': 'XRAY', 'иксрею': 'XRAY', 'иксреем': 'XRAY', 'иксрее': 'XRAY',
    'самара': 'Samara', 'самары': 'Samara', 'самаре': 'Samara', 'самару': 'Samara', 'самарой': 'Samara', 'самарою': 'Samara', 'самарах': 'Samara',
    'приора': 'Priora', 'приоры': 'Priora', 'приоре': 'Priora', 'приору': 'Priora', 'приорой': 'Priora', 'приорою': 'Priora', 'приорах': 'Priora',
    'калина': 'Kalina', 'калины': 'Kalina', 'калине': 'Kalina', 'калину': 'Kalina', 'калиной': 'Kalina', 'калиною': 'Kalina', 'калинах': 'Kalina',
}

# Словарь синонимов BMW моделей
BMW_MODEL_SYNONYMS = {
    # X-серия
    'x1': 'X1', 'х1': 'X1', 'икс1': 'X1',
    'x2': 'X2', 'х2': 'X2', 'икс2': 'X2',
    'x3': 'X3', 'х3': 'X3', 'икс3': 'X3', 'x3 xdrive': 'X3 XDRIVE', 'x3 xdrive30l': 'X3 XDRIVE30L',
    'x4': 'X4', 'х4': 'X4', 'икс4': 'X4',
    'x5': 'X5', 'х5': 'X5', 'икс5': 'X5', 'x 5': 'X5', 'x-5': 'X5', 'xdrive': 'X5', 'x5 xdrive': 'X5 XDRIVE',
    'x6': 'X6', 'х6': 'X6', 'икс6': 'X6',
    'x7': 'X7', 'х7': 'X7', 'икс7': 'X7',
    'xm': 'XM', 'хм': 'XM', 'иксм': 'XM',
    
    # Седан серия
    '1 серии': '1 серии', '1 серия': '1 серии', '1 series': '1 серии',
    '2 серии': '2 серии', '2 серия': '2 серии', '2 series': '2 серии',
    '3 серии': '3 серии', '3 серия': '3 серии', '3 series': '3 серии',
    '4 серии': '4 серии', '4 серия': '4 серии', '4 series': '4 серии',
    '5 серии': '5 серии', '5 серия': '5 серии', '5 series': '5 серии', '520d': '520D', '520d xdrive': '520D xDrive',
    '6 серии': '6 серии', '6 серия': '6 серии', '6 series': '6 серии',
    '7 серии': '7 серии', '7 серия': '7 серии', '7 series': '7 серии',
    '8 серии': '8 серии', '8 серия': '8 серии', '8 series': '8 серии',
    
    # Конкретные модели
    '420': '420', '420i': '420', '420d': '420',
    '520d': '520D', '520d xdrive': '520D xDrive',
    'x3 xdrive30l': 'X3 XDRIVE30L',
    
    # M-серия
    'm3': 'M3', 'м3': 'M3',
    'm4': 'M4', 'м4': 'M4',
    'm5': 'M5', 'м5': 'M5',
    'm7': 'M7', 'м7': 'M7',
    'm8': 'M8', 'м8': 'M8',
    'x5m': 'X5M', 'х5м': 'X5M',
    'x6m': 'X6M', 'х6м': 'X6M',
}

# Словарь синонимов Mercedes-Benz моделей
MERCEDES_MODEL_SYNONYMS = {
    # A-класс
    'a-класс': 'A-класс', 'a класс': 'A-класс', 'a class': 'A-класс', 'a200': 'A-класс', 'a180': 'A-класс',
    
    # B-класс
    'b-класс': 'B-класс', 'b класс': 'B-класс', 'b class': 'B-класс',
    
    # C-класс
    'c-класс': 'C-класс', 'c класс': 'C-класс', 'c class': 'C-класс', 'c200': 'C-класс', 'c180': 'C-класс',
    
    # E-класс
    'e-класс': 'E-класс', 'e класс': 'E-класс', 'e class': 'E-класс', 'e200': 'E-класс', 'e300': 'E-класс',
    
    # S-класс
    's-класс': 'S-класс', 's класс': 'S-класс', 's class': 'S-класс', 's400': 'S-класс', 's500': 'S-класс',
    
    # GLA, GLB, GLC, GLE, GLS
    'gla': 'GLA', 'гла': 'GLA',
    'glb': 'GLB', 'глб': 'GLB',
    'glc': 'GLC', 'глс': 'GLC',
    'gle': 'GLE', 'гле': 'GLE',
    'gls': 'GLS', 'глс': 'GLS',
    
    # G-класс
    'g-класс': 'G-класс', 'g класс': 'G-класс', 'g class': 'G-класс', 'g63': 'G-класс', 'g500': 'G-класс',
    
    # AMG модели
    'amg': 'AMG', 'амг': 'AMG',
    'c63 amg': 'C63 AMG', 'e63 amg': 'E63 AMG', 's63 amg': 'S63 AMG',
}

# Словарь синонимов Audi моделей
AUDI_MODEL_SYNONYMS = {
    # A-серия
    'a1': 'A1', 'а1': 'A1',
    'a3': 'A3', 'а3': 'A3',
    'a4': 'A4', 'а4': 'A4',
    'a5': 'A5', 'а5': 'A5',
    'a6': 'A6', 'а6': 'A6',
    'a7': 'A7', 'а7': 'A7',
    'a8': 'A8', 'а8': 'A8',
    
    # Q-серия
    'q2': 'Q2', 'к2': 'Q2',
    'q3': 'Q3', 'к3': 'Q3',
    'q4': 'Q4', 'к4': 'Q4',
    'q5': 'Q5', 'к5': 'Q5',
    'q7': 'Q7', 'к7': 'Q7',
    'q8': 'Q8', 'к8': 'Q8',
    
    # RS и S модели
    'rs3': 'RS3', 'рс3': 'RS3',
    'rs4': 'RS4', 'рс4': 'RS4',
    'rs6': 'RS6', 'рс6': 'RS6',
    's3': 'S3', 'с3': 'S3',
    's4': 'S4', 'с4': 'S4',
}

# Словарь синонимов Volkswagen моделей
VW_MODEL_SYNONYMS = {
    # Golf серия
    'golf': 'Golf', 'гольф': 'Golf', 'голф': 'Golf',
    'golf gti': 'Golf GTI', 'гольф гти': 'Golf GTI',
    'golf r': 'Golf R', 'гольф р': 'Golf R',
    
    # Passat
    'passat': 'Passat', 'пассат': 'Passat',
    
    # Tiguan, Touareg
    'tiguan': 'Tiguan', 'тигуан': 'Tiguan',
    'touareg': 'Touareg', 'туарег': 'Touareg',
    
    # Polo, Jetta
    'polo': 'Polo', 'поло': 'Polo',
    'jetta': 'Jetta', 'джетта': 'Jetta',
    
    # ID серия
    'id3': 'ID.3', 'id 3': 'ID.3',
    'id4': 'ID.4', 'id 4': 'ID.4',
}

# Словарь синонимов Toyota моделей
TOYOTA_MODEL_SYNONYMS = {
    # Camry, Corolla
    'camry': 'Camry', 'камри': 'Camry',
    'corolla': 'Corolla', 'королла': 'Corolla',
    
    # RAV4, Highlander
    'rav4': 'RAV4', 'рав4': 'RAV4', 'рав 4': 'RAV4',
    'highlander': 'Highlander', 'хайлендер': 'Highlander',
    
    # Land Cruiser
    'land cruiser': 'Land Cruiser', 'ленд крузер': 'Land Cruiser', 'ленд круизер': 'Land Cruiser',
    'prado': 'Prado', 'прадо': 'Prado',
    
    # Prius, Yaris
    'prius': 'Prius', 'приус': 'Prius',
    'yaris': 'Yaris', 'ярис': 'Yaris',
    
    # Hilux, Tacoma
    'hilux': 'Hilux', 'хилукс': 'Hilux',
    'tacoma': 'Tacoma', 'такома': 'Tacoma',
}

# Словарь синонимов Honda моделей
HONDA_MODEL_SYNONYMS = {
    'civic': 'Civic', 'сивик': 'Civic',
    'accord': 'Accord', 'аккорд': 'Accord',
    'cr-v': 'CR-V', 'crv': 'CR-V', 'кр-в': 'CR-V', 'крв': 'CR-V',
    'pilot': 'Pilot', 'пилот': 'Pilot',
    'fit': 'Fit', 'фит': 'Fit',
}

# Словарь синонимов Mazda моделей
MAZDA_MODEL_SYNONYMS = {
    'cx-3': 'CX-3', 'cx3': 'CX-3', 'кс-3': 'CX-3', 'кс3': 'CX-3',
    'cx-5': 'CX-5', 'cx5': 'CX-5', 'кс-5': 'CX-5', 'кс5': 'CX-5',
    'cx-30': 'CX-30', 'cx30': 'CX-30', 'кс-30': 'CX-30', 'кс30': 'CX-30',
    'cx-50': 'CX-50', 'cx50': 'CX-50', 'кс-50': 'CX-50', 'кс50': 'CX-50',
    'cx-60': 'CX-60', 'cx60': 'CX-60', 'кс-60': 'CX-60', 'кс60': 'CX-60',
    'cx-90': 'CX-90', 'cx90': 'CX-90', 'кс-90': 'CX-90', 'кс90': 'CX-90',
    'mazda3': 'Mazda 3', 'мазда3': 'Mazda 3', 'мазда 3': 'Mazda 3', '3': 'Mazda 3', 'три': 'Mazda 3',
    'mazda6': 'Mazda 6', 'мазда6': 'Mazda 6', 'мазда 6': 'Mazda 6', '6': 'Mazda 6', 'шесть': 'Mazda 6',
}

# Словарь синонимов Lexus моделей
LEXUS_MODEL_SYNONYMS = {
    'es': 'ES', 'ес': 'ES',
    'is': 'IS', 'ис': 'IS',
    'ls': 'LS', 'лс': 'LS',
    'gs': 'GS', 'гс': 'GS',
    'rx': 'RX', 'рх': 'RX',
    'nx': 'NX', 'нх': 'NX',
    'ux': 'UX', 'ух': 'UX',
    'lx': 'LX', 'лх': 'LX',
    'gx': 'GX', 'гх': 'GX',
}

# Словарь синонимов KIA моделей
KIA_MODEL_SYNONYMS = {
    'rio': 'Rio', 'рио': 'Rio',
    'ceed': 'Ceed', 'сид': 'Ceed',
    'sportage': 'Sportage', 'спортейдж': 'Sportage',
    'sorento': 'Sorento', 'соренто': 'Sorento',
    'cerato': 'Cerato', 'серато': 'Cerato',
    'picanto': 'Picanto', 'пиканто': 'Picanto',
    'stinger': 'Stinger', 'стингер': 'Stinger',
    'ev6': 'EV6', 'ев6': 'EV6',
}

# Словарь синонимов Hyundai моделей
HYUNDAI_MODEL_SYNONYMS = {
    'solaris': 'Solaris', 'солярис': 'Solaris',
    'elantra': 'Elantra', 'элантра': 'Elantra',
    'sonata': 'Sonata', 'соната': 'Sonata',
    'creta': 'Creta', 'крета': 'Creta',
    'tucson': 'Tucson', 'туссан': 'Tucson',
    'santa fe': 'Santa Fe', 'санта фе': 'Santa Fe',
    'palisade': 'Palisade', 'палисейд': 'Palisade',
    'ioniq': 'IONIQ', 'ионик': 'IONIQ',
    'kona': 'Kona', 'кона': 'Kona',
}

# Словарь синонимов Nissan моделей
NISSAN_MODEL_SYNONYMS = {
    'qashqai': 'Qashqai', 'кашкай': 'Qashqai', 'кашкаи': 'Qashqai',
    'x-trail': 'X-Trail', 'икс-трейл': 'X-Trail', 'икс трейл': 'X-Trail',
    'juke': 'Juke', 'джюк': 'Juke',
    'micra': 'Micra', 'микра': 'Micra',
    'note': 'Note', 'ноут': 'Note',
    'leaf': 'Leaf', 'лиф': 'Leaf',
    'murano': 'Murano', 'мурано': 'Murano',
    'pathfinder': 'Pathfinder', 'патфайндер': 'Pathfinder',
}

# Словарь синонимов Ford моделей
FORD_MODEL_SYNONYMS = {
    'focus': 'Focus', 'фокус': 'Focus',
    'mondeo': 'Mondeo', 'мондео': 'Mondeo',
    'fiesta': 'Fiesta', 'фиеста': 'Fiesta',
    'explorer': 'Explorer', 'эксплорер': 'Explorer',
    'escape': 'Escape', 'эскейп': 'Escape',
    'edge': 'Edge', 'эдж': 'Edge',
    'mustang': 'Mustang', 'мустанг': 'Mustang',
    'f-150': 'F-150', 'f150': 'F-150', 'ф-150': 'F-150', 'ф150': 'F-150',
}

# Словарь синонимов Volvo моделей
VOLVO_MODEL_SYNONYMS = {
    'xc60': 'XC60', 'хс60': 'XC60', 'кс60': 'XC60',
    'xc90': 'XC90', 'хс90': 'XC90', 'кс90': 'XC90',
    's60': 'S60', 'с60': 'S60',
    's90': 'S90', 'с90': 'S90',
    'v60': 'V60', 'в60': 'V60',
    'v90': 'V90', 'в90': 'V90',
    'c40': 'C40', 'с40': 'C40',
    'x40': 'X40', 'х40': 'X40',
}

# Словарь синонимов Porsche моделей
PORSCHE_MODEL_SYNONYMS = {
    '911': 'Porsche 911', 'девять один один': 'Porsche 911', 'девять-один-один': 'Porsche 911', 'девять один': 'Porsche 911',
    'cayenne': 'Cayenne', 'кайен': 'Cayenne', 'кайенн': 'Cayenne',
    'macan': 'Macan', 'макан': 'Macan',
    'panamera': 'Panamera', 'панамера': 'Panamera',
    'boxster': 'Boxster', 'бокстер': 'Boxster',
    'cayman': 'Cayman', 'кайман': 'Cayman',
    'taycan': 'Taycan', 'тайкан': 'Taycan',
}

# Словарь синонимов Chevrolet моделей
CHEVROLET_MODEL_SYNONYMS = {
    'cruze': 'Cruze', 'круз': 'Cruze',
    'aveo': 'Aveo', 'авео': 'Aveo',
    'lacetti': 'Lacetti', 'лачетти': 'Lacetti',
    'captiva': 'Captiva', 'каптива': 'Captiva',
    'orlando': 'Orlando', 'орландо': 'Orlando',
    'camaro': 'Camaro', 'камаро': 'Camaro',
    'corvette': 'Corvette', 'корвет': 'Corvette',
    'tahoe': 'Tahoe', 'тахо': 'Tahoe',
    'suburban': 'Suburban', 'сабурбан': 'Suburban',
}

# Словарь синонимов Lada моделей
LADA_MODEL_SYNONYMS = {
    'granta': 'Granta', 'гранта': 'Granta',
    'vesta': 'Vesta', 'веста': 'Vesta',
    'largus': 'Largus', 'ларгус': 'Largus',
    'xray': 'XRAY', 'иксрей': 'XRAY', 'x-ray': 'XRAY',
    'niva': 'Niva', 'нива': 'Niva',
    'kalina': 'Kalina', 'калина': 'Kalina',
    'priora': 'Priora', 'приора': 'Priora',
    'samara': 'Samara', 'самара': 'Samara',
}

# Словарь синонимов AITO моделей
AITO_MODEL_SYNONYMS = {
    'm5': 'M5', 'м5': 'M5',
    'm7': 'M7', 'м7': 'M7',
}

# Словарь синонимов CHANGAN моделей
CHANGAN_MODEL_SYNONYMS = {
    'alsvin': 'ALSVIN', 'алсвин': 'ALSVIN',
    'cs35plus': 'CS35PLUS', 'кс35плюс': 'CS35PLUS',
    'cs75plus': 'CS75PLUS', 'кс75плюс': 'CS75PLUS',
    'cs95new': 'CS95NEW', 'кс95нью': 'CS95NEW',
    'eado plus': 'EADO PLUS', 'еадо плюс': 'EADO PLUS',
    'uni-k': 'UNI-K', 'уни-к': 'UNI-K',
    'uni-s': 'UNI-S', 'уни-с': 'UNI-S',
    'uni-t': 'UNI-T', 'уни-т': 'UNI-T',
    'uni-v': 'UNI-V', 'уни-в': 'UNI-V',
}

# Словарь синонимов JAECOO моделей
JAECOO_MODEL_SYNONYMS = {
    'j7': 'J7', 'дж7': 'J7',
    'j74wd': 'J74WD', 'дж74вд': 'J74WD',
    'j84wd': 'J84WD', 'дж84вд': 'J84WD',
}

# Словарь синонимов OMODA моделей
OMODA_MODEL_SYNONYMS = {
    'c5': 'C5', 'с5': 'C5',
    'c5awd': 'C5AWD', 'с5авд': 'C5AWD',
    'c7': 'C7', 'с7': 'C7',
    'c74wd': 'C74WD', 'с74вд': 'C74WD',
    's5': 'S5', 'с5': 'S5',
    's5 gt': 'S5 GT', 'с5 гт': 'S5 GT',
}

# Словарь синонимов SOLARIS моделей
SOLARIS_MODEL_SYNONYMS = {
    'hc': 'HC', 'хс': 'HC',
    'krs': 'KRS', 'крс': 'KRS',
    'krx': 'KRX', 'крх': 'KRX',
}

# Словарь синонимов Tank моделей
TANK_MODEL_SYNONYMS = {
    '300': '300', 'триста': '300',
    '400': '400', 'четыреста': '400',
    '500': '500', 'пятьсот': '500',
    '700': '700', 'семьсот': '700',
    'tank 300': 'Tank 300', 'танк 300': 'Tank 300',
}

# Словарь синонимов Tesla моделей
TESLA_MODEL_SYNONYMS = {
    'model s': 'Model S', 'модел с': 'Model S',
    'model 3': 'Model 3', 'модел 3': 'Model 3',
    'model x': 'Model X', 'модел х': 'Model X',
    'model y': 'Model Y', 'модел у': 'Model Y',
}

# Словарь синонимов Москвич моделей
MOSKVICH_MODEL_SYNONYMS = {
    'москвич 3': 'МОСКВИЧ 3', 'м3': 'МОСКВИЧ 3',
    'москвич 6': 'МОСКВИЧ 6', 'м6': 'МОСКВИЧ 6',
    'москвич 8': 'Москвич 8', 'м8': 'Москвич 8',
}

# Объединенный словарь синонимов моделей
MODEL_SYNONYMS = {
    **CHINESE_MODEL_SYNONYMS,
    **BMW_MODEL_SYNONYMS,
    **MERCEDES_MODEL_SYNONYMS,
    **AUDI_MODEL_SYNONYMS,
    **VW_MODEL_SYNONYMS,
    **TOYOTA_MODEL_SYNONYMS,
    **HONDA_MODEL_SYNONYMS,
    **MAZDA_MODEL_SYNONYMS,
    **LEXUS_MODEL_SYNONYMS,
    **KIA_MODEL_SYNONYMS,
    **HYUNDAI_MODEL_SYNONYMS,
    **NISSAN_MODEL_SYNONYMS,
    **FORD_MODEL_SYNONYMS,
    **PORSCHE_MODEL_SYNONYMS,
    **VOLVO_MODEL_SYNONYMS,
    **CHEVROLET_MODEL_SYNONYMS,
    **LADA_MODEL_SYNONYMS,
    **AITO_MODEL_SYNONYMS,
    **CHANGAN_MODEL_SYNONYMS,
    **JAECOO_MODEL_SYNONYMS,
    **OMODA_MODEL_SYNONYMS,
    **SOLARIS_MODEL_SYNONYMS,
    **TANK_MODEL_SYNONYMS,
    **TESLA_MODEL_SYNONYMS,
    **MOSKVICH_MODEL_SYNONYMS,
}

# Отечественные бренды
OTECHESTVENNYE = {'Москвич', 'Lada', 'УАЗ', 'ГАЗ', 'КАМАЗ'}

# Функция для получения всех уникальных брендов из базы данных
@lru_cache(maxsize=1)
def get_all_brands_from_db():
    """Получает все уникальные бренды из базы данных"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cars.db')
    if not os.path.exists(db_path):
        return set()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT mark FROM car 
                UNION 
                SELECT DISTINCT mark FROM used_car
                WHERE mark IS NOT NULL AND mark != ''
            """)
            brands = {row[0] for row in cursor.fetchall()}
            return brands
    except Exception as e:
        print(f"Ошибка при получении брендов из БД: {e}")
        return set()

# Функция для создания расширенного словаря синонимов
def create_extended_brand_synonyms():
    """Создает расширенный словарь синонимов на основе данных из БД"""
    db_brands = get_all_brands_from_db()
    extended_synonyms = BRAND_SYNONYMS.copy()
    
    # Группируем похожие бренды по каноническим названиям
    brand_groups = {}
    
    for brand in db_brands:
        if not brand:
            continue
            
        brand_lower = brand.lower().strip()
        
        # Определяем каноническое название бренда
        canonical_brand = None
        
        # Сначала проверяем базовый словарь
        if brand_lower in BRAND_SYNONYMS:
            canonical_brand = BRAND_SYNONYMS[brand_lower]
        else:
            # Если бренд не найден в словаре, определяем каноническое название
            canonical_brand = determine_canonical_brand(brand)
        
        # Создаем группу для этого бренда
        if canonical_brand not in brand_groups:
            brand_groups[canonical_brand] = set()
        
        # Добавляем все варианты написания
        brand_groups[canonical_brand].add(brand)  # оригинал как есть
        brand_groups[canonical_brand].add(brand.lower())  # нижний регистр
        brand_groups[canonical_brand].add(brand.upper())  # верхний регистр
        brand_groups[canonical_brand].add(brand.title())  # с заглавной буквы
        
        # Добавляем каноническое название
        brand_groups[canonical_brand].add(canonical_brand)
    
    # Создаем расширенный словарь
    for canonical, variants in brand_groups.items():
        for variant in variants:
            if variant != canonical:
                extended_synonyms[variant.lower()] = canonical
    
    return extended_synonyms

def determine_canonical_brand(brand):
    """Определяет каноническое название бренда на основе различных правил"""
    brand_lower = brand.lower().strip()
    
    # Правила для определения канонического названия
    canonical_rules = {
        # Китайские бренды
        'chery': 'Chery',
        'geely': 'Geely',
        'haval': 'Haval',
        'byd': 'BYD',
        'changan': 'Changan',
        'exeed': 'Exeed',
        'omoda': 'Omoda',
        'jaecoo': 'Jaecoo',
        'jac': 'JAC',
        'faw': 'FAW',
        'dongfeng': 'Dongfeng',
        'gac': 'GAC',
        'tank': 'Tank',
        'jetour': 'Jetour',
        'kaiyi': 'Kaiyi',
        'baic': 'BAIC',
        'swm': 'SWM',
        'hongqi': 'Hongqi',
        'aito': 'AITO',
        'belgee': 'Belgee',
        'knewstar': 'Knewstar',
        'seres': 'SERES',
        'solaris': 'SOLARIS',
        'wey': 'WEY',
        'jishi': 'JISHI',
        'voyah': 'Voyah',
        'zeekr': 'Zeekr',
        
        # Корейские бренды
        'kia': 'Kia',
        'hyundai': 'Hyundai',
        'ssangyong': 'SsangYong',
        
        # Японские бренды
        'toyota': 'Toyota',
        'nissan': 'Nissan',
        'honda': 'Honda',
        'mazda': 'Mazda',
        'lexus': 'Lexus',
        'mitsubishi': 'Mitsubishi',
        'subaru': 'Subaru',
        'suzuki': 'Suzuki',
        'infiniti': 'Infiniti',
        'daihatsu': 'Daihatsu',
        
        # Немецкие бренды
        'bmw': 'BMW',
        'mercedes-benz': 'Mercedes-Benz',
        'audi': 'Audi',
        'volkswagen': 'Volkswagen',
        'skoda': 'Skoda',
        'opel': 'Opel',
        'porsche': 'Porsche',
        'mini': 'MINI',
        'maybach': 'Maybach',
        'smart': 'Smart',
        'alpina': 'Alpina',
        
        # Французские бренды
        'renault': 'Renault',
        'peugeot': 'Peugeot',
        'citroen': 'Citroen',
        'dacia': 'Dacia',
        
        # Итальянские бренды
        'fiat': 'Fiat',
        'alfa romeo': 'Alfa Romeo',
        'lancia': 'Lancia',
        'maserati': 'Maserati',
        'ferrari': 'Ferrari',
        'lamborghini': 'Lamborghini',
        
        # Американские бренды
        'ford': 'Ford',
        'chevrolet': 'Chevrolet',
        'jeep': 'Jeep',
        'dodge': 'Dodge',
        'chrysler': 'Chrysler',
        'cadillac': 'Cadillac',
        'lincoln': 'Lincoln',
        'buick': 'Buick',
        'pontiac': 'Pontiac',
        'saturn': 'Saturn',
        'hummer': 'Hummer',
        'gmc': 'GMC',
        'ram': 'RAM',
        
        # Шведские бренды
        'volvo': 'Volvo',
        'saab': 'Saab',
        
        # Британские бренды
        'jaguar': 'Jaguar',
        'land rover': 'Land Rover',
        'rolls-royce': 'Rolls-Royce',
        'bentley': 'Bentley',
        'aston martin': 'Aston Martin',
        'mclaren': 'McLaren',
        'lotus': 'Lotus',
        
        # Отечественные бренды
        'lada': 'Lada',
        'москвич': 'Москвич',
        'уаз': 'УАЗ',
        'газ': 'ГАЗ',
        'камаз': 'КАМАЗ',
        
        # Другие популярные бренды
        'seat': 'Seat',
        'tesla': 'Tesla',
        'rivian': 'Rivian',
        'lucid': 'Lucid',
        'polestar': 'Polestar',
        'canoo': 'Canoo',
        'fisker': 'Fisker',
        'nikola': 'Nikola',
        'lordstown': 'Lordstown',
        
        # Китайские электромобили
        'li auto': 'Li Auto',
        'lixiang': 'LiXiang',
        'lynk & co': 'Lynk & Co',
        'mg': 'MG',
        'neta': 'Neta',
        'nio': 'NIO',
        'voyah': 'Voyah',
        'xev': 'XEV',
        'xpeng': 'XPeng',
        'zeekr': 'Zeekr',
    }
    
    # Проверяем точное совпадение
    if brand_lower in canonical_rules:
        return canonical_rules[brand_lower]
    
    # Проверяем частичные совпадения
    for key, canonical in canonical_rules.items():
        if brand_lower in key or key in brand_lower:
            return canonical
    
    # Если ничего не найдено, возвращаем в Title Case
    return brand.title()

# Функция для получения всех вариантов бренда
def get_all_brand_variants(brand_input=None):
    """Получает все варианты брендов"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cars.db')
    if not os.path.exists(db_path):
        return set()
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT mark FROM car 
                UNION 
                SELECT DISTINCT mark FROM used_car
                WHERE mark IS NOT NULL AND mark != ''
            """)
            brands = {row[0] for row in cursor.fetchall()}
            return brands
    except Exception as e:
        print(f"Ошибка при получении брендов из БД: {e}")
        return set()

def is_same_brand(brand1, brand2):
    """Проверяет, являются ли два бренда одним и тем же"""
    brand1_lower = brand1.lower().strip()
    brand2_lower = brand2.lower().strip()
    
    # Прямое сравнение
    if brand1_lower == brand2_lower:
        return True
    
    # Проверяем через канонические названия
    canonical1 = determine_canonical_brand(brand1)
    canonical2 = determine_canonical_brand(brand2)
    
    return canonical1.lower() == canonical2.lower()

# Функция для поиска похожих брендов
def find_similar_brands(user_input, threshold=0.8):
    """Находит похожие бренды в базе данных с учетом несоответствий"""
    user_input_lower = user_input.lower().strip()
    
    # Сначала проверяем точное совпадение в словаре
    if user_input_lower in BRAND_SYNONYMS:
        canonical = BRAND_SYNONYMS[user_input_lower]
        return get_all_brand_variants(canonical)
    
    # Получаем все бренды из БД
    db_brands = get_all_brands_from_db()
    
    # Ищем похожие бренды
    similar_brands = []
    for brand in db_brands:
        if not brand:
            continue
        
        # Проверяем различные варианты написания
        brand_variants = [
            brand.lower(),
            brand,
            brand.upper(),
            brand.title()
        ]
        
        for variant in brand_variants:
            if user_input_lower in variant.lower() or variant.lower() in user_input_lower:
                # Добавляем все варианты этого бренда
                all_variants = get_all_brand_variants(brand)
                similar_brands.extend(all_variants)
                break
        
        # Используем difflib для более точного поиска
        if get_close_matches(user_input_lower, [brand.lower()], n=1, cutoff=threshold):
            all_variants = get_all_brand_variants(brand)
            similar_brands.extend(all_variants)
    
    return list(set(similar_brands))

# Функция для нормализации бренда с учетом всех вариантов
def normalize_brand_extended(brand_input):
    """Нормализует бренд с учетом всех возможных вариантов написания"""
    if not brand_input:
        return None
    
    brand_input_lower = brand_input.lower().strip()
    
    # Проверяем базовый словарь
    if brand_input_lower in BRAND_SYNONYMS:
        return BRAND_SYNONYMS[brand_input_lower]
    
    # Получаем расширенный словарь
    extended_synonyms = create_extended_brand_synonyms()
    
    # Проверяем расширенный словарь
    if brand_input_lower in extended_synonyms:
        return extended_synonyms[brand_input_lower]
    
    # Ищем похожие бренды
    similar_brands = find_similar_brands(brand_input)
    if similar_brands:
        # Возвращаем каноническое название первого найденного
        first_brand = next(iter(similar_brands))
        return determine_canonical_brand(first_brand)
    
    # Если ничего не найдено, возвращаем в Title Case
    return brand_input.title()

# Создаем расширенный словарь при импорте модуля
EXTENDED_BRAND_SYNONYMS = create_extended_brand_synonyms() 