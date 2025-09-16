import difflib
from typing import List, Tuple, Optional
import re


class FuzzySearch:
    """Класс для нечёткого поиска и исправления опечаток"""
    
    def __init__(self):
        # Убраны дубликаты брендов
        self.brand_synonyms = {
            'bmw': ['бмв', 'бмвв', 'bmvv', 'bmw'],
            'mercedes': ['мерседес', 'мерс', 'mercedes-benz', 'benz', 'мерседес-бенц'],
            'audi': ['ауди', 'аудии', 'audii'],
            'toyota': ['тойота', 'тойотта', 'toyotaa'],
            'honda': ['хонда', 'хондда', 'hondaa'],
            'nissan': ['ниссан', 'нисан', 'nissann'],
            'mazda': ['мазда', 'маззда', 'mazdaa'],
            'volkswagen': ['фольксваген', 'vw', 'фв', 'volkswagon'],
            'ford': ['форд', 'форрд', 'fordd'],
            'chevrolet': ['шевроле', 'chevvy', 'chevy', 'шев'],
            'kia': ['киа', 'кииа', 'kiia'],
            'hyundai': ['хендай', 'хундай', 'hyundaii'],
            'lada': ['лада', 'ваз', 'автоваз', 'ladda'],
            'renault': ['рено', 'реннольт', 'renaultt'],
            'peugeot': ['пежо', 'пежжо', 'peugeott'],
            'citroen': ['ситроен', 'ситрон', 'citroenn'],
            'skoda': ['шкода', 'шкодда', 'skodaa'],
            'volvo': ['вольво', 'волво', 'volvoo'],
            'lexus': ['лексус', 'лекссус', 'lexuss'],
            'infiniti': ['инфинити', 'инфинитти', 'infinitii'],
            'acura': ['акура', 'акурра', 'acuraa'],
            'subaru': ['субару', 'суббару', 'subaruu'],
            'mitsubishi': ['мицубиси', 'митсубиши', 'mitsubishii'],
            'suzuki': ['сузуки', 'судзуки', 'suzukii'],
            'daihatsu': ['дайхатсу', 'дайхацу', 'daihatsuu'],
            'opel': ['опель', 'опелл', 'opell'],
            'fiat': ['фиат', 'фиатт', 'fiat'],
            'alfa romeo': ['альфа ромео', 'альфа-ромео', 'alfaromeo'],
            'jaguar': ['ягуар', 'джагуар', 'jaguarr'],
            'land rover': ['ленд ровер', 'ленд-ровер', 'landrover'],
            'range rover': ['рейндж ровер', 'рейндж-ровер', 'rangerover'],
            'porsche': ['порше', 'поршше', 'porschee'],
            'ferrari': ['феррари', 'феррарии', 'ferrarri'],
            'lamborghini': ['ламборгини', 'ламборджини', 'lamborghinii'],
            'maserati': ['мазерати', 'масерати', 'maseratii'],
            'bentley': ['бентли', 'бенттли', 'bentleyy'],
            'rolls royce': ['роллс ройс', 'роллс-ройс', 'rollsroyce'],
            'aston martin': ['астон мартин', 'астон-мартин', 'astonmartin'],
            'lotus': ['лотос', 'лотус', 'lotuss'],
            'mclaren': ['макларен', 'макларен', 'mclarenn'],
            'bugatti': ['бугатти', 'бугаттии', 'bugattii'],
            'koenigsegg': ['кёнигсегг', 'кенигсегг', 'koenigseggg'],
            'pagani': ['пагани', 'паганни', 'paganii'],
            'rimac': ['римак', 'римакк', 'rimacc'],
            'tesla': ['тесла', 'тессла', 'teslaa'],
            'rivian': ['ривиан', 'ривианн', 'riviann'],
            'lucid': ['люсид', 'люсидд', 'lucidd'],
            'nio': ['нио', 'ниоо', 'nioo'],
            'xpeng': ['кспенг', 'кспеннг', 'xpenng'],
            'li auto': ['ли авто', 'ли-авто', 'liauto'],
            'byd': ['би-вай-ди', 'бивайди', 'bydd'],
            'geely': ['джили', 'геели', 'geelyy'],
            'haval': ['хавал', 'хаваль', 'havall'],
            'great wall': ['грейт валл', 'грейт-валл', 'greatwall'],
            'changan': ['чанган', 'чангаан', 'changann'],
            'dongfeng': ['донгфенг', 'донгфеннг', 'dongfengg'],
            'faw': ['фав', 'фавв', 'faww'],
            'sail': ['сайл', 'сайлл', 'saill'],
            'chery': ['чери', 'черри', 'cheryy'],
            'omoda': ['омода', 'омодда', 'omodaa'],
            'jaecoo': ['джаекоо', 'джаеко', 'jaecooo'],
            'exeed': ['ексид', 'ексиид', 'exeedd'],
            'jetour': ['джетур', 'джетуур', 'jetourr'],
            'wey': ['вей', 'веий', 'weyy'],
            'ora': ['ора', 'орра', 'oraa'],
            'zeekr': ['зикр', 'зикрр', 'zeekrr'],
            'lynk & co': ['линк энд ко', 'линк-энд-ко', 'lynkco'],
            'polestar': ['полестар', 'поллестар', 'polestarr'],
            'smart': ['смарт', 'смаррт', 'smartt'],
            'mini': ['мини', 'минии', 'minii'],
            'abarth': ['абарт', 'абаарт', 'abarthh'],
            'lancia': ['ланча', 'ланнча', 'lanciaa'],
            'jeep': ['джип', 'джиип', 'jeepp'],
            'dodge': ['додж', 'доддж', 'dodgge'],
            'chrysler': ['крайслер', 'крайсллер', 'chryslerr'],
            'ram': ['рам', 'раам', 'ramm'],
            'cadillac': ['кадиллак', 'кадиллакк', 'cadillacc'],
            'buick': ['бьюик', 'бьюикк', 'buickk'],
            'gmc': ['джи-эм-си', 'джиэмси', 'gmcc'],
            'pontiac': ['понтиак', 'понтиаак', 'pontiacc'],
            'oldsmobile': ['олдсмобил', 'олдсмобилл', 'oldsmobilee'],
            'saturn': ['сатурн', 'сатурнн', 'saturrn'],
            'hummer': ['хаммер', 'хаммерр', 'hummerr'],
            'saab': ['сааб', 'саааб', 'saabb'],
            'vauxhall': ['воксхолл', 'воксхоллл', 'vauxhalll'],
            'holden': ['холден', 'холлден', 'holdenn'],
            'isuzu': ['исузу', 'исузуу', 'isuzuu'],
        }
        
        # Модели без изменений
        self.model_synonyms = {
            'x5': ['x-5', 'x5', 'икс5', 'икс-5'],
            'x6': ['x-6', 'x6', 'икс6', 'икс-6'],
            'x7': ['x-7', 'x7', 'икс7', 'икс-7'],
            'x3': ['x-3', 'x3', 'икс3', 'икс-3'],
            'x1': ['x-1', 'x1', 'икс1', 'икс-1'],
            'x4': ['x-4', 'x4', 'икс4', 'икс-4'],
            'x2': ['x-2', 'x2', 'икс2', 'икс-2'],
            'x8': ['x-8', 'x8', 'икс8', 'икс-8'],
            'm3': ['m-3', 'm3', 'эм3', 'эм-3'],
            'm5': ['m-5', 'm5', 'эм5', 'эм-5'],
            'm4': ['m-4', 'm4', 'эм4', 'эм-4'],
            'm2': ['m-2', 'm2', 'эм2', 'эм-2'],
            'm8': ['m-8', 'm8', 'эм8', 'эм-8'],
            'm1': ['m-1', 'm1', 'эм1', 'эм-1'],
            'm6': ['m-6', 'm6', 'эм6', 'эм-6'],
            'm7': ['m-7', 'm7', 'эм7', 'эм-7'],
            'i3': ['i-3', 'i3', 'ай3', 'ай-3'],
            'i4': ['i-4', 'i4', 'ай4', 'ай-4'],
            'i5': ['i-5', 'i5', 'ай5', 'ай-5'],
            'i7': ['i-7', 'i7', 'ай7', 'ай-7'],
            'i8': ['i-8', 'i8', 'ай8', 'ай-8'],
            'i9': ['i-9', 'i9', 'ай9', 'ай-9'],
            'z3': ['z-3', 'z3', 'зет3', 'зет-3'],
            'z4': ['z-4', 'z4', 'зет4', 'зет-4'],
            'z8': ['z-8', 'z8', 'зет8', 'зет-8'],
            '1 series': ['1-series', '1 серия', '1-серия', 'series 1'],
            '2 series': ['2-series', '2 серия', '2-серия', 'series 2'],
            '3 series': ['3-series', '3 серия', '3-серия', 'series 3'],
            '4 series': ['4-series', '4 серия', '4-серия', 'series 4'],
            '5 series': ['5-series', '5 серия', '5-серия', 'series 5'],
            '6 series': ['6-series', '6 серия', '6-серия', 'series 6'],
            '7 series': ['7-series', '7 серия', '7-серия', 'series 7'],
            '8 series': ['8-series', '8 серия', '8-серия', 'series 8'],
            'camry': ['камри', 'каммри', 'camryy'],
            'corolla': ['королла', 'короллла', 'corollaa'],
            'rav4': ['рав4', 'рав-4', 'rav-4', 'rav4'],
            'highlander': ['хайлендер', 'хайленддер', 'highlanderr'],
            '4runner': ['4-раннер', '4раннер', '4runner'],
            'tacoma': ['такома', 'таккома', 'tacomaa'],
            'tundra': ['тундра', 'тунндра', 'tundrra'],
            'sequoia': ['секвойя', 'секвойяя', 'sequoiaa'],
            'land cruiser': ['лэнд крузер', 'лэнд-крузер', 'landcruiser'],
            'prius': ['приус', 'приуус', 'priuss'],
            'avalon': ['авалон', 'аваллон', 'avalon'],
            'sienna': ['сиенна', 'сиеннна', 'siennaa'],
            'venza': ['венза', 'веннза', 'venzaa'],
            'c-hr': ['с-хр', 'chr', 'c-hr'],
            'yaris': ['ярис', 'ярисс', 'yariss'],
            'yaris cross': ['ярис кросс', 'ярис-кросс', 'yariscross'],
            'corolla cross': ['королла кросс', 'королла-кросс', 'corollacross'],
            'bZ4X': ['bz4x', 'бз4х', 'b-z-4-x'],
            'crown': ['краун', 'краунн', 'crownn'],
            'mirai': ['мирай', 'мирайй', 'miraii'],
            'supra': ['супра', 'суппра', 'supraa'],
            '86': ['86', 'gt86', 'gt-86'],
            'gr86': ['gr-86', 'gr86'],
            'gr yaris': ['gr ярис', 'gr-ярис', 'gryaris'],
            'gr corolla': ['gr королла', 'gr-королла', 'grcorolla'],
            'a3': ['a-3', 'a3', 'а3'],
            'a4': ['a-4', 'a4', 'а4'],
            'a5': ['a-5', 'a5', 'а5'],
            'a6': ['a-6', 'a6', 'а6'],
            'a7': ['a-7', 'a7', 'а7'],
            'a8': ['a-8', 'a8', 'а8'],
            'q3': ['q-3', 'q3', 'ку3'],
            'q4': ['q-4', 'q4', 'ку4'],
            'q5': ['q-5', 'q5', 'ку5'],
            'q7': ['q-7', 'q7', 'ку7'],
            'q8': ['q-8', 'q8', 'ку8'],
            'rs3': ['rs-3', 'rs3', 'рс3'],
            'rs4': ['rs-4', 'rs4', 'рс4'],
            'rs5': ['rs-5', 'rs5', 'рс5'],
            'rs6': ['rs-6', 'rs6', 'рс6'],
            'rs7': ['rs-7', 'rs7', 'рс7'],
            's3': ['s-3', 's3', 'с3'],
            's4': ['s-4', 's4', 'с4'],
            's5': ['s-5', 's5', 'с5'],
            's6': ['s-6', 's6', 'с6'],
            's7': ['s-7', 's7', 'с7'],
            's8': ['s-8', 's8', 'с8'],
            'tt': ['tt', 'тт'],
            'r8': ['r-8', 'r8', 'р8'],
            'e-tron': ['e-tron', 'етрон', 'e-tron'],
            'e-tron gt': ['e-tron gt', 'етрон gt', 'e-tron-gt'],
            'cx-5': ['cx5', 'сх-5', 'сх5'],
            'cx-30': ['cx30', 'сх-30', 'сх30'],
            'cx-50': ['cx50', 'сх-50', 'сх50'],
            'cx-60': ['cx60', 'сх-60', 'сх60'],
            'cx-70': ['cx70', 'сх-70', 'сх70'],
            'cx-80': ['cx80', 'сх-80', 'сх80'],
            'cx-90': ['cx90', 'сх-90', 'сх90'],
            'mx-5': ['mx5', 'мх-5', 'мх5'],
            'mx-30': ['mx30', 'мх-30', 'мх30'],
            'mazda3': ['mazda-3', 'мазда3', 'мазда-3'],
            'mazda6': ['mazda-6', 'мазда6', 'мазда-6'],
            'mazda2': ['mazda-2', 'мазда2', 'мазда-2'],
            'mazda cx-3': ['mazda cx3', 'мазда сх-3', 'мазда сх3'],
            'mazda cx-9': ['mazda cx9', 'мазда сх-9', 'мазда сх9'],
            'mazda cx-8': ['mazda cx8', 'мазда сх-8', 'мазда сх8'],
            'mazda cx-7': ['mazda cx7', 'мазда сх-7', 'мазда сх7'],
            'mazda cx-6': ['mazda cx6', 'мазда сх-6', 'мазда сх6'],
            'mazda cx-4': ['mazda cx4', 'мазда сх-4', 'мазда сх4'],
            'mazda cx-2': ['mazda cx2', 'мазда сх-2', 'мазда сх2'],
            'mazda cx-1': ['mazda cx1', 'мазда сх-1', 'мазда сх1'],
        }

    def normalize_text(self, text: str) -> str:
        """Нормализует текст для поиска"""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def find_best_match(self, query: str, candidates: List[str], threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """Находит лучшее совпадение среди кандидатов"""
        if not candidates:
            return None
            
        query = self.normalize_text(query)
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            normalized_candidate = self.normalize_text(candidate)
            score = difflib.SequenceMatcher(None, query, normalized_candidate).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
                
        return (best_match, best_score) if best_match else None

    def correct_brand(self, brand: str) -> Optional[str]:
        """Исправляет опечатки в названии бренда"""
        if not brand:
            return None
            
        normalized_brand = self.normalize_text(brand)
        
        # Поиск по синонимам
        for correct_brand, synonyms in self.brand_synonyms.items():
            if normalized_brand == self.normalize_text(correct_brand):
                return correct_brand
            if normalized_brand in [self.normalize_text(syn) for syn in synonyms]:
                return correct_brand
                
        # Fuzzy search
        all_brands = list(self.brand_synonyms.keys())
        result = self.find_best_match(normalized_brand, all_brands)
        
        return result[0] if result else None

    def correct_model(self, model: Optional[str] = None, brand: Optional[str] = None) -> Optional[str]:
        """Исправляет опечатки в названии модели"""
        if not model:
            return None
            
        normalized_model = self.normalize_text(model or '')
        
        # Поиск по синонимам
        for correct_model, synonyms in self.model_synonyms.items():
            if normalized_model == self.normalize_text(correct_model):
                return correct_model
            if normalized_model in [self.normalize_text(syn) for syn in synonyms]:
                return correct_model
                
        # Fuzzy search
        all_models = list(self.model_synonyms.keys())
        result = self.find_best_match(normalized_model, all_models)
        
        return result[0] if result else None

    def suggest_corrections(self, text: str) -> List[str]:
        """Предлагает исправления для текста"""
        suggestions = []
        words = text.split()
        
        for word in words:
            # Проверка брендов
            brand_correction = self.correct_brand(word or '')
            if brand_correction and brand_correction != word:
                suggestions.append(f"'{word}' -> '{brand_correction}' (бренд)")
                
            # Проверка моделей
            model_correction = self.correct_model(word or '', word or '')
            if model_correction and model_correction != word:
                suggestions.append(f"'{word}' -> '{model_correction}' (модель)")
                
        return suggestions

    def auto_correct_text(self, text: str) -> str:
        """Автоматически исправляет текст"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Исправление брендов
            if brand_correction := self.correct_brand(word or ''):
                corrected_words.append(brand_correction)
            # Исправление моделей
            elif model_correction := self.correct_model(word or '', word or ''):
                corrected_words.append(model_correction)
            else:
                corrected_words.append(word)
            
        return ' '.join(corrected_words)


# Создаем глобальный экземпляр
fuzzy_search = FuzzySearch() 
 
 
 
 
 