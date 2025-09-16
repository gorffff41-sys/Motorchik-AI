import logging
import time
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from functools import wraps


class SystemMonitor:
    """Мониторинг системы и производительности"""
    
    def __init__(self, db_path: str = "instance/cars.db"):
        self.db_path = db_path
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AutoAssistant')
        
    def get_system_stats(self) -> Dict:
        """Получение статистики системы"""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': self.get_network_stats(),
                'process_count': len(psutil.pids())
            }
            return stats
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики системы: {e}")
            return {}
    
    def get_network_stats(self) -> Dict:
        """Получение статистики сети"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики сети: {e}")
            return {}
    
    def get_database_stats(self) -> Dict:
        """Получение статистики базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Размер базы данных
                db_size = os.path.getsize(self.db_path)
                
                # Количество записей в таблицах
                tables = ['car', 'dealer_centers', 'user_profiles', 'chat_history']
                table_counts = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_counts[table] = count
                    except sqlite3.OperationalError:
                        table_counts[table] = 0
                
                # Статистика по запросам
                cursor.execute("""
                    SELECT COUNT(*) as total_queries,
                           COUNT(DISTINCT user_id) as unique_users,
                           COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM chat_history
                """)
                query_stats = cursor.fetchone()
                
                return {
                    'db_size_mb': round(db_size / (1024 * 1024), 2),
                    'table_counts': table_counts,
                    'total_queries': query_stats[0] if query_stats[0] else 0,
                    'unique_users': query_stats[1] if query_stats[1] else 0,
                    'active_days': query_stats[2] if query_stats[2] else 0
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики БД: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict:
        """Получение метрик производительности"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Среднее время ответа (если есть поле response_time)
                try:
                    cursor.execute("""
                        SELECT AVG(response_time) as avg_response_time,
                               MAX(response_time) as max_response_time,
                               MIN(response_time) as min_response_time
                        FROM chat_history
                        WHERE response_time IS NOT NULL
                    """)
                    response_times = cursor.fetchone()
                except sqlite3.OperationalError:
                    response_times = (0, 0, 0)
                
                # Популярные интенты
                cursor.execute("""
                    SELECT intent, COUNT(*) as count
                    FROM chat_history
                    WHERE intent IS NOT NULL AND intent != ''
                    GROUP BY intent
                    ORDER BY count DESC
            
                """)
                popular_intents = cursor.fetchall()
                
                return {
                    'avg_response_time_ms': round(response_times[0] or 0, 2),
                    'max_response_time_ms': response_times[1] or 0,
                    'min_response_time_ms': response_times[2] or 0,
                    'popular_intents': [{'intent': intent, 'count': count} for intent, count in popular_intents]
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения метрик производительности: {e}")
            return {}
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, 
                       response_time: float, user_id: Optional[str] = None):
        """Логирование API запросов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создаем таблицу для логов API если её нет
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        endpoint TEXT,
                        method TEXT,
                        status_code INTEGER,
                        response_time REAL,
                        user_id TEXT,
                        ip_address TEXT
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO api_logs (endpoint, method, status_code, response_time, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (endpoint, method, status_code, response_time, user_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Ошибка логирования API запроса: {e}")
    
    def get_api_logs(self, hours: int = 24) -> List[Dict]:
        """Получение логов API за последние часы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT endpoint, method, status_code, response_time, user_id, timestamp
                    FROM api_logs
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                logs = cursor.fetchall()
                return [
                    {
                        'endpoint': log[0],
                        'method': log[1],
                        'status_code': log[2],
                        'response_time': log[3],
                        'user_id': log[4],
                        'timestamp': log[5]
                    }
                    for log in logs
                ]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения логов API: {e}")
            return []
    
    def get_error_logs(self, hours: int = 24) -> List[Dict]:
        """Получение логов ошибок"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT endpoint, method, status_code, response_time, user_id, timestamp
                    FROM api_logs
                    WHERE status_code >= 400 
                    AND timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                errors = cursor.fetchall()
                return [
                    {
                        'endpoint': error[0],
                        'method': error[1],
                        'status_code': error[2],
                        'response_time': error[3],
                        'user_id': error[4],
                        'timestamp': error[5]
                    }
                    for error in errors
                ]
                
        except Exception as e:
            self.logger.error(f"Ошибка получения логов ошибок: {e}")
            return []
    
    def cleanup_old_logs(self, days: int = 30):
        """Очистка старых логов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM api_logs
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Удалено {deleted_count} старых записей логов")
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых логов: {e}")
    
    def generate_report(self) -> Dict:
        """Генерация полного отчета"""
        return {
            'system_stats': self.get_system_stats(),
            'database_stats': self.get_database_stats(),
            'performance_metrics': self.get_performance_metrics(),
            'recent_errors': self.get_error_logs(1),  # Ошибки за последний час
            'api_activity': {
                'total_requests_24h': len(self.get_api_logs(24)),
                'error_rate_24h': len(self.get_error_logs(24)),
                'avg_response_time_24h': self.calculate_avg_response_time(24)
            }
        }
    
    def calculate_avg_response_time(self, hours: int) -> float:
        """Расчет среднего времени ответа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT AVG(response_time)
                    FROM api_logs
                    WHERE timestamp >= datetime('now', '-{} hours')
                    AND response_time IS NOT NULL
                """.format(hours))
                
                result = cursor.fetchone()
                return round(result[0] or 0, 2)
                
        except Exception as e:
            self.logger.error(f"Ошибка расчета среднего времени ответа: {e}")
            return 0.0

    def log_llama_feedback(self, user_id: str, query: str, llama_response: str, quality_score: int, comment: str = ""):
        """Логирование обратной связи по Llama-ответу"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO llama_feedback (user_id, query, llama_response, quality_score, comment)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, query, llama_response, quality_score, comment))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Ошибка логирования llama_feedback: {e}")

    def get_llama_feedback_daily_trend(self, days: int = 14):
        """Динамика среднего балла Llama-ответов по дням"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT DATE(created_at) as day, AVG(quality_score) as avg_score, COUNT(*) as count
                    FROM llama_feedback
                    WHERE created_at >= datetime('now', '-{days} days')
                    GROUP BY day
                    ORDER BY day ASC
                """)
                return [
                    {"day": row[0], "avg_score": round(row[1] or 0, 2), "count": row[2]} for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Ошибка получения тренда llama_feedback: {e}")
            return []

    def get_llama_feedback_comments(self, limit: int = 10, period: int = 14, min_score: int = 1):
        """Последние комментарии пользователей к Llama-ответам за период и с минимальной оценкой"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT user_id, query, llama_response, quality_score, comment, created_at
                    FROM llama_feedback
                    WHERE created_at >= datetime('now', '-{period} days')
                      AND quality_score >= ?
                      AND comment IS NOT NULL AND comment != ''
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (min_score, limit))
                return [
                    {
                        "user_id": row[0],
                        "query": row[1],
                        "llama_response": row[2],
                        "quality_score": row[3],
                        "comment": row[4],
                        "created_at": row[5]
                    } for row in cursor.fetchall()
                ]
        except Exception as e:
            self.logger.error(f"Ошибка получения комментариев llama_feedback: {e}")
            return []

    def check_llama_quality_alerts(self, days: int = 7, min_avg: float = 3.5, max_bad: int = 3):
        """Проверяет качество Llama-ответов и возвращает алерты"""
        alerts = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Средний балл за период
                cursor.execute(f"""
                    SELECT AVG(quality_score), COUNT(*)
                    FROM llama_feedback
                    WHERE created_at >= datetime('now', '-{days} days')
                """)
                avg_score, count = cursor.fetchone()
                if avg_score is not None and count > 10:
                    if avg_score < 3.0:
                        alerts.append({
                            "type": "quality",
                            "severity": "high",
                            "title": "Низкое качество Llama-ответов",
                            "description": f"Средний балл за {days} дней: {avg_score:.2f} из 5.0"
                        })
                    elif avg_score < min_avg:
                        alerts.append({
                            "type": "quality",
                            "severity": "medium",
                            "title": "Снижение качества Llama-ответов",
                            "description": f"Средний балл за {days} дней: {avg_score:.2f} из 5.0"
                        })
                # Количество плохих оценок
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM llama_feedback
                    WHERE created_at >= datetime('now', '-{days} days')
                      AND quality_score <= 2
                """)
                bad_count = cursor.fetchone()[0]
                if bad_count >= max_bad:
                    alerts.append({
                        "type": "quality",
                        "severity": "high",
                        "title": "Много низких оценок Llama-ответов",
                        "description": f"Количество оценок <=2 за {days} дней: {bad_count}"
                    })
            return alerts
        except Exception as e:
            self.logger.error(f"Ошибка проверки качества Llama: {e}")
            return alerts


def monitor_performance(func):
    """Декоратор для мониторинга производительности функций"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000  # в миллисекундах
            return result
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            raise e
        finally:
            # Логируем время выполнения
            logging.getLogger('AutoAssistant').info(
                f"Функция {func.__name__} выполнена за {response_time:.2f}ms"
            )
    return wrapper


def log_api_call(endpoint: str, user_id: Optional[str] = None):
    """Декоратор для логирования API вызовов"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000
                
                # Логируем успешный запрос
                monitor = SystemMonitor()
                monitor.log_api_request(
                    endpoint=endpoint,
                    method="GET" if "get" in func.__name__.lower() else "POST",
                    status_code=200,
                    response_time=response_time,
                    user_id=user_id
                )
                
                return result
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                
                # Логируем ошибку
                monitor = SystemMonitor()
                monitor.log_api_request(
                    endpoint=endpoint,
                    method="GET" if "get" in func.__name__.lower() else "POST",
                    status_code=500,
                    response_time=response_time,
                    user_id=user_id
                )
                
                raise e
        return wrapper
    return decorator


# Создаем директорию для логов если её нет
os.makedirs('logs', exist_ok=True)

# Глобальный экземпляр монитора
system_monitor = SystemMonitor() 