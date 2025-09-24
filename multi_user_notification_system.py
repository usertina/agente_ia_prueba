import sqlite3, hashlib, uuid, json, time, threading
from datetime import datetime, timedelta
from contextlib import contextmanager

from sources.papers import check_papers
from sources.patents import check_patents
from sources.ayudas import check_ayudas
from sources.emails import check_emails

class MultiUserNotificationSystem:
    def __init__(self):
        self.db_file = "notifications.db"
        self.init_database()
        self.running = False
        self.monitor_thread = None
        self.monitor_interval = 60  # segundos entre comprobaciones automáticas

    # ----------------------------
    # Base de datos
    # ----------------------------
    def init_database(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        device_id TEXT,
                        device_name TEXT,
                        config TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        notification_type TEXT,
                        title TEXT,
                        message TEXT,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        delivered BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );

                    CREATE TABLE IF NOT EXISTS user_state (
                        user_id TEXT PRIMARY KEY,
                        last_email_check TIMESTAMP,
                        last_patent_check TIMESTAMP,
                        last_papers_check TIMESTAMP,
                        last_ayudas_check TIMESTAMP,
                        email_count INTEGER DEFAULT 0,
                        patent_count INTEGER DEFAULT 0,
                        papers_count INTEGER DEFAULT 0,
                        ayudas_count INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
                ''')
                print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")

    @contextmanager
    def get_db_connection(self):
        conn = sqlite3.connect(self.db_file, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ----------------------------
    # Usuarios
    # ----------------------------
    def generate_user_id(self, ip_address: str, user_agent: str) -> str:
        salt = "gemini_agent_2024"
        unique_string = f"{salt}_{ip_address}_{user_agent}"
        return "user_" + hashlib.md5(unique_string.encode()).hexdigest()[:12]

    def register_user(self, ip_address: str, user_agent: str, device_info: dict = None):
        user_id = self.generate_user_id(ip_address, user_agent)
        session_id = str(uuid.uuid4())
        device_id = device_info.get("device_id", str(uuid.uuid4())[:8]) if device_info else str(uuid.uuid4())[:8]
        device_name = device_info.get("device_name", "Dispositivo Desconocido") if device_info else "Dispositivo Desconocido"

        default_config = {
            "email_notifications": False,
            "patent_notifications": False,
            "papers_notifications": False,
            "ayudas_notifications": False,
            "patent_keywords": [],
            "papers_keywords": [],
            "papers_categories": ["cs.AI", "cs.LG", "cs.CV"],
            "email_check_interval": 300,
            "patent_check_interval": 3600,
            "papers_check_interval": 1800,
            "ayudas_check_interval": 86400,
            "device_name": device_name,
            "max_papers_per_check": 5,
            "max_patents_per_check": 3,
            "region": "Euskadi"
        }

        with self.get_db_connection() as conn:
            existing = conn.execute("SELECT config FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE users SET session_id=?, device_id=?, device_name=?, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
                    (session_id, device_id, device_name, user_id)
                )
                config = json.loads(existing["config"])
            else:
                conn.execute(
                    "INSERT INTO users (user_id, session_id, device_id, device_name, config) VALUES (?, ?, ?, ?, ?)",
                    (user_id, session_id, device_id, device_name, json.dumps(default_config))
                )
                conn.execute("INSERT INTO user_state (user_id) VALUES (?)", (user_id,))
                config = default_config
            conn.commit()

        return user_id, session_id, config

    def update_user_config(self, user_id: str, config: dict) -> bool:
        try:
            with self.get_db_connection() as conn:
                current = conn.execute("SELECT config FROM users WHERE user_id=?", (user_id,)).fetchone()
                if not current:
                    return False
                current_config = json.loads(current["config"])
                current_config.update(config)
                conn.execute("UPDATE users SET config=?, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
                             (json.dumps(current_config), user_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error updating user config: {e}")
            return False

    def get_user_config(self, user_id: str) -> dict:
        try:
            with self.get_db_connection() as conn:
                result = conn.execute("SELECT config FROM users WHERE user_id=?", (user_id,)).fetchone()
                return json.loads(result["config"]) if result else {}
        except Exception as e:
            print(f"❌ Error getting user config: {e}")
            return {}

    # ----------------------------
    # Notificaciones
    # ----------------------------
    def save_notification(self, user_id: str, notif: dict):
        try:
            with self.get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO notifications (user_id, notification_type, title, message, data) VALUES (?, ?, ?, ?, ?)",
                    (user_id, notif["type"], notif["title"], notif["message"], json.dumps(notif["data"]))
                )
                conn.commit()
        except Exception as e:
            print(f"❌ Error saving notification: {e}")

    def get_pending_notifications(self, user_id: str) -> list:
        """Obtener notificaciones pendientes para un usuario"""
        try:
            with self.get_db_connection() as conn:
                notifications = conn.execute("""
                    SELECT id, notification_type, title, message, data, created_at 
                    FROM notifications 
                    WHERE user_id = ? AND delivered = FALSE 
                    ORDER BY created_at DESC
                """, (user_id,)).fetchall()
                
                # Marcar como entregadas
                if notifications:
                    notification_ids = [n["id"] for n in notifications]
                    placeholders = ",".join("?" * len(notification_ids))
                    conn.execute(f"UPDATE notifications SET delivered = TRUE WHERE id IN ({placeholders})", notification_ids)
                    conn.commit()
                
                # Convertir a formato JSON
                result = []
                for notif in notifications:
                    result.append({
                        "id": notif["id"],
                        "type": notif["notification_type"],
                        "title": notif["title"],
                        "message": notif["message"],
                        "data": json.loads(notif["data"]) if notif["data"] else {},
                        "created_at": notif["created_at"]
                    })
                
                return result
        except Exception as e:
            print(f"❌ Error getting pending notifications: {e}")
            return []

    def add_notification(self, user_id: str, notif_type: str, title: str, message: str, data: dict = None):
        """Agregar una nueva notificación"""
        try:
            with self.get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO notifications (user_id, notification_type, title, message, data) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, notif_type, title, message, json.dumps(data) if data else "{}"))
                conn.commit()
                print(f"✅ Notification added for user {user_id[:8]}: {title}")
        except Exception as e:
            print(f"❌ Error adding notification: {e}")

    def get_active_users(self, hours: int = 24) -> list:
        """Obtener usuarios activos en las últimas X horas"""
        try:
            with self.get_db_connection() as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                users = conn.execute("""
                    SELECT user_id FROM users 
                    WHERE last_active >= ? 
                    OR created_at >= ?
                """, (cutoff_time, cutoff_time)).fetchall()
                
                return [u["user_id"] for u in users]
        except Exception as e:
            print(f"❌ Error getting active users: {e}")
            return []

    def get_user_stats(self, user_id: str) -> dict:
        """Obtener estadísticas completas de un usuario"""
        try:
            with self.get_db_connection() as conn:
                # Obtener config
                user_row = conn.execute("SELECT config FROM users WHERE user_id = ?", (user_id,)).fetchone()
                config = json.loads(user_row["config"]) if user_row else {}
                
                # Obtener state
                state_row = conn.execute("SELECT * FROM user_state WHERE user_id = ?", (user_id,)).fetchone()
                state = dict(state_row) if state_row else {}
                
                # Contar notificaciones totales
                total_notifications = conn.execute(
                    "SELECT COUNT(*) as count FROM notifications WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()["count"]
                
                return {
                    "config": config,
                    "state": state,
                    "total_notifications": total_notifications
                }
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {"config": {}, "state": {}, "total_notifications": 0}

    def get_all_notifications(self, user_id: str, limit: int = 50, include_delivered: bool = True) -> list:
        """Obtener todas las notificaciones de un usuario (entregadas y pendientes)"""
        try:
            with self.get_db_connection() as conn:
                if include_delivered:
                    query = """
                        SELECT id, notification_type, title, message, data, created_at, delivered 
                        FROM notifications 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """
                    params = (user_id, limit)
                else:
                    query = """
                        SELECT id, notification_type, title, message, data, created_at, delivered 
                        FROM notifications 
                        WHERE user_id = ? AND delivered = FALSE 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """
                    params = (user_id, limit)
                
                notifications = conn.execute(query, params).fetchall()
                
                result = []
                for notif in notifications:
                    result.append({
                        "id": notif["id"],
                        "type": notif["notification_type"],
                        "title": notif["title"],
                        "message": notif["message"],
                        "data": json.loads(notif["data"]) if notif["data"] else {},
                        "created_at": notif["created_at"],
                        "delivered": bool(notif["delivered"])
                    })
                
                return result
        except Exception as e:
            print(f"❌ Error getting all notifications: {e}")
            return []

    def delete_notification(self, user_id: str, notification_id: int) -> bool:
        """Eliminar una notificación específica"""
        try:
            with self.get_db_connection() as conn:
                # Verificar que la notificación pertenece al usuario
                existing = conn.execute(
                    "SELECT id FROM notifications WHERE id = ? AND user_id = ?", 
                    (notification_id, user_id)
                ).fetchone()
                
                if not existing:
                    return False
                
                conn.execute("DELETE FROM notifications WHERE id = ? AND user_id = ?", 
                            (notification_id, user_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error deleting notification: {e}")
            return False

    def delete_all_notifications(self, user_id: str, notification_type: str = None) -> int:
        """Eliminar todas las notificaciones de un usuario (opcionalmente por tipo)"""
        try:
            with self.get_db_connection() as conn:
                if notification_type:
                    result = conn.execute(
                        "DELETE FROM notifications WHERE user_id = ? AND notification_type = ?", 
                        (user_id, notification_type)
                    )
                else:
                    result = conn.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
                
                conn.commit()
                return result.rowcount
        except Exception as e:
            print(f"❌ Error deleting all notifications: {e}")
            return 0

    def get_notifications_by_type(self, user_id: str, notification_type: str, limit: int = 20) -> list:
        """Obtener notificaciones de un tipo específico"""
        try:
            with self.get_db_connection() as conn:
                notifications = conn.execute("""
                    SELECT id, notification_type, title, message, data, created_at, delivered 
                    FROM notifications 
                    WHERE user_id = ? AND notification_type = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, notification_type, limit)).fetchall()
                
                result = []
                for notif in notifications:
                    result.append({
                        "id": notif["id"],
                        "type": notif["notification_type"],
                        "title": notif["title"],
                        "message": notif["message"],
                        "data": json.loads(notif["data"]) if notif["data"] else {},
                        "created_at": notif["created_at"],
                        "delivered": bool(notif["delivered"])
                    })
                
                return result
        except Exception as e:
            print(f"❌ Error getting notifications by type: {e}")
            return []

    def get_notification_summary(self, user_id: str) -> dict:
        """Obtener resumen de notificaciones por tipo"""
        try:
            with self.get_db_connection() as conn:
                # Contar por tipo
                counts = conn.execute("""
                    SELECT notification_type, COUNT(*) as count, 
                           SUM(CASE WHEN delivered = FALSE THEN 1 ELSE 0 END) as pending
                    FROM notifications 
                    WHERE user_id = ? 
                    GROUP BY notification_type
                """, (user_id,)).fetchall()
                
                # Total general
                total = conn.execute(
                    "SELECT COUNT(*) as count FROM notifications WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
                
                result = {
                    "total": total["count"] if total else 0,
                    "by_type": {}
                }
                
                for row in counts:
                    result["by_type"][row["notification_type"]] = {
                        "total": row["count"],
                        "pending": row["pending"],
                        "delivered": row["count"] - row["pending"]
                    }
                
                return result
        except Exception as e:
            print(f"❌ Error getting notification summary: {e}")
            return {"total": 0, "by_type": {}}

    def run_checks(self, user_id: str):
        config = self.get_user_config(user_id)
        since_date = datetime.now() - timedelta(hours=24)

        if config.get("papers_notifications"):
            papers = check_papers(config.get("papers_keywords", []), config.get("papers_categories", []), since_date)
            for n in papers:
                self.save_notification(user_id, n)

        if config.get("patent_notifications"):
            patents = check_patents(config.get("patent_keywords", []), since_date)
            for n in patents:
                self.save_notification(user_id, n)

        if config.get("ayudas_notifications"):
            ayudas = check_ayudas(config.get("region", "España"), since_date)
            for n in ayudas:
                self.save_notification(user_id, n)

        if config.get("email_notifications"):
            emails = check_emails(user_id, since_date)
            for n in emails:
                self.save_notification(user_id, n)

    # ----------------------------
    # Monitoreo en background
    # ----------------------------
    def start_background_monitoring(self) -> bool:
        """Iniciar monitoreo en background - versión mejorada"""
        if self.running:
            print("⚠️ Sistema de monitoreo ya está ejecutándose")
            return False
            
        self.running = True

        def monitor():
            print("🔄 Iniciando loop de monitoreo...")
            while self.running:
                try:
                    # Obtener usuarios activos
                    active_users = self.get_active_users(hours=24)
                    print(f"🔍 Monitoreando {len(active_users)} usuarios activos")
                    
                    for user_id in active_users:
                        # Solo procesar usuarios con notificaciones activadas
                        config = self.get_user_config(user_id)
                        if any([
                            config.get('email_notifications'),
                            config.get('patent_notifications'), 
                            config.get('papers_notifications'),
                            config.get('ayudas_notifications')
                        ]):
                            print(f"📬 Verificando notificaciones para {user_id[:8]}...")
                            self.run_checks(user_id)
                    
                except Exception as e:
                    print(f"❌ Error en monitor loop: {e}")
                
                # Esperar antes del siguiente ciclo
                time.sleep(self.monitor_interval)

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        print("🚀 Sistema de monitoreo iniciado correctamente")
        return True

    def stop_background_monitoring(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ Monitoreo de notificaciones detenido")

    def _get_current_timestamp(self) -> str:
        """Obtener timestamp actual en formato ISO"""
        return datetime.now().isoformat()

# Instancia global
multi_user_system = MultiUserNotificationSystem()