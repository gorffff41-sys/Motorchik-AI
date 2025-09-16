from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime
import wikipedia
from dotenv import load_dotenv
import threading
import queue
import re
import math
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Конфигурация
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'your_weather_api_key')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'your_news_api_key')

# Глобальные переменные для модели
model_loaded = True  # Всегда True для простой версии
model_loading = False

def get_weather(city):
    """Получение прогноза погоды"""
    try:
        # Если нет API ключа, возвращаем демо данные
        if WEATHER_API_KEY == 'your_weather_api_key':
            return {
                'city': city,
                'temperature': 22,
                'feels_like': 24,
                'description': 'ясно',
                'humidity': 65,
                'wind_speed': 3.2,
                'pressure': 1013
            }
        
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            weather_info = {
                'city': data['name'],
                'temperature': round(data['main']['temp']),
                'feels_like': round(data['main']['feels_like']),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure']
            }
            return weather_info
        else:
            return None
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None

def get_news(query="новости"):
    """Получение новостей"""
    try:
        # Если нет API ключа, возвращаем демо данные
        if NEWS_API_KEY == 'your_news_api_key':
            return [
                {
                    'title': 'Демо новость 1: Важные события в мире технологий',
                    'description': 'Последние достижения в области искусственного интеллекта и машинного обучения.',
                    'url': 'https://example.com/news1',
                    'publishedAt': '2025-07-31T10:00:00Z'
                },
                {
                    'title': 'Демо новость 2: Развитие экологически чистых технологий',
                    'description': 'Новые решения для защиты окружающей среды и устойчивого развития.',
                    'url': 'https://example.com/news2',
                    'publishedAt': '2025-07-31T09:30:00Z'
                },
                {
                    'title': 'Демо новость 3: Инновации в медицине',
                    'description': 'Передовые методы лечения и диагностики заболеваний.',
                    'url': 'https://example.com/news3',
                    'publishedAt': '2025-07-31T09:00:00Z'
                }
            ]
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'ru',
            'sortBy': 'publishedAt',
            'pageSize': 5
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article['title'],
                    'description': article['description'],
                    'url': article['url'],
                    'publishedAt': article['publishedAt']
                })
            return articles
        else:
            return []
    except Exception as e:
        print(f"Ошибка получения новостей: {e}")
        return []

def get_wikipedia_info(query):
    """Получение информации из Wikipedia"""
    try:
        wikipedia.set_lang('ru')
        # Поиск страницы
        search_results = wikipedia.search(query, results=3)
        if search_results:
            page = wikipedia.page(search_results[0])
            summary = wikipedia.summary(search_results[0], sentences=3)
            return {
                'title': page.title,
                'summary': summary,
                'url': page.url
            }
        else:
            return None
    except Exception as e:
        print(f"Ошибка Wikipedia: {e}")
        return None

def calculate_expression(expression):
    """Калькулятор - безопасное вычисление математических выражений"""
    try:
        # Удаляем все символы кроме цифр, операторов и скобок
        clean_expr = re.sub(r'[^0-9+\-*/().]', '', expression)
        
        # Проверяем безопасность выражения
        if not re.match(r'^[0-9+\-*/().\s]+$', clean_expr):
            return None, "Недопустимые символы в выражении"
        
        # Проверяем баланс скобок
        if clean_expr.count('(') != clean_expr.count(')'):
            return None, "Несбалансированные скобки"
        
        # Вычисляем результат
        result = eval(clean_expr)
        
        # Проверяем на бесконечность
        if not math.isfinite(result):
            return None, "Результат слишком большой"
        
        return result, None
    except Exception as e:
        return None, f"Ошибка вычисления: {str(e)}"

def convert_currency(amount, from_currency, to_currency):
    """Конвертер валют"""
    try:
        # Простые курсы валют (можно заменить на API)
        rates = {
            'USD': {'RUB': 95.0, 'EUR': 0.85, 'CNY': 6.5, 'GBP': 0.78},
            'EUR': {'RUB': 112.0, 'USD': 1.18, 'CNY': 7.65, 'GBP': 0.92},
            'RUB': {'USD': 0.0105, 'EUR': 0.0089, 'CNY': 0.068, 'GBP': 0.0082},
            'CNY': {'USD': 0.154, 'EUR': 0.131, 'RUB': 14.7, 'GBP': 0.12},
            'GBP': {'USD': 1.28, 'EUR': 1.09, 'RUB': 122.0, 'CNY': 8.33}
        }
        
        if from_currency == to_currency:
            return amount
        
        if from_currency in rates and to_currency in rates[from_currency]:
            return round(amount * rates[from_currency][to_currency], 2)
        else:
            return None
    except Exception as e:
        print(f"Ошибка конвертации валют: {e}")
        return None

def translate_text(text, target_lang='en'):
    """Простой переводчик (можно заменить на API)"""
    try:
        # Расширенный словарь для демонстрации
        translations = {
            'привет': 'hello',
            'пока': 'goodbye',
            'спасибо': 'thank you',
            'пожалуйста': 'please',
            'да': 'yes',
            'нет': 'no',
            'хорошо': 'good',
            'плохо': 'bad',
            'красиво': 'beautiful',
            'интересно': 'interesting',
            'сложно': 'difficult',
            'легко': 'easy',
            'большой': 'big',
            'маленький': 'small',
            'новый': 'new',
            'старый': 'old'
        }
        
        if target_lang == 'en':
            return translations.get(text.lower(), f"[Перевод: {text}]")
        else:
            return f"[Перевод на {target_lang}: {text}]"
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return None

def generate_ai_response(message):
    """Генерация ответа с помощью простого AI"""
    try:
        # Простые ответы на основе ключевых слов
        message_lower = message.lower()
        
        responses = {
            'привет': 'Привет! Как дела? Рад тебя видеть! 😊',
            'как дела': 'Отлично, спасибо! А у тебя как дела?',
            'анекдот': 'Программист заходит в лифт, а там написано "JS" и со стрелкой вниз. Программист подумал: "О, JavaScript!" 😄',
            'стихотворение': 'В мире кода и алгоритмов\nГде логика правит бал\nКаждая строка как символ\nВеликого цифрового храма',
            'искусственный интеллект': 'Искусственный интеллект - это технология, которая позволяет компьютерам обучаться и принимать решения, имитируя человеческое мышление.',
            'помощь': 'Я могу помочь с погодой, новостями, Wikipedia, калькулятором, конвертером валют и переводом!',
            'спасибо': 'Пожалуйста! Рад помочь! 😊',
            'пока': 'До свидания! Было приятно пообщаться! 👋'
        }
        
        # Поиск подходящего ответа
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        # Если нет точного совпадения, возвращаем общий ответ
        return "Интересный вопрос! Я - AI помощник, и я могу помочь с различными задачами. Попробуй спросить о погоде, новостях или других функциях!"
        
    except Exception as e:
        print(f"Ошибка генерации ответа: {e}")
        return "Извините, произошла ошибка при генерации ответа."

def process_message(message):
    """Обработка сообщения и определение типа запроса"""
    message_lower = message.lower()
    
    # Проверка на запрос погоды
    weather_keywords = ['погода', 'погоду', 'температура', 'климат', 'weather']
    if any(keyword in message_lower for keyword in weather_keywords):
        # Извлекаем название города
        words = message.split()
        city = None
        for i, word in enumerate(words):
            if word.lower() in weather_keywords:
                if i + 1 < len(words):
                    city = words[i + 1]
                break
        
        if not city:
            city = "Москва"  # По умолчанию
        
        weather = get_weather(city)
        if weather:
            return {
                'type': 'weather',
                'content': weather,
                'message': f"🌤️ Прогноз погоды для {weather['city']}:\n"
                          f"🌡️ Температура: {weather['temperature']}°C\n"
                          f"🌡️ Ощущается как: {weather['feels_like']}°C\n"
                          f"☁️ Описание: {weather['description']}\n"
                          f"💧 Влажность: {weather['humidity']}%\n"
                          f"💨 Ветер: {weather['wind_speed']} м/с\n"
                          f"🌡️ Давление: {weather['pressure']} гПа"
            }
        else:
            return {
                'type': 'error',
                'content': 'Не удалось получить прогноз погоды'
            }
    
    # Проверка на запрос новостей
    news_keywords = ['новости', 'новость', 'события', 'происшествия', 'news']
    if any(keyword in message_lower for keyword in news_keywords):
        news = get_news()
        if news:
            news_text = "📰 Последние новости:\n\n"
            for i, article in enumerate(news, 1):
                news_text += f"{i}. {article['title']}\n"
                news_text += f"   {article['description']}\n"
                news_text += f"   📅 {article['publishedAt'][:10]}\n\n"
            
            return {
                'type': 'news',
                'content': news,
                'message': news_text
            }
        else:
            return {
                'type': 'error',
                'content': 'Не удалось получить новости'
            }
    
    # Проверка на запрос информации из Wikipedia
    wiki_keywords = ['что такое', 'кто такой', 'определение', 'википедия', 'wikipedia']
    if any(keyword in message_lower for keyword in wiki_keywords):
        query = message.replace('что такое', '').replace('кто такой', '').replace('определение', '').replace('википедия', '').replace('wikipedia', '').strip()
        wiki_info = get_wikipedia_info(query)
        if wiki_info:
            return {
                'type': 'wikipedia',
                'content': wiki_info,
                'message': f"📚 {wiki_info['title']}\n\n{wiki_info['summary']}\n\n🔗 Подробнее: {wiki_info['url']}"
            }
        else:
            return {
                'type': 'error',
                'content': 'Не удалось найти информацию в Wikipedia'
            }
    
    # Проверка на калькулятор
    calc_patterns = [
        r'посчитай\s+(.+)',
        r'вычисли\s+(.+)',
        r'сколько будет\s+(.+)',
        r'вычислить\s+(.+)',
        r'calculate\s+(.+)'
    ]
    
    for pattern in calc_patterns:
        match = re.search(pattern, message_lower)
        if match:
            expression = match.group(1)
            result, error = calculate_expression(expression)
            if result is not None:
                return {
                    'type': 'calculator',
                    'content': {'expression': expression, 'result': result},
                    'message': f"🧮 Калькулятор:\n{expression} = {result}"
                }
            else:
                return {
                    'type': 'error',
                    'content': error
                }
    
    # Проверка на конвертер валют
    currency_patterns = [
        r'(\d+(?:\.\d+)?)\s*(usd|руб|рублей|доллар|долларов|eur|евро|eur|gbp|фунт|фунтов|cny|юань|юаней)\s*(?:в|to|конвертируй)\s*(rub|руб|рублей|usd|доллар|долларов|eur|евро|gbp|фунт|фунтов|cny|юань|юаней)',
        r'конвертируй\s+(\d+(?:\.\d+)?)\s*(usd|руб|рублей|доллар|долларов|eur|евро|gbp|фунт|фунтов|cny|юань|юаней)\s*(?:в|to)\s*(rub|руб|рублей|usd|доллар|долларов|eur|евро|gbp|фунт|фунтов|cny|юань|юаней)'
    ]
    
    for pattern in currency_patterns:
        match = re.search(pattern, message_lower)
        if match:
            amount = float(match.group(1))
            from_curr = match.group(2)
            to_curr = match.group(3)
            
            # Нормализация валют
            if from_curr in ['руб', 'рублей']:
                from_curr = 'RUB'
            elif from_curr in ['доллар', 'долларов', 'usd']:
                from_curr = 'USD'
            elif from_curr in ['евро', 'eur']:
                from_curr = 'EUR'
            elif from_curr in ['фунт', 'фунтов', 'gbp']:
                from_curr = 'GBP'
            elif from_curr in ['юань', 'юаней', 'cny']:
                from_curr = 'CNY'
            
            if to_curr in ['руб', 'рублей']:
                to_curr = 'RUB'
            elif to_curr in ['доллар', 'долларов', 'usd']:
                to_curr = 'USD'
            elif to_curr in ['евро', 'eur']:
                to_curr = 'EUR'
            elif to_curr in ['фунт', 'фунтов', 'gbp']:
                to_curr = 'GBP'
            elif to_curr in ['юань', 'юаней', 'cny']:
                to_curr = 'CNY'
            
            result = convert_currency(amount, from_curr, to_curr)
            if result is not None:
                return {
                    'type': 'currency',
                    'content': {'amount': amount, 'from': from_curr, 'to': to_curr, 'result': result},
                    'message': f"💱 Конвертация валют:\n{amount} {from_curr} = {result} {to_curr}"
                }
            else:
                return {
                    'type': 'error',
                    'content': 'Не удалось конвертировать валюту'
                }
    
    # Проверка на переводчик
    translate_patterns = [
        r'переведи\s+(.+)',
        r'перевод\s+(.+)',
        r'translate\s+(.+)'
    ]
    
    for pattern in translate_patterns:
        match = re.search(pattern, message_lower)
        if match:
            text = match.group(1).strip()
            translation = translate_text(text)
            if translation:
                return {
                    'type': 'translator',
                    'content': {'original': text, 'translation': translation},
                    'message': f"🌐 Перевод:\n{text} → {translation}"
                }
            else:
                return {
                    'type': 'error',
                    'content': 'Не удалось перевести текст'
                }
    
    # Обычный запрос к AI
    return {
        'type': 'gpt',
        'content': None,
        'message': None
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Обработка сообщения
        result = process_message(message)
        
        if result['type'] == 'gpt':
            # Используем AI модель
            response = generate_ai_response(message)
            
            return jsonify({
                'type': 'gpt',
                'message': response,
                'timestamp': datetime.now().isoformat()
            })
        
        elif result['type'] in ['weather', 'news', 'wikipedia', 'calculator', 'currency', 'translator']:
            return jsonify({
                'type': result['type'],
                'message': result['message'],
                'data': result['content'],
                'timestamp': datetime.now().isoformat()
            })
        
        else:
            return jsonify({
                'type': 'error',
                'message': result['content'],
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        return jsonify({
            'error': f'Произошла ошибка: {str(e)}'
        }), 500

@app.route('/api/status')
def status():
    return jsonify({
        'model_loaded': model_loaded,
        'model_loading': model_loading,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Запуск простой AI версии Чат-Бота...")
    print("📱 Приложение будет доступно по адресу: http://localhost:5000")
    print("✅ Модель готова к работе!")
    app.run(debug=True, host='0.0.0.0', port=5000) 