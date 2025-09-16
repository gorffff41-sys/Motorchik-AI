import sqlite3
import re
from typing import Dict, Any, List
from difflib import get_close_matches
import unicodedata
import jellyfish
from typing import Set, Tuple

# Импортируем синонимы из entity_extractor
from .entity_extractor import MANUAL_MARK_SYNONYMS, MANUAL_MODEL_SYNONYMS

def advanced_fuzzy_match_ner(query_word: str, synonym_set: Set[str], threshold: float = 0.85) -> bool:
    """
    Продвинутое fuzzy matching для NER Classifier
    """
    query_word = query_word.lower().strip()
    
    # 1. Точное совпадение
    if query_word in synonym_set:
        return True
    
    # 2. Jaro-Winkler расстояние
    for synonym in synonym_set:
        if jellyfish.jaro_winkler_similarity(query_word, synonym) >= threshold:
            return True
    
    # 3. Расстояние Левенштейна
    for synonym in synonym_set:
        if jellyfish.levenshtein_distance(query_word, synonym) <= 2:
            return True
    
    # 4. Метод Soundex для фонетического сравнения
    try:
        query_soundex = jellyfish.soundex(query_word)
        for synonym in synonym_set:
            if jellyfish.soundex(synonym) == query_soundex:
                return True
    except:
        pass
    
    # 5. Метод Metaphone
    try:
        query_metaphone = jellyfish.metaphone(query_word)
        for synonym in synonym_set:
            if jellyfish.metaphone(synonym) == query_metaphone:
                return True
    except:
        pass
    
    # 6. Частичное совпадение (для составных слов)
    for synonym in synonym_set:
        if len(query_word) > 3 and len(synonym) > 3:
            if query_word in synonym or synonym in query_word:
                return True
    
    return False

def phonetic_similarity_ner(word1: str, word2: str) -> float:
    """
    Вычисляет фонетическую схожесть между словами для NER
    """
    try:
        # Jaro-Winkler для общей схожести
        jaro = jellyfish.jaro_winkler_similarity(word1.lower(), word2.lower())
        
        # Soundex схожесть
        soundex1 = jellyfish.soundex(word1.lower())
        soundex2 = jellyfish.soundex(word2.lower())
        soundex_sim = 1.0 if soundex1 == soundex2 else 0.0
        
        # Metaphone схожесть
        metaphone1 = jellyfish.metaphone(word1.lower())
        metaphone2 = jellyfish.metaphone(word2.lower())
        metaphone_sim = 1.0 if metaphone1 == metaphone2 else 0.0
        
        # Взвешенная схожесть
        return (jaro * 0.5 + soundex_sim * 0.25 + metaphone_sim * 0.25)
    except:
        return 0.0

class NERIntentClassifier:
    """
    Универсальный модуль для извлечения сущностей (NER) и классификации намерения (Intent).
    """
    COLORS = [
        # Базовые цвета
        'белый', 'черный', 'серый', 'красный', 'синий', 'зеленый', 'коричневый', 'оранжевый', 'фиолетовый', 'голубой', 'бежевый', 'серебряный', 'желтый', 'розовый', 'темно-синий', 'золотистый',
        # Из БД (уникальные варианты)
        'арктический белый', 'атомный серый', 'благородный агат', 'галактический черный', 'голубой металлик', 'дымчатый жемчуг', 'звёздный белый', 'звёздный серый', 'зеленая морозная сосна', 'изумрудный металлик', 'искрящийся красный', 'керамический белый', 'космический зелёный', 'ледяной кристально-серый', 'лиловый перламутр', 'океанический лазурит', 'океанический синий', 'платиновый неон', 'позолоченный черный', 'светло-серый', 'серебристый металлик', 'серо-голубой', 'серо-фиолетовый металлик', 'серый шантар неметаллик', 'снежная иремель', 'черный богдо металлик', 'черный космос', 'черный нефрит', 'чёрный металлик', 'перламутровый белый', 'магнитный серый', 'базальтовый серый', 'diamond purple', 'ink black', 'crystal black', 'crystal white', 'platinum steel gray', 'mint green', 'sky blue', 'technical grey', 'pearl', 'magnetic gray', 'basalt gray', 'aurora blue', 'ceramic white', 'turquoise', 'maroon', 'khaki', 'pearl white', 'magnetic grey', 'deep black', 'bright white', 'noble agate', 'emerald metallic', 'dynamic black', 'snow irimel', 'ice crystal grey', 'atomic grey', 'star grey', 'star white', 'fiery red', 'sparkling white', 'noble agate', 'emerald metallic', 'dynamic black', 'snow irimel', 'ice crystal grey', 'atomic grey', 'star grey', 'star white', 'fiery red', 'sparkling white',
    ]
    COLOR_SYNONYMS = {
        # Базовые
        'белый': ['white', 'искрящийся белый', 'керамический белый', 'перламутровый белый', 'crystal white', 'snow irimel', 'sparkling white', 'bright white', 'star white', 'керамический белый ceramic white', 'белого', 'белая', 'белое', 'белые'],
        'черный': ['black', 'чёрный', 'черный металлик', 'ink black', 'crystal black', 'deep black', 'dynamic black', 'галактический черный', 'черный богдо металлик', 'черный космос', 'черный нефрит', 'позолоченный черный', 'черного', 'черная', 'черное', 'черные'],
        'серый': ['grey', 'gray', 'серый металлик', 'magnetic gray', 'magnetic grey', 'basalt gray', 'atomic grey', 'серый шантар неметаллик', 'платиновый стальной серый', 'platinum steel gray', 'серо-голубой', 'серо-фиолетовый металлик', 'diamond purple', 'technical grey', 'ice crystal grey', 'star grey', 'атомный серый', 'ледяной кристально-серый', 'магнитный серый', 'базальтовый серый', 'star grey', 'серого', 'серая', 'серое', 'серые'],
        'красный': ['red', 'fiery red', 'огненно-красный', 'искрящийся красный', 'maroon', 'красного', 'красная', 'красное', 'красные'],
        'синий': ['blue', 'sky blue', 'океанический синий', 'aurora blue', 'голубой', 'голубой металлик', 'небесно-голубой', 'океанический лазурит', 'синего', 'синяя', 'синее', 'синие'],
        'зеленый': ['green', 'mint green', 'emerald metallic', 'космический зелёный', 'зеленая морозная сосна', 'изумрудный металлик', 'зеленого', 'зеленая', 'зеленое', 'зеленые'],
        'коричневый': ['brown', 'noble agate', 'благородный агат', 'коричневого', 'коричневая', 'коричневое', 'коричневые'],
        'оранжевый': ['orange', 'оранжевого', 'оранжевая', 'оранжевое', 'оранжевые'],
        'фиолетовый': ['purple', 'diamond purple', 'лиловый перламутр', 'фиолетового', 'фиолетовая', 'фиолетовое', 'фиолетовые'],
        'бежевый': ['beige', 'бежевого', 'бежевая', 'бежевое', 'бежевые'],
        'серебряный': ['silver', 'серебристый', 'серебристый металлик', 'silver/black', 'silver серый', 'silver (kh)', 'silver (ku)', 'silver (kx)', 'серебряного', 'серебряная', 'серебряное', 'серебряные', 'серебристого', 'серебристой', 'серебристого', 'серебристых'],
        'перламутровый': ['pearl', 'перламутровый белый', 'pearl white', 'перламутрового', 'перламутровая', 'перламутровое', 'перламутровые'],
        'туркуаз': ['turquoise', 'туркуазного', 'туркуазная', 'туркуазное', 'туркуазные'],
        'хаки': ['khaki', 'хаки', 'хакишного', 'хакишная', 'хакишное', 'хакишные'],
        'голубой': ['sky blue', 'голубой металлик', 'небесно-голубой', 'aurora blue', 'голубого', 'голубая', 'голубое', 'голубые'],
        'желтый': ['yellow', 'желтого', 'желтая', 'желтое', 'желтые'],
        'розовый': ['pink', 'розового', 'розовая', 'розовое', 'розовые'],
        'темно-синий': ['dark blue', 'темно-синего', 'темно-синяя', 'темно-синее', 'темно-синие'],
        'золотистый': ['gold', 'golden', 'золотистого', 'золотистая', 'золотистое', 'золотистые'],
        # Варианты с "- черная крыша", "- белая крыша", "с черной крышей"
        'белый-черная крыша': ['белый - черная крыша', 'белый с черной крышей', 'white/black', 'white/black (ze)', 'арктический белый/чёрный'],
        'красный-черная крыша': ['красный - черная крыша', 'red/black', 'red/black (zf)'],
        'серый-черная крыша': ['серый - черная крыша', 'серо-голубой + черная крыша'],
        'голубой-черная крыша': ['голубой - черная крыша'],
        # Металлик, перламутр, жемчуг
        'жемчуг': ['дымчатый жемчуг'],
        'металлик': ['металлик', 'черный металлик', 'серебристый металлик', 'изумрудный металлик', 'серый металлик', 'голубой металлик'],
    }
    BODY_TYPES = {
        'кабриолет': 'кабриолет', 'открытой крышей': 'кабриолет', 'универсал': 'универсал', 'седан': 'седан', 'хэтчбек': 'хэтчбек',
        'купе': 'купе', 'внедорожник': 'внедорожник', 'джип': 'внедорожник', 'пикап': 'пикап', 'минивэн': 'минивэн',
        'микроавтобус': 'микроавтобус', 'фургон': 'фургон', 'лимузин': 'лимузин', 'родстер': 'родстер', 'тарга': 'тарга',
        'лифтбек': 'лифтбек', 'фастбек': 'фастбек', 'комби': 'универсал', 'suv': 'внедорожник', 'crossover': 'внедорожник'
    }
    BODY_TYPE_SYNONYMS = {
        'внедорожник': ['suv', 'джип', 'crossover', 'кроссовер'],
        'седан': ['sedan'],
        'универсал': ['wagon', 'универсал', 'комби'],
        'кабриолет': ['cabrio', 'convertible', 'открытая крыша'],
        'купе': ['coupe'],
        'минивэн': ['minivan'],
        'хэтчбек': ['hatchback'],
        'пикап': ['pickup'],
        'фургон': ['van'],
        'лимузин': ['limousine'],
        'родстер': ['roadster'],
        'тарга': ['targa'],
        'лифтбек': ['liftback'],
        'фастбек': ['fastback']
    }
    MARKS = [
        'мерседес', 'bmw', 'лада', 'тойота', 'audi', 'volkswagen', 'nissan', 'mazda', 'honda', 'hyundai', 'kia', 'renault', 'ford',
        'skoda', 'chery', 'geely', 'haval', 'lexus', 'porsche', 'subaru', 'suzuki', 'mitsubishi', 'peugeot', 'citroen', 'fiat', 'opel',
        'chevrolet', 'uaz', 'ваз', 'volvo', 'infiniti', 'acura', 'tesla', 'bentley', 'bugatti', 'rolls-royce', 'mini', 'smart', 'jac',
        'exeed', 'dongfeng', 'byd', 'li', 'xpeng', 'zeekr', 'tank', 'jetour', 'gac', 'aiways', 'nio', 'voyah', 'moskvich', 'evolute',
        'genesis', 'ravon', 'datsun', 'daewoo', 'great wall', 'ssangyong', 'proton', 'saab', 'seat', 'changan', 'dongfeng', 'faw', 'gac',
        'jac', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 'haima', 'hafei', 'geely', 'chery', 'foton', 'dfm', 'dongfeng',
        'gac', 'jac', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 'haima', 'hafei', 'geely', 'chery', 'foton', 'dfm',
        'omoda', 'changan', 'faw', 'jac', 'hozon', 'leapmotor', 'seres', 'voyah', 'hongqi', 'jetour', 'swm', 'baic', 'dongfeng', 'gwm', 'haval', 'changan', 'chery', 'zeekr', 'exeed', 'tank', 'nio', 'xpeng', 'li auto', 'byd', 'wuling', 'lynk&co', 'roewe', 'mg', 'maxus', 'polestar', 'smart', 'geometry', 'aito', 'avatr', 'arcfox', 'denza', 'im', 'rising auto', 'weltmeister', 'skywell', 'forthing'
    ]
    MARK_SYNONYMS = {
        'мерседес': ['mercedes', 'mercedes-benz', 'mb'],
        'bmw': ['бмв'],
        'лада': ['lada', 'ваз', 'ладу', 'лады', 'ладе', 'ладой', 'ладою'],
        'тойота': ['toyota'],
        'audi': ['ауди'],
        'volkswagen': ['vw', 'фольксваген'],
        'nissan': ['ниссан'],
        'mazda': ['мазда'],
        'honda': ['хонда'],
        'hyundai': ['хендай', 'хундай'],
        'kia': ['киа'],
        'renault': ['рено'],
        'ford': ['форд'],
        'skoda': ['шкода'],
        'chery': ['черри'],
        'geely': ['джили'],
        'haval': ['хавейл', 'хавал'],
        'lexus': ['лексус'],
        'porsche': ['порше'],
        'subaru': ['субару'],
        'suzuki': ['сузуки'],
        'mitsubishi': ['митсубиси'],
        'peugeot': ['пежо'],
        'citroen': ['ситроен'],
        'fiat': ['фиат'],
        'opel': ['опель'],
        'chevrolet': ['шевроле'],
        'uaz': ['уаз'],
        'ваз': ['лада', 'ваз'],
        'volvo': ['вольво'],
        'infiniti': ['инфинити'],
        'acura': ['акура'],
        'tesla': ['тесла'],
        'bentley': ['бентли'],
        'bugatti': ['бугатти'],
        'rolls-royce': ['роллс-ройс'],
        'mini': ['мини'],
        'smart': ['смарт'],
        'jac': ['жак'],
        'exeed': ['эксид'],
        'dongfeng': ['донгфенг'],
        'byd': ['бид'],
        'li': ['ли'],
        'xpeng': ['икспенг'],
        'zeekr': ['зикр'],
        'tank': ['танк'],
        'jetour': ['жетур'],
        'gac': ['гак'],
        'aiways': ['айвейс'],
        'nio': ['нио'],
        'voyah': ['вояж'],
        'moskvich': ['москвич'],
        'evolute': ['эволют'],
        'genesis': ['генезис'],
        'ravon': ['равон'],
        'datsun': ['датсун'],
        'daewoo': ['дэу'],
        'great wall': ['грейтуолл'],
        'ssangyong': ['ссангйонг'],
        'proton': ['протон'],
        'saab': ['сааб'],
        'seat': ['сеат'],
        'changan': ['чанган'],
        'faw': ['фав'],
        'lifan': ['лифан'],
        'zotye': ['зоти'],
        'brilliance': ['бриллианс'],
        'baic': ['баик'],
        'baw': ['бау'],
        'jinbei': ['джинбей'],
        'haima': ['хайма'],
        'hafei': ['хафей'],
        'foton': ['фотон'],
        'dfm': ['дфм'],
        'omoda': ['омода'],
        'changan': ['чанган'],
        'faw': ['фав'],
        'jac': ['жак'],
        'hozon': ['хозон'],
        'leapmotor': ['липмотор', 'лип мотор'],
        'seres': ['серес'],
        'voyah': ['воя', 'вояж'],
        'hongqi': ['хончи', 'хонци'],
        'jetour': ['жетур'],
        'swm': ['свм'],
        'baic': ['баик'],
        'dongfeng': ['донгфенг', 'dfm'],
        'gwm': ['греат волл', 'гвм'],
        'haval': ['хавал', 'хавейл'],
        'chery': ['черри'],
        'zeekr': ['зикр'],
        'exeed': ['эксид'],
        'tank': ['танк'],
        'nio': ['нио'],
        'xpeng': ['икспенг'],
        'li auto': ['ли авто', 'ли'],
        'byd': ['бид'],
        'wuling': ['вулинг'],
        'lynk&co': ['линк энд ко', 'линк'],
        'roewe': ['рове'],
        'mg': ['мг'],
        'maxus': ['максус'],
        'polestar': ['полстар'],
        'smart': ['смарт'],
        'geometry': ['геометрия'],
        'aito': ['айто'],
        'avatr': ['аватр'],
        'arcfox': ['аркофокс'],
        'denza': ['денза'],
        'im': ['айэм'],
        'rising auto': ['райзинг авто'],
        'weltmeister': ['вельтмайстер'],
        'skywell': ['скайвелл'],
        'forthing': ['фортинг']
    }
    
    # Новые сущности для расширенных фильтров
    CAR_STATES = {
        'новый': 'new',
        'с пробегом': 'used',
        'б/у': 'used',
        'подержанный': 'used',
        'новый автомобиль': 'new',
        'автомобиль с пробегом': 'used'
    }
    
    POPULAR_OPTIONS = {
        'люк': ['S403A', 'люк', 'sunroof', 'открывающаяся крыша'],
        'панорамная крыша': ['S423A', 'панорамная крыша', 'panoramic roof', 'панорамная'],
        'климат-контроль': ['S430A', 'климат-контроль', 'climate control', 'кондиционер'],
        'подогрев сидений': ['S431A', 'подогрев сидений', 'heated seats', 'подогрев'],
        'электрорегулировка сидений': ['S459A', 'электрорегулировка сидений', 'power seats'],
        'система парковки': ['S494A', 'система парковки', 'parking system'],
        'навигация': ['S502A', 'навигация', 'navigation', 'gps'],
        'парктроник': ['S508A', 'парктроник', 'parking sensors'],
        'датчик дождя': ['S521A', 'датчик дождя', 'rain sensor'],
        'ксенон': ['S522A', 'ксенон', 'xenon'],
        'адаптивные фары': ['S524A', 'адаптивные фары', 'adaptive headlights'],
        'система комфортного доступа': ['S534A', 'система комфортного доступа', 'comfort access'],
        'люкс-комплектация': ['LUXURY', 'люкс', 'luxury'],
        'комфорт-комплектация': ['COMFORT', 'комфорт', 'comfort'],
        'спорт-комплектация': ['SPORT', 'спорт', 'sport'],
        'семейная комплектация': ['FAMILY', 'семейная', 'family'],
        'бизнес-комплектация': ['BUSINESS', 'бизнес', 'business']
    }
    
    MILEAGE_RANGES = {
        'до 20 тыс': {'mileage_to': 20000},
        'до 50 тыс': {'mileage_to': 50000},
        'до 100 тыс': {'mileage_to': 100000},
        'до 200 тыс': {'mileage_to': 200000},
        '20-50 тыс': {'mileage_from': 20000, 'mileage_to': 50000},
        '50-100 тыс': {'mileage_from': 50000, 'mileage_to': 100000},
        '100-200 тыс': {'mileage_from': 100000, 'mileage_to': 200000},
        'более 200 тыс': {'mileage_from': 200000},
        'маленький пробег': {'mileage_to': 50000},
        'средний пробег': {'mileage_from': 50000, 'mileage_to': 150000},
        'большой пробег': {'mileage_from': 150000}
    }
    
    POPULAR_SCENARIOS = {
        'семейный': ['семейный', 'семья', 'family', 'для семьи', 'с детьми'],
        'для города': ['городской', 'город', 'city', 'компактный', 'маневренный'],
        'для путешествий': ['путешествия', 'поездки', 'travel', 'внедорожник', 'кроссовер'],
        'для работы': ['работа', 'бизнес', 'work', 'business', 'солидный'],
        'для дачи': ['дача', 'загородный', 'проходимость', 'вместительность'],
        'для молодежи': ['молодежный', 'молодежь', 'youth', 'спортивный', 'динамичный'],
        'для бизнеса': ['бизнес', 'престижный', 'люкс', 'premium'],
        'экономичный': ['экономичный', 'экономия', 'дешевый', 'бюджетный']
    }
    
    # Новые сущности для расширенного анализа
    FUEL_TYPES = {
        'бензин': ['petrol', 'gasoline', 'бензиновый'],
        'дизель': ['diesel', 'дизельный'],
        'электро': ['electric', 'электро', 'электрический', 'ev'],
        'гибрид': ['hybrid', 'гибридный', 'hybrid-electric'],
        'газ': ['lpg', 'cng', 'газовый', 'метан', 'пропан'],
        'водород': ['hydrogen', 'водородный', 'h2']
    }
    
    TRANSMISSION_TYPES = {
        'механика': ['manual', 'механическая', 'механической', 'ручная', 'ручной', 'механика', 'механическая коробка', 'механической коробкой', 'ручная коробка', 'ручной коробкой', 'механика', 'механическая трансмиссия', 'механической трансмиссией', 'механическая коробка передач', 'механической коробкой передач'],
        'автомат': ['automatic', 'автоматическая', 'автоматической', 'автомат', 'автоматическая коробка', 'автоматической коробкой', 'автоматическая трансмиссия', 'автоматической трансмиссией', 'автоматическая коробка передач', 'автоматической коробкой передач', 'автомат', 'автоматическая коробка передач', 'автоматической коробкой передач'],
        'робот': ['robot', 'роботизированная', 'роботизированной', 'робот', 'роботизированная коробка', 'роботизированной коробкой', 'роботизированная трансмиссия', 'роботизированной трансмиссией', 'роботизированная коробка передач', 'роботизированной коробкой передач', 'роботизированная коробка передач', 'роботизированной коробкой передач'],
        'вариатор': ['cvt', 'вариаторная', 'вариаторной', 'вариатор', 'вариаторная коробка', 'вариаторной коробкой', 'вариаторная коробка передач', 'вариаторной коробкой передач', 'бесступенчатая трансмиссия', 'бесступенчатой трансмиссией', 'вариаторная коробка передач', 'вариаторной коробкой передач']
    }
    
    DRIVE_TYPES = {
        'передний': ['front-wheel drive', 'fwd', 'переднеприводный', 'переднеприводной', 'передний привод', 'передним приводом', 'переднеприводная', 'переднеприводной', 'передний привод', 'передним приводом', 'переднеприводный автомобиль', 'переднеприводным автомобилем', 'передний привод', 'передним приводом'],
        'задний': ['rear-wheel drive', 'rwd', 'заднеприводный', 'заднеприводной', 'задний привод', 'задним приводом', 'заднеприводная', 'заднеприводной', 'задний привод', 'задним приводом', 'заднеприводный автомобиль', 'заднеприводным автомобилем', 'задний привод', 'задним приводом'],
        'полный': ['all-wheel drive', 'awd', '4wd', 'полноприводный', 'полноприводной', 'полный привод', 'полным приводом', 'полноприводная', 'полноприводной', '4x4', 'полноприводный автомобиль', 'полноприводным автомобилем', 'полный привод', 'полным приводом', 'полный привод', 'полным приводом'],
        'подключаемый полный': ['part-time 4wd', 'подключаемый полный привод', 'подключаемым полным приводом', 'подключаемый полноприводный', 'подключаемым полноприводным', 'подключаемый полный привод', 'подключаемым полным приводом']
    }
    
    PRICE_CATEGORIES = {
        'бюджетный': ['до 500 тыс', 'до 500000', 'до 500к', 'до 500k'],
        'средний': ['500-1500 тыс', '500000-1500000', '500к-1500к'],
        'премиум': ['1500-3000 тыс', '1500000-3000000', '1500к-3000к'],
        'люкс': ['более 3000 тыс', 'более 3000000', 'более 3000к']
    }
    
    ENGINE_SIZES = {
        'малолитражный': ['до 1.0', 'до 1000', 'малый объем'],
        'средний': ['1.0-2.0', '1000-2000', 'средний объем'],
        'большой': ['более 2.0', 'более 2000', 'большой объем']
    }

    # Новые сущности для расширенных характеристик
    POWER_RANGES = {
        'до 100 л.с.': {'power_to': 100},
        '100-150 л.с.': {'power_from': 100, 'power_to': 150},
        '150-200 л.с.': {'power_from': 150, 'power_to': 200},
        '200-300 л.с.': {'power_from': 200, 'power_to': 300},
        'более 300 л.с.': {'power_from': 300},
        'слабый': {'power_to': 100},
        'средний': {'power_from': 100, 'power_to': 200},
        'мощный': {'power_from': 200}
    }
    
    ENGINE_VOLUME_RANGES = {
        'до 1.0 л': {'engine_vol_to': 1.0},
        '1.0-1.5 л': {'engine_vol_from': 1.0, 'engine_vol_to': 1.5},
        '1.5-2.0 л': {'engine_vol_from': 1.5, 'engine_vol_to': 2.0},
        '2.0-3.0 л': {'engine_vol_from': 2.0, 'engine_vol_to': 3.0},
        'более 3.0 л': {'engine_vol_from': 3.0},
        'малый объем': {'engine_vol_to': 1.5},
        'средний объем': {'engine_vol_from': 1.5, 'engine_vol_to': 2.5},
        'большой объем': {'engine_vol_from': 2.5}
    }
    
    OWNERS_COUNT = {
        'первый владелец': {'owners_count': 1},
        'второй владелец': {'owners_count': 2},
        'третий владелец': {'owners_count': 3},
        'более 3 владельцев': {'owners_count_from': 3},
        'один владелец': {'owners_count': 1},
        'два владельца': {'owners_count': 2},
        'три владельца': {'owners_count': 3}
    }
    
    STEERING_WHEEL_TYPES = {
        'левый': ['left', 'левый руль', 'левым рулем'],
        'правый': ['right', 'правый руль', 'правым рулем']
    }
    
    ACCIDENT_HISTORY = {
        'без аварий': ['no accidents', 'не битый', 'не аварийный', 'чистый'],
        'с авариями': ['with accidents', 'битый', 'аварийный', 'в авариях'],
        'незначительные повреждения': ['minor damage', 'легкие повреждения', 'царапины'],
        'серьезные повреждения': ['major damage', 'серьезные повреждения', 'сильно битый']
    }
    
    # Новые словари для характеристик автомобилей по ключевым словам
    SPEED_CHARACTERISTICS = {
        'быстрый': {'power_from': 200, 'acceleration_to': 6.0},
        'быстрая': {'power_from': 200, 'acceleration_to': 6.0},
        'быстрое': {'power_from': 200, 'acceleration_to': 6.0},
        'быстрые': {'power_from': 200, 'acceleration_to': 6.0},
        'медленный': {'power_to': 120, 'acceleration_from': 8.0},
        'медленная': {'power_to': 120, 'acceleration_from': 8.0},
        'медленное': {'power_to': 120, 'acceleration_from': 8.0},
        'медленные': {'power_to': 120, 'acceleration_from': 8.0},
        'скоростной': {'power_from': 250, 'acceleration_to': 5.0},
        'скоростная': {'power_from': 250, 'acceleration_to': 5.0},
        'скоростное': {'power_from': 250, 'acceleration_to': 5.0},
        'скоростные': {'power_from': 250, 'acceleration_to': 5.0},
        'тихоходный': {'power_to': 100, 'acceleration_from': 10.0},
        'тихоходная': {'power_to': 100, 'acceleration_from': 10.0},
        'тихоходное': {'power_to': 100, 'acceleration_from': 10.0},
        'тихоходные': {'power_to': 100, 'acceleration_from': 10.0},
        'динамичный': {'power_from': 180, 'acceleration_to': 7.0},
        'динамичная': {'power_from': 180, 'acceleration_to': 7.0},
        'динамичное': {'power_from': 180, 'acceleration_to': 7.0},
        'динамичные': {'power_from': 180, 'acceleration_to': 7.0},
        'резвый': {'power_from': 220, 'acceleration_to': 6.5},
        'резвая': {'power_from': 220, 'acceleration_to': 6.5},
        'резвое': {'power_from': 220, 'acceleration_to': 6.5},
        'резвые': {'power_from': 220, 'acceleration_to': 6.5},
        'проворный': {'power_from': 200, 'acceleration_to': 6.0},
        'проворная': {'power_from': 200, 'acceleration_to': 6.0},
        'проворное': {'power_from': 200, 'acceleration_to': 6.0},
        'проворные': {'power_from': 200, 'acceleration_to': 6.0}
    }
    
    PRICE_CHARACTERISTICS = {
        'дорогой': {'price_from': 3000000},
        'дешевый': {'price_to': 1500000},
        'бюджетный': {'price_to': 2000000},
        'премиум': {'price_from': 5000000},
        'люкс': {'price_from': 8000000},
        'эконом': {'price_to': 1000000},
        'доступный': {'price_to': 2500000},
        'недорогой': {'price_to': 1800000}
    }
    
    FUEL_EFFICIENCY_CHARACTERISTICS = {
        'экономичный': {'fuel_efficiency': 'high'},
        'экономичная': {'fuel_efficiency': 'high'},
        'экономичное': {'fuel_efficiency': 'high'},
        'экономичные': {'fuel_efficiency': 'high'},
        'неэкономичный': {'fuel_efficiency': 'low'},
        'неэкономичная': {'fuel_efficiency': 'low'},
        'неэкономичное': {'fuel_efficiency': 'low'},
        'неэкономичные': {'fuel_efficiency': 'low'},
        'прожорливый': {'fuel_efficiency': 'low'},
        'прожорливая': {'fuel_efficiency': 'low'},
        'прожорливое': {'fuel_efficiency': 'low'},
        'прожорливые': {'fuel_efficiency': 'low'},
        'экономный': {'fuel_efficiency': 'high'},
        'экономная': {'fuel_efficiency': 'high'},
        'экономное': {'fuel_efficiency': 'high'},
        'экономные': {'fuel_efficiency': 'high'},
        'жадный': {'fuel_efficiency': 'low'},
        'жадная': {'fuel_efficiency': 'low'},
        'жадное': {'fuel_efficiency': 'low'},
        'жадные': {'fuel_efficiency': 'low'},
        'расходный': {'fuel_efficiency': 'low'},
        'расходная': {'fuel_efficiency': 'low'},
        'расходное': {'fuel_efficiency': 'low'},
        'расходные': {'fuel_efficiency': 'low'}
    }
    
    ENGINE_SIZE_CHARACTERISTICS = {
        'маленький двигатель': {'engine_vol_from': 0.8, 'engine_vol_to': 1.4},
        'большой двигатель': {'engine_vol_from': 3.0, 'engine_vol_to': 8.0},
        'средний двигатель': {'engine_vol_from': 1.4, 'engine_vol_to': 3.0},
        'малолитражный': {'engine_vol_from': 0.8, 'engine_vol_to': 1.2},
        'многолитровый': {'engine_vol_from': 4.0, 'engine_vol_to': 8.0}
    }
    
    SPORT_CAR_CHARACTERISTICS = {
        'спорткар': {'power_from': 300, 'acceleration_to': 5.0, 'body_type': ['купе', 'кабриолет', 'родстер']},
        'спорткары': {'power_from': 300, 'acceleration_to': 5.0, 'body_type': ['купе', 'кабриолет', 'родстер']},
        'спортивный': {'power_from': 250, 'acceleration_to': 6.0},
        'гоночный': {'power_from': 400, 'acceleration_to': 4.0},
        'трековый': {'power_from': 350, 'acceleration_to': 4.5}
    }

    DB_PATH = r'E:\Users\diman\OneDrive\Документы\Рабочий стол\2\хрень — копия\instance\cars.db'

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self.DB_PATH
        self.dynamic_marks = set()
        self.dynamic_models = set()
        self._load_marks_models_from_db()

    def _load_marks_models_from_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT mark FROM car WHERE mark IS NOT NULL")
            marks1 = [row[0].strip().lower() for row in cursor.fetchall() if row[0]]
            cursor.execute("SELECT DISTINCT mark FROM used_car WHERE mark IS NOT NULL")
            marks2 = [row[0].strip().lower() for row in cursor.fetchall() if row[0]]
            self.dynamic_marks = set(marks1 + marks2)
            cursor.execute("SELECT DISTINCT model FROM car WHERE model IS NOT NULL")
            models1 = [row[0].strip().lower() for row in cursor.fetchall() if row[0]]
            cursor.execute("SELECT DISTINCT model FROM used_car WHERE model IS NOT NULL")
            models2 = [row[0].strip().lower() for row in cursor.fetchall() if row[0]]
            self.dynamic_models = set(models1 + models2)
            conn.close()
        except Exception as e:
            print(f"[NERIntentClassifier] Ошибка при загрузке марок/моделей из БД: {e}")

    def _map_synonym(self, value: str, mapping: Dict[str, List[str]]) -> str:
        v = value.lower()
        for k, syns in mapping.items():
            if v == k or v in syns:
                return k
        return value
    
    def _fuzzy_match(self, query: str, candidates: List[str], threshold: float = 0.8) -> List[str]:
        """Улучшенный нечеткий поиск с использованием нескольких алгоритмов"""
        matches = []
        query_lower = query.lower().strip()
        
        for candidate in candidates:
            # Убеждаемся, что candidate - это строка
            if not isinstance(candidate, str):
                candidate = str(candidate)
            candidate_lower = candidate.lower().strip()
            
            # 1. Прямое совпадение
            if query_lower == candidate_lower:
                matches.append(candidate)
                continue
            
            # 2. Jaro-Winkler расстояние
            try:
                # Дополнительная проверка типов
                if not isinstance(query_lower, str):
                    query_lower = str(query_lower)
                if not isinstance(candidate_lower, str):
                    candidate_lower = str(candidate_lower)
                
                jaro_score = jellyfish.jaro_winkler_similarity(query_lower, candidate_lower)
                if jaro_score >= threshold:
                    matches.append(candidate)
                    continue
            except Exception:
                # Пропускаем этот алгоритм и продолжаем
                pass
            
            # 3. Расстояние Левенштейна
            try:
                levenshtein_dist = jellyfish.levenshtein_distance(query_lower, candidate_lower)
                max_len = max(len(query_lower), len(candidate_lower))
                if max_len > 0 and (1 - levenshtein_dist / max_len) >= threshold:
                    matches.append(candidate)
                    continue
            except Exception:
                # Пропускаем этот алгоритм и продолжаем
                pass
            
            # 4. Метод Soundex
            try:
                if jellyfish.soundex(query_lower) == jellyfish.soundex(candidate_lower):
                    matches.append(candidate)
                    continue
            except Exception:
                pass
            
            # 5. Метод Metaphone
            try:
                if jellyfish.metaphone(query_lower) == jellyfish.metaphone(candidate_lower):
                    matches.append(candidate)
                    continue
            except Exception:
                pass
            
            # 6. Нормализация и поиск похожих строк
            query_norm = self._normalize_text(query_lower)
            candidate_norm = self._normalize_text(candidate_lower)
            similar = get_close_matches(query_norm, [candidate_norm], n=1, cutoff=threshold)
            if similar:
                matches.append(candidate)
        
        return matches
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста для нечеткого поиска"""
        # Удаление специальных символов
        text = re.sub(r'[^\w\s]', '', text)
        # Нормализация пробелов
        text = re.sub(r'\s+', ' ', text).strip()
        # Транслитерация (если доступна)
        try:
            import transliterate
            if any(ord(c) > 127 for c in text):  # Есть кириллица
                text = transliterate.translit(text, 'ru', reversed=True)
        except ImportError:
            pass
        return text
    
    def _extract_options(self, query: str) -> List[str]:
        """Извлечение опций из запроса"""
        found_options = []
        ql = query.lower()
        
        # Исключаем короткие слова, которые могут быть моделями
        query_words = set(ql.split())
        short_words = {word for word in query_words if len(word) <= 3}
        
        for option, synonyms in self.POPULAR_OPTIONS.items():
            for synonym in synonyms:
                # Пропускаем коды опций (S524A и т.д.)
                if re.match(r'^[A-Z]\d+[A-Z]$', synonym):
                    continue
                    
                if re.search(rf'\b{re.escape(synonym)}\b', ql):
                    # Дополнительная проверка: не добавляем опции, если найдено только короткое слово
                    if len(synonym) > 3 or not any(word in short_words for word in synonyms):
                        found_options.append(option)
                        break
        
        return found_options
    
    def _extract_fuel_types(self, query: str) -> List[str]:
        """Извлечение типов топлива из запроса"""
        found_fuels = []
        ql = query.lower()
        
        # Исключаем короткие слова, которые могут быть брендами
        query_words = set(ql.split())
        short_words = {word for word in query_words if len(word) <= 4}
        
        for fuel_type, synonyms in self.FUEL_TYPES.items():
            for synonym in synonyms:
                if re.search(rf'\b{re.escape(synonym)}\b', ql):
                    # Дополнительная проверка: не добавляем типы топлива, если найдено только короткое слово
                    if len(synonym) > 4 or not any(word in short_words for word in synonyms):
                        found_fuels.append(fuel_type)
                        break
        
        return found_fuels
    
    def _fuzzy_extract_options(self, query: str) -> List[str]:
        """Нечеткий поиск опций"""
        found_options = []
        ql = query.lower()
        words = ql.split()
        
        # Исключаем слова, которые точно не являются опциями
        exclude_words = {'audi', 'a4', 'bmw', 'mercedes', 'toyota', 'honda', 'ford', 'volkswagen', 
                        'nissan', 'mazda', 'hyundai', 'kia', 'renault', 'skoda', 'chery', 'geely', 
                        'haval', 'lexus', 'porsche', 'subaru', 'suzuki', 'mitsubishi', 'peugeot', 
                        'citroen', 'fiat', 'opel', 'chevrolet', 'uaz', 'vaz', 'volvo', 'infiniti', 
                        'acura', 'tesla', 'bentley', 'bugatti', 'rolls-royce', 'mini', 'smart', 
                        'jac', 'exeed', 'dongfeng', 'byd', 'li', 'xpeng', 'zeekr', 'tank', 'jetour', 
                        'gac', 'aiways', 'nio', 'voyah', 'moskvich', 'evolute', 'genesis', 'ravon', 
                        'datsun', 'daewoo', 'great', 'wall', 'ssangyong', 'proton', 'saab', 'seat', 
                        'changan', 'faw', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 
                        'haima', 'hafei', 'foton', 'dfm', 'omoda', 'hozon', 'leapmotor', 'seres', 
                        'hongqi', 'swm', 'gwm', 'wuling', 'lynk', 'co', 'roewe', 'mg', 'maxus', 
                        'polestar', 'geometry', 'aito', 'avatr', 'arcfox', 'denza', 'im', 'rising', 
                        'auto', 'weltmeister', 'skywell', 'forthing'}
        
        for word in words:
            # Пропускаем исключенные слова
            if word in exclude_words:
                continue
                
            for option, synonyms in self.POPULAR_OPTIONS.items():
                # Прямое совпадение
                if word in synonyms:
                    found_options.append(option)
                    continue
                
                # Нечеткий поиск с более высоким порогом
                fuzzy_matches = self._fuzzy_match(word, synonyms, threshold=0.8)
                if fuzzy_matches:
                    # Дополнительная проверка: слово должно быть достаточно длинным
                    if len(word) >= 3:
                        found_options.append(option)
        
        return list(set(found_options))
    
    def _fuzzy_extract_fuel_types(self, query: str) -> List[str]:
        """Нечеткий поиск типов топлива"""
        found_fuels = []
        ql = query.lower()
        words = ql.split()
        
        # Исключаем слова, которые точно не являются типами топлива
        exclude_words = {'audi', 'a4', 'bmw', 'mercedes', 'toyota', 'honda', 'ford', 'volkswagen', 
                        'nissan', 'mazda', 'hyundai', 'kia', 'renault', 'skoda', 'chery', 'geely', 
                        'haval', 'lexus', 'porsche', 'subaru', 'suzuki', 'mitsubishi', 'peugeot', 
                        'citroen', 'fiat', 'opel', 'chevrolet', 'uaz', 'vaz', 'volvo', 'infiniti', 
                        'acura', 'tesla', 'bentley', 'bugatti', 'rolls-royce', 'mini', 'smart', 
                        'jac', 'exeed', 'dongfeng', 'byd', 'li', 'xpeng', 'zeekr', 'tank', 'jetour', 
                        'gac', 'aiways', 'nio', 'voyah', 'moskvich', 'evolute', 'genesis', 'ravon', 
                        'datsun', 'daewoo', 'great', 'wall', 'ssangyong', 'proton', 'saab', 'seat', 
                        'changan', 'faw', 'lifan', 'zotye', 'brilliance', 'baic', 'baw', 'jinbei', 
                        'haima', 'hafei', 'foton', 'dfm', 'omoda', 'hozon', 'leapmotor', 'seres', 
                        'hongqi', 'swm', 'gwm', 'wuling', 'lynk', 'co', 'roewe', 'mg', 'maxus', 
                        'polestar', 'geometry', 'aito', 'avatr', 'arcfox', 'denza', 'im', 'rising', 
                        'auto', 'weltmeister', 'skywell', 'forthing'}
        
        for word in words:
            # Пропускаем исключенные слова
            if word in exclude_words:
                continue
                
            for fuel_type, synonyms in self.FUEL_TYPES.items():
                # Прямое совпадение
                if word in synonyms:
                    found_fuels.append(fuel_type)
                    continue
                
                # Нечеткий поиск с более высоким порогом
                fuzzy_matches = self._fuzzy_match(word, synonyms, threshold=0.8)
                if fuzzy_matches:
                    # Дополнительная проверка: слово должно быть достаточно длинным
                    if len(word) >= 3:
                        found_fuels.append(fuel_type)
        
        return list(set(found_fuels))

    def extract_entities(self, query: str) -> Dict[str, Any]:
        # Убеждаемся, что query - это строка
        if not isinstance(query, str):
            query = str(query)
        entities = {}
        ql = query.lower()
        
        # Цвета с улучшенной обработкой синонимов
        found_colors = set()
        
        # Поиск по корневым словам (только если цвет действительно упоминается)
        for color in self.COLORS:
            # Прямое совпадение
            if re.search(rf'\b{re.escape(color)}\b', ql):
                found_colors.add(color)
                continue
            
            # Поиск по синонимам
            if color in self.COLOR_SYNONYMS:
                for syn in self.COLOR_SYNONYMS[color]:
                    if re.search(rf'\b{re.escape(syn)}\b', ql):
                        found_colors.add(color)
                        break
        
        # Нечеткий поиск для цветов (только для слов длиной > 3)
        words = ql.split()
        for word in words:
            if len(word) <= 3:  # Пропускаем короткие слова
                continue
                
            for color, syns in self.COLOR_SYNONYMS.items():
                # Более строгий нечеткий поиск
                fuzzy_matches = self._fuzzy_match(word, syns, threshold=0.8)
                if fuzzy_matches:
                    found_colors.add(color)
        
        if found_colors:
            # Дополнительная проверка: добавляем цвета только если они действительно упоминаются в запросе
            query_words = set(ql.split())
            valid_colors = []
            for color in found_colors:
                if color in query_words or any(str(syn).lower() in query_words for syn in self.COLOR_SYNONYMS.get(color, [])):
                    valid_colors.append(color)
            
            if valid_colors:
                entities['color'] = valid_colors if len(valid_colors) > 1 else valid_colors[0]
        
        # --- Опции ---
        found_options = self._extract_options(query)
        if found_options and len(found_options) > 0:
            # Дополнительная проверка: убеждаемся, что опции действительно присутствуют в запросе
            query_words = set(ql.split())
            valid_options = []
            for option in found_options:
                option_synonyms = self.POPULAR_OPTIONS.get(option, [])
                if any(str(syn).lower() in query_words for syn in option_synonyms if len(str(syn)) > 3):
                    valid_options.append(option)
            
            if valid_options:
                entities['option_description'] = valid_options
                print(f"[DEBUG] Found options: {valid_options}")
        
        # --- Типы топлива ---
        found_fuel_types = self._extract_fuel_types(query)
        if found_fuel_types and len(found_fuel_types) > 0:
            # Дополнительная проверка: убеждаемся, что типы топлива действительно присутствуют в запросе
            query_words = set(ql.split())
            valid_fuels = []
            for fuel in found_fuel_types:
                fuel_synonyms = self.FUEL_TYPES.get(fuel, [])
                if any(str(syn).lower() in query_words for syn in fuel_synonyms if len(str(syn)) > 4):
                    valid_fuels.append(fuel)
            
            if valid_fuels:
                entities['fuel_type'] = valid_fuels[0] if len(valid_fuels) == 1 else valid_fuels
                print(f"[DEBUG] Found fuel types: {valid_fuels}")
        
        # --- Нечеткий поиск для опций ---
        if not found_options:
            # ВРЕМЕННО ОТКЛЮЧАЕМ НЕЧЕТКИЙ ПОИСК ДЛЯ ОПЦИЙ
            # fuzzy_options = self._fuzzy_extract_options(query)
            # if fuzzy_options and len(fuzzy_options) > 0:
            #     # Дополнительная проверка: убеждаемся, что найденные опции действительно присутствуют в запросе
            #     query_words = set(ql.split())
            #     valid_options = []
            #     for option in fuzzy_options:
            #         option_synonyms = self.POPULAR_OPTIONS.get(option, [])
            #         if any(syn.lower() in query_words for syn in option_synonyms):
            #             valid_options.append(option)
            #     if valid_options:
            #         entities['option_description'] = valid_options
            #         print(f"[DEBUG] Found fuzzy options: {valid_options}")
            pass
        
        # --- Нечеткий поиск для типов топлива ---
        if not found_fuel_types:
            # ВРЕМЕННО ОТКЛЮЧАЕМ НЕЧЕТКИЙ ПОИСК ДЛЯ ТИПОВ ТОПЛИВА
            # fuzzy_fuels = self._fuzzy_extract_fuel_types(query)
            # if fuzzy_fuels and len(fuzzy_fuels) > 0:
            #     # Дополнительная проверка: убеждаемся, что найденные типы топлива действительно присутствуют в запросе
            #     query_words = set(ql.split())
            #     valid_fuels = []
            #     for fuel in fuzzy_fuels:
            #         fuel_synonyms = self.FUEL_TYPES.get(fuel, [])
            #         if any(syn.lower() in query_words for syn in fuel_synonyms):
            #             valid_fuels.append(fuel)
            #     if valid_fuels:
            #         entities['fuel_type'] = valid_fuels[0] if len(valid_fuels) == 1 else valid_fuels
            #         print(f"[DEBUG] Found fuzzy fuel types: {valid_fuels}")
            pass
        
        # --- Марки ---
        found_brands = []
        found_brand_synonyms = set()
        
        # Улучшенный поиск множественных марок для сравнений
        # Паттерны для составных названий (марка + модель)
        comparison_patterns = [
            r'([a-zA-Z]+)\s+([a-zA-Z0-9]+)\s+и\s+([a-zA-Z]+)\s+([a-zA-Z0-9]+)',  # BMW X3 и Haval Jolion
            r'([a-zA-Z]+)\s+([a-zA-Z0-9]+)\s+или\s+([a-zA-Z]+)\s+([a-zA-Z0-9]+)',  # BMW X3 или Haval Jolion
            r'([a-zA-Z]+)\s+([a-zA-Z0-9]+),\s*([a-zA-Z]+)\s+([a-zA-Z0-9]+)',  # BMW X3, Haval Jolion
        ]
        
        # Сначала ищем составные названия
        for pattern in comparison_patterns:
            matches = re.findall(pattern, ql)
            for match in matches:
                brand1, model1, brand2, model2 = match
                # Проверяем, что это действительно марки
                all_marks = list(self.MARKS) + list(self.dynamic_marks)
                if brand1.lower() in [m.lower() for m in all_marks]:
                    found_brands.append(brand1.lower())
                if brand2.lower() in [m.lower() for m in all_marks]:
                    found_brands.append(brand2.lower())
        
        # Простые паттерны для одиночных марок
        brand_patterns = [
            r'([\w\-]+)\s+и\s+([\w\-]+)',
            r'([\w\-]+)\s+или\s+([\w\-]+)',
            r'([\w\-]+),\s*([\w\-]+)',
        ]
        for pattern in brand_patterns:
            matches = re.findall(pattern, ql)
            for match in matches:
                for brand in match:
                    all_marks = list(self.dynamic_marks) + list(self.MARKS)
                    if brand.lower() in [m.lower() for m in all_marks]:
                        found_brands.append(brand.lower())
        
        # 1. По динамическому списку из БД (только точные совпадения)
        for m in self.dynamic_marks:
            if re.search(rf'\b{re.escape(m)}\b', ql):
                if m.lower() not in found_brands:
                    found_brands.append(m.lower())
        
        # 2. По синонимам (добавляем оба: синоним и основной бренд)
        for mark, syns in self.MARK_SYNONYMS.items():
            for syn in syns:
                if re.search(rf'\b{re.escape(syn)}\b', ql):
                    found_brands.append(syn.lower())
                    found_brand_synonyms.add(syn.lower())
        
        # 2.5. Нечеткий поиск для синонимов (только для слов длиной > 3)
        words = ql.split()
        for word in words:
            if len(word) <= 3:  # Пропускаем короткие слова
                continue
                
            # Ищем похожие синонимы с более строгим порогом
            for mark, syns in self.MARK_SYNONYMS.items():
                fuzzy_matches = self._fuzzy_match(word, syns, threshold=0.8)
                if fuzzy_matches:
                    found_brands.extend([m.lower() for m in fuzzy_matches])
                    found_brand_synonyms.update([m.lower() for m in fuzzy_matches])
        
        # 2.6. Поиск по русским синонимам
        for word in words:
            for mark, syns in self.MARK_SYNONYMS.items():
                if word.lower() in [s.lower() for s in syns]:
                    found_brands.append(mark.lower())
                    found_brand_synonyms.add(word.lower())
        
        # 2.7. Поиск по русским названиям марок
        for word in words:
            for mark, syns in MANUAL_MARK_SYNONYMS.items():
                if word.lower() in [s.lower() for s in syns] or word.lower() == mark.lower():
                    found_brands.append(mark.lower())
                    found_brand_synonyms.add(word.lower())
        
        # 3. По статическому списку (только точные совпадения)
        for m in self.MARKS:
            if re.search(rf'\b{re.escape(m)}\b', ql):
                if m.lower() not in found_brands:
                    found_brands.append(m.lower())
        
        # 3.5. Поиск по русским названиям моделей
        found_models = []
        for word in words:
            for model, syns in MANUAL_MODEL_SYNONYMS.items():
                if word.lower() in [s.lower() for s in syns] or word.lower() == model.lower():
                    found_models.append(model.lower())
        
        # 4. Добавляем синонимы, если они явно встречаются
        for syn in found_brand_synonyms:
            if syn.lower() not in found_brands:
                found_brands.append(syn.lower())
        # Приводим к структуре {'en': ..., 'ru': ...}
        brand_results = []
        for b in found_brands:
            en = None
            ru = None
            for mark, syns in self.MARK_SYNONYMS.items():
                if b == mark:
                    ru = mark
                    en = syns[0] if syns else mark
                elif b in syns:
                    en = b
                    ru = mark
            # Исправление: en — английское, ru — русское
            # Если en содержит только кириллицу, а ru только латиницу — меняем местами
            cyrillic = re.compile(r'[а-яё]', re.IGNORECASE)
            latin = re.compile(r'[a-z]', re.IGNORECASE)
            if en and cyrillic.search(en) and ru and latin.search(ru):
                en, ru = ru, en
            # Если только одно найдено, дублируем
            if not en:
                en = ru if ru else b
            if not ru:
                ru = en if en else b
            # Не добавлять дубликаты
            if not any(x['en'] == en and x['ru'] == ru for x in brand_results):
                brand_results.append({'en': en, 'ru': ru})
        if brand_results:
            # Дополнительная проверка: добавляем бренды только если они действительно упоминаются в запросе
            query_words = set(ql.split())
            valid_brands = []
            for brand in brand_results:
                brand_en = brand.get('en', '').lower()
                brand_ru = brand.get('ru', '').lower()
                if (brand_en in query_words or brand_ru in query_words or 
                    any(str(syn).lower() in query_words for syn in self.MARK_SYNONYMS.get(brand_ru, []))):
                    valid_brands.append(brand)
            
            if valid_brands:
                entities['brand'] = valid_brands if len(valid_brands) > 1 else valid_brands[0]

        # --- Модели ---
        found_models = []
        
        # Проверяем, есть ли в запросе ценовые выражения, чтобы избежать извлечения цифр как моделей
        price_indicators = ['до', 'от', 'не дороже', 'дешевле', 'дороже', 'за', 'в пределах', 'примерно', 'около', 'миллион', 'миллионов', 'млн', 'тысяч', 'тыс', 'руб', '₽']
        has_price_context = any(indicator in ql for indicator in price_indicators)
        
        # Если есть ценовой контекст, проверяем, не является ли цифра частью цены
        if has_price_context:
            # Ищем цифры в контексте цен
            price_pattern = re.compile(r'(\d+)\s*(?:млн|миллион|миллионов|тыс|тысяч|руб|₽)')
            price_matches = price_pattern.findall(ql)
            
            # Если найдены цифры в ценовом контексте, не извлекаем их как модели
            if price_matches:
                # Пропускаем извлечение моделей, если цифры являются частью цены
                pass
            else:
                # Извлекаем модели только если нет ценового контекста
                # Сначала ищем в MODEL_SYNONYMS для получения канонических значений
                try:
                    from brand_synonyms import MODEL_SYNONYMS
                    query_words = set(ql.split())
                    for model_key, model_value in MODEL_SYNONYMS.items():
                        # MODEL_SYNONYMS имеет структуру {'икс3': 'X3'}, а не {'икс3': ['x3', 'x-3']}
                        if re.search(rf'\b{re.escape(model_key)}\b', ql):
                            # Дополнительная проверка: убеждаемся, что модель действительно упоминается в запросе
                            if model_key.lower() in query_words:
                                found_models.append(model_value)  # Используем значение, а не ключ
                                break
                except ImportError:
                    pass
        
                # Затем ищем в MANUAL_MODEL_SYNONYMS для дополнительных вариантов
                query_words = set(ql.split())
                for model, syns in MANUAL_MODEL_SYNONYMS.items():
                    for syn in syns:
                        if re.search(rf'\b{re.escape(syn)}\b', ql):
                            # Дополнительная проверка: убеждаемся, что модель действительно упоминается в запросе
                            if any(syn.lower() in query_words for syn in syns):
                                found_models.append(model)
                                break
        else:
            # Если нет ценового контекста, извлекаем модели как обычно
            # Сначала ищем в MODEL_SYNONYMS для получения канонических значений
            try:
                from brand_synonyms import MODEL_SYNONYMS
                query_words = set(ql.split())
                for model_key, model_value in MODEL_SYNONYMS.items():
                    # MODEL_SYNONYMS имеет структуру {'икс3': 'X3'}, а не {'икс3': ['x3', 'x-3']}
                    if re.search(rf'\b{re.escape(model_key)}\b', ql):
                        # Дополнительная проверка: убеждаемся, что модель действительно упоминается в запросе
                        if model_key.lower() in query_words:
                            found_models.append(model_value)  # Используем значение, а не ключ
                            break
            except ImportError:
                pass
    
        # Затем ищем в MANUAL_MODEL_SYNONYMS для дополнительных вариантов
        query_words = set(ql.split())
        for model, syns in MANUAL_MODEL_SYNONYMS.items():
            for syn in syns:
                if re.search(rf'\b{re.escape(syn)}\b', ql):
                    # Дополнительная проверка: убеждаемся, что модель действительно упоминается в запросе
                    if any(syn.lower() in query_words for syn in syns):
                        found_models.append(model)
                        break
        
        # Убираем дубликаты и оставляем только канонические значения
        unique_models = []
        for m in found_models:
            if m not in unique_models:
                unique_models.append(m)
        
        if unique_models:
            # Если есть несколько моделей, выбираем каноническое значение (с заглавными буквами)
            if len(unique_models) > 1:
                # Ищем каноническое значение (с заглавными буквами)
                canonical_model = None
                for model in unique_models:
                    if model.isupper() or (len(model) > 1 and model[0].isupper() and any(c.isupper() for c in model[1:])):
                        canonical_model = model
                        break
                
                if canonical_model:
                    entities['model'] = canonical_model
                else:
                    entities['model'] = unique_models[0]
            else:
                entities['model'] = unique_models[0]

        # --- ПРОБЕГ (обрабатываем ПЕРЕД ценами) ---
        mileage_patterns = [
            (r'от\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage_from'),
            (r'до\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage_to'),
            (r'не больше\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage_to'),
            (r'меньше\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage_to'),
            (r'больше\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage_from'),
            (r'примерно\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage'),
            (r'около\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage'),
            (r'(\d+\.?\d*)\s*тысяч\s*км', 'mileage'),
            (r'(\d+\.?\d*)\s*тыс\s*км', 'mileage'),
            (r'пробег\s*(\d+\.?\d*)\s*(?:км|тыс|к)', 'mileage'),
            (r'(\d+\.?\d*)\s*тысяч', 'mileage'),
            (r'(\d+\.?\d*)\s*тыс', 'mileage'),
        ]
        mileage_value = None
        for pat, key in mileage_patterns:
            m = re.search(pat, ql)
            if m:
                val = self._parse_mileage(m.group(1))
                if val:
                    entities[key] = val
                    mileage_value = val
                    break

        # --- ЦЕНА ---
        price_patterns = [
            (r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(?:руб|₽|тыс|к|млн)', 'price_range'),
            (r'от\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_from'),
            (r'до\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_to'),
            (r'не дороже\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_to'),
            (r'дешевле\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_to'),
            (r'дороже\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_from'),
            (r'за\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price'),
            (r'в пределах\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price_to'),
            (r'примерно\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price'),
            (r'около\s*(\d+\.?\d*\s*(?:руб|₽|тыс|к|млн|миллион|миллионов)?)', 'price'),
            (r'(\d+\.?\d*\s*миллион)', 'price'),
            (r'(\d+\.?\d*\s*миллионов)', 'price'),
            (r'(\d+\.?\d*\s*млн)', 'price'),
            (r'(\d+\.?\d*\s*тысяч)', 'price'),
            (r'(\d+\.?\d*\s*тыс)', 'price'),
        ]
        price_value = None
        for pat, key in price_patterns:
            if key == 'price_range':
                m = re.search(pat, ql)
                if m:
                    val1 = self._parse_price(m.group(1) + ' млн' if 'млн' in m.group(0) or 'миллион' in m.group(0) or 'миллионов' in m.group(0) else m.group(1))
                    val2 = self._parse_price(m.group(2) + ' млн' if 'млн' in m.group(0) or 'миллион' in m.group(0) or 'миллионов' in m.group(0) else m.group(2))
                    if val1 and val2:
                        entities['price_from'] = val1
                        entities['price_to'] = val2
                        entities['price'] = val2
                        price_value = val2
                        break
        for pat, key in price_patterns:
            if key != 'price_range':
                m = re.search(pat, ql)
                if m:
                    # Получаем полную строку для правильного парсинга
                    full_match = m.group(0)
                    number_part = m.group(1)
                    
                    # Если это паттерн с "до", "от", "за" и т.д., нужно восстановить полную строку
                    if key in ['price_to', 'price_from', 'price'] and any(prefix in full_match for prefix in ['до', 'от', 'за', 'не дороже', 'дешевле', 'дороже', 'в пределах', 'примерно', 'около']):
                        # Извлекаем число и единицу измерения
                        unit_match = re.search(rf'{re.escape(number_part)}\s*((?:руб|₽|тыс|к|млн|миллион|миллионов))', full_match)
                        if unit_match:
                            price_string = number_part + ' ' + unit_match.group(1)
                        else:
                            price_string = number_part
                    else:
                        price_string = number_part
                    
                    val = self._parse_price(price_string)
                    # Не добавлять price, если это дублирует пробег или если есть price_to в числах (например, 3)
                    if val and key not in entities and (not mileage_value or val != mileage_value):
                        # Если price_to — это просто число (например, 3), а price — в рублях (3000000), оставлять только price
                        if key == 'price_to' and 'price' in entities and val < 10000 and entities['price'] > 10000:
                            continue
                        entities[key] = val
                        if key == 'price' or key == 'price_to':
                            price_value = val
        if 'price_from' in entities and 'price_to' in entities and 'price' not in entities:
            entities['price'] = entities['price_to']
        if 'price' in entities and 'price_to' not in entities and 'price_from' not in entities:
            price_value = entities['price']
        # --- Фильтрация лишних ценовых сущностей и дублирования с пробегом ---
        # Если есть пробег и цена совпадает с пробегом, удаляем цену
        if 'mileage_to' in entities and 'price' in entities and entities['mileage_to'] == entities['price']:
            del entities['price']
        if 'mileage_to' in entities and 'price_to' in entities and entities['mileage_to'] == entities['price_to']:
            del entities['price_to']
        if 'mileage' in entities and 'price' in entities and entities['mileage'] == entities['price']:
            del entities['price']
        if 'mileage' in entities and 'price_to' in entities and entities['mileage'] == entities['price_to']:
            del entities['price_to']
        # Если есть price и price_to, и price_to подозрительно мал, удаляем price_to
        if 'price' in entities and 'price_to' in entities and entities['price_to'] < 10000 and entities['price'] > 10000:
            del entities['price_to']

        # --- Год выпуска ---
        year_patterns = [
            (r'от\s*(19\d{2}|20\d{2})', 'year_from'),
            (r'с\s*(19\d{2}|20\d{2})', 'year_from'),
            (r'до\s*(19\d{2}|20\d{2})', 'year_to'),
            (r'старше\s*(19\d{2}|20\d{2})', 'year_from'),
            (r'новее\s*(19\d{2}|20\d{2})', 'year_from'),
            (r'младше\s*(19\d{2}|20\d{2})', 'year_to'),
            (r'за\s*(19\d{2}|20\d{2})', 'year'),
            (r'примерно\s*(19\d{2}|20\d{2})', 'year'),
            (r'около\s*(19\d{2}|20\d{2})', 'year'),
            (r'(19\d{2}|20\d{2})\s+года', 'year'),
            (r'(19\d{2}|20\d{2})\s+г', 'year'),
            (r'года\s+(19\d{2}|20\d{2})', 'year'),
            (r'г\s+(19\d{2}|20\d{2})', 'year'),
            (r'(19\d{2}|20\d{2})\s+выпуска', 'year'),
            (r'выпуска\s+(19\d{2}|20\d{2})', 'year'),
            (r'(19\d{2}|20\d{2})\s+производства', 'year'),
            (r'производства\s+(19\d{2}|20\d{2})', 'year'),
            (r'(19\d{2}|20\d{2})\s+год', 'year'),
            (r'год\s+(19\d{2}|20\d{2})', 'year'),
            (r'(19\d{2}|20\d{2})\s+модель', 'year'),
            (r'модель\s+(19\d{2}|20\d{2})', 'year')
        ]
        year_value = None
        for pat, key in year_patterns:
            m = re.search(pat, ql)
            if m:
                val = int(m.group(1))
                entities[key] = val
                year_value = val
        if 'year_from' in entities and 'year_to' in entities and 'year' not in entities:
            entities['year'] = entities['year_to']
        if 'year' not in entities and year_value:
            entities['year'] = year_value

        # Тип кузова
        for k, v in self.BODY_TYPES.items():
            if re.search(rf'\b{k}\b', ql):
                entities['body_type'] = self._map_synonym(v, self.BODY_TYPE_SYNONYMS)
                break
        for body, syns in self.BODY_TYPE_SYNONYMS.items():
            for syn in syns:
                if re.search(rf'\b{syn}\b', ql):
                    entities['body_type'] = body
                    break
        # Маппинг: маленькая машина → body_type IN ('хэтчбек', 'купе')
        if re.search(r'маленьк(ая|ий|ое|ие|ую|им|ом|их|ими)?\s+машин', ql):
            entities['body_type'] = ['хэтчбек', 'купе']
        # Маппинг: компактная/городская машина → body_type IN ('хэтчбек', 'купе', 'лифтбек')
        if re.search(r'(компактн(ая|ый|ое|ие|ую|им|ом|их|ими)?|городск(ая|ой|ое|ие|ую|им|ом|их|ими)?)\s+машин', ql):
            entities['body_type'] = ['хэтчбек', 'купе', 'лифтбек']
        # Маппинг: универсальная/пассажирская машина → body_type IN ('универсал', 'минивэн', 'микроавтобус')
        if re.search(r'(универсальн(ая|ый|ое|ие|ую|им|ом|их|ими)?|пассажирск(ая|ий|ое|ие|ую|им|ом|их|ими)?)\s+машин', ql):
            entities['body_type'] = ['универсал', 'минивэн', 'микроавтобус']
        # Маппинг: для большой семьи/много детей/много пассажиров → body_type IN ('минивэн', 'микроавтобус', 'универсал')
        if re.search(r'для\s+(больш(ой|ой семьи)|много\s+детей|много\s+пассажиров|семьи|путешествий\s+семьёй)', ql):
            entities['body_type'] = ['минивэн', 'микроавтобус', 'универсал']
        # Маппинг: для дальних поездок/путешествий → body_type IN ('универсал', 'внедорожник', 'минивэн')
        if re.search(r'для\s+(дальних\s+поездок|путешеств(ий|ия|овать|у|ам|ах))', ql):
            entities['body_type'] = ['универсал', 'внедорожник', 'минивэн']
        # Маппинг: для перевозки/рабочая/грузовая машина → body_type IN ('фургон', 'пикап', 'универсал', 'микроавтобус')
        if re.search(r'(для\s+перевозки|рабоч(ая|ий|ее|ие|ую|им|ом|их|ими)?\s+машин|грузов(ая|ой|ое|ие|ую|им|ом|их|ими)?\s+машин)', ql):
            entities['body_type'] = ['фургон', 'пикап', 'универсал', 'микроавтобус']
        # Маппинг: спортивная/для активного отдыха → body_type IN ('купе', 'кабриолет', 'родстер')
        if re.search(r'(спортивн(ая|ый|ое|ие|ую|им|ом|их|ими)?|для\s+активного\s+отдыха)', ql):
            entities['body_type'] = ['купе', 'кабриолет', 'родстер']
        # Маппинг: для дачи/для детей/для поездок за город/для рыбалки/для охоты → body_type IN ('универсал', 'внедорожник', 'минивэн')
        if re.search(r'для\s+(дачи|детей|поездок\s+за\s+город|рыбалки|охоты)', ql):
            entities['body_type'] = ['универсал', 'внедорожник', 'минивэн']
        # Маппинг: для такси/для бизнеса/для работы/для перевозки пассажиров → body_type IN ('седан', 'универсал', 'минивэн')
        if re.search(r'для\s+(такси|бизнеса|работы|перевозки\s+пассажиров)', ql):
            entities['body_type'] = ['седан', 'универсал', 'минивэн']
        # Маппинг: просторный/вместительный/много места/много багажа/большой багажник → body_type IN ('универсал', 'минивэн', 'микроавтобус', 'внедорожник')
        if re.search(r'(просторн(ый|ая|ое|ие|ую|им|ом|их|ими)?|вместительн(ый|ая|ое|ие|ую|им|ом|их|ими)?|много\s+места|много\s+багажа|больш(ой|ой\s+багажник))', ql):
            entities['body_type'] = ['универсал', 'минивэн', 'микроавтобус', 'внедорожник']
        # Маппинг: семиместный/8 мест/9 мест/10 мест → body_type IN ('минивэн', 'микроавтобус', 'универсал')
        if re.search(r'(семиместн(ый|ая|ое|ие|ую|им|ом|их|ими)?|8\s*мест|9\s*мест|10\s*мест)', ql):
            entities['body_type'] = ['минивэн', 'микроавтобус', 'универсал']

        # --- Маппинги по количеству человек/мест/пассажиров ---
        # для 1 человека/1 пассажира/1 место → купе
        if re.search(r'(для\s*1\s*(человека|пассажир))|(1\s*(мест|пассажир))', ql):
            # Для одного — только купе
            entities['body_type'] = 'купе'  # 1 человек
        # для 2 человек/2 пассажиров/2 места → купе, кабриолет
        if re.search(r'(для\s*2\s*(человек|пассажир))|(2\s*(мест|пассажир))', ql):
            entities['body_type'] = ['купе', 'кабриолет']  # 2 человека
        # для 3 человек/3 пассажиров/3 места → хэтчбек, купе
        if re.search(r'(для\s*3\s*(человек|пассажир))|(3\s*(мест|пассажир))', ql):
            entities['body_type'] = ['хэтчбек', 'купе']  # 3 человека
        # для 4 человек/4 пассажиров/4 места → седан, хэтчбек, купе
        if re.search(r'(для\s*4\s*(человек|пассажир))|(4\s*(мест|пассажир))', ql):
            entities['body_type'] = ['седан', 'хэтчбек', 'купе']  # 4 человека
        # для 5 человек/5 пассажиров/5 мест → седан, хэтчбек, универсал, кроссовер
        if re.search(r'(для\s*5\s*(человек|пассажир))|(5\s*(мест|пассажир))', ql):
            entities['body_type'] = ['седан', 'хэтчбек', 'универсал', 'кроссовер']  # 5 человек
        # для 6 человек/6 пассажиров/6 мест → минивэн, универсал, внедорожник
        if re.search(r'(для\s*6\s*(человек|пассажир))|(6\s*(мест|пассажир))', ql):
            entities['body_type'] = ['минивэн', 'универсал', 'внедорожник']  # 6 человек
        # для 7 человек/7 пассажиров/7 мест → минивэн, микроавтобус, универсал
        if re.search(r'(для\s*7\s*(человек|пассажир))|(7\s*(мест|пассажир))', ql):
            entities['body_type'] = ['минивэн', 'микроавтобус', 'универсал']  # 7 человек
        # для 8 человек/8 пассажиров/8 мест → микроавтобус, минивэн
        if re.search(r'(для\s*8\s*(человек|пассажир))|(8\s*(мест|пассажир))', ql):
            entities['body_type'] = ['микроавтобус', 'минивэн']  # 8 человек
        # для 9 человек/9 пассажиров/9 мест → микроавтобус
        if re.search(r'(для\s*9\s*(человек|пассажир))|(9\s*(мест|пассажир))', ql):
            entities['body_type'] = ['микроавтобус']  # 9 человек
        # для 10 человек/10 пассажиров/10 мест → микроавтобус
        if re.search(r'(для\s*10\s*(человек|пассажир))|(10\s*(мест|пассажир))', ql):
            entities['body_type'] = ['микроавтобус']  # 10 человек

        # Количество мест
        match = re.search(r'(\d+)\s*мест', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Количество мест с "пассажирами"
        match = re.search(r'(\d+)\s*пассажир', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Количество мест с "человек"
        match = re.search(r'(\d+)\s*человек', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Количество мест с "людей"
        match = re.search(r'(\d+)\s*людей', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Количество мест с "для"
        match = re.search(r'для\s*(\d+)\s*(?:человек|людей|пассажир)', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Количество мест с "на"
        match = re.search(r'на\s*(\d+)\s*мест', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Специальные случаи
        if re.search(r'одного человек', ql):
            entities['seats'] = 1
        
        # Прилагательные с числительными (5-местный, пятиместный)
        match = re.search(r'(\d+)-местн', ql)
        if match:
            entities['seats'] = int(match.group(1))
        
        # Словесные числительные для мест
        seats_words = {
            'одноместн': 1, 'двухместн': 2, 'трехместн': 3, 'четырехместн': 4,
            'пятиместн': 5, 'шестиместн': 6, 'семиместн': 7, 'восьмиместн': 8,
            'девятиместн': 9, 'десятиместн': 10,
            'одно-местн': 1, 'двух-местн': 2, 'трех-местн': 3, 'четырех-местн': 4,
            'пяти-местн': 5, 'шести-местн': 6, 'семи-местн': 7, 'восьми-местн': 8,
            'девяти-местн': 9, 'десяти-местн': 10
        }
        
        for word, seats_count in seats_words.items():
            if word in ql:
                entities['seats'] = seats_count
                break
        
        # Словесные числительные (пять, пяти, пятью)
        number_words = {
            'один': 1, 'одного': 1, 'одному': 1, 'одним': 1, 'одном': 1,
            'два': 2, 'двух': 2, 'двум': 2, 'двумя': 2, 'двух': 2,
            'три': 3, 'трех': 3, 'трем': 3, 'тремя': 3, 'трех': 3,
            'четыре': 4, 'четырех': 4, 'четырем': 4, 'четырьмя': 4, 'четырех': 4,
            'пять': 5, 'пяти': 5, 'пятью': 5, 'пяти': 5,
            'шесть': 6, 'шести': 6, 'шестью': 6, 'шести': 6,
            'семь': 7, 'семи': 7, 'семью': 7, 'семи': 7,
            'восемь': 8, 'восьми': 8, 'восемью': 8, 'восьми': 8,
            'девять': 9, 'девяти': 9, 'девятью': 9, 'девяти': 9,
            'десять': 10, 'десяти': 10, 'десятью': 10, 'десяти': 10
        }
        
        # Поиск словесных числительных в контексте мест
        for word, number in number_words.items():
            if re.search(rf'\b{word}\b.*мест', ql) or re.search(rf'мест.*\b{word}\b', ql):
                entities['seats'] = number
                break
        
        # Дополнительные паттерны для "для X человек/пассажиров"
        for word, number in number_words.items():
            # "для пяти человек", "для семи пассажиров"
            if re.search(rf'для\s+{word}\s+(?:человек|пассажир)', ql):
                entities['seats'] = number
                break
            # "машина для пяти человек", "авто для семи пассажиров"
            if re.search(rf'(?:машин|авто|автомобиль).*для\s+{word}\s+(?:человек|пассажир)', ql):
                entities['seats'] = number
                break
        
        # --- Новые сущности ---
        
        # Состояние автомобиля (новый/б/у)
        for state_key, state_value in self.CAR_STATES.items():
            if re.search(rf'\b{re.escape(state_key)}\b', ql):
                entities['state'] = state_value
                break
        
        # Популярные опции
        found_options = []
        for option_name, option_codes in self.POPULAR_OPTIONS.items():
            for code_or_synonym in option_codes:
                if re.search(rf'\b{re.escape(code_or_synonym)}\b', ql):
                    found_options.append(option_codes[0])  # Берем первый код как основной
                    break
        if found_options:
            entities['option_codes'] = found_options
        
        # Диапазоны пробега (текстовые)
        for range_name, range_values in self.MILEAGE_RANGES.items():
            if re.search(rf'\b{re.escape(range_name)}\b', ql):
                entities.update(range_values)
                break
        
        # Популярные сценарии
        for scenario_name, scenario_keywords in self.POPULAR_SCENARIOS.items():
            for keyword in scenario_keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', ql):
                    entities['scenario'] = scenario_name
                    break
            if 'scenario' in entities:
                break
        
        # Дилер (простой поиск по ключевым словам)
        dealer_patterns = [
            r'дилер\s+([а-яё\s]+)',
            r'в\s+([а-яё\s]+)\s+дилер',
            r'у\s+([а-яё\s]+)\s+дилер'
        ]
        for pattern in dealer_patterns:
            m = re.search(pattern, ql)
            if m:
                dealer_name = m.group(1).strip()
                if len(dealer_name) > 2:  # Минимальная длина названия дилера
                    entities['dealer'] = dealer_name
                    break
        
        # Тип топлива
        for fuel_type, synonyms in self.FUEL_TYPES.items():
            for synonym in synonyms:
                if re.search(rf'\b{re.escape(synonym)}\b', ql):
                    entities['fuel_type'] = fuel_type
                    break
            if 'fuel_type' in entities:
                break
        
        # Тип трансмиссии
        for transmission_type, synonyms in self.TRANSMISSION_TYPES.items():
            for synonym in synonyms:
                # Для многословных фраз убираем границы слов
                if ' ' in synonym:
                    if synonym in ql:
                        entities['transmission'] = transmission_type
                        break
                else:
                    if re.search(rf'\b{re.escape(synonym)}\b', ql):
                        entities['transmission'] = transmission_type
                        break
            if 'transmission' in entities:
                break
        
        # Тип привода
        for drive_type, synonyms in self.DRIVE_TYPES.items():
            for synonym in synonyms:
                # Для многословных фраз убираем границы слов
                if ' ' in synonym:
                    if synonym in ql:
                        entities['drive_type'] = drive_type
                        break
                else:
                    if re.search(rf'\b{re.escape(synonym)}\b', ql):
                        entities['drive_type'] = drive_type
                        break
            if 'drive_type' in entities:
                break
        
        # Категория цены
        for price_category, patterns in self.PRICE_CATEGORIES.items():
            for pattern in patterns:
                if re.search(rf'\b{re.escape(pattern)}\b', ql):
                    entities['price_category'] = price_category
                    break
            if 'price_category' in entities:
                break
        
        # Объем двигателя
        for engine_size, patterns in self.ENGINE_SIZES.items():
            for pattern in patterns:
                if re.search(rf'\b{re.escape(pattern)}\b', ql):
                    entities['engine_size'] = engine_size
                    break
            if 'engine_size' in entities:
                break
        
        # Мощность двигателя
        for power_range, power_values in self.POWER_RANGES.items():
            if re.search(rf'\b{re.escape(power_range)}\b', ql):
                entities.update(power_values)
                break
        
        # Объем двигателя (диапазоны)
        for volume_range, volume_values in self.ENGINE_VOLUME_RANGES.items():
            if re.search(rf'\b{re.escape(volume_range)}\b', ql):
                entities.update(volume_values)
                break
        
        # Количество владельцев
        for owners_range, owners_values in self.OWNERS_COUNT.items():
            if re.search(rf'\b{re.escape(owners_range)}\b', ql):
                entities.update(owners_values)
                break
        
        # Тип руля
        for steering_type, synonyms in self.STEERING_WHEEL_TYPES.items():
            for synonym in synonyms:
                if re.search(rf'\b{re.escape(synonym)}\b', ql):
                    entities['steering_wheel'] = steering_type
                    break
            if 'steering_wheel' in entities:
                break
        
        # История аварий
        for accident_type, synonyms in self.ACCIDENT_HISTORY.items():
            for synonym in synonyms:
                if re.search(rf'\b{re.escape(synonym)}\b', ql):
                    entities['accident_history'] = accident_type
                    break
            if 'accident_history' in entities:
                break
        
        # Скоростные характеристики
        for speed_char, speed_values in self.SPEED_CHARACTERISTICS.items():
            if re.search(rf'\b{re.escape(speed_char)}\b', ql):
                entities.update(speed_values)
                break
            # Дополнительная проверка для частичного совпадения (например, "медленную" содержит "медленн")
            elif re.search(rf'\b{re.escape(speed_char[:6])}\w*', ql):
                entities.update(speed_values)
                break
        
        # Ценовые характеристики
        for price_char, price_values in self.PRICE_CHARACTERISTICS.items():
            if re.search(rf'\b{re.escape(price_char)}\b', ql):
                entities.update(price_values)
                break
        
        # Характеристики расхода топлива
        for fuel_char, fuel_values in self.FUEL_EFFICIENCY_CHARACTERISTICS.items():
            if re.search(rf'\b{re.escape(fuel_char)}\b', ql):
                entities.update(fuel_values)
                break
            # Дополнительная проверка для частичного совпадения
            elif re.search(rf'\b{re.escape(fuel_char[:6])}\w*', ql):
                entities.update(fuel_values)
                break
        
        # Характеристики размера двигателя
        for engine_char, engine_values in self.ENGINE_SIZE_CHARACTERISTICS.items():
            if re.search(rf'\b{re.escape(engine_char)}\b', ql):
                entities.update(engine_values)
                break
        
        # Спортивные характеристики
        for sport_char, sport_values in self.SPORT_CAR_CHARACTERISTICS.items():
            if re.search(rf'\b{re.escape(sport_char)}\b', ql):
                entities.update(sport_values)
                break
        
        # --- Ключевые слова: спорткар/спорткары ---
        # Базовая логика: при упоминании спорткара — повышаем порог мощности
        if re.search(r'\bспорткар(ы)?\b', ql):
            # Значения по умолчанию
            base_power_from = 300
            # Вариант бюджетного/начального уровня спорткара
            if re.search(r'(бюджетн|начал|входн)', ql):
                base_power_from = 200
            # Вариант супер-/гиперкаров
            if re.search(r'(суперкар|гиперкар|супер\s*кар|гипер\s*кар)', ql):
                base_power_from = 500
            # Устанавливаем нижнюю границу мощности
            # Не перезаписываем, если пользователь уже указал конкретные рамки
            if 'power_from' not in entities and 'power_exact' not in entities:
                entities['power_from'] = base_power_from
            # Также подскажем спортивные типы кузова, если они ещё не выставлены
            if 'body_type' not in entities:
                entities['body_type'] = ['купе', 'кабриолет', 'родстер']

        # Парсинг конкретных значений мощности
        power_patterns = [
            r'(\d+)\s*л\.с\.',
            r'мощность\s+(\d+)',
            r'(\d+)\s*лошадиных'
        ]
        for pattern in power_patterns:
            matches = re.findall(pattern, ql)
            if matches:
                try:
                    power_value = int(matches[0])
                    entities['power_exact'] = power_value
                    break
                except ValueError:
                    continue
        
        # Парсинг конкретных значений объема двигателя
        volume_patterns = [
            r'(\d+(?:\.\d+)?)\s*л',
            r'объем\s+(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*литра'
        ]
        for pattern in volume_patterns:
            matches = re.findall(pattern, ql)
            if matches:
                try:
                    volume_value = float(matches[0])
                    entities['engine_vol_exact'] = volume_value
                    break
                except ValueError:
                    continue
        
        # Парсинг конкретных значений пробега
        mileage_patterns = [
            r'(\d+(?:\s*\d+)*)\s*км',
            r'пробег\s+(\d+(?:\s*\d+)*)',
            r'(\d+(?:\s*\d+)*)\s*километров'
        ]
        for pattern in mileage_patterns:
            matches = re.findall(pattern, ql)
            if matches:
                try:
                    mileage_str = matches[0].replace(' ', '')
                    mileage_value = int(mileage_str)
                    entities['mileage_exact'] = mileage_value
                    break
                except ValueError:
                    continue
        
        return entities

    def _parse_price(self, s: str) -> int:
        s = s.replace(' ', '')
        
        # Обработка миллионов с десятичными значениями (включая множественное число)
        if 'миллион' in s or 'млн' in s or 'миллионов' in s:
            try:
                # Убираем слова "миллион", "миллионов" или "млн" (важен порядок!)
                number_str = s.replace('миллионов', '').replace('миллион', '').replace('млн', '').replace(',', '.')
                # Парсим как float для поддержки десятичных значений
                number = float(number_str)
                return int(number * 1_000_000)
            except Exception:
                return None
        
        # Обработка тысяч с десятичными значениями (включая множественное число)
        if 'тыс' in s or 'k' in s or 'тысяч' in s:
            try:
                number_str = s.replace('тысяч', '').replace('тыс', '').replace('k', '').replace(',', '.')
                number = float(number_str)
                return int(number * 1_000)
            except Exception:
                return None
        
        # Обычные числа
        try:
            return int(s)
        except Exception:
            return None

    def _parse_mileage(self, s: str) -> int:
        s = s.replace(' ', '')
        # Добавляем обработку "тысяч км" (важен порядок!)
        if 'тысяч' in s:
            try:
                number_str = s.replace('тысяч', '').replace('км', '').replace(',', '.')
                number = float(number_str)
                return int(number * 1_000)
            except Exception:
                return None
        if 'тыс' in s or 'k' in s:
            try:
                return int(float(s.replace('тыс', '').replace('k', '').replace(',', '.')) * 1_000)
            except Exception:
                return None
        try:
            return int(s)
        except Exception:
            return None

    def classify_intent(self, query: str) -> str:
        # Убеждаемся, что query - это строка
        if not isinstance(query, str):
            query = str(query)
        q = query.lower()
        # Приоритет: кредит, сравнение, опции, болтовня, справка, поиск, сценарии
        if any(w in q for w in ['кредит', 'рассрочка', 'платеж', 'ипотека', 'сколько в месяц', 'рассчитать']):
            return 'loan'
        if any(w in q for w in ['сравни', 'vs', 'отличия', 'разница', 'чем лучше', 'чем отличается', 'сравнение']):
            return 'compare'
        if any(w in q for w in ['опция', 'комплектация', 'что входит', 'доступно', 'люк', 'навигация', 'климат']):
            return 'car_option'
        if any(w in q for w in ['как дела', 'привет', 'расскажи', 'шутка', 'анекдот', 'поговорим']):
            return 'chitchat'
        if any(w in q for w in ['справка', 'что ты умеешь', 'инструкция', 'help', 'помощь', 'как пользоваться']):
            return 'help'
        # Новые интенты для сценариев
        if any(w in q for w in ['семейный', 'семья', 'с детьми', 'для семьи']):
            return 'family_car'
        if any(w in q for w in ['город', 'городской', 'компактный', 'маневренный', 'для города']):
            return 'city_car'
        if any(w in q for w in ['путешествия', 'поездки', 'внедорожник', 'кроссовер', 'для путешествий']):
            return 'travel_car'
        if any(w in q for w in ['работа', 'бизнес', 'солидный', 'для работы', 'деловой']):
            return 'business_car'
        if any(w in q for w in ['дача', 'загородный', 'проходимость', 'для дачи']):
            return 'country_car'
        if any(w in q for w in ['молодежный', 'молодежь', 'спортивный', 'динамичный', 'для молодежи']):
            return 'youth_car'
        if any(w in q for w in ['экономичный', 'экономия', 'дешевый', 'бюджетный', 'экономить']):
            return 'economy_car'
        if any(w in q for w in ['машин', 'авто', 'купить', 'продать', 'найди', 'цена', 'год', 'пробег', 'дилер']):
            return 'car_search'
        # Новые интенты для расширенного анализа
        if any(w in q for w in ['отзыв', 'мнение', 'рейтинг', 'качество', 'надежность']):
            return 'car_review'
        if any(w in q for w in ['фото', 'изображение', 'картинка', 'видео']):
            return 'car_media'
        if any(w in q for w in ['характеристики', 'технические данные', 'спецификации', 'технические характеристики']):
            return 'car_specs'
        if any(w in q for w in ['гарантия', 'сервис', 'обслуживание', 'ремонт']):
            return 'car_service'
        if any(w in q for w in ['страховка', 'страхование', 'каско', 'осаго']):
            return 'car_insurance'
        if any(w in q for w in ['регистрация', 'постановка на учет', 'документы']):
            return 'car_registration'
        if any(w in q for w in ['экологичность', 'выбросы', 'расход топлива', 'экономичность']):
            return 'car_efficiency'
        if any(w in q for w in ['безопасность', 'краш-тест', 'системы безопасности']):
            return 'car_safety'
        return 'general' 