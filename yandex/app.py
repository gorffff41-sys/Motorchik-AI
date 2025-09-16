from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import requests
from datetime import datetime
import wikipedia
from dotenv import load_dotenv
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import threading
import queue
import re
import math

load_dotenv()

app = Flask(__name__)
CORS(app)

# Конфигурация
MODEL_NAME = "yandex/YandexGPT-5-Lite-8B-instruct"
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', 'your_weather_api_key')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'your_news_api_key')
EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY', 'your_exchange_api_key')

# Глобальные переменные для модели
model = None
tokenizer = None
model_loaded = False

def load_model():
    """Загрузка модели Yandex GPT в отдельном потоке"""
    global model, tokenizer, model_loaded
    try:
        print("Загрузка модели Yandex GPT...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            device_map="auto",
            torch_dtype="auto",
        )
        model_loaded = True
        print("Модель успешно загружена!")
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        model_loaded = False

# Запуск загрузки модели в фоне
threading.Thread(target=load_model, daemon=True).start()

def get_weather(city):
    """Получение прогноза погоды"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        response = requests.get(url, params=params)
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
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'ru',
            'sortBy': 'publishedAt',
            'pageSize': 5
        }
        response = requests.get(url, params=params)
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
            'USD': {'RUB': 95.0, 'EUR': 0.85, 'CNY': 6.5},
            'EUR': {'RUB': 112.0, 'USD': 1.18, 'CNY': 7.65},
            'RUB': {'USD': 0.0105, 'EUR': 0.0089, 'CNY': 0.068},
            'CNY': {'USD': 0.154, 'EUR': 0.131, 'RUB': 14.7}
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
        # Простой словарь для демонстрации
        translations = {
            'привет': 'hello',
            'пока': 'goodbye',
            'спасибо': 'thank you',
            'пожалуйста': 'please',
            'да': 'yes',
            'нет': 'no'
        }
        
        if target_lang == 'en':
            return translations.get(text.lower(), f"[Перевод: {text}]")
        else:
            return f"[Перевод на {target_lang}: {text}]"
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return None

def generate_yandex_response(messages):
    """Генерация ответа с помощью Yandex GPT"""
    global model, tokenizer, model_loaded
    
    if not model_loaded:
        return "Модель еще загружается. Пожалуйста, подождите немного..."
    
    try:
        input_ids = tokenizer.apply_chat_template(
            messages, tokenize=True, return_tensors="pt"
        )
        
        if torch.cuda.is_available():
            input_ids = input_ids.to("cuda")
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids, 
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        response = tokenizer.decode(
            outputs[0][input_ids.size(1):], 
            skip_special_tokens=True
        )
        return response.strip()
    
    except Exception as e:
        print(f"Ошибка генерации ответа: {e}")
        return "Извините, произошла ошибка при генерации ответа."

def process_message(message):
    """Обработка сообщения и определение типа запроса"""
    message_lower = message.lower()
    
    # Проверка на запрос погоды
    weather_keywords = ['погода', 'погоду', 'температура', 'климат']
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
    news_keywords = ['новости', 'новость', 'события', 'происшествия']
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
    wiki_keywords = ['что такое', 'кто такой', 'определение', 'википедия']
    if any(keyword in message_lower for keyword in wiki_keywords):
        query = message.replace('что такое', '').replace('кто такой', '').replace('определение', '').replace('википедия', '').strip()
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
        r'вычислить\s+(.+)'
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
        r'(\d+(?:\.\d+)?)\s*(usd|руб|рублей|доллар|долларов)\s*(?:в|to)\s*(rub|руб|рублей|usd|доллар|долларов)',
        r'конвертируй\s+(\d+(?:\.\d+)?)\s*(usd|руб|рублей|доллар|долларов)\s*(?:в|to)\s*(rub|руб|рублей|usd|доллар|долларов)'
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
            
            if to_curr in ['руб', 'рублей']:
                to_curr = 'RUB'
            elif to_curr in ['доллар', 'долларов', 'usd']:
                to_curr = 'USD'
            
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
    
    # Обычный запрос к Yandex GPT
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
            # Используем Yandex GPT
            messages = [{"role": "user", "content": message}]
            response = generate_yandex_response(messages)
            
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
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 