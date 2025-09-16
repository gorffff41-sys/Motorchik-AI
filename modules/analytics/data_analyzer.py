import pandas as pd
import numpy as np
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

class DataAnalyzer:
    """
    Модуль для анализа данных автомобилей с визуализацией и статистикой.
    """
    
    def __init__(self, db_path: str = "instance/cars.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Настройки для визуализации
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Кэш для производительности
        self.cache = {}
        self.cache_ttl = 3600  # 1 час
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """Получает базовую статистику по автомобилям."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Статистика новых автомобилей
            new_cars_stats = pd.read_sql_query("""
                                SELECT
                    COUNT(*) as total_cars,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(manufacture_year) as avg_year,
                    MIN(manufacture_year) as min_year,
                    MAX(manufacture_year) as max_year,
                    COUNT(DISTINCT mark) as unique_brands,
                    COUNT(DISTINCT model) as unique_models
                FROM car
            """, conn)
            
            # Статистика подержанных автомобилей
            used_cars_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_cars,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(year) as avg_year,
                    MIN(year) as min_year,
                    MAX(year) as max_year,
                    COUNT(DISTINCT mark) as unique_brands,
                    COUNT(DISTINCT model) as unique_models
                FROM used_car
            """, conn)
            
            conn.close()
            
            return {
                'new_cars': new_cars_stats.to_dict('records')[0] if not new_cars_stats.empty else {},
                'used_cars': used_cars_stats.to_dict('records')[0] if not used_cars_stats.empty else {},
                'total_cars': (new_cars_stats['total_cars'].iloc[0] if not new_cars_stats.empty else 0) + 
                             (used_cars_stats['total_cars'].iloc[0] if not used_cars_stats.empty else 0)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении базовой статистики: {e}")
            return {}
    
    def get_price_analysis(self) -> Dict[str, Any]:
        """Анализ цен по категориям."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные о ценах
            new_cars = pd.read_sql_query("""
                                SELECT price, mark, model, manufacture_year
                FROM car
                WHERE price IS NOT NULL AND price > 0
            """, conn)
            
            used_cars = pd.read_sql_query("""
                SELECT price, mark, model, year
                FROM used_car 
                WHERE price IS NOT NULL AND price > 0
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_cars = pd.concat([new_cars, used_cars], ignore_index=True)
            
            if all_cars.empty:
                return {}
            
            # Анализ цен
            price_stats = {
                'total_cars': len(all_cars),
                'avg_price': float(all_cars['price'].mean()),
                'median_price': float(all_cars['price'].median()),
                'min_price': float(all_cars['price'].min()),
                'max_price': float(all_cars['price'].max()),
                'std_price': float(all_cars['price'].std())
            }
            
            # Ценовые категории
            price_categories = {
                'budget': len(all_cars[all_cars['price'] <= 500000]),
                'medium': len(all_cars[(all_cars['price'] > 500000) & (all_cars['price'] <= 1500000)]),
                'premium': len(all_cars[(all_cars['price'] > 1500000) & (all_cars['price'] <= 3000000)]),
                'luxury': len(all_cars[all_cars['price'] > 3000000])
            }
            
            # Топ-10 самых дорогих автомобилей
            top_expensive = all_cars.nlargest(10, 'price')[['mark', 'model', 'price', 'year']].to_dict('records')
            
            # Топ-10 самых дешевых автомобилей
            top_cheap = all_cars.nsmallest(10, 'price')[['mark', 'model', 'price', 'year']].to_dict('records')
            
            return {
                'price_statistics': price_stats,
                'price_categories': price_categories,
                'top_expensive': top_expensive,
                'top_cheap': top_cheap
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе цен: {e}")
            return {}
    
    def get_brand_analysis(self) -> Dict[str, Any]:
        """Анализ по маркам автомобилей."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Статистика по маркам (новые автомобили)
            new_brands = pd.read_sql_query("""
                SELECT mark, COUNT(*) as count, AVG(price) as avg_price
                FROM car 
                WHERE mark IS NOT NULL
                GROUP BY mark 
                ORDER BY count DESC
            """, conn)
            
            # Статистика по маркам (подержанные автомобили)
            used_brands = pd.read_sql_query("""
                SELECT mark, COUNT(*) as count, AVG(price) as avg_price
                FROM used_car 
                WHERE mark IS NOT NULL
                GROUP BY mark 
                ORDER BY count DESC
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_brands = pd.concat([
                new_brands.assign(type='new'),
                used_brands.assign(type='used')
            ], ignore_index=True)
            
            if all_brands.empty:
                return {}
            
            # Топ-10 марок по количеству
            top_brands = all_brands.groupby('mark').agg({
                'count': 'sum',
                'avg_price': 'mean'
            }).sort_values('count', ascending=False).head(10)
            
            # Топ-10 самых дорогих марок
            expensive_brands = all_brands.groupby('mark').agg({
                'count': 'sum',
                'avg_price': 'mean'
            }).sort_values('avg_price', ascending=False).head(10)
            
            # Распределение по типам (новые/подержанные)
            type_distribution = all_brands.groupby('type')['count'].sum().to_dict()
            
            return {
                'top_brands_by_count': top_brands.to_dict('index'),
                'top_brands_by_price': expensive_brands.to_dict('index'),
                'type_distribution': type_distribution,
                'total_brands': len(all_brands['mark'].unique())
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе марок: {e}")
            return {}
    
    def get_year_analysis(self) -> Dict[str, Any]:
        """Анализ по годам выпуска."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные о годах
            new_cars = pd.read_sql_query("""
                                SELECT manufacture_year, COUNT(*) as count, AVG(price) as avg_price
                FROM car
                WHERE manufacture_year IS NOT NULL
                GROUP BY manufacture_year
                ORDER BY manufacture_year
            """, conn)
            
            used_cars = pd.read_sql_query("""
                SELECT year, COUNT(*) as count, AVG(price) as avg_price
                FROM used_car 
                WHERE year IS NOT NULL
                GROUP BY year 
                ORDER BY year
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_years = pd.concat([new_cars, used_cars], ignore_index=True)
            
            if all_years.empty:
                return {}
            
            # Группируем по годам
            year_stats = all_years.groupby('year').agg({
                'count': 'sum',
                'avg_price': 'mean'
            }).reset_index()
            
            # Статистика по годам
            year_analysis = {
                'total_years': len(year_stats),
                'min_year': int(year_stats['year'].min()),
                'max_year': int(year_stats['year'].max()),
                'most_popular_year': int(year_stats.loc[year_stats['count'].idxmax(), 'year']),
                'most_expensive_year': int(year_stats.loc[year_stats['avg_price'].idxmax(), 'year'])
            }
            
            # Топ-5 лет по количеству автомобилей
            top_years_by_count = year_stats.nlargest(5, 'count')[['year', 'count', 'avg_price']].to_dict('records')
            
            # Топ-5 лет по средней цене
            top_years_by_price = year_stats.nlargest(5, 'avg_price')[['year', 'count', 'avg_price']].to_dict('records')
            
            return {
                'year_statistics': year_analysis,
                'top_years_by_count': top_years_by_count,
                'top_years_by_price': top_years_by_price,
                'year_distribution': year_stats.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе годов: {e}")
            return {}
    
    def get_city_analysis(self) -> Dict[str, Any]:
        """Анализ по городам."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Статистика по городам
            city_stats = pd.read_sql_query("""
                SELECT city, COUNT(*) as count, AVG(price) as avg_price
                FROM car 
                WHERE city IS NOT NULL AND city != ''
                GROUP BY city 
                ORDER BY count DESC
            """, conn)
            
            used_city_stats = pd.read_sql_query("""
                SELECT city, COUNT(*) as count, AVG(price) as avg_price
                FROM used_car 
                WHERE city IS NOT NULL AND city != ''
                GROUP BY city 
                ORDER BY count DESC
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_cities = pd.concat([city_stats, used_city_stats], ignore_index=True)
            
            if all_cities.empty:
                return {}
            
            # Группируем по городам
            city_analysis = all_cities.groupby('city').agg({
                'count': 'sum',
                'avg_price': 'mean'
            }).sort_values('count', ascending=False)
            
            # Топ-10 городов по количеству автомобилей
            top_cities = city_analysis.head(10).to_dict('index')
            
            # Топ-10 самых дорогих городов
            expensive_cities = city_analysis.sort_values('avg_price', ascending=False).head(10).to_dict('index')
            
            return {
                'top_cities_by_count': top_cities,
                'top_cities_by_price': expensive_cities,
                'total_cities': len(city_analysis),
                'city_statistics': {
                    'total_cars': int(city_analysis['count'].sum()),
                    'avg_price_overall': float(city_analysis['avg_price'].mean())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе городов: {e}")
            return {}
    
    def create_price_distribution_chart(self) -> str:
        """Создает график распределения цен."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные о ценах
            new_cars = pd.read_sql_query("SELECT price FROM car WHERE price > 0", conn)
            used_cars = pd.read_sql_query("SELECT price FROM used_car WHERE price > 0", conn)
            
            conn.close()
            
            # Объединяем данные
            all_prices = pd.concat([new_cars, used_cars], ignore_index=True)
            
            if all_prices.empty:
                return "Нет данных для создания графика"
            
            # Создаем график
            plt.figure(figsize=(12, 6))
            
            # Гистограмма распределения цен
            plt.subplot(1, 2, 1)
            plt.hist(all_prices['price'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Распределение цен автомобилей')
            plt.xlabel('Цена (руб)')
            plt.ylabel('Количество')
            plt.yscale('log')  # Логарифмическая шкала для лучшей видимости
            
            # Box plot
            plt.subplot(1, 2, 2)
            plt.boxplot(all_prices['price'])
            plt.title('Box Plot цен')
            plt.ylabel('Цена (руб)')
            
            plt.tight_layout()
            
            # Сохраняем график
            chart_path = 'static/price_distribution.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании графика цен: {e}")
            return ""
    
    def create_brand_popularity_chart(self) -> str:
        """Создает график популярности марок."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные о марках
            new_brands = pd.read_sql_query("""
                SELECT mark, COUNT(*) as count
                FROM car 
                WHERE mark IS NOT NULL
                GROUP BY mark 
                ORDER BY count DESC
            """, conn)
            
            used_brands = pd.read_sql_query("""
                SELECT mark, COUNT(*) as count
                FROM used_car 
                WHERE mark IS NOT NULL
                GROUP BY mark 
                ORDER BY count DESC
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_brands = pd.concat([new_brands, used_brands], ignore_index=True)
            
            if all_brands.empty:
                return "Нет данных для создания графика"
            
            # Группируем по маркам
            brand_stats = all_brands.groupby('mark')['count'].sum().sort_values(ascending=False).head(15)
            
            # Создаем график
            plt.figure(figsize=(14, 8))
            
            # Столбчатая диаграмма
            bars = plt.bar(range(len(brand_stats)), brand_stats.values, color='lightcoral')
            plt.title('Топ-15 марок по популярности', fontsize=16)
            plt.xlabel('Марка', fontsize=12)
            plt.ylabel('Количество автомобилей', fontsize=12)
            plt.xticks(range(len(brand_stats)), brand_stats.index, rotation=45, ha='right')
            
            # Добавляем значения на столбцы
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Сохраняем график
            chart_path = 'static/brand_popularity.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании графика марок: {e}")
            return ""
    
    def create_interactive_price_chart(self) -> str:
        """Создает интерактивный график цен с Plotly."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные
            new_cars = pd.read_sql_query("""
                                SELECT mark, model, price, manufacture_year, city
                FROM car
                WHERE price > 0 AND mark IS NOT NULL
            """, conn)
            
            used_cars = pd.read_sql_query("""
                SELECT mark, model, price, year, city
                FROM used_car 
                WHERE price > 0 AND mark IS NOT NULL
            """, conn)
            
            conn.close()
            
            # Объединяем данные
            all_cars = pd.concat([new_cars, used_cars], ignore_index=True)
            
            if all_cars.empty:
                return ""
            
            # Создаем интерактивный график
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Распределение цен', 'Цены по маркам', 'Цены по годам', 'Цены по городам'),
                specs=[[{"type": "histogram"}, {"type": "box"}],
                       [{"type": "scatter"}, {"type": "box"}]]
            )
            
            # Гистограмма цен
            fig.add_trace(
                go.Histogram(x=all_cars['price'], name='Распределение цен', nbinsx=50),
                row=1, col=1
            )
            
            # Box plot по маркам (топ-10)
            top_brands = all_cars.groupby('mark')['price'].mean().sort_values(ascending=False).head(10).index
            for brand in top_brands:
                brand_data = all_cars[all_cars['mark'] == brand]['price']
                fig.add_trace(
                    go.Box(y=brand_data, name=brand),
                    row=1, col=2
                )
            
            # Scatter plot: год vs цена
            fig.add_trace(
                go.Scatter(x=all_cars['year'], y=all_cars['price'], 
                          mode='markers', name='Год vs Цена'),
                row=2, col=1
            )
            
            # Box plot по городам (топ-10)
            top_cities = all_cars.groupby('city')['price'].mean().sort_values(ascending=False).head(10).index
            for city in top_cities:
                city_data = all_cars[all_cars['city'] == city]['price']
                fig.add_trace(
                    go.Box(y=city_data, name=city),
                    row=2, col=2
                )
            
            # Обновляем layout
            fig.update_layout(
                title_text="Интерактивный анализ цен автомобилей",
                showlegend=False,
                height=800
            )
            
            # Сохраняем как HTML
            chart_path = 'static/interactive_price_analysis.html'
            fig.write_html(chart_path)
            
            return chart_path
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании интерактивного графика: {e}")
            return ""
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Получает комплексный отчет по всем данным."""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'basic_statistics': self.get_basic_statistics(),
                'price_analysis': self.get_price_analysis(),
                'brand_analysis': self.get_brand_analysis(),
                'year_analysis': self.get_year_analysis(),
                'city_analysis': self.get_city_analysis(),
                'charts': {
                    'price_distribution': self.create_price_distribution_chart(),
                    'brand_popularity': self.create_brand_popularity_chart(),
                    'interactive_analysis': self.create_interactive_price_chart()
                }
            }
            
            # Сохраняем отчет
            report_path = f'reports/comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            os.makedirs('reports', exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании комплексного отчета: {e}")
            return {}
    
    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Анализ трендов за последние дни."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Получаем данные за последние дни
            start_date = datetime.now() - timedelta(days=days)
            
            # Анализ по дням (если есть временные метки)
            daily_stats = pd.read_sql_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as new_cars,
                    AVG(price) as avg_price
                FROM car 
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn, params=(start_date,))
            
            conn.close()
            
            if daily_stats.empty:
                return {}
            
            # Анализ трендов
            trend_analysis = {
                'total_days': len(daily_stats),
                'total_new_cars': int(daily_stats['new_cars'].sum()),
                'avg_daily_cars': float(daily_stats['new_cars'].mean()),
                'price_trend': 'increasing' if daily_stats['avg_price'].iloc[-1] > daily_stats['avg_price'].iloc[0] else 'decreasing',
                'growth_rate': float((daily_stats['new_cars'].iloc[-1] - daily_stats['new_cars'].iloc[0]) / daily_stats['new_cars'].iloc[0] * 100) if daily_stats['new_cars'].iloc[0] > 0 else 0
            }
            
            return {
                'trend_analysis': trend_analysis,
                'daily_data': daily_stats.to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе трендов: {e}")
            return {} 
 
 