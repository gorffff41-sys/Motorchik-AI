#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-интерфейс для управления тегами автомобилей
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import logging
from datetime import datetime
import os
from database import get_db
from llama_entity_extractor import llama_entity_extractor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем доступные таблицы
AVAILABLE_TABLES = ['car', 'used_car']

# Определяем доступные теги
AVAILABLE_TAGS = [
    'budget_tag',      # Бюджетный
    'premium_tag',     # Премиум
    'family_tag',      # Семейный
    'sport_tag',       # Спортивный
    'city_tag',        # Городской
    'offroad_tag',     # Внедорожный
    'eco_tag',         # Экологичный
    'reliable_tag',    # Надежный
    'new_tag',         # Новый
    'used_tag'         # Подержанный
]

@app.route('/')
def index():
    """Главная страница"""
    return render_template('tag_manager.html', 
                         tables=AVAILABLE_TABLES, 
                         tags=AVAILABLE_TAGS)

@app.route('/api/tables')
def get_tables():
    """Получить список таблиц"""
    return jsonify({'tables': AVAILABLE_TABLES})

@app.route('/api/table/<table_name>/columns')
def get_table_columns(table_name):
    """Получить колонки таблицы"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            return jsonify({'columns': columns})
    except Exception as e:
        logger.error(f"Ошибка получения колонок: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/data')
def get_table_data(table_name):
    """Получить данные таблицы"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        offset = (page - 1) * per_page
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Получаем общее количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()[0]
            
            # Получаем данные с пагинацией
            cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (per_page, offset))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                # Конвертируем datetime объекты в строки
                for key, value in record.items():
                    if hasattr(value, 'isoformat'):
                        record[key] = value.isoformat()
                data.append(record)
            
            return jsonify({
                'data': data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            })
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/add_tags_column', methods=['POST'])
def add_tags_column(table_name):
    """Добавить колонку тегов в таблицу"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли колонка
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' in columns:
                return jsonify({'message': 'Колонка тегов уже существует'})
            
            # Добавляем колонку
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN tags TEXT")
            conn.commit()
            
            logger.info(f"Добавлена колонка тегов в таблицу {table_name}")
            return jsonify({'message': 'Колонка тегов успешно добавлена'})
            
    except Exception as e:
        logger.error(f"Ошибка добавления колонки: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/clear_tags', methods=['POST'])
def clear_tags(table_name):
    """Очистить все теги в таблице"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли колонка
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' not in columns:
                return jsonify({'error': 'Колонка тегов не найдена'}), 404
            
            # Очищаем теги
            cursor.execute(f"UPDATE {table_name} SET tags = NULL")
            conn.commit()
            
            logger.info(f"Очищены теги в таблице {table_name}")
            return jsonify({'message': 'Теги успешно очищены'})
            
    except Exception as e:
        logger.error(f"Ошибка очистки тегов: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/generate_tags', methods=['POST'])
def generate_tags(table_name):
    """Генерировать теги с помощью Llama"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        data = request.get_json()
        batch_size = data.get('batch_size', 10)
        start_id = data.get('start_id', 1)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли колонка
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' not in columns:
                return jsonify({'error': 'Колонка тегов не найдена'}), 404
            
            # Получаем общее количество записей для обработки
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE id >= ? AND (tags IS NULL OR tags = '')
            """, (start_id,))
            total_to_process = cursor.fetchone()[0]
            
            if total_to_process == 0:
                return jsonify({'message': 'Нет записей для обработки'})
            
            # Получаем записи для обработки
            cursor.execute(f"""
                SELECT id, mark, model, price, body_type, fuel_type, power, seats, manufacture_year 
                FROM {table_name} 
                WHERE id >= ? AND (tags IS NULL OR tags = '') 
                LIMIT ?
            """, (start_id, batch_size))
            
            records = cursor.fetchall()
            
            processed = 0
            errors = 0
            
            for record in records:
                try:
                    record_id, mark, model, price, body_type, fuel_type, power, seats, year = record
                    
                    # Формируем описание автомобиля для Llama с акцентом на теги
                    car_description = f"Автомобиль {mark} {model}"
                    if year:
                        car_description += f" {year} года"
                    if price:
                        car_description += f", цена {price:,.0f} руб"
                    if body_type:
                        car_description += f", {body_type}"
                    if fuel_type:
                        car_description += f", {fuel_type}"
                    if power:
                        car_description += f", {power} л.с."
                    if seats:
                        car_description += f", {seats} мест"
                    
                    # Добавляем контекст для определения тегов
                    car_description += ". Определи теги: бюджетный/премиум, семейный/спортивный, городской/внедорожный, экологичный, надежный, новый/подержанный"
                    
                    # Извлекаем теги с помощью Llama
                    entities = llama_entity_extractor.extract_entities_with_fallback(car_description)
                    
                    # Извлекаем только теги
                    tags = []
                    for tag in AVAILABLE_TAGS:
                        if entities.get(tag):
                            tags.append(tag)
                    
                    # Сохраняем теги в БД
                    tags_json = json.dumps(tags) if tags else None
                    cursor.execute(f"UPDATE {table_name} SET tags = ? WHERE id = ?", (tags_json, record_id))
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки записи {record[0]}: {e}")
                    errors += 1
            
            conn.commit()
            
            logger.info(f"Обработано {processed} записей, ошибок: {errors}")
            return jsonify({
                'message': f'Обработано {processed} записей',
                'processed': processed,
                'errors': errors,
                'total_to_process': total_to_process,
                'progress': min(100, (processed / total_to_process) * 100)
            })
            
    except Exception as e:
        logger.error(f"Ошибка генерации тегов: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>/stats')
def get_table_stats(table_name):
    """Получить статистику по тегам"""
    if table_name not in AVAILABLE_TABLES:
        return jsonify({'error': 'Таблица не найдена'}), 404
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли колонка
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Общее количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            
            # Записи с тегами (если колонка существует)
            tagged_records = 0
            tag_stats = {}
            
            if 'tags' in columns:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE tags IS NOT NULL AND tags != ''")
                tagged_records = cursor.fetchone()[0]
                
                # Статистика по каждому тегу
                for tag in AVAILABLE_TAGS:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE tags LIKE ?", (f'%{tag}%',))
                    tag_stats[tag] = cursor.fetchone()[0]
            
            return jsonify({
                'total_records': total_records,
                'tagged_records': tagged_records,
                'untagged_records': total_records - tagged_records,
                'tag_stats': tag_stats,
                'has_tags_column': 'tags' in columns
            })
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Создаем папку для шаблонов
    os.makedirs('templates', exist_ok=True)
    
    # Запускаем приложение
    app.run(host='0.0.0.0', port=3000, debug=True)
