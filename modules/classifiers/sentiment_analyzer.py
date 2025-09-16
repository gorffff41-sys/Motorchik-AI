import re
from typing import Dict, Any, Tuple
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    """
    Модуль для анализа настроений пользователей в контексте автомобильной тематики.
    """
    
    def __init__(self):
        # Автомобильные ключевые слова для контекстного анализа
        self.car_positive_words = {
            'отличный', 'прекрасный', 'великолепный', 'потрясающий', 'удивительный',
            'надежный', 'качественный', 'прочный', 'безопасный', 'комфортный',
            'экономичный', 'выгодный', 'дешевый', 'доступный', 'приемлемый',
            'быстрый', 'динамичный', 'мощный', 'энергичный', 'спортивный',
            'стильный', 'красивый', 'элегантный', 'современный', 'модный',
            'удобный', 'просторный', 'вместительный', 'практичный', 'функциональный',
            'новый', 'свежий', 'актуальный', 'современный', 'инновационный',
            'популярный', 'востребованный', 'проверенный', 'надежный', 'стабильный'
        }
        
        self.car_negative_words = {
            'плохой', 'ужасный', 'отвратительный', 'некачественный', 'ненадежный',
            'дорогой', 'завышенный', 'недоступный', 'невыгодный', 'неоправданный',
            'медленный', 'вялый', 'слабый', 'неэффективный', 'неэкономичный',
            'некрасивый', 'уродливый', 'старомодный', 'устаревший', 'несовременный',
            'неудобный', 'тесный', 'непрактичный', 'нефункциональный', 'неудобный',
            'старый', 'изношенный', 'проблемный', 'неисправный', 'сломанный',
            'непопулярный', 'невостребованный', 'сомнительный', 'ненадежный', 'рискованный'
        }
        
        self.car_neutral_words = {
            'обычный', 'стандартный', 'типичный', 'средний', 'нормальный',
            'приемлемый', 'удовлетворительный', 'достаточный', 'подходящий',
            'разный', 'различный', 'разнообразный', 'множественный', 'многочисленный'
        }
        
        # Контекстные фразы для автомобильной тематики
        self.car_context_phrases = {
            'positive': [
                'хороший выбор', 'отличная покупка', 'рекомендую', 'доволен',
                'нравится', 'подходит', 'удовлетворен', 'рад', 'счастлив',
                'стоит своих денег', 'качество на высоте', 'не пожалел',
                'лучший в своем классе', 'превосходит ожидания'
            ],
            'negative': [
                'плохой выбор', 'не рекомендую', 'недоволен', 'не нравится',
                'не подходит', 'разочарован', 'жалею', 'неудачная покупка',
                'не стоит денег', 'качество плохое', 'пожалел',
                'худший в своем классе', 'не оправдал ожидания'
            ]
        }
        
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Анализирует настроение текста с учетом автомобильного контекста.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Словарь с результатами анализа
        """
        text_lower = text.lower()
        
        # Базовый анализ с помощью VADER
        vader_scores = self.sia.polarity_scores(text)
        
        # Контекстный анализ для автомобильной тематики
        car_context_score = self._analyze_car_context(text_lower)
        
        # Комбинированный анализ
        combined_score = self._combine_scores(vader_scores, car_context_score)
        
        # Определение эмоционального состояния
        emotion = self._classify_emotion(text_lower)
        
        # Определение уровня уверенности
        confidence = self._calculate_confidence(text_lower, vader_scores, car_context_score)
        
        return {
            'sentiment': combined_score['sentiment'],
            'overall_sentiment': combined_score['sentiment'],
            'sentiment_score': combined_score['score'],
            'vader_scores': vader_scores,
            'car_context_score': car_context_score,
            'emotion': emotion,
            'confidence': confidence,
            'positive_words': self._extract_positive_words(text_lower),
            'negative_words': self._extract_negative_words(text_lower),
            'car_specific_terms': self._extract_car_terms(text_lower)
        }
    
    def _analyze_car_context(self, text: str) -> Dict[str, float]:
        """Анализирует контекст автомобильной тематики."""
        positive_count = sum(1 for word in self.car_positive_words if word in text)
        negative_count = sum(1 for word in self.car_negative_words if word in text)
        neutral_count = sum(1 for word in self.car_neutral_words if word in text)
        
        # Анализ контекстных фраз
        positive_phrases = sum(1 for phrase in self.car_context_phrases['positive'] if phrase in text)
        negative_phrases = sum(1 for phrase in self.car_context_phrases['negative'] if phrase in text)
        
        total_car_terms = positive_count + negative_count + neutral_count + positive_phrases + negative_phrases
        
        if total_car_terms == 0:
            return {'score': 0.0, 'confidence': 0.0}
        
        # Взвешенный скор
        weighted_score = (positive_count + positive_phrases * 2 - negative_count - negative_phrases * 2) / total_car_terms
        
        # Нормализация к диапазону [-1, 1]
        normalized_score = max(-1.0, min(1.0, weighted_score))
        
        return {
            'score': normalized_score,
            'confidence': min(1.0, total_car_terms / 10.0),  # Уверенность на основе количества терминов
            'positive_count': positive_count + positive_phrases,
            'negative_count': negative_count + negative_phrases,
            'neutral_count': neutral_count
        }
    
    def _combine_scores(self, vader_scores: Dict[str, float], car_context: Dict[str, float]) -> Dict[str, Any]:
        """Полностью переписанная логика анализа настроений."""
        vader_compound = vader_scores['compound']
        car_score = car_context['score']
        car_confidence = car_context['confidence']
        
        # Получаем количество позитивных и негативных слов
        positive_count = car_context.get('positive_count', 0)
        negative_count = car_context.get('negative_count', 0)
        
        # Определяем настроение на основе ключевых слов
        if positive_count > negative_count and positive_count > 0:
            sentiment = 'positive'
            combined_score = 0.3
        elif negative_count > positive_count and negative_count > 0:
            sentiment = 'negative'
            combined_score = -0.3
        else:
            # Используем VADER как основу
            combined_score = vader_compound
            
            # Определяем настроение с более мягкими порогами
            if combined_score >= 0.05:
                sentiment = 'positive'
            elif combined_score <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': combined_score,
            'vader_compound': vader_compound,
            'car_score': car_score,
            'car_confidence': car_confidence,
            'positive_words': positive_count,
            'negative_words': negative_count
        }
    
    def _classify_emotion(self, text: str) -> str:
        """Классифицирует эмоциональное состояние."""
        emotions = {
            'joy': ['рад', 'счастлив', 'доволен', 'восторг', 'восхищение'],
            'anger': ['злой', 'раздражен', 'недоволен', 'возмущен', 'разочарован'],
            'fear': ['боюсь', 'страшно', 'опасно', 'риск', 'сомневаюсь'],
            'sadness': ['грустно', 'печально', 'жаль', 'разочарован', 'неудачно'],
            'surprise': ['удивительно', 'неожиданно', 'потрясающе', 'впечатляет'],
            'disgust': ['отвратительно', 'ужасно', 'плохо', 'неприятно'],
            'trust': ['доверяю', 'надежный', 'проверенный', 'качественный'],
            'anticipation': ['ожидаю', 'надеюсь', 'планирую', 'будущее']
        }
        
        emotion_scores = {}
        for emotion, keywords in emotions.items():
            score = sum(1 for keyword in keywords if keyword in text)
            emotion_scores[emotion] = score
        
        if not any(emotion_scores.values()):
            return 'neutral'
        
        return max(emotion_scores, key=emotion_scores.get)
    
    def _calculate_confidence(self, text: str, vader_scores: Dict[str, float], car_context: Dict[str, float]) -> float:
        """Рассчитывает уровень уверенности в анализе."""
        # Базовая уверенность от VADER
        vader_confidence = abs(vader_scores['compound'])
        
        # Уверенность от автомобильного контекста
        car_confidence = car_context['confidence']
        
        # Дополнительные факторы
        text_length_factor = min(1.0, len(text.split()) / 20.0)
        
        # Комбинированная уверенность
        confidence = (vader_confidence * 0.4 + car_confidence * 0.4 + text_length_factor * 0.2)
        
        return min(1.0, confidence)
    
    def _extract_positive_words(self, text: str) -> list:
        """Извлекает позитивные слова из текста."""
        return [word for word in self.car_positive_words if word in text]
    
    def _extract_negative_words(self, text: str) -> list:
        """Извлекает негативные слова из текста."""
        return [word for word in self.car_negative_words if word in text]
    
    def _extract_car_terms(self, text: str) -> Dict[str, list]:
        """Извлекает автомобильные термины из текста."""
        car_terms = {
            'positive': self._extract_positive_words(text),
            'negative': self._extract_negative_words(text),
            'neutral': [word for word in self.car_neutral_words if word in text]
        }
        return car_terms
    
    def analyze_user_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Специализированный анализ для пользовательских отзывов."""
        sentiment_result = self.analyze_sentiment(feedback_text)
        
        # Дополнительный анализ для отзывов
        feedback_analysis = {
            'is_complaint': self._is_complaint(feedback_text),
            'is_recommendation': self._is_recommendation(feedback_text),
            'urgency_level': self._calculate_urgency(feedback_text),
            'satisfaction_level': self._calculate_satisfaction(feedback_text)
        }
        
        sentiment_result.update(feedback_analysis)
        return sentiment_result
    
    def _is_complaint(self, text: str) -> bool:
        """Определяет, является ли текст жалобой."""
        complaint_keywords = ['жалоба', 'проблема', 'неисправность', 'поломка', 'дефект', 'недостаток']
        return any(keyword in text.lower() for keyword in complaint_keywords)
    
    def _is_recommendation(self, text: str) -> bool:
        """Определяет, является ли текст рекомендацией."""
        recommendation_keywords = ['рекомендую', 'советую', 'стоит', 'лучше', 'предпочитаю']
        return any(keyword in text.lower() for keyword in recommendation_keywords)
    
    def _calculate_urgency(self, text: str) -> str:
        """Рассчитывает уровень срочности."""
        urgent_keywords = ['срочно', 'немедленно', 'критично', 'важно', 'неотложно']
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in text.lower())
        
        if urgent_count >= 2:
            return 'high'
        elif urgent_count == 1:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_satisfaction(self, text: str) -> float:
        """Рассчитывает уровень удовлетворенности."""
        satisfaction_keywords = {
            'very_satisfied': ['очень доволен', 'полностью доволен', 'превосходно', 'отлично'],
            'satisfied': ['доволен', 'хорошо', 'нормально', 'устраивает'],
            'neutral': ['нейтрально', 'обычно', 'стандартно'],
            'dissatisfied': ['недоволен', 'плохо', 'не устраивает'],
            'very_dissatisfied': ['очень недоволен', 'ужасно', 'отвратительно']
        }
        
        scores = {
            'very_satisfied': 1.0,
            'satisfied': 0.7,
            'neutral': 0.5,
            'dissatisfied': 0.3,
            'very_dissatisfied': 0.0
        }
        
        max_score = 0.0
        for level, keywords in satisfaction_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                max_score = max(max_score, scores[level])
        
        return max_score 
 
 