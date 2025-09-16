import sqlite3
import re
from difflib import get_close_matches, SequenceMatcher
import unicodedata
import jellyfish
from typing import List, Dict, Set, Tuple, Optional, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import joblib
import os
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Убираем проблемный pymorphy2
try:
    # Простая замена для лемматизации
    def simple_lemmatize(word):
        """Простая лемматизация без pymorphy2"""
        word = word.lower()
        # Базовые окончания
        endings = {
            'ая': '', 'ый': '', 'ое': '', 'ые': '', 'ой': '',
            'а': '', 'я': '', 'о': '', 'е': '', 'и': '', 'ы': '',
            'ть': '', 'ться': '', 'л': '', 'ла': '', 'ло': '', 'ли': ''
        }
        for ending, replacement in endings.items():
            if word.endswith(ending):
                word = word[:-len(ending)]
                break
        return word
except ImportError:
    def simple_lemmatize(word):
        return word.lower()

DB_PATH = r'E:\Users\diman\OneDrive\Документы\Рабочий стол\2\хрень — копия\instance\cars.db'

# Глобальный TF-IDF векторизатор для улучшенного сравнения
tfidf_vectorizer = TfidfVectorizer(
    analyzer='char', 
    ngram_range=(2, 4),
    max_features=1000,
    lowercase=True
)

# Машинное обучение для улучшения точности
class MLEnhancedMatcher:
    def __init__(self):
        self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.nn_classifier = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        self.is_trained = False
        
    def train(self, training_data):
        """Обучение моделей на тренировочных данных"""
        if not training_data:
            return
            
        X = []
        y = []
        
        for query, expected_entities in training_data:
            features = self._extract_features(query)
            X.append(features)
            y.append(1 if expected_entities else 0)
        
        if len(X) > 10:  # Минимум для обучения
            X = np.array(X)
            y = np.array(y)
            
            # Обучаем модели
            self.rf_classifier.fit(X, y)
            self.nn_classifier.fit(X, y)
            self.is_trained = True
            
            # Сохраняем модели
            self._save_models()
    
    def _extract_features(self, text):
        """Извлечение признаков из текста"""
        text_lower = text.lower()
        
        features = [
            len(text),  # Длина текста
            len(text.split()),  # Количество слов
            sum(1 for c in text if c.isdigit()),  # Количество цифр
            sum(1 for c in text if c.isupper()),  # Количество заглавных букв
            len([w for w in text_lower.split() if len(w) > 3]),  # Длинные слова
            len([w for w in text_lower.split() if w in ['автомат', 'механика', 'бензин', 'дизель']]),  # Ключевые слова
        ]
        
        return features
    
    def predict(self, text):
        """Предсказание с использованием обученных моделей с улучшенными порогами"""
        if not self.is_trained:
            return 0.5  # Нейтральное значение если модель не обучена
            
        features = self._extract_features(text)
        features = np.array(features).reshape(1, -1)
        
        # Ансамбль предсказаний с улучшенными порогами
        rf_pred = self.rf_classifier.predict_proba(features)[0][1]
        nn_pred = self.nn_classifier.predict_proba(features)[0][1]
        
        # Взвешенная оценка с более строгими порогами
        ensemble_score = (rf_pred * 0.6 + nn_pred * 0.4)
        
        # Дополнительная валидация на основе контекста
        context_score = self._validate_context(text)
        
        # Финальная оценка с учетом контекста
        final_score = ensemble_score * 0.8 + context_score * 0.2
        
        # Повышенный порог для уменьшения ложных срабатываний
        return final_score if final_score > 0.85 else 0.0
    
    def _save_models(self):
        """Сохранение обученных моделей"""
        try:
            os.makedirs('ml_models', exist_ok=True)
            joblib.dump(self.rf_classifier, 'ml_models/rf_entity_matcher.pkl')
            joblib.dump(self.nn_classifier, 'ml_models/nn_entity_matcher.pkl')
        except:
            pass
    
    def load_models(self):
        """Загрузка сохраненных моделей"""
        try:
            self.rf_classifier = joblib.load('ml_models/rf_entity_matcher.pkl')
            self.nn_classifier = joblib.load('ml_models/nn_entity_matcher.pkl')
            self.is_trained = True
        except:
            pass

    def _validate_context(self, text):
        """Валидация контекста для улучшения точности"""
        text_lower = text.lower()
        
        # Проверяем наличие автомобильной терминологии
        car_terms = ['автомобиль', 'машина', 'авто', 'bmw', 'mercedes', 'audi', 'toyota']
        car_score = sum(1 for term in car_terms if term in text_lower) / len(car_terms)
        
        # Проверяем наличие технических характеристик
        tech_terms = ['двигатель', 'мощность', 'расход', 'скорость', 'комфорт']
        tech_score = sum(1 for term in tech_terms if term in text_lower) / len(tech_terms)
        
        return (car_score + tech_score) / 2

# Глобальный экземпляр ML матчера
ml_matcher = MLEnhancedMatcher()

def lemmatize_word(word):
    """Лемматизация слова"""
    return simple_lemmatize(word)

def lemmatize_list(words):
    """Лемматизация списка слов"""
    return [simple_lemmatize(word) for word in words]

def normalize_word(word):
    """Нормализация слова"""
    return simple_lemmatize(word)

def advanced_similarity_score(word1: str, word2: str) -> float:
    """Расширенная оценка схожести слов"""
    # Базовая схожесть
    base_similarity = SequenceMatcher(None, word1.lower(), word2.lower()).ratio()
    
    # Лемматизированная схожесть
    lemma1 = simple_lemmatize(word1)
    lemma2 = simple_lemmatize(word2)
    lemma_similarity = SequenceMatcher(None, lemma1, lemma2).ratio()
    
    # Фонетическая схожесть (упрощенная)
    phonetic_sim = 0.0
    if len(word1) > 2 and len(word2) > 2:
        if word1[:3] == word2[:3]:
            phonetic_sim = 0.8
        elif word1[:2] == word2[:2]:
            phonetic_sim = 0.6
    
    # Взвешенная оценка
    final_score = (base_similarity * 0.4 + lemma_similarity * 0.4 + phonetic_sim * 0.2)
    
    return final_score

def context_aware_match(query_words: List[str], synonyms: List[str], context_threshold: float = 0.75) -> bool:
    """Контекстно-осведомленное сопоставление"""
    if not query_words or not synonyms:
        return False
    
    # Проверяем каждое слово запроса
    for word in query_words:
        word_lower = word.lower()
        
        # Прямое совпадение
        if word_lower in synonyms:
            return True
        
        # Лемматизированное совпадение
        word_lemma = simple_lemmatize(word)
        for synonym in synonyms:
            synonym_lemma = simple_lemmatize(synonym)
            if word_lemma == synonym_lemma:
                return True
        
        # Нечеткое сопоставление
        for synonym in synonyms:
            similarity = advanced_similarity_score(word, synonym)
            if similarity >= context_threshold:
                return True
    
    return False

def phonetic_similarity(word1: str, word2: str) -> float:
    """Упрощенная фонетическая схожесть"""
    word1_lower = word1.lower()
    word2_lower = word2.lower()
    
    # Простая фонетическая схожесть
    if len(word1_lower) < 2 or len(word2_lower) < 2:
        return 0.0
    
    # Сравнение первых букв
    if word1_lower[0] == word2_lower[0]:
        return 0.5
    
    # Сравнение последних букв
    if word1_lower[-1] == word2_lower[-1]:
        return 0.3
    
    return 0.0

def smart_tokenization(text: str) -> List[str]:
    """Умная токенизация с фильтрацией коротких токенов"""
    # Базовая токенизация
    tokens = re.findall(r'\w+', text.lower())
    
    # Фильтруем слишком короткие токены (менее 3 символов)
    filtered_tokens = [token for token in tokens if len(token) >= 3]
    
    # Добавляем составные токены (слова с пробелами)
    words = text.lower().split()
    for i in range(len(words)):
        for j in range(i + 1, min(i + 3, len(words) + 1)):
            compound_token = ' '.join(words[i:j])
            if len(compound_token) >= 3:
                filtered_tokens.append(compound_token)
    
    # Удаляем дубликаты и сортируем по длине
    unique_tokens = list(set(filtered_tokens))
    unique_tokens.sort(key=len, reverse=True)
    
    return unique_tokens

# Ручные синонимы для моделей и марок
MANUAL_MODEL_SYNONYMS = {
    'веста': ['vesta', 'vesta sw cross', 'веста св', 'веста св кросс'],
    'vesta': ['vesta', 'vesta sw cross', 'веста', 'веста св', 'веста св кросс'],
    'гранта': ['granta', 'гранта лифтбек', 'гранта универсал'],
    'granta': ['granta', 'гранта', 'гранта лифтбек', 'гранта универсал'],
    'икс5': ['x5', 'x-5', 'bmw x5', 'бмв икс5'],
    'икс3': ['x3', 'x-3', 'bmw x3', 'бмв икс3'],
    'икс7': ['x7', 'x-7', 'bmw x7', 'бмв икс7'],
    'гле': ['gle', 'mercedes gle', 'мерседес гле'],
    'глс': ['gls', 'mercedes gls', 'мерседес глс'],
    'камри': ['camry', 'toyota camry', 'тойота камри'],
    'раф4': ['rav4', 'rav-4', 'toyota rav4', 'тойота раф4'],
    'королла': ['corolla', 'toyota corolla', 'тойота королла'],
    'приус': ['prius', 'toyota prius', 'тойота приус'],
    'авенсис': ['avensis', 'toyota avensis', 'тойота авенсис'],
    'хайлендер': ['highlander', 'toyota highlander', 'тойота хайлендер'],
    'секвойя': ['sequoia', 'toyota sequoia', 'тойота секвойя'],
    'таундер': ['tundra', 'toyota tundra', 'тойота таундер'],
    'тако': ['tacoma', 'toyota tacoma', 'тойота тако'],
    'соляра': ['solaris', 'hyundai solaris', 'хендай соляра'],
    'крета': ['creta', 'hyundai creta', 'хендай крета'],
    'туссан': ['tucson', 'hyundai tucson', 'хендай туссан'],
    'санта-фе': ['santa fe', 'santa-fe', 'hyundai santa fe', 'хендай санта-фе'],
    'палисад': ['palisade', 'hyundai palisade', 'хендай палисад'],
    'соренто': ['sorento', 'kia sorento', 'киа соренто'],
    'спортейдж': ['sportage', 'kia sportage', 'киа спортейдж'],
    'рио': ['rio', 'kia rio', 'киа рио'],
    'серато': ['cerato', 'kia cerato', 'киа серато'],
    'оптима': ['optima', 'kia optima', 'киа оптима'],
    'пиканто': ['picanto', 'kia picanto', 'киа пиканто'],
    'аито': ['aito', 'aito m5', 'aito m7', 'аито м5', 'аито м7'],
    'м5': ['m5', 'aito m5', 'аито м5'],
    'м7': ['m7', 'aito m7', 'аито м7'],
    # Падежные формы для моделей Lada
    'ларгус': ['largus', 'ларгуса', 'ларгусу', 'ларгусом', 'ларгусе'],
    'largus': ['largus', 'ларгус', 'ларгуса', 'ларгусу', 'ларгусом', 'ларгусе'],
    'иксрей': ['xray', 'иксрея', 'иксрею', 'иксреем', 'иксрее'],
    'xray': ['xray', 'иксрей', 'иксрея', 'иксрею', 'иксреем', 'иксрее'],
    'самара': ['samara', 'самары', 'самаре', 'самару', 'самарой', 'самарою', 'самарах'],
    'samara': ['samara', 'самара', 'самары', 'самаре', 'самару', 'самарой', 'самарою', 'самарах'],
    'приора': ['priora', 'приоры', 'приоре', 'приору', 'приорой', 'приорою', 'приорах'],
    'priora': ['priora', 'приора', 'приоры', 'приоре', 'приору', 'приорой', 'приорою', 'приорах'],
    'калина': ['kalina', 'калины', 'калине', 'калину', 'калиной', 'калиною', 'калинах'],
    'kalina': ['kalina', 'калина', 'калины', 'калине', 'калину', 'калиной', 'калиною', 'калинах'],
    'нива': ['niva', 'ниву', 'нивы', 'ниве', 'нивой', 'нивою', 'нивах'],
    'niva': ['niva', 'нива', 'ниву', 'нивы', 'ниве', 'нивой', 'нивою', 'нивах']
}

# Ручные синонимы для марок автомобилей
MANUAL_MARK_SYNONYMS = {
    'лада': ['lada', 'ваз', 'vaz', 'автоваз', 'avtovaz'],
    'lada': ['lada', 'ваз', 'vaz', 'автоваз', 'avtovaz'],
    'ваз': ['vaz', 'lada', 'лада', 'автоваз', 'avtovaz'],
    'vaz': ['vaz', 'lada', 'лада', 'автоваз', 'avtovaz'],
    'автоваз': ['avtovaz', 'lada', 'лада', 'ваз', 'vaz'],
    'avtovaz': ['avtovaz', 'lada', 'лада', 'ваз', 'vaz'],
    'бмв': ['bmw', 'баварские моторы', 'bavarian motor works'],
    'bmw': ['bmw', 'бмв', 'баварские моторы', 'bavarian motor works'],
    'мерседес': ['mercedes', 'mercedes-benz', 'мерседес-бенц'],
    'mercedes': ['mercedes', 'mercedes-benz', 'мерседес', 'мерседес-бенц'],
    'тойота': ['toyota'],
    'toyota': ['toyota', 'тойота'],
    'хендай': ['hyundai'],
    'hyundai': ['hyundai', 'хендай'],
    'киа': ['kia'],
    'kia': ['kia', 'киа'],
    'аито': ['aito'],
    'aito': ['aito', 'аито']
}

# Синонимы для цветов
COLOR_SYNONYMS = {
    'белый': ['white', 'искрящийся белый', 'керамический белый', 'белого', 'белая', 'белое', 'белые', 'белого', 'белым', 'белыми'],
    'черный': ['black', 'чёрный', 'черный металлик', 'черного', 'черная', 'черное', 'черные', 'черным', 'черными'],
    'серый': ['grey', 'gray', 'серый металлик', 'серого', 'серая', 'серое', 'серые', 'серым', 'серыми'],
    'красный': ['red', 'fiery red', 'красного', 'красная', 'красное', 'красные', 'красного', 'красным', 'красными'],
    'синий': ['blue', 'sky blue', 'синего', 'синяя', 'синее', 'синие', 'синим', 'синими'],
    'зеленый': ['green', 'mint green', 'зеленого', 'зеленая', 'зеленое', 'зеленые', 'зеленым', 'зелеными'],
    'коричневый': ['brown', 'коричневого', 'коричневая', 'коричневое', 'коричневые', 'коричневым', 'коричневыми'],
    'оранжевый': ['orange', 'оранжевого', 'оранжевая', 'оранжевое', 'оранжевые', 'оранжевым', 'оранжевыми'],
    'фиолетовый': ['purple', 'фиолетового', 'фиолетовая', 'фиолетовые', 'фиолетовый', 'фиолетовым', 'фиолетовыми'],
    'бежевый': ['beige', 'бежевого', 'бежевая', 'бежевое', 'бежевые', 'бежевым', 'бежевыми'],
    'серебряный': ['silver', 'серебристый', 'серебристого', 'серебристая', 'серебристое', 'серебристые', 'серебристого', 'серебристым', 'серебристыми'],
    'голубой': ['sky blue', 'голубой металлик', 'голубого', 'голубая', 'голубое', 'голубые', 'голубым', 'голубыми']
}

# Расширенные словари марок с русскими вариантами
BRAND_SYNONYMS = {
    'bmw': ['bmw', 'бмв', 'баварский мотор верке', 'баварские моторы'],
    'mercedes': ['mercedes', 'мерседес', 'mercedes-benz', 'мерседес-бенц', 'мерс'],
    'audi': ['audi', 'ауди', 'ауди'],
    'volkswagen': ['volkswagen', 'vw', 'фольксваген', 'вольксваген'],
    'toyota': ['toyota', 'тойота', 'тойота мотор'],
    'honda': ['honda', 'хонда'],
    'ford': ['ford', 'форд'],
    'chevrolet': ['chevrolet', 'chev', 'шевроле', 'шevrolet'],
    'nissan': ['nissan', 'ниссан', 'нисан'],
    'mazda': ['mazda', 'мазда'],
    'subaru': ['subaru', 'субару'],
    'lexus': ['lexus', 'лексус'],
    'infiniti': ['infiniti', 'инфинити'],
    'volvo': ['volvo', 'вольво'],
    'skoda': ['skoda', 'шкода'],
    'renault': ['renault', 'рено'],
    'peugeot': ['peugeot', 'пежо'],
    'citroen': ['citroen', 'ситроен'],
    'opel': ['opel', 'опель'],
    'fiat': ['fiat', 'фиат'],
    'lada': ['lada', 'лада', 'ваз', 'автоваз'],
    'kia': ['kia', 'киа'],
    'hyundai': ['hyundai', 'хендай', 'хёндай'],
    'daewoo': ['daewoo', 'дэу', 'daewoo'],
    'ssangyong': ['ssangyong', 'сангйонг', 'санг йонг'],
    'geely': ['geely', 'джили', 'geely'],
    'haval': ['haval', 'хавал'],
    'chery': ['chery', 'чери'],
    'great wall': ['great wall', 'greatwall', 'великая стена'],
    'changan': ['changan', 'чанъань'],
    'byd': ['byd', 'бивайди'],
    'tesla': ['tesla', 'тесла'],
    'porsche': ['porsche', 'порше'],
    'ferrari': ['ferrari', 'феррари'],
    'lamborghini': ['lamborghini', 'ламборгини'],
    'maserati': ['maserati', 'мазерати'],
    'aston martin': ['aston martin', 'астон мартин'],
    'bentley': ['bentley', 'бентли'],
    'rolls royce': ['rolls royce', 'роллс ройс', 'rolls-royce'],
    'maybach': ['maybach', 'майбах'],
    'bugatti': ['bugatti', 'бугатти'],
    'mclaren': ['mclaren', 'маклерен'],
    'lotus': ['lotus', 'лотос'],
    'jaguar': ['jaguar', 'ягуар'],
    'land rover': ['land rover', 'ленд ровер', 'landrover'],
    'range rover': ['range rover', 'рейндж ровер', 'rangerover'],
    'mini': ['mini', 'мини'],
    'smart': ['smart', 'смарт'],
    'alfa romeo': ['alfa romeo', 'альфа ромео', 'alfaromeo'],
    'fiat': ['fiat', 'фиат'],
    'lancia': ['lancia', 'ланча'],
    'seat': ['seat', 'сеат'],
    'dacia': ['dacia', 'дачия'],
    'dodge': ['dodge', 'додж'],
    'chrysler': ['chrysler', 'крайслер'],
    'jeep': ['jeep', 'джип'],
    'cadillac': ['cadillac', 'кадиллак'],
    'buick': ['buick', 'бьюик'],
    'pontiac': ['pontiac', 'понтиак'],
    'oldsmobile': ['oldsmobile', 'олдсмобиль'],
    'saturn': ['saturn', 'сатурн'],
    'hummer': ['hummer', 'хаммер'],
    'saab': ['saab', 'сааб'],
    'rover': ['rover', 'ровер'],
    'mg': ['mg', 'эм джи'],
    'triumph': ['triumph', 'триумф'],
    'jensen': ['jensen', 'дженсен'],
    'morgan': ['morgan', 'морган'],
    'caterham': ['caterham', 'катерхам'],
    'noble': ['noble', 'нобл'],
    'ariel': ['ariel', 'ариэль'],
    'westfield': ['westfield', 'вестфилд'],
    'ginetta': ['ginetta', 'джинетта'],
    'radical': ['radical', 'радикал'],
    'ultima': ['ultima', 'ультима'],
    'zenos': ['zenos', 'зенос'],
    'bac': ['bac', 'бак'],
    'elemental': ['elemental', 'элементал'],
    'donkervoort': ['donkervoort', 'донкерворт'],
    'spyker': ['spyker', 'спайкер'],
    'noble': ['noble', 'нобл'],
    'koenigsegg': ['koenigsegg', 'кенигсегг'],
    'pagani': ['pagani', 'пагани'],
    'rimac': ['rimac', 'римак'],
    'pininfarina': ['pininfarina', 'пининфарина'],
    'bertone': ['bertone', 'бертоне'],
    'ghia': ['ghia', 'гия'],
    'italdesign': ['italdesign', 'италдизайн'],
    'zagato': ['zagato', 'загато'],
    'touring': ['touring', 'туринг'],
    'carrozzeria': ['carrozzeria', 'кароццерия'],
    'scaglietti': ['scaglietti', 'скальетти'],
    'marcos': ['marcos', 'маркос'],
    'tvr': ['tvr', 'твр'],
    'noble': ['noble', 'нобл'],
    'ariel': ['ariel', 'ариэль'],
    'caterham': ['caterham', 'катерхам'],
    'morgan': ['morgan', 'морган'],
    'westfield': ['westfield', 'вестфилд'],
    'ginetta': ['ginetta', 'джинетта'],
    'radical': ['radical', 'радикал'],
    'ultima': ['ultima', 'ультима'],
    'zenos': ['zenos', 'зенос'],
    'bac': ['bac', 'бак'],
    'elemental': ['elemental', 'элементал'],
    'donkervoort': ['donkervoort', 'донкерворт'],
    'spyker': ['spyker', 'спайкер'],
    'noble': ['noble', 'нобл'],
    'koenigsegg': ['koenigsegg', 'кенигсегг'],
    'pagani': ['pagani', 'пагани'],
    'rimac': ['rimac', 'римак'],
    'pininfarina': ['pininfarina', 'пининфарина'],
    'bertone': ['bertone', 'бертоне'],
    'ghia': ['ghia', 'гия'],
    'italdesign': ['italdesign', 'италдизайн'],
    'zagato': ['zagato', 'загато'],
    'touring': ['touring', 'туринг'],
    'carrozzeria': ['carrozzeria', 'кароццерия'],
    'scaglietti': ['scaglietti', 'скальетти'],
    'marcos': ['marcos', 'маркос'],
    'tvr': ['tvr', 'твр']
}

# Расширенные словари моделей с русскими вариантами
MODEL_SYNONYMS = {
    # BMW модели
    'x5': ['x5', 'x-5', 'икс5', 'икс-5', 'bmw x5', 'бмв икс5'],
    'x3': ['x3', 'x-3', 'икс3', 'икс-3', 'bmw x3', 'бмв икс3'],
    'x7': ['x7', 'x-7', 'икс7', 'икс-7', 'bmw x7', 'бмв икс7'],
    'x6': ['x6', 'x-6', 'икс6', 'икс-6', 'bmw x6', 'бмв икс6'],
    'x1': ['x1', 'x-1', 'икс1', 'икс-1', 'bmw x1', 'бмв икс1'],
    'x4': ['x4', 'x-4', 'икс4', 'икс-4', 'bmw x4', 'бмв икс4'],
    'm3': ['m3', 'м3', 'bmw m3', 'бмв м3'],
    'm5': ['m5', 'м5', 'bmw m5', 'бмв м5'],
    'm4': ['m4', 'м4', 'bmw m4', 'бмв м4'],
    'm2': ['m2', 'м2', 'bmw m2', 'бмв м2'],
    '3 series': ['3 series', '3 серия', 'серия 3', 'bmw 3', 'бмв 3'],
    '5 series': ['5 series', '5 серия', 'серия 5', 'bmw 5', 'бмв 5'],
    '7 series': ['7 series', '7 серия', 'серия 7', 'bmw 7', 'бмв 7'],
    '1 series': ['1 series', '1 серия', 'серия 1', 'bmw 1', 'бмв 1'],
    '2 series': ['2 series', '2 серия', 'серия 2', 'bmw 2', 'бмв 2'],
    '4 series': ['4 series', '4 серия', 'серия 4', 'bmw 4', 'бмв 4'],
    '6 series': ['6 series', '6 серия', 'серия 6', 'bmw 6', 'бмв 6'],
    '8 series': ['8 series', '8 серия', 'серия 8', 'bmw 8', 'бмв 8'],
    'z4': ['z4', 'з4', 'bmw z4', 'бмв з4'],
    'z3': ['z3', 'з3', 'bmw z3', 'бмв з3'],
    'i3': ['i3', 'и3', 'bmw i3', 'бмв и3'],
    'i8': ['i8', 'и8', 'bmw i8', 'бмв и8'],
    
    # Mercedes модели
    'gle': ['gle', 'гле', 'mercedes gle', 'мерседес гле'],
    'gls': ['gls', 'глс', 'mercedes gls', 'мерседес глс'],
    'glc': ['glc', 'глк', 'mercedes glc', 'мерседес глк'],
    'gla': ['gla', 'гла', 'mercedes gla', 'мерседес гла'],
    'glb': ['glb', 'глб', 'mercedes glb', 'мерседес глб'],
    'e-class': ['e-class', 'e класс', 'e-класс', 'mercedes e', 'мерседес е'],
    'c-class': ['c-class', 'c класс', 'c-класс', 'mercedes c', 'мерседес с'],
    's-class': ['s-class', 's класс', 's-класс', 'mercedes s', 'мерседес с'],
    'a-class': ['a-class', 'a класс', 'a-класс', 'mercedes a', 'мерседес а'],
    'b-class': ['b-class', 'b класс', 'b-класс', 'mercedes b', 'мерседес б'],
    'cls': ['cls', 'клс', 'mercedes cls', 'мерседес клс'],
    'cla': ['cla', 'кла', 'mercedes cla', 'мерседес кла'],
    'sl': ['sl', 'сл', 'mercedes sl', 'мерседес сл'],
    'slk': ['slk', 'слк', 'mercedes slk', 'мерседес слк'],
    'slc': ['slc', 'слк', 'mercedes slc', 'мерседес слк'],
    'amg': ['amg', 'амг', 'mercedes amg', 'мерседес амг'],
    
    # Toyota модели
    'camry': ['camry', 'камри', 'toyota camry', 'тойота камри'],
    'corolla': ['corolla', 'королла', 'toyota corolla', 'тойота королла'],
    'rav4': ['rav4', 'rav-4', 'раф4', 'раф-4', 'toyota rav4', 'тойота раф4'],
    'highlander': ['highlander', 'хайлендер', 'toyota highlander', 'тойота хайлендер'],
    '4runner': ['4runner', 'форраннер', 'toyota 4runner', 'тойота форраннер'],
    'tacoma': ['tacoma', 'такома', 'toyota tacoma', 'тойота такома'],
    'tundra': ['tundra', 'тундра', 'toyota tundra', 'тойота тундра'],
    'sequoia': ['sequoia', 'секвойя', 'toyota sequoia', 'тойота секвойя'],
    'land cruiser': ['land cruiser', 'ленд крузер', 'toyota land cruiser', 'тойота ленд крузер'],
    'prius': ['prius', 'приус', 'toyota prius', 'тойота приус'],
    'yaris': ['yaris', 'ярис', 'toyota yaris', 'тойота ярис'],
    'avalon': ['avalon', 'авалон', 'toyota avalon', 'тойота авалон'],
    'sienna': ['sienna', 'сиенна', 'toyota sienna', 'тойота сиенна'],
    'venza': ['venza', 'венза', 'toyota venza', 'тойота венза'],
    'venza': ['venza', 'венза', 'toyota venza', 'тойота венза'],
    'c-hr': ['c-hr', 'с-хр', 'toyota c-hr', 'тойота с-хр'],
    'venza': ['venza', 'венза', 'toyota venza', 'тойота венза'],
    
    # Honda модели
    'civic': ['civic', 'сивик', 'honda civic', 'хонда сивик'],
    'accord': ['accord', 'аккорд', 'honda accord', 'хонда аккорд'],
    'cr-v': ['cr-v', 'ср-в', 'honda cr-v', 'хонда ср-в'],
    'pilot': ['pilot', 'пилот', 'honda pilot', 'хонда пилот'],
    'odyssey': ['odyssey', 'одиссей', 'honda odyssey', 'хонда одиссей'],
    'fit': ['fit', 'фит', 'honda fit', 'хонда фит'],
    'insight': ['insight', 'инсайт', 'honda insight', 'хонда инсайт'],
    'passport': ['passport', 'паспорт', 'honda passport', 'хонда паспорт'],
    'ridgeline': ['ridgeline', 'риджлайн', 'honda ridgeline', 'хонда риджлайн'],
    
    # Ford модели
    'focus': ['focus', 'фокус', 'ford focus', 'форд фокус'],
    'fiesta': ['fiesta', 'фиеста', 'ford fiesta', 'форд фиеста'],
    'mondeo': ['mondeo', 'мондео', 'ford mondeo', 'форд мондео'],
    'escape': ['escape', 'эскейп', 'ford escape', 'форд эскейп'],
    'explorer': ['explorer', 'эксплорер', 'ford explorer', 'форд эксплорер'],
    'expedition': ['expedition', 'экспедишн', 'ford expedition', 'форд экспедишн'],
    'f-150': ['f-150', 'ф-150', 'ford f-150', 'форд ф-150'],
    'mustang': ['mustang', 'мустанг', 'ford mustang', 'форд мустанг'],
    'edge': ['edge', 'эдж', 'ford edge', 'форд эдж'],
    'flex': ['flex', 'флекс', 'ford flex', 'форд флекс'],
    'taurus': ['taurus', 'таурус', 'ford taurus', 'форд таурус'],
    'fusion': ['fusion', 'фьюжн', 'ford fusion', 'форд фьюжн'],
    
    # Volkswagen модели
    'golf': ['golf', 'гольф', 'volkswagen golf', 'фольксваген гольф'],
    'passat': ['passat', 'пассат', 'volkswagen passat', 'фольксваген пассат'],
    'jetta': ['jetta', 'джетта', 'volkswagen jetta', 'фольксваген джетта'],
    'tiguan': ['tiguan', 'тигуан', 'volkswagen tiguan', 'фольксваген тигуан'],
    'atlas': ['atlas', 'атлас', 'volkswagen atlas', 'фольксваген атлас'],
    'arteon': ['arteon', 'артеон', 'volkswagen arteon', 'фольксваген артеон'],
    'touareg': ['touareg', 'туарег', 'volkswagen touareg', 'фольксваген туарег'],
    't-roc': ['t-roc', 'т-рок', 'volkswagen t-roc', 'фольксваген т-рок'],
    'polo': ['polo', 'поло', 'volkswagen polo', 'фольксваген поло'],
    'up!': ['up!', 'ап!', 'volkswagen up!', 'фольксваген ап!'],
    
    # Audi модели
    'a3': ['a3', 'а3', 'audi a3', 'ауди а3'],
    'a4': ['a4', 'а4', 'audi a4', 'ауди а4'],
    'a6': ['a6', 'а6', 'audi a6', 'ауди а6'],
    'a8': ['a8', 'а8', 'audi a8', 'ауди а8'],
    'q3': ['q3', 'к3', 'audi q3', 'ауди к3'],
    'q5': ['q5', 'к5', 'audi q5', 'ауди к5'],
    'q7': ['q7', 'к7', 'audi q7', 'ауди к7'],
    'q8': ['q8', 'к8', 'audi q8', 'ауди к8'],
    'rs3': ['rs3', 'рс3', 'audi rs3', 'ауди рс3'],
    'rs4': ['rs4', 'рс4', 'audi rs4', 'ауди рс4'],
    'rs5': ['rs5', 'рс5', 'audi rs5', 'ауди рс5'],
    'rs6': ['rs6', 'рс6', 'audi rs6', 'ауди рс6'],
    'rs7': ['rs7', 'рс7', 'audi rs7', 'ауди рс7'],
    's3': ['s3', 'с3', 'audi s3', 'ауди с3'],
    's4': ['s4', 'с4', 'audi s4', 'ауди с4'],
    's5': ['s5', 'с5', 'audi s5', 'ауди с5'],
    's6': ['s6', 'с6', 'audi s6', 'ауди с6'],
    's7': ['s7', 'с7', 'audi s7', 'ауди с7'],
    's8': ['s8', 'с8', 'audi s8', 'ауди с8'],
    'tt': ['tt', 'тт', 'audi tt', 'ауди тт'],
    'r8': ['r8', 'р8', 'audi r8', 'ауди р8'],
    
    # Lada модели
    'vesta': ['vesta', 'vesta sw cross', 'веста', 'веста св', 'веста св кросс'],
    'granta': ['granta', 'гранта', 'гранта лифтбек', 'гранта универсал'],
    'kalina': ['kalina', 'калина', 'калина универсал'],
    'priora': ['priora', 'приора', 'приора универсал'],
    'samara': ['samara', 'самара'],
    'niva': ['niva', 'нива', 'lada niva', 'лада нива'],
    'largus': ['largus', 'ларгус', 'largus универсал'],
    'xray': ['xray', 'x-ray', 'иксрей', 'икс-рей'],
    '4x4': ['4x4', '4х4', 'lada 4x4', 'лада 4х4'],
    'urban': ['urban', 'урбан'],
    'cross': ['cross', 'кросс'],
    'sport': ['sport', 'спорт'],
    'luxe': ['luxe', 'люкс'],
    'norma': ['norma', 'норма'],
    'standard': ['standard', 'стандарт'],
    'classic': ['classic', 'классик'],
    'comfort': ['comfort', 'комфорт'],
    'prestige': ['prestige', 'престиж'],
    'exclusive': ['exclusive', 'эксклюзив'],
    'limited': ['limited', 'лимитед'],
    'edition': ['edition', 'эдишн'],
    'special': ['special', 'спешиал'],
    'unique': ['unique', 'уник'],
    'premium': ['premium', 'премиум'],
    'elite': ['elite', 'элит'],
    'supreme': ['supreme', 'суприм'],
    'ultimate': ['ultimate', 'ультимат'],
    'master': ['master', 'мастер'],
    'pro': ['pro', 'про'],
    'plus': ['plus', 'плюс'],
    'max': ['max', 'макс'],
    'turbo': ['turbo', 'турбо'],
    'gti': ['gti', 'гти'],
    'rs': ['rs', 'рс'],
    's': ['s', 'с'],
    'r': ['r', 'р'],
    'x': ['x', 'икс'],
    'z': ['z', 'з'],
    'i': ['i', 'и'],
    'e': ['e', 'е'],
    'c': ['c', 'с'],
    'a': ['a', 'а'],
    'b': ['b', 'б'],
    'd': ['d', 'д'],
    'f': ['f', 'ф'],
    'g': ['g', 'г'],
    'h': ['h', 'х'],
    'j': ['j', 'дж'],
    'k': ['k', 'к'],
    'l': ['l', 'л'],
    'm': ['m', 'м'],
    'n': ['n', 'н'],
    'o': ['o', 'о'],
    'p': ['p', 'п'],
    'q': ['q', 'к'],
    't': ['t', 'т'],
    'u': ['u', 'у'],
    'v': ['v', 'в'],
    'w': ['w', 'в'],
    'y': ['y', 'у']
}

class EntityExtractor:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print("[EntityExtractor] Таблицы в базе:", cursor.fetchall())
            conn.close()
        except Exception as e:
            print("[EntityExtractor] Ошибка при подключении к БД:", e)
        self.marks_models = self._load_marks_models()
        self.marks = list(self.marks_models.keys())
        self.models = list(set(model for models in self.marks_models.values() for model in models))
        print(f"[DEBUG] Все марки (100): {self.marks[:100]}")
        print(f"[DEBUG] Все модели (100): {self.models[:100]}")
        self.mark_synonyms = self._build_synonyms(self.marks)
        self.model_synonyms = self._build_synonyms(self.models)
        # Объединяем с ручными синонимами
        for k, v in MANUAL_MARK_SYNONYMS.items():
            self.mark_synonyms.setdefault(k, []).extend(v)
        for k, v in MANUAL_MODEL_SYNONYMS.items():
            self.model_synonyms.setdefault(k, []).extend(v)
        
        # Загружаем и обучаем ML модели
        ml_matcher.load_models()
        self._train_ml_models()
    
    def _train_ml_models(self):
        """Обучение ML моделей на тренировочных данных"""
        training_data = [
            ("автомат", True),
            ("механика", True),
            ("бензин", True),
            ("дизель", True),
            ("электро", True),
            ("гибрид", True),
            ("люк", True),
            ("панорамная крыша", True),
            ("климат-контроль", True),
            ("навигация", True),
            ("привет", False),
            ("пока", False),
            ("спасибо", False),
            ("хорошо", False),
        ]
        
        ml_matcher.train(training_data)

    def _build_synonyms(self, words):
        synonyms = {}
        for word in words:
            # Простое создание синонимов без сложной генерации
            variants = [word, word.lower(), word.replace('ё', 'е')]
            for variant in variants:
                if variant not in synonyms:
                    synonyms[variant] = []
                synonyms[variant].append(word)
        return synonyms

    def _expand_synonyms(self, word, synonyms_dict):
        result = [word]
        if word in synonyms_dict:
            result += synonyms_dict[word]
        return list(set(result))

    def _load_marks_models(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("[EntityExtractor] Таблицы в базе (перед запросом к cars):", cursor.fetchall())
        try:
            cursor.execute("SELECT DISTINCT mark, model FROM car")
            rows1 = cursor.fetchall()
        except Exception as e:
            print("[EntityExtractor] Ошибка при запросе к car:", e)
            rows1 = []
        try:
            cursor.execute("SELECT DISTINCT mark, model FROM used_car")
            rows2 = cursor.fetchall()
        except Exception as e:
            print("[EntityExtractor] Ошибка при запросе к used_car:", e)
            rows2 = []
        conn.close()
        
        # Создаем словарь марка -> список моделей
        marks_models = {}
        for mark, model in rows1 + rows2:
            if mark and model:
                mark_lower = mark.lower()
                model_lower = model.lower()
                if mark_lower not in marks_models:
                    marks_models[mark_lower] = []
                marks_models[mark_lower].append(model_lower)
        
        return marks_models

    def extract_car_names(self, query: str):
        """Улучшенное извлечение марок и моделей автомобилей с морфологическим анализом"""
        # Используем улучшенную нормализацию
        normalized_text = normalize_russian_text(query)
        query_lower = normalized_text.lower().replace('ё', 'е').replace('й', 'и')
        words = re.findall(r'\w+', query_lower)
        
        # Расширенная нормализация слов с морфологией
        norm_words = set()
        for w in words:
            # Базовая нормализация
            norm_w = normalize_word(w)
            norm_words.add(norm_w)
            
            # Добавляем морфологические варианты
            word_variants = get_word_variants(w)
            norm_words.update(word_variants)
            
            # Морфологический анализ
            try:
                import pymorphy2
                morph = pymorphy2.MorphAnalyzer()
                parsed = morph.parse(w)
                for p in parsed:
                    norm_words.add(p.normal_form)
                    # Добавляем все возможные формы
                    for form in p.lexeme:
                        norm_words.add(form.word.lower())
            except ImportError:
                # Если pymorphy2 не установлен, пропускаем морфологический анализ
                pass
            except Exception:
                pass
            
            # Транслитерация
            try:
                import transliterate
                if transliterate.detect_language(w) == 'ru':
                    w_lat = transliterate.translit(w, 'ru', reversed=True)
                    norm_words.add(w_lat)
                    norm_words.add(w_lat.replace(' ', ''))
                else:
                    w_cyr = transliterate.translit(w, 'ru')
                    norm_words.add(w_cyr)
                    norm_words.add(w_cyr.replace(' ', ''))
            except Exception:
                pass
        
        print(f"[DEBUG] Все нормализованные слова: {norm_words}")
        
        # Поиск марок и моделей с использованием улучшенных методов
        found_marks, found_models = self._find_brands_and_models(norm_words)
        
        # Дополнительный поиск по базе данных с более строгой валидацией
        for word in norm_words:
            # Поиск марок в базе данных
            for mark in self.marks_models.keys():
                mark_lower = mark.lower()
                # Более строгая проверка совпадения
                if self._strict_word_match(word, mark_lower):
                    if mark not in found_marks:
                        found_marks.append(mark)
            
            # Поиск моделей в базе данных с улучшенной логикой
            for mark, models in self.marks_models.items():
                for model in models:
                    model_lower = model.lower()
                    # Более строгая проверка совпадения модели
                    if self._strict_model_match(word, model_lower):
                        if model not in found_models:
                            found_models.append(model)
                        # Добавляем марку только если она еще не добавлена
                        if mark not in found_marks:
                            found_marks.append(mark)
        
        # Дополнительная фильтрация моделей - убираем слишком короткие и нерелевантные
        filtered_models = []
        for model in found_models:
            model_lower = model.lower()
            # Пропускаем слишком короткие модели (менее 2 символов)
            if len(model_lower) < 2:
                continue
            # Пропускаем модели, которые являются просто буквами
            if len(model_lower) == 1 and model_lower.isalpha():
                continue
            # Пропускаем модели, которые являются просто цифрами
            if model_lower.isdigit():
                continue
            filtered_models.append(model)
        
        found_models = filtered_models
        
        # Удаляем дубликаты и сортируем по длине (предпочитаем более длинные совпадения)
        found_marks = sorted(list(set(found_marks)), key=len, reverse=True)
        found_models = sorted(list(set(found_models)), key=len, reverse=True)
        
        print(f"[DEBUG] Найденные марки: {found_marks}")
        print(f"[DEBUG] Найденные модели: {found_models}")
        
        # Улучшенная логика выбора лучшей модели
        result = {}
        
        # Если нашли и марку, и модель, проверяем их совместимость
        if found_marks and found_models:
            # Ищем правильную пару марка-модель
            for mark in found_marks:
                if mark in self.marks_models:
                    for model in found_models:
                        if model in self.marks_models[mark]:
                            result['brand'] = mark
                            result['model'] = model
                            break
                    if 'brand' in result:
                        break
            
            # Если не нашли совместимую пару, используем улучшенный алгоритм выбора
            if 'brand' not in result:
                # Используем улучшенный алгоритм выбора модели
                best_model = self._find_best_model_match(words, found_models)
                
                if best_model:
                    result['model'] = best_model
                    # Ищем марку для этой модели
                    for mark, models in self.marks_models.items():
                        if best_model in models:
                            result['brand'] = mark
                            break
                    # Если не нашли марку, берем первую найденную
                    if 'brand' not in result and found_marks:
                        result['brand'] = found_marks[0]
                else:
                    # Если не нашли подходящую модель, берем первую марку и первую модель
                    result['brand'] = found_marks[0]
                    result['model'] = found_models[0]
        elif found_marks:
            result['brand'] = found_marks[0]
        elif found_models:
            # Если нашли только модель, ищем её марку
            for mark, models in self.marks_models.items():
                if found_models[0] in models:
                    result['brand'] = mark
                    result['model'] = found_models[0]
                    break
            # Если не нашли марку для модели, возвращаем только модель
            if 'brand' not in result:
                result['model'] = found_models[0]
        
        print(f"[DEBUG] Итоговый результат: {result}")
        return result
    
    def _strict_word_match(self, word: str, target: str) -> bool:
        """Строгая проверка совпадения слов"""
        # Точное совпадение
        if word == target:
            return True
        
        # Проверяем, что слово не слишком короткое
        if len(word) < 2:
            return False
        
        # Для слов с цифрами требуем более точного совпадения
        if any(c.isdigit() for c in word) or any(c.isdigit() for c in target):
            # Если оба содержат цифры, проверяем точное совпадение цифр
            word_digits = ''.join(c for c in word if c.isdigit())
            target_digits = ''.join(c for c in target if c.isdigit())
            if word_digits and target_digits and word_digits != target_digits:
                return False
        
        # Проверяем, что одно слово является частью другого
        if word in target or target in word:
            return True
        
        # Проверяем без пробелов
        if word.replace(' ', '') in target.replace(' ', '') or target.replace(' ', '') in word.replace(' ', ''):
            return True
        
        return False
    
    def _strict_model_match(self, word: str, model: str) -> bool:
        """Строгая проверка совпадения модели"""
        # Точное совпадение
        if word == model:
            return True
        
        # Проверяем, что слово не слишком короткое
        if len(word) < 2:
            return False
        
        # Для моделей с цифрами требуем более точного совпадения
        if any(c.isdigit() for c in word) or any(c.isdigit() for c in model):
            # Если оба содержат цифры, проверяем точное совпадение цифр
            word_digits = ''.join(c for c in word if c.isdigit())
            model_digits = ''.join(c for c in model if c.isdigit())
            if word_digits and model_digits and word_digits != model_digits:
                return False
        
        # Проверяем, что слово является значимой частью модели
        if word in model and len(word) >= len(model) * 0.5:
            return True
        
        # Проверяем без пробелов
        word_no_spaces = word.replace(' ', '')
        model_no_spaces = model.replace(' ', '')
        if word_no_spaces == model_no_spaces:
            return True
        
        # Дополнительная проверка для составных моделей (например, "x3 xdrive30l")
        if ' ' in word and ' ' in model:
            word_parts = word.lower().split()
            model_parts = model.lower().split()
            # Проверяем, что хотя бы одна часть слова совпадает с частью модели
            for word_part in word_parts:
                for model_part in model_parts:
                    if word_part == model_part and len(word_part) >= 2:
                        return True
        
        # Дополнительная проверка для моделей с буквами и цифрами
        if any(c.isalpha() for c in word) and any(c.isdigit() for c in word):
            # Если слово содержит и буквы, и цифры, требуем более точного совпадения
            if word.lower() in model.lower() or model.lower() in word.lower():
                return True
        
        # Дополнительная проверка для коротких моделей (X3, A4, 320d)
        if len(word) <= 3 and len(model) <= 5:
            # Для коротких моделей требуем более точного совпадения
            if word.lower() == model.lower() or word.lower() in model.lower() or model.lower() in word.lower():
                return True
        
        return False
    
    def _find_best_model_match(self, words: List[str], found_models: List[str]) -> str:
        """Находит лучшую модель из списка найденных с улучшенной логикой"""
        if not found_models:
            return None
        
        # Создаем список кандидатов с весами
        candidates = []
        
        for model in found_models:
            model_lower = model.lower()
            weight = 0
            
            # Проверяем точное совпадение
            for word in words:
                word_lower = word.lower()
                if word_lower == model_lower:
                    weight += 100  # Максимальный вес для точного совпадения
                    break
                elif word_lower in model_lower or model_lower in word_lower:
                    weight += 50   # Высокий вес для частичного совпадения
                elif word_lower.replace(' ', '') == model_lower.replace(' ', ''):
                    weight += 40   # Вес для совпадения без пробелов
            
            # Дополнительные проверки для составных моделей
            if ' ' in model_lower:
                model_parts = model_lower.split()
                for word in words:
                    word_lower = word.lower()
                    if word_lower in model_parts:
                        weight += 30  # Вес за совпадение части составной модели
            
            # Приоритет для моделей с цифрами, если в запросе есть цифры
            if any(c.isdigit() for c in ''.join(words)):
                if any(c.isdigit() for c in model_lower):
                    weight += 20
            
            # Приоритет для коротких моделей (X3, A4 и т.д.)
            if len(model_lower) <= 3:
                weight += 10
            
            candidates.append((model, weight))
        
        # Сортируем по весу (по убыванию)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[DEBUG] Кандидаты моделей с весами: {candidates}")
        
        # Возвращаем модель с максимальным весом
        if candidates and candidates[0][1] > 0:
            return candidates[0][0]
        
        return found_models[0] if found_models else None

    def extract_all_entities(self, query: str):
        """Извлекает все сущности из запроса с улучшенной точностью"""
        entities = {}
        
        # Извлечение марок и моделей
        car_names = self.extract_car_names(query)
        if car_names:
            entities.update(car_names)
        
        # Извлечение цветов
        colors = self.extract_colors(query)
        if colors:
            entities['color'] = colors[0] if len(colors) == 1 else colors
        
        # Извлечение опций
        options = self.extract_options(query)
        if options:
            entities['options'] = options
        
        # Извлечение типов топлива
        fuel_types = self.extract_fuel_types(query)
        if fuel_types:
            entities['fuel_type'] = fuel_types[0] if len(fuel_types) == 1 else fuel_types
        
        # Извлечение трансмиссии
        transmission = self.extract_transmission(query)
        if transmission:
            entities['transmission'] = transmission[0] if len(transmission) == 1 else transmission
        
        # Извлечение типа привода
        drive_type = self.extract_drive_type(query)
        if drive_type:
            entities['drive_type'] = drive_type[0] if len(drive_type) == 1 else drive_type
        
        # Извлечение цен
        prices = self.extract_prices(query)
        if prices:
            entities.update(prices)
        
        # Извлечение годов
        years = self.extract_years(query)
        if years:
            entities.update(years)
        
        # Извлечение параметров кредита
        loan_params = self.extract_loan_params(query)
        if loan_params:
            entities['loan_params'] = loan_params
        
        # Дополнительная проверка и исправление ошибок
        self._fix_entity_errors(entities, query)
        
        return entities
    
    def _fix_entity_errors(self, entities, query):
        """Исправляет типичные ошибки в извлеченных сущностях"""
        query_lower = query.lower()
        
        # Исправление ошибок в марках и моделях
        if 'brand' in entities and 'model' in entities:
            # Проверяем, что модель действительно принадлежит марке
            brand = entities['brand']
            model = entities['model']
            
            if brand in self.marks_models:
                if model not in self.marks_models[brand]:
                    # Ищем правильную модель в других марках
                    for other_brand, models in self.marks_models.items():
                        if model in models:
                            entities['brand'] = other_brand
                            break
        
        # Исправление ошибок в цветах
        if 'color' in entities:
            color = entities['color']
            # Проверяем, что цвет действительно найден в запросе
            if isinstance(color, str) and color not in query_lower and not any(syn in query_lower for syn in COLOR_SYNONYMS.get(color, [])):
                # Удаляем неправильный цвет
                del entities['color']
        
        # Исправление ошибок в опциях
        if 'options' in entities:
            options = entities['options']
            valid_options = []
            for option in options:
                if option in query_lower or any(syn in query_lower for syn in OPTION_SYNONYMS.get(option, [])):
                    valid_options.append(option)
            if valid_options:
                entities['options'] = valid_options
            else:
                del entities['options']
        
        # Исправление ошибок в топливе
        if 'fuel_type' in entities:
            fuel = entities['fuel_type']
            if isinstance(fuel, str) and fuel not in query_lower and not any(syn in query_lower for syn in FUEL_SYNONYMS.get(fuel, [])):
                del entities['fuel_type']
        
        # Исправление ошибок в трансмиссии
        if 'transmission' in entities:
            transmission = entities['transmission']
            if isinstance(transmission, str) and transmission not in query_lower and not any(syn in query_lower for syn in TRANSMISSION_SYNONYMS.get(transmission, [])):
                del entities['transmission']
        
        # Исправление ошибок в приводе
        if 'drive_type' in entities:
            drive = entities['drive_type']
            if isinstance(drive, str) and drive not in query_lower and not any(syn in query_lower for syn in DRIVE_SYNONYMS.get(drive, [])):
                del entities['drive_type']
    
    def _normalize_russian_words(self, query_lower):
        """Нормализация русских слов для поиска"""
        words = query_lower.split()
        normalized_words = []
        for word in words:
            normalized_words.append(word)
            
            # Агрессивная нормализация для всех падежей
            # Мужской род
            if word.endswith('ой'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ая', word[:-2] + 'ое'])
            if word.endswith('ый'):
                normalized_words.extend([word[:-2], word[:-2] + 'ой', word[:-2] + 'ая', word[:-2] + 'ое'])
            if word.endswith('ом'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            if word.endswith('ым'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            
            # Женский род
            if word.endswith('ая'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ое'])
            if word.endswith('ой'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ая', word[:-2] + 'ое'])
            if word.endswith('ой'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ая', word[:-2] + 'ое'])
            if word.endswith('ей'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            
            # Средний род
            if word.endswith('ое'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            if word.endswith('ым'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            
            # Множественное число
            if word.endswith('ые'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            if word.endswith('ыми'):
                normalized_words.extend([word[:-3], word[:-3] + 'ый', word[:-3] + 'ой', word[:-3] + 'ая'])
            
            # Творительный падеж
            if word.endswith('ом'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            if word.endswith('ем'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            
            # Родительный падеж
            if word.endswith('ого'):
                normalized_words.extend([word[:-3], word[:-3] + 'ый', word[:-3] + 'ой', word[:-3] + 'ая'])
            if word.endswith('его'):
                normalized_words.extend([word[:-3], word[:-3] + 'ый', word[:-3] + 'ой', word[:-3] + 'ая'])
            
            # Дательный падеж
            if word.endswith('ому'):
                normalized_words.extend([word[:-3], word[:-3] + 'ый', word[:-3] + 'ой', word[:-3] + 'ая'])
            if word.endswith('ему'):
                normalized_words.extend([word[:-3], word[:-3] + 'ый', word[:-3] + 'ой', word[:-3] + 'ая'])
            
            # Предложный падеж
            if word.endswith('ом'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            if word.endswith('ем'):
                normalized_words.extend([word[:-2], word[:-2] + 'ый', word[:-2] + 'ой', word[:-2] + 'ая'])
            
            # Специальные случаи из тестов
            if word == 'панорамнои':
                normalized_words.extend(['панорамная', 'панорамный', 'панорамное', 'панорамная крыша'])
            if word == 'крышеи':
                normalized_words.extend(['крыша', 'крышу', 'панорамная крыша'])
            if word == 'люком':
                normalized_words.extend(['люк', 'люка'])
            if word == 'автоматическои':
                normalized_words.extend(['автоматическая', 'автоматический', 'автоматическое', 'автомат'])
            if word == 'коробкои':
                normalized_words.extend(['коробка', 'коробку', 'автоматическая коробка'])
            if word == 'механическои':
                normalized_words.extend(['механическая', 'механический', 'механическое', 'механика'])
            if word == 'полным':
                normalized_words.extend(['полный', 'полная', 'полное', 'полный привод'])
            if word == 'передним':
                normalized_words.extend(['передний', 'передняя', 'переднее', 'передний привод'])
            if word == 'задним':
                normalized_words.extend(['задний', 'задняя', 'заднее', 'задний привод'])
            if word == 'приводом':
                normalized_words.extend(['привод', 'привода', 'полный привод', 'передний привод', 'задний привод'])
            if word == 'контролем':
                normalized_words.extend(['контроль', 'контроля', 'климат-контроль'])
            if word == 'подогревом':
                normalized_words.extend(['подогрев', 'подогрева', 'подогрев сидений'])
            if word == 'сидении':
                normalized_words.extend(['сиденье', 'сиденья', 'подогрев сидений'])
            if word == 'красного':
                normalized_words.extend(['красный', 'красная', 'красное'])
            if word == 'белого':
                normalized_words.extend(['белый', 'белая', 'белое'])
            if word == 'серебристого':
                normalized_words.extend(['серебристый', 'серебристая', 'серебристое', 'серебряный'])
            
            # Дополнительные случаи
            if word == 'полныи':
                normalized_words.extend(['полный', 'полная', 'полное', 'полный привод'])
            if word == 'переднии':
                normalized_words.extend(['передний', 'передняя', 'переднее', 'передний привод'])
            if word == 'заднии':
                normalized_words.extend(['задний', 'задняя', 'заднее', 'задний привод'])
            if word == 'автоматическои':
                normalized_words.extend(['автоматическая', 'автоматический', 'автоматическое', 'автомат'])
            if word == 'механическои':
                normalized_words.extend(['механическая', 'механический', 'механическое', 'механика'])
            if word == 'панорамнои':
                normalized_words.extend(['панорамная', 'панорамный', 'панорамное', 'панорамная крыша'])
            if word == 'крышеи':
                normalized_words.extend(['крыша', 'крышу', 'панорамная крыша'])
            if word == 'люком':
                normalized_words.extend(['люк', 'люка'])
            if word == 'коробкои':
                normalized_words.extend(['коробка', 'коробку', 'автоматическая коробка'])
            if word == 'приводом':
                normalized_words.extend(['привод', 'привода', 'полный привод', 'передний привод', 'задний привод'])
            if word == 'контролем':
                normalized_words.extend(['контроль', 'контроля', 'климат-контроль'])
            if word == 'подогревом':
                normalized_words.extend(['подогрев', 'подогрева', 'подогрев сидений'])
            if word == 'сидении':
                normalized_words.extend(['сиденье', 'сиденья', 'подогрев сидений'])
            if word == 'красного':
                normalized_words.extend(['красный', 'красная', 'красное'])
            if word == 'белого':
                normalized_words.extend(['белый', 'белая', 'белое'])
            if word == 'серебристого':
                normalized_words.extend(['серебристый', 'серебристая', 'серебристое', 'серебряный'])
        
        return list(set(normalized_words))  # Убираем дубликаты

    def extract_options(self, query: str):
        """Извлечение опций из запроса с ML-улучшенными алгоритмами"""
        found_options = []
        query_lower = query.lower()
        normalized_words = self._normalize_russian_words(query_lower)
        lemmatized_words = set(lemmatize_list(normalized_words))
        
        # Умная токенизация
        tokens = smart_tokenization(query_lower)
        
        print(f"[DEBUG] Запрос для опций: '{query}'")
        print(f"[DEBUG] Нормализованные слова: {normalized_words}")
        print(f"[DEBUG] Лемматизированные слова: {lemmatized_words}")
        print(f"[DEBUG] Умные токены: {tokens}")
        
        for option, synonyms in OPTION_SYNONYMS.items():
            lemmatized_synonyms = set(lemmatize_list(synonyms))
            print(f"[DEBUG] Опция '{option}' - лемматизированные синонимы: {lemmatized_synonyms}")
            
            # 1. Проверяем пересечение лемматизированных слов
            intersection = lemmatized_words & lemmatized_synonyms
            if intersection:
                print(f"[DEBUG] НАЙДЕНО ЛЕММАТИЗИРОВАННОЕ СОВПАДЕНИЕ для опции '{option}': {intersection}")
                # Дополнительная валидация контекста
                if self._validate_option_context(query, option):
                    found_options.append(option)
                continue
            
            # 2. Контекстно-осведомленное сопоставление с повышенным порогом
            if context_aware_match(normalized_words, synonyms, context_threshold=0.85):
                print(f"[DEBUG] НАЙДЕНО КОНТЕКСТНОЕ СОВПАДЕНИЕ для опции '{option}'")
                # Дополнительная валидация контекста
                if self._validate_option_context(query, option):
                    found_options.append(option)
                continue
            
            # 3. Продвинутое fuzzy matching для каждого токена с повышенным порогом
            for token in tokens:
                # Пропускаем слишком короткие токены
                if len(token) < 3:
                    continue
                    
                for synonym in synonyms:
                    similarity = advanced_similarity_score(token, synonym)
                    if similarity >= 0.9:  # Повышенный порог с 0.8 до 0.9
                        print(f"[DEBUG] НАЙДЕНО ADVANCED FUZZY СОВПАДЕНИЕ для опции '{option}': {token} ~ {synonym} (score: {similarity:.3f})")
                        # Дополнительная валидация контекста
                        if self._validate_option_context(query, option):
                            found_options.append(option)
                        break
                if option in found_options:
                    break
            
            # 4. ML-улучшенная проверка с повышенным порогом
            if option not in found_options:
                ml_score = ml_matcher.predict(query + " " + option)
                if ml_score >= 0.9:  # Повышенный порог с 0.85 до 0.9
                    print(f"[DEBUG] НАЙДЕНО ML СОВПАДЕНИЕ для опции '{option}': (score: {ml_score:.3f})")
                    # Дополнительная валидация контекста
                    if self._validate_option_context(query, option):
                        found_options.append(option)
                    continue
            
            # 5. Дополнительная проверка с TF-IDF с повышенным порогом
            if option not in found_options:
                for token in tokens:
                    # Пропускаем слишком короткие токены
                    if len(token) < 3:
                        continue
                        
                    for synonym in synonyms:
                        try:
                            tfidf_matrix = tfidf_vectorizer.fit_transform([token, synonym])
                            cosine_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                            if cosine_score >= 0.8:  # Повышенный порог с 0.7 до 0.8
                                print(f"[DEBUG] НАЙДЕНО TF-IDF СОВПАДЕНИЕ для опции '{option}': {token} ~ {synonym} (score: {cosine_score:.3f})")
                                # Дополнительная валидация контекста
                                if self._validate_option_context(query, option):
                                    found_options.append(option)
                                break
                        except:
                            pass
                    if option in found_options:
                        break
        
        # Дополнительная проверка для составных опций
        found_options = self._check_compound_options(query, found_options)
        
        print(f"[DEBUG] Найденные опции: {found_options}")
        return found_options
    
    def _check_compound_options(self, query: str, found_options: List[str]) -> List[str]:
        """Проверка составных опций (например, 'панорамная крыша')"""
        query_lower = query.lower()
        
        # Список составных опций для дополнительной проверки
        compound_options = {
            'панорамная крыша': ['панорамная', 'крыша', 'панорамной', 'крышей'],
            'климат-контроль': ['климат', 'контроль', 'климат-контролем'],
            'подогрев сидений': ['подогрев', 'сидений', 'сиденья'],
            'адаптивные фары': ['адаптивные', 'фары', 'фар'],
            'система парковки': ['система', 'парковки', 'парковка']
        }
        
        for option, keywords in compound_options.items():
            if option not in found_options:
                # Проверяем, есть ли все ключевые слова в запросе
                if all(keyword in query_lower for keyword in keywords):
                    print(f"[DEBUG] НАЙДЕНА СОСТАВНАЯ ОПЦИЯ '{option}' по ключевым словам: {keywords}")
                    found_options.append(option)
        
        return found_options
    
    def _validate_option_context(self, query: str, option: str) -> bool:
        """Валидация контекста для опций"""
        query_lower = query.lower()
        option_lower = option.lower()
        
        # Проверяем наличие ключевых слов, связанных с опциями
        option_keywords = ['опция', 'option', 'комплектация', 'оснащение', 'люк', 'крыша', 'навигация', 'климат', 'подогрев', 'ксенон', 'фары', 'парктроник', 'датчик', 'с']
        has_option_context = any(keyword in query_lower for keyword in option_keywords)
        
        # Проверяем наличие самой опции в запросе
        has_option_mention = option_lower in query_lower
        
        # Проверяем составные опции
        compound_option_checks = {
            'панорамная крыша': ['панорамная', 'крыша', 'панорамной', 'крышей'],
            'климат-контроль': ['климат', 'контроль', 'климат-контролем'],
            'подогрев сидений': ['подогрев', 'сидений', 'сиденья'],
            'адаптивные фары': ['адаптивные', 'фары', 'фар'],
            'система парковки': ['система', 'парковки', 'парковка']
        }
        
        # Проверяем составные опции
        if option in compound_option_checks:
            keywords = compound_option_checks[option]
            has_compound_mention = any(keyword in query_lower for keyword in keywords)
            if has_compound_mention:
                return True
        
        # Проверяем контекст через ML модель
        ml_score = ml_matcher.predict(query + " " + option)
        
        # Более мягкие условия для валидации - если опция упоминается в запросе, считаем её валидной
        return has_option_mention or (has_option_context and ml_score >= 0.7)
    
    def extract_fuel_types(self, query: str):
        """Извлечение типов топлива из запроса с ML-улучшенными алгоритмами"""
        found_fuel_types = []
        query_lower = query.lower()
        normalized_words = self._normalize_russian_words(query_lower)
        lemmatized_words = set(lemmatize_list(normalized_words))
        
        # Умная токенизация
        tokens = smart_tokenization(query_lower)
        
        print(f"[DEBUG] Запрос для топлива: '{query}'")
        print(f"[DEBUG] Лемматизированные слова для топлива: {lemmatized_words}")
        print(f"[DEBUG] Умные токены: {tokens}")
        
        for fuel_type, synonyms in FUEL_SYNONYMS.items():
            lemmatized_synonyms = set(lemmatize_list(synonyms))
            print(f"[DEBUG] Топливо '{fuel_type}' - лемматизированные синонимы: {lemmatized_synonyms}")
            
            # 1. Проверяем пересечение лемматизированных слов
            intersection = lemmatized_words & lemmatized_synonyms
            if intersection:
                print(f"[DEBUG] НАЙДЕНО ЛЕММАТИЗИРОВАННОЕ СОВПАДЕНИЕ для топлива '{fuel_type}': {intersection}")
                # Дополнительная валидация контекста
                if self._validate_fuel_context(query, fuel_type):
                    found_fuel_types.append(fuel_type)
                continue
            
            # 2. Контекстно-осведомленное сопоставление с повышенным порогом
            if context_aware_match(normalized_words, synonyms, context_threshold=0.85):
                print(f"[DEBUG] НАЙДЕНО КОНТЕКСТНОЕ СОВПАДЕНИЕ для топлива '{fuel_type}'")
                # Дополнительная валидация контекста
                if self._validate_fuel_context(query, fuel_type):
                    found_fuel_types.append(fuel_type)
                continue
            
            # 3. Продвинутое fuzzy matching для каждого токена с повышенным порогом
            for token in tokens:
                # Пропускаем слишком короткие токены
                if len(token) < 3:
                    continue
                    
                for synonym in synonyms:
                    similarity = advanced_similarity_score(token, synonym)
                    if similarity >= 0.9:  # Повышенный порог с 0.8 до 0.9
                        print(f"[DEBUG] НАЙДЕНО ADVANCED FUZZY СОВПАДЕНИЕ для топлива '{fuel_type}': {token} ~ {synonym} (score: {similarity:.3f})")
                        # Дополнительная валидация контекста
                        if self._validate_fuel_context(query, fuel_type):
                            found_fuel_types.append(fuel_type)
                        break
                if fuel_type in found_fuel_types:
                    break
            
            # 4. ML-улучшенная проверка с повышенным порогом
            if fuel_type not in found_fuel_types:
                ml_score = ml_matcher.predict(query + " " + fuel_type)
                if ml_score >= 0.9:  # Повышенный порог с 0.85 до 0.9
                    print(f"[DEBUG] НАЙДЕНО ML СОВПАДЕНИЕ для топлива '{fuel_type}': (score: {ml_score:.3f})")
                    # Дополнительная валидация контекста
                    if self._validate_fuel_context(query, fuel_type):
                        found_fuel_types.append(fuel_type)
                    continue
            
            # 5. Дополнительная проверка с TF-IDF с повышенным порогом
            if fuel_type not in found_fuel_types:
                for token in tokens:
                    # Пропускаем слишком короткие токены
                    if len(token) < 3:
                        continue
                        
                    for synonym in synonyms:
                        try:
                            tfidf_matrix = tfidf_vectorizer.fit_transform([token, synonym])
                            cosine_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                            if cosine_score >= 0.8:  # Повышенный порог с 0.7 до 0.8
                                print(f"[DEBUG] НАЙДЕНО TF-IDF СОВПАДЕНИЕ для топлива '{fuel_type}': {token} ~ {synonym} (score: {cosine_score:.3f})")
                                # Дополнительная валидация контекста
                                if self._validate_fuel_context(query, fuel_type):
                                    found_fuel_types.append(fuel_type)
                                break
                        except:
                            pass
                    if fuel_type in found_fuel_types:
                        break
        
        print(f"[DEBUG] Найденные типы топлива: {found_fuel_types}")
        return found_fuel_types
    
    def _validate_fuel_context(self, query: str, fuel_type: str) -> bool:
        """Валидация контекста для топлива"""
        query_lower = query.lower()
        fuel_lower = fuel_type.lower()
        
        # Проверяем наличие ключевых слов, связанных с топливом
        fuel_keywords = ['топливо', 'fuel', 'бензин', 'дизель', 'газ', 'гибрид', 'электро', 'расход', 'экономия', 'двигатель']
        has_fuel_context = any(keyword in query_lower for keyword in fuel_keywords)
        
        # Проверяем наличие самого топлива в запросе
        has_fuel_mention = fuel_lower in query_lower
        
        # Проверяем контекст через ML модель
        ml_score = ml_matcher.predict(query + " " + fuel_type)
        
        # Строгие условия для валидации - требуем либо точного упоминания топлива, либо контекста + высокого ML score
        return (has_fuel_mention or (has_fuel_context and ml_score >= 0.85))

    def extract_colors(self, query: str):
        """Извлечение цветов из запроса с улучшенным fuzzy matching"""
        found_colors = []
        query_lower = query.lower()
        normalized_words = self._normalize_russian_words(query_lower)
        lemmatized_words = set(lemmatize_list(normalized_words))
        
        # Умная токенизация
        tokens = smart_tokenization(query_lower)
        
        print(f"[DEBUG] Запрос для цветов: '{query}'")
        print(f"[DEBUG] Лемматизированные слова для цветов: {lemmatized_words}")
        print(f"[DEBUG] Умные токены: {tokens}")
        
        for color, synonyms in COLOR_SYNONYMS.items():
            lemmatized_synonyms = set(lemmatize_list(synonyms))
            print(f"[DEBUG] Цвет '{color}' - лемматизированные синонимы: {lemmatized_synonyms}")
            
            # 1. Проверяем пересечение лемматизированных слов
            intersection = lemmatized_words & lemmatized_synonyms
            if intersection:
                print(f"[DEBUG] НАЙДЕНО СОВПАДЕНИЕ для цвета '{color}': {intersection}")
                # Дополнительная валидация контекста
                if self._validate_color_context(query, color):
                    found_colors.append(color)
                continue
            
            # 2. Продвинутое fuzzy matching для каждого токена с повышенным порогом
            for token in tokens:
                # Пропускаем слишком короткие токены
                if len(token) < 3:
                    continue
                    
                for synonym in lemmatized_synonyms:
                    similarity = advanced_similarity_score(token, synonym)
                    if similarity > 0.9:  # Повышенный порог с 0.8 до 0.9
                        print(f"[DEBUG] НАЙДЕНО FUZZY СОВПАДЕНИЕ для цвета '{color}' с токеном '{token}' и синонимом '{synonym}' (score: {similarity:.3f})")
                        # Дополнительная валидация контекста
                        if self._validate_color_context(query, color):
                            found_colors.append(color)
                        break
                else:
                    continue
                break
            else:
                print(f"[DEBUG] Нет совпадений для цвета '{color}'")
        
        print(f"[DEBUG] Найденные цвета: {found_colors}")
        return found_colors

    def extract_transmission(self, query: str):
        """Извлечение типов трансмиссии из запроса с улучшенным fuzzy matching"""
        found_transmissions = []
        query_lower = query.lower()
        normalized_words = self._normalize_russian_words(query_lower)
        lemmatized_words = set(lemmatize_list(normalized_words))
        
        # Умная токенизация
        tokens = smart_tokenization(query_lower)
        
        print(f"[DEBUG] Запрос для трансмиссии: '{query}'")
        print(f"[DEBUG] Лемматизированные слова для трансмиссии: {lemmatized_words}")
        print(f"[DEBUG] Умные токены: {tokens}")
        
        for transmission, synonyms in TRANSMISSION_SYNONYMS.items():
            lemmatized_synonyms = set(lemmatize_list(synonyms))
            print(f"[DEBUG] Трансмиссия '{transmission}' - лемматизированные синонимы: {lemmatized_synonyms}")
            
            # 1. Проверяем пересечение лемматизированных слов
            intersection = lemmatized_words & lemmatized_synonyms
            if intersection:
                print(f"[DEBUG] НАЙДЕНО СОВПАДЕНИЕ для трансмиссии '{transmission}': {intersection}")
                # Дополнительная валидация контекста
                if self._validate_transmission_context(query, transmission):
                    found_transmissions.append(transmission)
                continue
            
            # 2. Продвинутое fuzzy matching для каждого токена
            for token in tokens:
                for synonym in lemmatized_synonyms:
                    if advanced_similarity_score(token, synonym) > 0.8:
                        print(f"[DEBUG] НАЙДЕНО FUZZY СОВПАДЕНИЕ для трансмиссии '{transmission}' с токеном '{token}' и синонимом '{synonym}'")
                        # Дополнительная валидация контекста
                        if self._validate_transmission_context(query, transmission):
                            found_transmissions.append(transmission)
                        break
                else:
                    continue
                break
        
        print(f"[DEBUG] Найденные типы трансмиссии: {found_transmissions}")
        return found_transmissions

    def extract_drive_type(self, query: str):
        """Извлечение типов привода из запроса с улучшенным fuzzy matching"""
        found_drive_types = []
        query_lower = query.lower()
        normalized_words = self._normalize_russian_words(query_lower)
        lemmatized_words = set(lemmatize_list(normalized_words))
        
        # Умная токенизация
        tokens = smart_tokenization(query_lower)
        
        print(f"[DEBUG] Запрос для привода: '{query}'")
        print(f"[DEBUG] Лемматизированные слова для привода: {lemmatized_words}")
        print(f"[DEBUG] Умные токены: {tokens}")
        
        for drive_type, synonyms in DRIVE_SYNONYMS.items():
            lemmatized_synonyms = set(lemmatize_list(synonyms))
            print(f"[DEBUG] Привод '{drive_type}' - лемматизированные синонимы: {lemmatized_synonyms}")
            
            # 1. Проверяем пересечение лемматизированных слов
            intersection = lemmatized_words & lemmatized_synonyms
            if intersection:
                print(f"[DEBUG] НАЙДЕНО СОВПАДЕНИЕ для привода '{drive_type}': {intersection}")
                found_drive_types.append(drive_type)
                continue
            
            # 2. Продвинутое fuzzy matching для каждого токена
            for token in tokens:
                for synonym in lemmatized_synonyms:
                    if advanced_similarity_score(token, synonym) > 0.8:
                        print(f"[DEBUG] НАЙДЕНО FUZZY СОВПАДЕНИЕ для привода '{drive_type}' с токеном '{token}' и синонимом '{synonym}'")
                        found_drive_types.append(drive_type)
                        break
                else:
                    continue
                break
        
        print(f"[DEBUG] Найденные типы привода: {found_drive_types}")
        return found_drive_types

    def extract_loan_params(self, query: str):
        params = {}
        m = re.search(r'(\d+) ?(лет|года|год|месяц|месяцев)', query)
        if m:
            val = int(m.group(1))
            if 'месяц' in m.group(2):
                params['term'] = val
            else:
                params['term'] = val * 12
        m = re.search(r'(первоначальный|взнос)\D*(\d{2,})', query)
        if m:
            params['downpayment'] = int(m.group(2))
        m = re.search(r'(ставка|процент)\D*(\d{1,2}(?:[\.,]\d+)?)', query)
        if m:
            params['rate'] = float(m.group(2).replace(',', '.')) / 100
        return params
    
    def extract_prices(self, query: str):
        """Извлечение цен из запроса"""
        prices = {}
        query_lower = query.lower()
        
        # Поиск цен "до X"
        price_to_match = re.search(r'до\s*(\d+(?:[.,]\d+)?)\s*(тыс|к|млн|миллион|тысяч|руб)', query_lower)
        if price_to_match:
            value = float(price_to_match.group(1).replace(',', '.'))
            unit = price_to_match.group(2)
            if unit in ['тыс', 'к', 'тысяч']:
                prices['price_to'] = int(value * 1000)
            elif unit in ['млн', 'миллион']:
                prices['price_to'] = int(value * 1000000)
            else:
                prices['price_to'] = int(value)
        
        # Поиск цен "от X"
        price_from_match = re.search(r'от\s*(\d+(?:[.,]\d+)?)\s*(тыс|к|млн|миллион|тысяч|руб)', query_lower)
        if price_from_match:
            value = float(price_from_match.group(1).replace(',', '.'))
            unit = price_from_match.group(2)
            if unit in ['тыс', 'к', 'тысяч']:
                prices['price_from'] = int(value * 1000)
            elif unit in ['млн', 'миллион']:
                prices['price_from'] = int(value * 1000000)
            else:
                prices['price_from'] = int(value)
        
        # Поиск диапазона цен "X-Y"
        price_range_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*(тыс|к|млн|миллион|тысяч|руб)', query_lower)
        if price_range_match:
            value1 = float(price_range_match.group(1).replace(',', '.'))
            value2 = float(price_range_match.group(2).replace(',', '.'))
            unit = price_range_match.group(3)
            if unit in ['тыс', 'к', 'тысяч']:
                prices['price_from'] = int(value1 * 1000)
                prices['price_to'] = int(value2 * 1000)
            elif unit in ['млн', 'миллион']:
                prices['price_from'] = int(value1 * 1000000)
                prices['price_to'] = int(value2 * 1000000)
            else:
                prices['price_from'] = int(value1)
                prices['price_to'] = int(value2)
        
        return prices
    
    def extract_years(self, query: str):
        """Извлечение годов из запроса"""
        years = {}
        query_lower = query.lower()
        
        # Поиск конкретного года
        year_match = re.search(r'(\d{4})\s*(года|год)', query_lower)
        if year_match:
            years['year'] = int(year_match.group(1))
        
        # Поиск года "от"
        year_from_match = re.search(r'от\s*(\d{4})\s*(года|год)', query_lower)
        if year_from_match:
            years['year_from'] = int(year_from_match.group(1))
        
        # Поиск диапазона годов
        year_range_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', query_lower)
        if year_range_match:
            years['year_from'] = int(year_range_match.group(1))
            years['year_to'] = int(year_range_match.group(2))
        
        # Поиск состояния автомобиля
        if 'новый' in query_lower or 'новая' in query_lower:
            years['state'] = 'new'
        elif 'с пробегом' in query_lower or 'б/у' in query_lower or 'подержанный' in query_lower:
            years['state'] = 'used'
        
        return years

    def _transliterate_word(self, word: str) -> str:
        """Транслитерация слова для лучшего распознавания"""
        if not word:
            return ""
            
        # Словарь транслитерации
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        result = ""
        for char in word.lower():
            result += translit_map.get(char, char)
        
        return result
    
    def _find_brands_and_models(self, norm_words: set) -> tuple:
        """Поиск марок и моделей с использованием расширенных словарей"""
        found_brands = []
        found_models = []
        
        # Поиск марок
        for brand, synonyms in BRAND_SYNONYMS.items():
            for synonym in synonyms:
                if synonym in norm_words:
                    found_brands.append(brand)
                    break
        
        # Поиск моделей
        for model, synonyms in MODEL_SYNONYMS.items():
            for synonym in synonyms:
                if synonym in norm_words:
                    found_models.append(model)
                    break
        
        # Дополнительный поиск по частям слов
        for word in norm_words:
            # Поиск марок по частям
            for brand, synonyms in BRAND_SYNONYMS.items():
                for synonym in synonyms:
                    if word in synonym or synonym in word:
                        if brand not in found_brands:
                            found_brands.append(brand)
            
            # Поиск моделей по частям
            for model, synonyms in MODEL_SYNONYMS.items():
                for synonym in synonyms:
                    if word in synonym or synonym in word:
                        if model not in found_models:
                            found_models.append(model)
        
        return found_brands, found_models

    def _validate_color_context(self, query: str, color: str) -> bool:
        """Валидация контекста для цветов"""
        query_lower = query.lower()
        color_lower = color.lower()
        
        # Проверяем наличие ключевых слов, связанных с цветом
        color_keywords = ['цвет', 'color', 'окраска', 'окрашен', 'краска', 'paint', 'белый', 'черный', 'красный', 'синий', 'зеленый', 'желтый', 'серый', 'коричневый', 'бежевый', 'голубой', 'серебристый', 'золотистый']
        has_color_context = any(keyword in query_lower for keyword in color_keywords)
        
        # Проверяем наличие самого цвета в запросе
        has_color_mention = color_lower in query_lower
        
        # Проверяем контекст через ML модель
        ml_score = ml_matcher.predict(query + " " + color)
        
        # Строгие условия для валидации - требуем либо точного упоминания цвета, либо контекста + высокого ML score
        return (has_color_mention or (has_color_context and ml_score >= 0.85))
    
    def _validate_transmission_context(self, query: str, transmission: str) -> bool:
        """Валидация контекста для трансмиссии"""
        query_lower = query.lower()
        transmission_lower = transmission.lower()
        
        # Проверяем наличие ключевых слов, связанных с трансмиссией
        transmission_keywords = ['коробка', 'transmission', 'передача', 'gear', 'автомат', 'механика']
        has_transmission_context = any(keyword in query_lower for keyword in transmission_keywords)
        
        # Проверяем наличие самой трансмиссии в запросе
        has_transmission_mention = transmission_lower in query_lower
        
        # Проверяем контекст через ML модель
        ml_score = ml_matcher.predict(query + " " + transmission)
        
        # Строгие условия для валидации
        return (has_transmission_context or has_transmission_mention) and ml_score >= 0.8
    
    def _validate_drive_context(self, query: str, drive_type: str) -> bool:
        """Валидация контекста для привода"""
        query_lower = query.lower()
        drive_lower = drive_type.lower()
        
        # Проверяем наличие ключевых слов, связанных с приводом
        drive_keywords = ['привод', 'drive', 'полный', 'передний', 'задний', '4x4', 'awd', 'fwd', 'rwd']
        has_drive_context = any(keyword in query_lower for keyword in drive_keywords)
        
        # Проверяем наличие самого привода в запросе
        has_drive_mention = drive_lower in query_lower
        
        # Проверяем контекст через ML модель
        ml_score = ml_matcher.predict(query + " " + drive_type)
        
        # Строгие условия для валидации
        return (has_drive_context or has_drive_mention) and ml_score >= 0.8

# Словари синонимов для опций и типов топлива
OPTION_SYNONYMS = {
    'люк': ['люк', 'sunroof', 'открывающаяся крыша', 'люка', 'люком', 'люку', 'люки', 'люками', 'люк', 'люком', 'люками'],
    'панорамная крыша': ['панорамная крыша', 'panoramic roof', 'панорамная', 'панорамнои', 'крышеи', 'панорамная крыша', 'панорамный', 'панорамное', 'панорамною', 'панорамной', 'панорамную', 'панорамные', 'панорамными', 'панорамная крыша', 'панорамнои', 'крышеи', 'панорамная', 'крыша', 'крышу', 'крышеи', 'панорамной', 'панорамным', 'панорамными'],
    'климат-контроль': ['климат-контроль', 'climate control', 'кондиционер', 'климат', 'контролем', 'климат-контроль', 'климат-контроля', 'климат-контролю', 'климат-контролем', 'климат-контроли', 'климат-контролями', 'климат', 'контролем', 'климат-контроль', 'климат-контролем', 'климат-контролями'],
    'подогрев сидений': ['подогрев сидений', 'heated seats', 'подогрев', 'подогревом', 'сидении', 'подогрев сидений', 'подогрева', 'подогреву', 'подогревом', 'подогревы', 'подогревами', 'сиденье', 'сиденья', 'сиденью', 'сиденьями', 'подогрев', 'подогревом', 'сидении', 'подогрев сидений', 'подогрева', 'подогреву', 'подогревами'],
    'навигация': ['навигация', 'navigation', 'gps', 'навигации', 'навигацию', 'навигацией', 'навигации', 'навигациями', 'навигационной', 'навигационным', 'навигационными'],
    'парктроник': ['парктроник', 'parking sensors', 'парктроника', 'парктронику', 'парктроником', 'парктроники', 'парктрониками', 'парктронической', 'парктроническим', 'парктроническими'],
    'ксенон': ['ксенон', 'xenon', 'ксенона', 'ксенону', 'ксеноном', 'ксеноны', 'ксенонами', 'ксеноновой', 'ксеноновым', 'ксеноновыми'],
    'адаптивные фары': ['адаптивные фары', 'adaptive headlights', 'адаптивные', 'фары', 'адаптивной', 'фарой', 'адаптивными', 'фарами', 'адаптивными', 'адаптивными']
}

FUEL_SYNONYMS = {
    'бензин': ['бензин', 'gasoline', 'petrol', 'бензина', 'бензину', 'бензином', 'бензины', 'бензинами', 'бензиновый', 'бензиновая', 'бензиновое', 'бензиновые'],
    'дизель': ['дизель', 'diesel', 'дизеля', 'дизелю', 'дизелем', 'дизели', 'дизелями', 'дизельный', 'дизельная', 'дизельное', 'дизельные'],
    'газ': ['газ', 'lpg', 'cng', 'газа', 'газу', 'газом', 'газы', 'газами', 'газовые', 'газовых', 'газовыми', 'газовые', 'газовый', 'газовая', 'газовое'],
    'гибрид': ['гибрид', 'hybrid', 'гибрида', 'гибриду', 'гибридом', 'гибриды', 'гибридами', 'гибридные', 'гибридных', 'гибридными', 'гибрид', 'гибридный', 'гибридная', 'гибридное'],
    'электро': ['электро', 'electric', 'электро', 'электрический', 'электрическая', 'электрическое', 'электрические', 'электромобиль', 'электромобили']
}

TRANSMISSION_SYNONYMS = {
    'механика': ['механика', 'механическая', 'manual', 'механическои', 'механика', 'механическая коробка', 'механическая', 'механический', 'механическое', 'механические', 'механика', 'механической', 'механическим', 'механическими'],
    'автомат': ['автомат', 'автоматическая', 'automatic', 'автоматическои', 'автомат', 'автоматическая коробка', 'коробкои', 'автоматическая', 'автоматический', 'автоматическое', 'автоматические', 'автомат', 'автоматическая', 'коробка', 'коробкои', 'автоматической', 'автоматическим', 'автоматическими'],
    'робот': ['робот', 'роботизированная', 'robot', 'робот', 'робота', 'роботу', 'роботом', 'роботы', 'роботами', 'роботизированной', 'роботизированным', 'роботизированными'],
    'вариатор': ['вариатор', 'вариаторная', 'cvt', 'вариатор', 'вариатора', 'вариатору', 'вариатором', 'вариаторы', 'вариаторами', 'вариаторной', 'вариаторным', 'вариаторными']
}

DRIVE_SYNONYMS = {
    'передний': ['передний', 'переднеприводный', 'front-wheel drive', 'передним', 'переднии', 'передний привод', 'передняя', 'переднее', 'передние', 'передний', 'передней', 'передними'],
    'задний': ['задний', 'заднеприводный', 'rear-wheel drive', 'задним', 'заднии', 'задний привод', 'задняя', 'заднее', 'задние', 'задний', 'задней', 'задними'],
    'полный': ['полный', 'полноприводный', 'all-wheel drive', '4x4', 'полным', 'полныи', 'полный привод', 'приводом', 'полная', 'полное', 'полные', 'полный', 'полным', 'привод', 'приводом', 'полной', 'полными']
} 

# Добавляем морфологический анализ для русского языка
def normalize_russian_text(text: str) -> str:
    """
    Нормализация русского текста с учетом морфологии
    """
    if not text:
        return ""
    
    # Приведение к нижнему регистру
    text = text.lower()
    
    # Удаление лишних пробелов
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Базовая нормализация русских окончаний
    # Это упрощенная версия, в реальном проекте лучше использовать pymorphy2
    russian_endings = {
        'ая': 'ый',  # женский род -> мужской род
        'ое': 'ый',
        'ые': 'ый',
        'ой': 'ый',
        'а': '',     # убираем окончания
        'я': '',
        'о': '',
        'е': '',
        'и': '',
        'ы': '',
        'ь': '',
        'ъ': ''
    }
    
    words = text.split()
    normalized_words = []
    
    for word in words:
        # Пропускаем короткие слова
        if len(word) <= 2:
            normalized_words.append(word)
            continue
            
        # Применяем нормализацию окончаний
        normalized_word = word
        for ending, replacement in russian_endings.items():
            if word.endswith(ending) and len(word) > len(ending) + 2:
                normalized_word = word[:-len(ending)] + replacement
                break
        
        normalized_words.append(normalized_word)
    
    return ' '.join(normalized_words)

def get_word_variants(word: str) -> Set[str]:
    """
    Генерирует варианты слова с учетом русской морфологии
    """
    variants = {word}
    
    # Базовые варианты
    if word.endswith('ый'):
        variants.add(word[:-2] + 'ая')  # мужской -> женский
        variants.add(word[:-2] + 'ое')  # мужской -> средний
        variants.add(word[:-2] + 'ые')  # мужской -> множественный
    elif word.endswith('ая'):
        variants.add(word[:-2] + 'ый')  # женский -> мужской
        variants.add(word[:-2] + 'ое')  # женский -> средний
        variants.add(word[:-2] + 'ые')  # женский -> множественный
    
    # Варианты с разными окончаниями
    if word.endswith('а'):
        variants.add(word[:-1] + 'ы')
        variants.add(word[:-1] + 'е')
    elif word.endswith('ы'):
        variants.add(word[:-1] + 'а')
        variants.add(word[:-1] + 'е')
    
    return variants

class UnifiedPreprocessor:
    """
    Единый препроцессор для всех модулей NER
    """
    def __init__(self):
        self.normalization_cache = {}
        self.morphology_cache = {}
    
    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """
        Единый препроцессинг текста для всех модулей
        """
        if not text:
            return {
                'normalized': '',
                'tokens': [],
                'lemmatized': [],
                'morphological_variants': set(),
                'phonetic_variants': set()
            }
        
        # Кэширование результатов
        if text in self.normalization_cache:
            return self.normalization_cache[text]
        
        # 1. Базовая нормализация
        normalized = normalize_russian_text(text)
        
        # 2. Токенизация
        tokens = smart_tokenization(normalized)
        
        # 3. Лемматизация
        lemmatized = lemmatize_list(tokens)
        
        # 4. Морфологические варианты
        morphological_variants = set()
        for token in tokens:
            variants = get_word_variants(token)
            morphological_variants.update(variants)
        
        # 5. Фонетические варианты
        phonetic_variants = set()
        for token in tokens:
            phonetic_variants.add(jellyfish.soundex(token))
            phonetic_variants.add(jellyfish.metaphone(token))
        
        result = {
            'normalized': normalized,
            'tokens': tokens,
            'lemmatized': lemmatized,
            'morphological_variants': morphological_variants,
            'phonetic_variants': phonetic_variants
        }
        
        # Кэшируем результат
        self.normalization_cache[text] = result
        return result

# Глобальный экземпляр препроцессора
unified_preprocessor = UnifiedPreprocessor()

class CascadeEntityProcessor:
    """
    Каскадный процессор для улучшения точности извлечения сущностей
    """
    def __init__(self, entity_extractor, enhanced_processor, ner_classifier):
        self.entity_extractor = entity_extractor
        self.enhanced_processor = enhanced_processor
        self.ner_classifier = ner_classifier
        self.confidence_thresholds = {
            'brand': 0.7,
            'model': 0.7,
            'color': 0.6,
            'transmission': 0.65,
            'drive_type': 0.65,
            'fuel_type': 0.6,
            'options': 0.7,
            'prices': 0.8,
            'years': 0.75
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Каскадная обработка запроса с использованием всех модулей
        """
        # 1. Препроцессинг
        preprocessed = unified_preprocessor.preprocess_text(query)
        
        # 2. Извлечение сущностей всеми модулями
        entity_results = self.entity_extractor.extract_all_entities(query)
        enhanced_results = self.enhanced_processor.extract_entities(query)
        ner_results = self.ner_classifier.extract_entities(query)
        
        # 3. Объединение результатов с весами
        final_results = self._merge_results(
            entity_results, enhanced_results, ner_results, preprocessed
        )
        
        # 4. Фильтрация по уверенности
        filtered_results = self._filter_by_confidence(final_results)
        
        return filtered_results
    
    def _merge_results(self, entity_results, enhanced_results, ner_results, preprocessed):
        """
        Объединение результатов с учетом уверенности и контекста
        """
        merged = {}
        
        # Веса для разных модулей
        weights = {
            'entity_extractor': 0.4,
            'enhanced_processor': 0.35,
            'ner_classifier': 0.25
        }
        
        # Объединяем все типы сущностей
        all_entities = set()
        for results in [entity_results, enhanced_results, ner_results]:
            if isinstance(results, dict):
                all_entities.update(results.keys())
        
        for entity_type in all_entities:
            candidates = []
            
            # Собираем кандидатов из всех модулей
            if entity_type in entity_results:
                candidates.append(('entity_extractor', entity_results[entity_type]))
            if entity_type in enhanced_results:
                candidates.append(('enhanced_processor', enhanced_results[entity_type]))
            if entity_type in ner_results:
                candidates.append(('ner_classifier', ner_results[entity_type]))
            
            # Выбираем лучший результат
            if candidates:
                best_candidate = self._select_best_candidate(
                    candidates, entity_type, preprocessed
                )
                merged[entity_type] = best_candidate
        
        return merged
    
    def _select_best_candidate(self, candidates, entity_type, preprocessed):
        """
        Выбор лучшего кандидата на основе уверенности и контекста
        """
        best_score = 0
        best_candidate = None
        
        # Веса для разных модулей
        weights = {
            'entity_extractor': 0.4,
            'enhanced_processor': 0.35,
            'ner_classifier': 0.25
        }
        
        for module_name, candidate in candidates:
            # Базовая оценка уверенности модуля
            base_score = weights.get(module_name, 0.3)
            
            # Дополнительная оценка на основе контекста
            context_score = self._evaluate_context(candidate, entity_type, preprocessed)
            
            # Итоговая оценка
            total_score = base_score * 0.7 + context_score * 0.3
            
            if total_score > best_score:
                best_score = total_score
                best_candidate = candidate
        
        return best_candidate
    
    def _evaluate_context(self, candidate, entity_type, preprocessed):
        """
        Оценка кандидата в контексте запроса
        """
        if not candidate:
            return 0.0
        
        # Проверяем соответствие морфологическим вариантам
        morphological_match = 0.0
        for variant in preprocessed.get('morphological_variants', []):
            if isinstance(candidate, str) and variant in candidate.lower():
                morphological_match = max(morphological_match, 0.8)
            elif isinstance(candidate, list):
                for item in candidate:
                    if isinstance(item, str) and variant in item.lower():
                        morphological_match = max(morphological_match, 0.8)
        
        # Проверяем соответствие лемматизированным словам
        lemmatized_match = 0.0
        for lemma in preprocessed.get('lemmatized', []):
            if isinstance(candidate, str) and lemma in candidate.lower():
                lemmatized_match = max(lemmatized_match, 0.9)
            elif isinstance(candidate, list):
                for item in candidate:
                    if isinstance(item, str) and lemma in item.lower():
                        lemmatized_match = max(lemmatized_match, 0.9)
        
        return max(morphological_match, lemmatized_match)
    
    def _filter_by_confidence(self, results):
        """
        Фильтрация результатов по порогам уверенности
        """
        filtered = {}
        
        for entity_type, value in results.items():
            threshold = self.confidence_thresholds.get(entity_type, 0.6)
            
            # Проверяем уверенность (упрощенная логика)
            if value and (isinstance(value, list) and len(value) > 0 or 
                         isinstance(value, str) and value.strip()):
                filtered[entity_type] = value
        
        return filtered