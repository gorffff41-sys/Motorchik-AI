import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import urljoin, urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarParser:
    """Парсер для извлечения информации об автомобилях с сайта aaa-motors.ru"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Маппинг марок для URL
        self.brand_mapping = {
            'BMW': 'bmw',
            'AITO': 'aito',
            'AUDI': 'audi',
            'Audi': 'audi',
            'Alfa Romeo': 'alfa-romeo',
            'BYD': 'byd',
            'Belgee': 'belgee',
            'CHANGAN': 'changan',
            'Chery': 'chery',
            'Chevrolet': 'chevrolet',
            'Citroen': 'citroen',
            'DONGFENG': 'dongfeng',
            'Dodge': 'dodge',
            'Exeed': 'exeed',
            'Fiat': 'fiat',
            'Ford': 'ford',
            'GAC': 'gac',
            'GEELY': 'geely',
            'Geely': 'geely',
            'GMC': 'gmc',
            'HYUNDAI': 'hyundai',
            'Hyundai': 'hyundai',
            'Haval': 'haval',
            'Honda': 'honda',
            'JAC': 'jac',
            'JAECOO': 'jaecoo',
            'Jaecoo': 'jaecoo',
            'JEEP': 'jeep',
            'Jeep': 'jeep',
            'JISHI': 'jishi',
            'KIA': 'kia',
            'Kia': 'kia',
            'kia': 'kia',
            'Knewstar': 'knewstar',
            'LADA': 'lada',
            'Lada': 'lada',
            'Lada (ВАЗ)': 'lada',
            'Land Rover': 'land-rover',
            'Lexus': 'lexus',
            'Li Auto': 'li-auto',
            'LiXiang': 'lixiang',
            'Lixiang': 'lixiang',
            'MAZDA': 'mazda',
            'Mazda': 'mazda',
            'Mercedes-Benz': 'mercedes-benz',
            'Mitsubishi': 'mitsubishi',
            'NISSAN': 'nissan',
            'Nissan': 'nissan',
            'OMODA': 'omoda',
            'Omoda': 'omoda',
            'Opel': 'opel',
            'Peugeot': 'peugeot',
            'Porsche': 'porsche',
            'RAM ': 'ram',
            'Renault': 'renault',
            'SERES': 'seres',
            'SKODA': 'skoda',
            'Skoda': 'skoda',
            'SOLARIS': 'solaris',
            'SsangYong': 'ssangyong',
            'Subaru': 'subaru',
            'Suzuki': 'suzuki',
            'Tank': 'tank',
            'Tesla': 'tesla',
            'Toyota': 'toyota',
            'VOLKSWAGEN': 'volkswagen',
            'Volkswagen': 'volkswagen',
            'Volvo': 'volvo',
            'Voyah': 'voyah',
            'WEY': 'wey',
            'Zeekr': 'zeekr',
            'Москвич': 'moskvich'
        }
        
        # Маппинг моделей для URL
        old_model_mapping = {
            # BMW
            'X3': 'x3', 'X5': 'x5', 'X6': 'x6', 'X7': 'x7', 'X4': 'x4', 'X6M': 'x6m',
            '5 серии': '5-series', '5 серия': '5-series', '520D xDrive': '520d-xdrive',
            '520i': '520i', '530Li xDrive': '530li-xdrive', '7er 730': '7er-730',
            '7er 760': '7er-760', '420': '420', 'x7': 'x7', 'X3 XDRIVE30L': 'x3-xdrive30l',
            # AITO
            'M5': 'm5', 'M7': 'm7', ' M5': 'm5', ' M7': 'm7',
            # Audi
            'A3': 'a3', 'A4': 'a4', 'A6': 'a6', 'A7': 'a7', 'A8': 'a8',
            'Q3': 'q3', 'Q7': 'q7', 'Q8': 'q8', 'A6 Avant': 'a6-avant',
            # Mercedes-Benz
            'GLC': 'glc', 'GLE': 'gle', 'GLS': 'gls', 'S-Class': 's-class',
            'E-Класс': 'e-class', 'E-klasse E 220 d 4 MATIC': 'e220d-4matic',
            'E-klasse E 300': 'e300', 'E200': 'e200', 'GLC 250D 4MATIC': 'glc250d-4matic',
            'GLE ': 'gle', 'A-klasse A 180': 'a180', 'C-Класс': 'c-class',
            'CLS-klasse CLS 350': 'cls350', 'GLK-Класс': 'glk-class',
            'M-Класс': 'm-class', 'V-Класс': 'v-class', 'Viano': 'viano',
            # Toyota
            'Camry': 'camry', 'Corolla': 'corolla', 'RAV4': 'rav4',
            'Land Cruiser': 'land-cruiser', 'Highlander': 'highlander',
            'HIGHLANDER': 'highlander', 'Corolla Cross': 'corolla-cross',
            'Land Cruiser 200': 'land-cruiser-200', 'Land Cruiser 300': 'land-cruiser-300',
            # Volkswagen
            'Tiguan': 'tiguan', 'Passat': 'passat', 'Polo': 'polo', 'Jetta': 'jetta',
            'Arteon': 'arteon', 'Touareg': 'touareg', 'Tiguan L PRO': 'tiguan-l-pro',
            'Tiguan L Pro': 'tiguan-l-pro', 'TERAMONT X': 'teramont-x',
            'Tavendor': 'tavendor', 'Tayron X': 'tayron-x', 'Caravelle': 'caravelle',
            'ID.4 X': 'id4-x',
            # Hyundai
            'Santa Fe': 'santa-fe', 'Tucson': 'tucson', 'Sonata': 'sonata',
            'Elantra': 'elantra', 'Accent': 'accent', 'Solaris': 'solaris',
            'Staria': 'staria', 'Grand Starex': 'grand-starex',
            'New Elantra': 'new-elantra', 'Santa Fe Classic': 'santa-fe-classic',
            'ix35': 'ix35',
            # Kia
            'Sportage': 'sportage', 'Sorento': 'sorento', 'Rio': 'rio', 'RIO': 'rio',
            'Ceed': 'ceed', 'Cerato': 'cerato', 'Soul': 'soul', 'Carnival': 'carnival',
            'Optima': 'optima', 'K3': 'k3', 'K5': 'k5', 'SELTOS': 'seltos',
            'SPORTAGE': 'sportage'
        }
        new_model_mapping = {  # ваш новый словарь, который вы прислали
            'X3': 'x3', 'X5': 'x5', 'X6': 'x6', 'X7': 'x7', 'X4': 'x4', 'X6M': 'x6m',
            '5 серии': '5-series', '5 серия': '5-series', '520D xDrive': '520d-xdrive',
            '520i': '520i', '530Li xDrive': '530li-xdrive', '7er 730': '7er-730',
            '7er 760': '7er-760', '420': '420', 'x7': 'x7', 'X3 XDRIVE30L': 'x3-xdrive30l',
            '1 Series': '1-series', '2 Series': '2-series', '3 Series': '3-series',
            '4 Series': '4-series', '6 Series': '6-series', '8 Series': '8-series',
            'M2': 'm2', 'M3': 'm3', 'M4': 'm4', 'M8': 'm8', 'i3': 'i3', 'i4': 'i4',
            'i7': 'i7', 'i8': 'i8', 'Z4': 'z4',
            'M5': 'm5', 'M7': 'm7', ' M5': 'm5', ' M7': 'm7',
            'A3': 'a3', 'A4': 'a4', 'A6': 'a6', 'A7': 'a7', 'A8': 'a8', 'A1': 'a1',
            'A5': 'a5', 'Q2': 'q2', 'Q3': 'q3', 'Q5': 'q5', 'Q7': 'q7', 'Q8': 'q8',
            'Q4 e-tron': 'q4-etron', 'Q5 e-tron': 'q5-etron', 'e-tron': 'e-tron',
            'e-tron GT': 'e-tron-gt', 'RS6': 'rs6', 'RS7': 'rs7', 'RS Q8': 'rs-q8',
            'S3': 's3', 'S4': 's4', 'S5': 's5', 'S6': 's6', 'S7': 's7', 'S8': 's8',
            'TT': 'tt', 'A6 Avant': 'a6-avant', 'A4 Allroad': 'a4-allroad',
            'Giulia': 'giulia', 'Stelvio': 'stelvio', 'Tonale': 'tonale', '4C': '4c',
            'Han': 'han', 'Tang': 'tang', 'Song': 'song', 'Yuan': 'yuan', 'Dolphin': 'dolphin',
            'Seal': 'seal', 'Atto 3': 'atto-3', 'F3': 'f3',
            'X50': 'x50', 'X60': 'x60',
            'CS35': 'cs35', 'CS55': 'cs55', 'CS75': 'cs75', 'CS95': 'cs95', 'UNI-K': 'uni-k',
            'UNI-T': 'uni-t', 'Eado': 'eado',
            'Tiggo': 'tiggo', 'Arrizo': 'arrizo', 'QQ': 'qq', 'Tiggo 7': 'tiggo-7',
            'Tiggo 8': 'tiggo-8', 'Tiggo 8 Pro': 'tiggo-8-pro',
            'Aveo': 'aveo', 'Camaro': 'camaro', 'Captiva': 'captiva', 'Cobalt': 'cobalt',
            'Corvette': 'corvette', 'Cruze': 'cruze', 'Equinox': 'equinox', 'Malibu': 'malibu',
            'Niva': 'niva', 'Tahoe': 'tahoe', 'Trailblazer': 'trailblazer', 'Traverse': 'traverse',
            'C3': 'c3', 'C4': 'c4', 'C5': 'c5', 'Berlingo': 'berlingo', 'Jumpy': 'jumpy',
            'AX7': 'ax7', 'Fengon': 'fengon',
            'Challenger': 'challenger', 'Charger': 'charger', 'Durango': 'durango',
            'LX': 'lx', 'TXL': 'txl', 'VX': 'vx',
            '500': '500', 'Doblo': 'doblo', 'Ducato': 'ducato', 'Panda': 'panda', 'Tipo': 'tipo',
            'Focus': 'focus', 'Fiesta': 'fiesta', 'Mondeo': 'mondeo', 'Explorer': 'explorer',
            'Escape': 'escape', 'Edge': 'edge', 'Kuga': 'kuga', 'Mustang': 'mustang',
            'Ranger': 'ranger', 'Transit': 'transit', 'Tourneo': 'tourneo',
            'GS3': 'gs3', 'GS4': 'gs4', 'GS8': 'gs8', 'GN8': 'gn8',
            'Coolray': 'coolray', 'Atlas': 'atlas', 'Emgrand': 'emgrand', 'Tugella': 'tugella',
            'Monjaro': 'monjaro',
            'Acadia': 'acadia', 'Sierra': 'sierra', 'Yukon': 'yukon',
            'Santa Fe': 'santa-fe', 'Tucson': 'tucson', 'Sonata': 'sonata',
            'Elantra': 'elantra', 'Accent': 'accent', 'Solaris': 'solaris',
            'Staria': 'staria', 'Grand Starex': 'grand-starex', 'Creta': 'creta',
            'New Elantra': 'new-elantra', 'Santa Fe Classic': 'santa-fe-classic',
            'ix35': 'ix35', 'Palisade': 'palisade', 'Kona': 'kona', 'Venue': 'venue',
            'IONIQ 5': 'ioniq-5', 'IONIQ 6': 'ioniq-6',
            'F7': 'f7', 'H6': 'h6', 'Jolion': 'jolion', 'Dargo': 'dargo',
            'Accord': 'accord', 'Civic': 'civic', 'CR-V': 'cr-v', 'Pilot': 'pilot',
            'HR-V': 'hr-v', 'Fit': 'fit', 'Odyssey': 'odyssey',
            'J7': 'j7', 'S7': 's7',
            'J7': 'j7', 'J8': 'j8',
            'Wrangler': 'wrangler', 'Grand Cherokee': 'grand-cherokee', 'Cherokee': 'cherokee',
            'Renegade': 'renegade', 'Compass': 'compass',
            'SX5': 'sx5',
            'Sportage': 'sportage', 'Sorento': 'sorento', 'Rio': 'rio', 'RIO': 'rio',
            'Ceed': 'ceed', 'Cerato': 'cerato', 'Soul': 'soul', 'Carnival': 'carnival',
            'Optima': 'optima', 'K3': 'k3', 'K5': 'k5', 'SELTOS': 'seltos',
            'SPORTAGE': 'sportage', 'Stinger': 'stinger', 'EV6': 'ev6', 'Telluride': 'telluride',
            'Picanto': 'picanto', 'Niro': 'niro',
            'K7': 'k7',
            'Granta': 'granta', 'Vesta': 'vesta', 'Largus': 'largus', 'Niva': 'niva',
            'XRAY': 'xray', '4x4': '4x4',
            'Defender': 'defender', 'Discovery': 'discovery', 'Discovery Sport': 'discovery-sport',
            'Range Rover': 'range-rover', 'Range Rover Evoque': 'range-rover-evoque',
            'Range Rover Sport': 'range-rover-sport', 'Range Rover Velar': 'range-rover-velar',
            'ES': 'es', 'GS': 'gs', 'IS': 'is', 'LS': 'ls', 'NX': 'nx', 'RX': 'rx',
            'UX': 'ux', 'GX': 'gx', 'LX': 'lx', 'RC': 'rc', 'LC': 'lc',
            'L7': 'l7', 'L8': 'l8', 'L9': 'l9',
            'One': 'one',
            '2': '2', '3': '3', '6': '6', 'CX-3': 'cx-3', 'CX-30': 'cx-30',
            'CX-5': 'cx-5', 'CX-9': 'cx-9', 'MX-5': 'mx-5',
            'GLC': 'glc', 'GLE': 'gle', 'GLS': 'gls', 'S-Class': 's-class',
            'E-Класс': 'e-class', 'E-klasse E 220 d 4 MATIC': 'e220d-4matic',
            'E-klasse E 300': 'e300', 'E200': 'e200', 'GLC 250D 4MATIC': 'glc250d-4matic',
            'GLE ': 'gle', 'A-klasse A 180': 'a180', 'C-Класс': 'c-class',
            'CLS-klasse CLS 350': 'cls350', 'GLK-Класс': 'glk-class',
            'M-Класс': 'm-class', 'V-Класс': 'v-class', 'Viano': 'viano',
            'A-Class': 'a-class', 'B-Class': 'b-class', 'CLA': 'cla', 'CLS': 'cls',
            'G-Class': 'g-class', 'GLB': 'glb', 'GLA': 'gla', 'AMG GT': 'amg-gt',
            'Maybach': 'maybach', 'EQE': 'eqe', 'EQS': 'eqs',
            'Outlander': 'outlander', 'Pajero': 'pajero', 'Pajero Sport': 'pajero-sport',
            'ASX': 'asx', 'Eclipse Cross': 'eclipse-cross', 'L200': 'l200',
            'Almera': 'almera', 'Juke': 'juke', 'Leaf': 'leaf', 'Murano': 'murano',
            'Pathfinder': 'pathfinder', 'Qashqai': 'qashqai', 'Rogue': 'rogue',
            'Sentra': 'sentra', 'Teana': 'teana', 'Terrano': 'terrano', 'X-Trail': 'x-trail',
            'Note': 'note', 'Navara': 'navara',
            'C5': 'c5',
            'Astra': 'astra', 'Corsa': 'corsa', 'Insignia': 'insignia', 'Mokka': 'mokka',
            'Vivaro': 'vivaro', 'Zafira': 'zafira',
            '208': '208', '301': '301', '308': '308', '408': '408', '508': '508',
            '2008': '2008', '3008': '3008', '4008': '4008', '5008': '5008',
            'Partner': 'partner', 'Boxer': 'boxer',
            '911': '911', 'Cayenne': 'cayenne', 'Macan': 'macan', 'Panamera': 'panamera',
            'Taycan': 'taycan',
            '1500': '1500', '2500': '2500', '3500': '3500',
            'Arkana': 'arkana', 'Duster': 'duster', 'Kaptur': 'kaptur', 'Logan': 'logan',
            'Sandero': 'sandro', 'Megane': 'megane', 'Koleos': 'koleos', 'Talisman': 'talisman',
            'Fluence': 'fluence', 'Scenic': 'scenic',
            'SF5': 'sf5',
            'Fabia': 'fabia', 'Octavia': 'octavia', 'Rapid': 'rapid', 'Superb': 'superb',
            'Kodiaq': 'kodiaq', 'Karoq': 'karoq', 'Kamiq': 'kamiq', 'Enyaq': 'enyaq',
            'C30': 'c30',
            'Actyon': 'actyon', 'Korando': 'korando', 'Rexton': 'rexton', 'Tivoli': 'tivoli',
            'Forester': 'forester', 'Outback': 'outback', 'XV': 'xv', 'Impreza': 'impreza',
            'Legacy': 'legacy', 'WRX': 'wrx', 'BRZ': 'brz',
            'Swift': 'swift', 'Vitara': 'vitara', 'SX4': 'sx4', 'Jimny': 'jimny',
            '300': '300', '500': '500',
            'Model 3': 'model-3', 'Model S': 'model-s', 'Model X': 'model-x',
            'Model Y': 'model-y', 'Cybertruck': 'cybertruck',
            'Camry': 'camry', 'Corolla': 'corolla', 'RAV4': 'rav4',
            'Land Cruiser': 'land-cruiser', 'Highlander': 'highlander',
            'HIGHLANDER': 'highlander', 'Corolla Cross': 'corolla-cross',
            'Land Cruiser 200': 'land-cruiser-200', 'Land Cruiser 300': 'land-cruiser-300',
            'Auris': 'auris', 'Avensis': 'avensis', 'C-HR': 'c-hr', 'Fortuner': 'fortuner',
            'Hilux': 'hilux', 'Prado': 'prado', 'Prius': 'prius', 'Yaris': 'yaris',
            'Yaris Cross': 'yaris-cross',
            'Tiguan': 'tiguan', 'Passat': 'passat', 'Polo': 'polo', 'Jetta': 'jetta',
            'Arteon': 'arteon', 'Touareg': 'touareg', 'Tiguan L PRO': 'tiguan-l-pro',
            'Tiguan L Pro': 'tiguan-l-pro', 'TERAMONT X': 'teramont-x',
            'Tavendor': 'tavendor', 'Tayron X': 'tayron-x', 'Caravelle': 'caravelle',
            'ID.4 X': 'id4-x', 'Golf': 'golf', 'ID.3': 'id3', 'ID.4': 'id4', 'ID.6': 'id6',
            'Caddy': 'caddy', 'Multivan': 'multivan', 'Amarok': 'amarok', 'Scirocco': 'scirocco',
            'Sharan': 'sharan',
            'S60': 's60', 'S90': 's90', 'V60': 'v60', 'V90': 'v90', 'XC40': 'xc40',
            'XC60': 'xc60', 'XC90': 'xc90',
            'Free': 'free', 'Dream': 'dream',
            'VV5': 'vv5', 'VV7': 'vv7',
            '001': '001', '009': '009', 'X': 'x',
            '3': '3', '3е': '3e'
        }
        # Объединение: приоритет у new_model_mapping
        merged_model_mapping = old_model_mapping.copy()
        merged_model_mapping.update(new_model_mapping)
        self.model_mapping = merged_model_mapping
    
    def generate_car_link(self, car: Dict[str, Any]) -> Optional[str]:
        """Генерирует ссылку на автомобиль на сайте aaa-motors.ru с учетом города (region_id)"""
        brand = car.get('mark') or car.get('brand') or ''
        model = car.get('model') or ''
        city = car.get('city') or ''
        if not brand or not model:
            logger.warning(f"Недостаточно данных для генерации ссылки: brand={brand}, model={model}")
            return None
        # Получаем slug для марки
        brand_slug = self.brand_mapping.get(brand, brand.lower().replace(' ', '-'))
        # Получаем slug для модели
        model_slug = self.model_mapping.get(model, model.lower().replace(' ', '-'))
        # Определяем region_id по городу
        city_region_map = {
            'Ростов-на-Дону': 1,
            'Воронеж': 2,
            'Краснодар': 3
        }
        region_id = city_region_map.get(city.strip(), 1)
        logger.info(f"Город для ссылки: '{city}', region_id={region_id}")
        url = f"https://aaa-motors.ru/catalog/{brand_slug}/{model_slug}?region_id={region_id}"
        logger.info(f"Сгенерирована ссылка: {url}")
        return url
    
    def extract_price_from_text(self, price_text: str) -> int:
        """Извлекает цену из текста"""
        if not price_text:
            return 0
        
        # Убираем лишние символы, но сохраняем пробелы в числах
        price_text = price_text.replace('\xa0', ' ').strip()
        
        # Ищем числа с пробелами в качестве разделителей тысяч
        # Паттерн: цифры, возможно разделенные пробелами, за которыми следует "р." или "руб"
        price_match = re.search(r'(\d{1,3}(?:\s\d{3})*)\s*(?:р\.|руб|₽|млн|тыс)', price_text, re.IGNORECASE)
        
        if price_match:
            price_str = price_match.group(1).replace(' ', '')  # Убираем пробелы из числа
            try:
                price = int(price_str)
                
                # Если в тексте есть "млн", умножаем на 1000000
                if 'млн' in price_text.lower():
                    price *= 1000000
                # Если в тексте есть "тыс", умножаем на 1000
                elif 'тыс' in price_text.lower():
                    price *= 1000
                
                logger.info(f"Извлечена цена: {price} из текста '{price_text}'")
                return price
            except ValueError:
                logger.warning(f"Не удалось преобразовать '{price_str}' в число")
        
        # Если не нашли с основным паттерном, пробуем альтернативный
        # Ищем любые цифры в тексте с различными разделителями
        digits_match = re.search(r'(\d{1,3}(?:[.,\s]\d{3})*)', price_text)
        if digits_match:
            price_str = digits_match.group(1).replace(' ', '').replace(',', '').replace('.', '')
            try:
                price = int(price_str)
                # Проверяем, что цена выглядит разумно (больше 1000)
                if price > 1000:
                    logger.info(f"Извлечена цена альтернативным способом: {price} из текста '{price_text}'")
                    return price
                else:
                    logger.warning(f"Извлеченная цена слишком мала: {price} из текста '{price_text}'")
            except ValueError:
                pass
        
        # Если все еще не нашли, пробуем найти просто число
        simple_match = re.search(r'(\d+)', price_text)
        if simple_match:
            price_str = simple_match.group(1)
            try:
                price = int(price_str)
                # Проверяем, что цена выглядит разумно (больше 100000)
                if price > 100000:
                    logger.info(f"Извлечена цена простым способом: {price} из текста '{price_text}'")
                    return price
            except ValueError:
                pass
        
        logger.warning(f"Не удалось извлечь цену из текста: '{price_text}'")
        return 0
    
    def parse_cars_from_html(self, html: str, target_brand: str, target_model: str) -> List[Dict[str, Any]]:
        """Парсит HTML и извлекает информацию об автомобилях"""
        cars = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем карточки автомобилей по селектору из анализа HTML
            car_cards = soup.find_all('a', class_='item-row js-item')
            
            logger.info(f"Найдено карточек автомобилей: {len(car_cards)}")
            
            # Если не нашли карточки, пробуем другие селекторы
            if not car_cards:
                logger.info("Пробуем другие селекторы для карточек...")
                car_cards = soup.find_all('a', class_='item-row')
                logger.info(f"Найдено карточек с селектором 'item-row': {len(car_cards)}")
            
            if not car_cards:
                logger.info("Пробуем поиск по частичному совпадению класса...")
                # Ищем все ссылки и фильтруем по классу
                all_links = soup.find_all('a')
                car_cards = [link for link in all_links if link.get('class') and any('item' in cls for cls in link.get('class', []))]
                logger.info(f"Найдено карточек с 'item' в классе: {len(car_cards)}")
            
            # Логируем найденные карточки
            for i, card in enumerate(car_cards[:5]):  # Логируем первые 5 карточек
                classes = card.get('class', [])
                href = card.get('href', '')
                logger.info(f"Карточка {i+1}: классы={classes}, href={href}")
            
            for card in car_cards:
                try:
                    car_info = self.extract_car_info(card, target_brand, target_model)
                    if car_info:
                        cars.append(car_info)
                        logger.info(f"Извлечена информация об авто: {car_info}")
                except Exception as e:
                    logger.error(f"Ошибка при парсинге карточки: {e}")
            
            # Если не нашли карточки, пробуем альтернативные селекторы
            if not cars:
                logger.info("Пробуем альтернативные селекторы...")
                # Ищем элементы с классами, содержащими ключевые слова
                alternative_selectors = [
                    'div[class*="car"]', 'div[class*="vehicle"]', 'div[class*="product"]',
                    'div[class*="item"]', 'div[class*="card"]', 'article[class*="car"]',
                    'article[class*="vehicle"]', 'article[class*="product"]'
                ]
                
                for selector in alternative_selectors:
                    car_cards = soup.select(selector)
                    logger.info(f"Селектор '{selector}': найдено {len(car_cards)} элементов")
                    for card in car_cards:
                        try:
                            car_info = self.extract_car_info_alternative(card, target_brand, target_model)
                            if car_info:
                                cars.append(car_info)
                                logger.info(f"Альтернативный поиск - найдено: {car_info}")
                        except Exception as e:
                            logger.error(f"Ошибка при альтернативном парсинге: {e}")
            
            # Если все еще не нашли, пробуем поиск по тексту страницы
            if not cars:
                logger.info("Пробуем поиск по тексту страницы...")
                body_text = soup.get_text()
                logger.info(f"Длина текста страницы: {len(body_text)} символов")
                
                # Ищем упоминания марки и модели
                brand_lower = target_brand.lower()
                model_lower = target_model.lower()
                
                if brand_lower in body_text.lower():
                    logger.info(f"Марка '{target_brand}' найдена в тексте страницы")
                else:
                    logger.warning(f"Марка '{target_brand}' НЕ найдена в тексте страницы")
                
                if model_lower in body_text.lower():
                    logger.info(f"Модель '{target_model}' найдена в тексте страницы")
                else:
                    logger.warning(f"Модель '{target_model}' НЕ найдена в тексте страницы")
                
                # Ищем цены в тексте
                price_pattern = re.compile(r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:руб|₽|млн|тыс)', re.IGNORECASE)
                price_matches = price_pattern.findall(body_text)
                logger.info(f"Найдено {len(price_matches)} упоминаний цен в тексте")
                
                if price_matches:
                    logger.info(f"Примеры цен: {price_matches[:5]}")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге HTML: {e}")
        
        return cars
    
    def extract_car_info(self, card, target_brand: str, target_model: str) -> Optional[Dict[str, Any]]:
        """Извлекает информацию об автомобиле из карточки"""
        try:
            # Получаем ссылку
            url = card.get('href')
            if not url:
                return None
            
            # Делаем ссылку абсолютной
            if url.startswith('/'):
                url = f"https://aaa-motors.ru{url}"
            
            # Ищем цену - пробуем разные селекторы
            price_element = None
            price_selectors = [
                'div.item__price-main',
                'div.item__price div.item__price-main',
                'div[class*="price"]',
                'span[class*="price"]',
                '.price',
                '[class*="Price"]',
                '[data-price]'
            ]
            
            for selector in price_selectors:
                price_element = card.select_one(selector)
                if price_element:
                    logger.info(f"Найден элемент цены с селектором: {selector}")
                    break
            
            if not price_element:
                # Ищем цену в тексте карточки
                card_text = card.get_text()
                price_matches = re.findall(r'(\d{1,3}(?:\s\d{3})*)\s*(?:р\.|руб|₽|млн|тыс)', card_text, re.IGNORECASE)
                if price_matches:
                    price_text = price_matches[0]
                    logger.info(f"Найдена цена в тексте карточки: {price_text}")
                else:
                    logger.warning("Цена не найдена в карточке")
                    return None
            else:
                price_text = price_element.get_text(strip=True)
                logger.info(f"Найдена цена в элементе: '{price_text}'")
            
            price = self.extract_price_from_text(price_text)
            if price <= 0:
                logger.warning(f"Не удалось извлечь цену из текста: '{price_text}'")
                return None
            
            # Ищем название - пробуем разные селекторы
            title_element = None
            title_selectors = [
                'div.item__title.js-item-title',
                'div.item__title',
                'h3',
                'h2',
                '[class*="title"]',
                '[class*="name"]'
            ]
            
            for selector in title_selectors:
                title_element = card.select_one(selector)
                if title_element:
                    break
            
            title = title_element.get_text(strip=True) if title_element else ''
            
            # Ищем технические характеристики
            tech_element = card.find('div', class_='item__tech')
            tech_info = {}
            if tech_element:
                tech_divs = tech_element.find_all('div')
                if len(tech_divs) >= 5:
                    tech_info = {
                        'year': tech_divs[0].get_text(strip=True).replace('\\', '').replace('\n', ''),
                        'fuel': tech_divs[1].get_text(strip=True).replace('\\', '').replace('\n', ''),
                        'transmission': tech_divs[2].get_text(strip=True).replace('\\', '').replace('\n', ''),
                        'power': tech_divs[3].get_text(strip=True).replace('\\', '').replace('\n', ''),
                        'volume': tech_divs[4].get_text(strip=True).replace('\\', '').replace('\n', '')
                    }
            
            # Ищем статус и адрес
            status_element = card.find('span', class_='item-row__info-status')
            status = status_element.get_text(strip=True) if status_element else ''
            
            address_element = card.find('div', class_='item-row__info-address')
            address = address_element.get_text(strip=True) if address_element else ''
            
            # Ищем изображение
            img_element = card.find('img')
            img_url = img_element.get('src') if img_element else ''
            
            # Проверяем, что карточка содержит нужную марку и модель
            card_text = card.get_text().lower()
            brand_lower = target_brand.lower()
            model_lower = target_model.lower()
            
            # Более гибкая проверка марки и модели
            brand_match = (brand_lower in card_text or 
                          brand_lower.replace(' ', '') in card_text or
                          brand_lower.replace('-', '') in card_text)
            
            model_match = (model_lower in card_text or 
                          model_lower.replace(' ', '') in card_text or
                          model_lower.replace('-', '') in card_text)
            
            # Если марка и модель не совпадают, логируем но не пропускаем
            if not brand_match:
                logger.warning(f"Марка '{target_brand}' не найдена в карточке")
            if not model_match:
                logger.warning(f"Модель '{target_model}' не найдена в карточке")
            
            # Возвращаем информацию даже если марка/модель не найдены (может быть ошибка в данных)
            return {
                'url': url,
                'title': title,
                'price': price,
                'brand': target_brand,
                'model': target_model,
                'tech_info': tech_info,
                'status': status,
                'address': address,
                'img_url': img_url,
                'brand_match': brand_match,
                'model_match': model_match
            }
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации об авто: {e}")
            return None
    
    def extract_car_info_alternative(self, card, target_brand: str, target_model: str) -> Optional[Dict[str, Any]]:
        """Альтернативный метод извлечения информации об автомобиле"""
        try:
            # Ищем ссылку
            link = card.find('a')
            if not link:
                return None
            
            url = link.get('href')
            if not url:
                return None
            
            # Делаем ссылку абсолютной
            if url.startswith('/'):
                url = f"https://aaa-motors.ru{url}"
            
            # Ищем цену в любом элементе
            price_elements = card.find_all(text=re.compile(r'\d{1,3}(?:[.,]\d{3})*\s*(?:руб|₽|млн|тыс)', re.IGNORECASE))
            
            if not price_elements:
                return None
            
            price = self.extract_price_from_text(price_elements[0])
            if price <= 0:
                return None
            
            return {
                'url': url,
                'price': price,
                'brand': target_brand,
                'model': target_model
            }
            
        except Exception as e:
            logger.error(f"Ошибка при альтернативном извлечении: {e}")
            return None
    
    def find_car_by_price(self, base_url: str, target_price: int, target_brand: str, target_model: str, tolerance: float = 0.1) -> Optional[Dict[str, Any]]:
        """Находит автомобиль по цене на странице каталога. Если не найдено — пробует -1 суффикс. Если и там не найдено, возвращает url_catalog_fallback."""
        try:
            logger.info(f"Парсим страницу: {base_url}")
            logger.info(f"Ищем авто с ценой: {target_price / 1000000:.1f} млн ₽")
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            html = response.text
            logger.info(f"HTML получен, длина: {len(html)}")
            # Сохраняем HTML для анализа (опционально)
            try:
                import os
                debug_dir = "debug_html"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                filename = f"{debug_dir}/{target_brand}_{target_model}_{target_price}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"HTML сохранен в файл: {filename}")
            except Exception as e:
                logger.warning(f"Не удалось сохранить HTML: {e}")
            # Парсим автомобили
            cars = self.parse_cars_from_html(html, target_brand, target_model)
            logger.info(f"Найдено автомобилей на странице: {len(cars)}")
            matching_car = self.find_matching_car(cars, target_price, tolerance)
            if matching_car:
                logger.info(f"Найден подходящий автомобиль: {matching_car}")
                return {
                    'url': matching_car['url'],
                    'brand': target_brand,
                    'model': target_model,
                    'price': target_price,
                    'region': 'Ростов-на-Дону',
                    'found_price': matching_car['price'],
                    'price_difference': abs(target_price - matching_car['price']),
                    'title': matching_car.get('title', ''),
                    'tech_info': matching_car.get('tech_info', {}),
                    'status': matching_car.get('status', ''),
                    'address': matching_car.get('address', ''),
                    'img_url': matching_car.get('img_url', '')
                }
            else:
                logger.info("Подходящий автомобиль не найден, возвращаем url_catalog_fallback")
                return {
                    'url_catalog_fallback': base_url
                }
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            # Fallback: если ошибка, пробуем -1 суффикс
            import re
            m = re.search(r"/([^/?]+)(\?region_id=\d+)", base_url)
            if m:
                model_part = m.group(1)
                region_part = m.group(2)
                if not model_part.endswith("-1"):
                    alt_url = base_url.replace(f"/{model_part}{region_part}", f"/{model_part}-1{region_part}")
                    logger.info(f"Пробуем fallback URL: {alt_url}")
                    try:
                        response = self.session.get(alt_url, timeout=30)
                        response.raise_for_status()
                        html = response.text
                        cars = self.parse_cars_from_html(html, target_brand, target_model)
                        matching_car = self.find_matching_car(cars, target_price, tolerance)
                        if matching_car:
                            logger.info(f"Найден подходящий автомобиль по fallback: {matching_car}")
                            return {
                                'url': matching_car['url'],
                                'brand': target_brand,
                                'model': target_model,
                                'price': target_price,
                                'region': 'Ростов-на-Дону',
                                'found_price': matching_car['price'],
                                'price_difference': abs(target_price - matching_car['price']),
                                'title': matching_car.get('title', ''),
                                'tech_info': matching_car.get('tech_info', {}),
                                'status': matching_car.get('status', ''),
                                'address': matching_car.get('address', ''),
                                'img_url': matching_car.get('img_url', '')
                            }
                        else:
                            logger.info("Подходящий автомобиль не найден по fallback, возвращаем url_catalog_fallback")
                            return {
                                'url_catalog_fallback': alt_url
                            }
                    except Exception as e2:
                        logger.error(f"Ошибка при fallback парсинге: {e2}")
            return None
    
    def find_matching_car(self, cars: List[Dict[str, Any]], target_price: int, tolerance: float = 0.1) -> Optional[Dict[str, Any]]:
        """Находит автомобиль с ценой в пределах допуска"""
        if not cars:
            logger.warning("Список автомобилей пуст")
            return None
        
        logger.info(f"Ищем автомобиль с ценой {target_price:,} руб среди {len(cars)} автомобилей")
        
        best_match = None
        min_difference = float('inf')
        
        for i, car in enumerate(cars):
            car_price = car.get('price', 0)
            if car_price <= 0:
                logger.warning(f"Автомобиль {i+1}: некорректная цена {car_price}")
                continue
            
            difference = abs(car_price - target_price)
            relative_difference = difference / target_price
            
            logger.info(f"Автомобиль {i+1}: цена {car_price:,} руб, разница {difference:,} руб ({relative_difference:.1%})")
            
            # Если разница в пределах допуска и меньше предыдущей лучшей
            if relative_difference <= tolerance and difference < min_difference:
                min_difference = difference
                best_match = car
                logger.info(f"Новый лучший кандидат: {car.get('title', 'Без названия')} за {car_price:,} руб")
        
        if best_match:
            final_difference = abs(best_match['price'] - target_price)
            final_relative = final_difference / target_price
            logger.info(f"Найден подходящий автомобиль: {best_match.get('title', 'Без названия')}")
            logger.info(f"Цена: {best_match['price']:,} руб (разница: {final_difference:,} руб, {final_relative:.1%})")
        else:
            logger.warning("Подходящий автомобиль не найден")
            # Показываем лучшие варианты для диагностики
            sorted_cars = sorted(cars, key=lambda x: abs(x.get('price', 0) - target_price))
            logger.info("Лучшие кандидаты:")
            for i, car in enumerate(sorted_cars[:3]):
                price = car.get('price', 0)
                diff = abs(price - target_price)
                rel_diff = diff / target_price
                logger.info(f"  {i+1}. {car.get('title', 'Без названия')}: {price:,} руб (разница: {diff:,} руб, {rel_diff:.1%})")
        
        return best_match

# Создаем глобальный экземпляр парсера
car_parser = CarParser() 