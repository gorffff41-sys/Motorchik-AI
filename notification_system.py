import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from database import get_db
from user_analytics import UserAnalytics
from recommendation_engine import RecommendationEngine
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Система уведомлений и алертов для автоассистента"""
    
    def __init__(self):
        self.user_analytics = UserAnalytics()
        self.recommendation_engine = RecommendationEngine()
        self.init_notification_tables()
    
    def init_notification_tables(self):
        """Инициализирует таблицы для уведомлений"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Таблица уведомлений
            cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,  -- 'system', 'recommendation', 'alert', 'promotion'
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority INTEGER DEFAULT 1,  -- 1-5, где 5 - высший приоритет
                is_read BOOLEAN DEFAULT FALSE,
                action_url TEXT,
                action_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                metadata TEXT  -- JSON с дополнительными данными
            )''')
            
            # Таблица алертов системы
            cursor.execute('''CREATE TABLE IF NOT EXISTS system_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,  -- 'performance', 'quality', 'security', 'maintenance'
                severity TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT  -- JSON с дополнительными данными
            )''')
            
            # Таблица настроек уведомлений пользователей
            cursor.execute('''CREATE TABLE IF NOT EXISTS notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                email_notifications BOOLEAN DEFAULT TRUE,
                push_notifications BOOLEAN DEFAULT TRUE,
                recommendation_notifications BOOLEAN DEFAULT TRUE,
                system_alerts BOOLEAN DEFAULT TRUE,
                promotion_notifications BOOLEAN DEFAULT TRUE,
                notification_frequency TEXT DEFAULT 'daily',  -- 'immediate', 'hourly', 'daily', 'weekly'
                quiet_hours_start TEXT DEFAULT '22:00',
                quiet_hours_end TEXT DEFAULT '08:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )''')
            
            # Таблица отправленных уведомлений
            cursor.execute('''CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                delivery_method TEXT NOT NULL,  -- 'email', 'push', 'in_app'
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_status TEXT DEFAULT 'sent',  -- 'sent', 'delivered', 'failed', 'opened'
                error_message TEXT,
                FOREIGN KEY (notification_id) REFERENCES notifications (id)
            )''')
            
            conn.commit()
    
    def create_notification(self, user_id: str, notification_type: str, title: str, 
                           message: str, priority: int = 1, action_url: Optional[str] = None,
                           action_text: Optional[str] = None, expires_at: Optional[datetime] = None,
                           metadata: Optional[Dict] = None) -> Optional[int]:
        """Создает новое уведомление"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notifications 
                    (user_id, notification_type, title, message, priority, 
                     action_url, action_text, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, notification_type, title, message, priority,
                    action_url, action_text, expires_at,
                    json.dumps(metadata) if metadata else None
                ))
                notification_id = cursor.lastrowid
                conn.commit()
                
                # Проверяем настройки пользователя и отправляем уведомление
                if notification_id:
                    self.process_notification(notification_id)
                
                return notification_id
                
        except Exception as e:
            logger.error(f"Ошибка создания уведомления: {e}")
            return None
    
    def get_user_notifications(self, user_id: str, limit: int = 20, 
                              unread_only: bool = False) -> List[Dict]:
        """Получает уведомления пользователя"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, notification_type, title, message, priority,
                           is_read, action_url, action_text, created_at, expires_at, metadata
                    FROM notifications
                    WHERE user_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """
                params = [user_id]
                
                if unread_only:
                    query += " AND is_read = FALSE"
                
                query += " ORDER BY priority DESC, created_at DESC"
                params.append(str(limit))
                
                cursor.execute(query, params)
                notifications = []
                
                for row in cursor.fetchall():
                    notifications.append({
                        'id': row[0],
                        'type': row[1],
                        'title': row[2],
                        'message': row[3],
                        'priority': row[4],
                        'is_read': bool(row[5]),
                        'action_url': row[6],
                        'action_text': row[7],
                        'created_at': row[8],
                        'expires_at': row[9],
                        'metadata': json.loads(row[10]) if row[10] else {}
                    })
                
                return notifications
                
        except Exception as e:
            logger.error(f"Ошибка получения уведомлений: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int, user_id: str) -> bool:
        """Отмечает уведомление как прочитанное"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE notifications 
                    SET is_read = TRUE 
                    WHERE id = ? AND user_id = ?
                """, (notification_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка отметки уведомления как прочитанного: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: str) -> bool:
        """Отмечает все уведомления пользователя как прочитанные"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE notifications 
                    SET is_read = TRUE 
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка отметки всех уведомлений: {e}")
            return False
    
    def delete_notification(self, notification_id: int, user_id: str) -> bool:
        """Удаляет уведомление"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM notifications 
                    WHERE id = ? AND user_id = ?
                """, (notification_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка удаления уведомления: {e}")
            return False
    
    def get_notification_count(self, user_id: str, unread_only: bool = True) -> int:
        """Получает количество уведомлений"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT COUNT(*) FROM notifications
                    WHERE user_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """
                params = [user_id]
                
                if unread_only:
                    query += " AND is_read = FALSE"
                
                cursor.execute(query, params)
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Ошибка подсчета уведомлений: {e}")
            return 0
    
    def create_system_alert(self, alert_type: str, severity: str, title: str,
                           description: str, metadata: Optional[Dict] = None) -> Optional[int]:
        """Создает системный алерт"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_alerts 
                    (alert_type, severity, title, description, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    alert_type, severity, title, description,
                    json.dumps(metadata) if metadata else None
                ))
                alert_id = cursor.lastrowid
                conn.commit()
                
                # Отправляем уведомления администраторам
                if alert_id:
                    self.notify_admins_about_alert(alert_id)
                
                return alert_id
                
        except Exception as e:
            logger.error(f"Ошибка создания системного алерта: {e}")
            return None
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """Получает активные системные алерты"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, alert_type, severity, title, description, created_at, metadata
                    FROM system_alerts
                    WHERE is_resolved = FALSE
                """
                params = []
                
                if severity:
                    query += " AND severity = ?"
                    params.append(severity)
                
                query += " ORDER BY severity DESC, created_at DESC"
                
                cursor.execute(query, params)
                alerts = []
                
                for row in cursor.fetchall():
                    alerts.append({
                        'id': row[0],
                        'type': row[1],
                        'severity': row[2],
                        'title': row[3],
                        'description': row[4],
                        'created_at': row[5],
                        'metadata': json.loads(row[6]) if row[6] else {}
                    })
                
                return alerts
                
        except Exception as e:
            logger.error(f"Ошибка получения алертов: {e}")
            return []
    
    def resolve_alert(self, alert_id: int, resolved_by: Optional[str] = None) -> bool:
        """Разрешает системный алерт"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE system_alerts 
                    SET is_resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                    WHERE id = ?
                """, (resolved_by or "system", alert_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка разрешения алерта: {e}")
            return False
    
    def process_notification(self, notification_id: int):
        """Обрабатывает уведомление и отправляет его пользователю"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT n.*, ns.email_notifications, ns.push_notifications, ns.notification_frequency
                    FROM notifications n
                    LEFT JOIN notification_settings ns ON n.user_id = ns.user_id
                    WHERE n.id = ?
                """, (notification_id,))
                
                row = cursor.fetchone()
                if not row:
                    return
                
                user_id = row[1]
                notification_type = row[2]
                title = row[3]
                message = row[4]
                priority = row[5]
                email_enabled = row[12] if row[12] is not None else True
                push_enabled = row[13] if row[13] is not None else True
                
                # Отправляем email уведомление
                if email_enabled and priority >= 3:
                    self.send_email_notification(user_id, title, message, notification_id)
                
                # Отправляем push уведомление
                if push_enabled:
                    self.send_push_notification(user_id, title, message, notification_id)
                
        except Exception as e:
            logger.error(f"Ошибка обработки уведомления: {e}")
    
    def send_email_notification(self, user_id: str, title: str, message: str, notification_id: int):
        """Отправляет email уведомление"""
        try:
            # Здесь должна быть логика отправки email
            # Для демонстрации просто логируем
            logger.info(f"Email уведомление для {user_id}: {title} - {message}")
            
            # Логируем отправку
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sent_notifications 
                    (notification_id, user_id, delivery_method, delivery_status)
                    VALUES (?, ?, 'email', 'sent')
                """, (notification_id, user_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
    
    def send_push_notification(self, user_id: str, title: str, message: str, notification_id: int):
        """Отправляет push уведомление"""
        try:
            # Здесь должна быть логика отправки push уведомлений
            # Для демонстрации просто логируем
            logger.info(f"Push уведомление для {user_id}: {title} - {message}")
            
            # Логируем отправку
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sent_notifications 
                    (notification_id, user_id, delivery_method, delivery_status)
                    VALUES (?, ?, 'push', 'sent')
                """, (notification_id, user_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Ошибка отправки push уведомления: {e}")
    
    def notify_admins_about_alert(self, alert_id: int):
        """Уведомляет администраторов о системном алерте"""
        try:
            # Получаем информацию об алерте
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT alert_type, severity, title, description
                    FROM system_alerts WHERE id = ?
                """, (alert_id,))
                
                row = cursor.fetchone()
                if not row:
                    return
                
                alert_type, severity, title, description = row
                
                # Создаем уведомления для всех администраторов
                # В реальной системе здесь был бы список админов
                admin_users = ['admin', 'system']  # Пример
                
                for admin_id in admin_users:
                    self.create_notification(
                        user_id=admin_id,
                        notification_type='system_alert',
                        title=f"Системный алерт: {title}",
                        message=f"Тип: {alert_type}\nСерьезность: {severity}\nОписание: {description}",
                        priority=5 if severity in ['high', 'critical'] else 3
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка уведомления админов: {e}")
    
    def create_recommendation_notification(self, user_id: str, car_data: Dict):
        """Создает уведомление о новой рекомендации"""
        try:
            title = f"Новая рекомендация: {car_data['brand']} {car_data['model']}"
            message = f"Мы подобрали для вас {car_data['brand']} {car_data['model']} {car_data['year']} года за {car_data['price']:,} ₽"
            
            return self.create_notification(
                user_id=user_id,
                notification_type='recommendation',
                title=title,
                message=message,
                priority=2,
                action_url=f"/car/{car_data['id']}",
                action_text="Посмотреть автомобиль",
                metadata={'car_id': car_data['id'], 'recommendation_score': car_data.get('score', 0)}
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания уведомления о рекомендации: {e}")
            return None
    
    def create_promotion_notification(self, user_id: str, promotion_data: Dict):
        """Создает уведомление о промо-акции"""
        try:
            title = f"Специальное предложение: {promotion_data['title']}"
            message = promotion_data['description']
            
            return self.create_notification(
                user_id=user_id,
                notification_type='promotion',
                title=title,
                message=message,
                priority=2,
                action_url=promotion_data.get('url'),
                action_text="Подробнее",
                expires_at=datetime.now() + timedelta(days=promotion_data.get('duration_days', 7)),
                metadata=promotion_data
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания промо-уведомления: {e}")
            return None
    
    def check_and_create_alerts(self):
        """Проверяет систему и создает алерты при необходимости"""
        try:
            # Проверяем качество Llama-ответов
            self.check_llama_quality_alerts()
            
            # Проверяем производительность системы
            self.check_performance_alerts()
            
            # Проверяем активность пользователей
            self.check_user_activity_alerts()
            
        except Exception as e:
            logger.error(f"Ошибка проверки алертов: {e}")
    
    def check_llama_quality_alerts(self):
        """Проверяет качество Llama-ответов и создает алерты"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Проверяем средний балл за последние 7 дней
                cursor.execute("""
                    SELECT AVG(quality_score), COUNT(*)
                    FROM llama_feedback
                    WHERE created_at >= datetime('now', '-7 days')
                """)
                
                avg_score, count = cursor.fetchone()
                
                if avg_score and count > 10:
                    if avg_score < 3.0:
                        self.create_system_alert(
                            alert_type='quality',
                            severity='high',
                            title='Низкое качество Llama-ответов',
                            description=f'Средний балл за 7 дней: {avg_score:.2f} из 5.0'
                        )
                    elif avg_score < 3.5:
                        self.create_system_alert(
                            alert_type='quality',
                            severity='medium',
                            title='Снижение качества Llama-ответов',
                            description=f'Средний балл за 7 дней: {avg_score:.2f} из 5.0'
                        )
                        
        except Exception as e:
            logger.error(f"Ошибка проверки качества Llama: {e}")
    
    def check_performance_alerts(self):
        """Проверяет производительность системы"""
        try:
            # Здесь можно добавить проверки CPU, памяти, времени ответа
            # Для демонстрации создаем фиктивный алерт
            pass
            
        except Exception as e:
            logger.error(f"Ошибка проверки производительности: {e}")
    
    def check_user_activity_alerts(self):
        """Проверяет активность пользователей"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Проверяем количество активных пользователей за последние 24 часа
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id)
                    FROM chat_history
                    WHERE timestamp >= datetime('now', '-24 hours')
                """)
                
                active_users = cursor.fetchone()[0]
                
                if active_users < 5:
                    self.create_system_alert(
                        alert_type='activity',
                        severity='medium',
                        title='Низкая активность пользователей',
                        description=f'Активных пользователей за 24 часа: {active_users}'
                    )
                    
        except Exception as e:
            logger.error(f"Ошибка проверки активности: {e}")
    
    def get_notification_statistics(self, days: int = 30) -> Dict:
        """Получает статистику уведомлений"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute("""
                    SELECT COUNT(*), COUNT(CASE WHEN is_read = TRUE THEN 1 END)
                    FROM notifications
                    WHERE created_at >= datetime('now', '-{} days')
                """.format(days))
                
                total, read = cursor.fetchone()
                
                # Статистика по типам
                cursor.execute("""
                    SELECT notification_type, COUNT(*)
                    FROM notifications
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY notification_type
                """.format(days))
                
                type_stats = dict(cursor.fetchall())
                
                # Статистика доставки
                cursor.execute("""
                    SELECT delivery_method, delivery_status, COUNT(*)
                    FROM sent_notifications
                    WHERE sent_at >= datetime('now', '-{} days')
                    GROUP BY delivery_method, delivery_status
                """.format(days))
                
                delivery_stats = {}
                for method, status, count in cursor.fetchall():
                    if method not in delivery_stats:
                        delivery_stats[method] = {}
                    delivery_stats[method][status] = count
                
                return {
                    'total_notifications': total,
                    'read_notifications': read,
                    'unread_notifications': total - read,
                    'read_rate': round(read / total * 100, 1) if total > 0 else 0,
                    'type_distribution': type_stats,
                    'delivery_statistics': delivery_stats
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики уведомлений: {e}")
            return {} 