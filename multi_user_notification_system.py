import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import hashlib
from threading import Thread
import time
from contextlib import contextmanager
import requests
import xml.etree.ElementTree as ET

class MultiUserNotificationSystem:
    def __init__(self):
        self.db_file = "notifications.db"
        self.init_database()
        self.monitoring_tasks = {}
        self.background_thread = None
        self.running = False
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
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
                        email_count INTEGER DEFAULT 0,
                        patent_count INTEGER DEFAULT 0,
                        papers_count INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, delivered);
                    CREATE INDEX IF NOT EXISTS idx_users_session ON users(session_id);
                    CREATE INDEX IF NOT EXISTS idx_users_active ON users(last_active);
                ''')
                print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    @contextmanager
    def get_db_connection(self):
        """Context manager para conexiones de BD"""
        conn = sqlite3.connect(self.db_file, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def generate_user_id(self, ip_address: str, user_agent: str) -> str:
        """Genera un ID único para el usuario basado en IP y User-Agent"""
        # Agregar salt para mayor seguridad
        salt = "gemini_agent_2024"
        unique_string = f"{salt}_{ip_address}_{user_agent}"
        return "user_" + hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def register_user(self, ip_address: str, user_agent: str, device_info: Dict = None) -> tuple:
        """Registra o actualiza un usuario"""
        try:
            user_id = self.generate_user_id(ip_address, user_agent)
            session_id = str(uuid.uuid4())
            device_id = device_info.get('device_id', str(uuid.uuid4())[:8]) if device_info else str(uuid.uuid4())[:8]
            device_name = device_info.get('device_name', 'Dispositivo Desconocido') if device_info else 'Dispositivo Desconocido'
            
            default_config = {
                "email_notifications": False,
                "patent_notifications": False,
                "papers_notifications": False,
                "patent_keywords": [],
                "papers_keywords": [],
                "papers_categories": ["cs.AI", "cs.LG", "cs.CV"],
                "email_check_interval": 300,
                "patent_check_interval": 3600,
                "papers_check_interval": 1800,
                "device_name": device_name,
                "max_papers_per_check": 5,
                "max_patents_per_check": 3
            }
            
            with self.get_db_connection() as conn:
                # Verificar si el usuario ya existe
                existing = conn.execute(
                    "SELECT config FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
                
                if existing:
                    # Actualizar sesión y última actividad
                    conn.execute('''
                        UPDATE users 
                        SET session_id = ?, device_id = ?, device_name = ?, last_active = CURRENT_TIMESTAMP 
                        WHERE user_id = ?
                    ''', (session_id, device_id, device_name, user_id))
                    config = json.loads(existing['config'])
                    print(f"🔄 Usuario existente actualizado: {user_id[:12]}...")
                else:
                    # Crear nuevo usuario
                    conn.execute('''
                        INSERT INTO users (user_id, session_id, device_id, device_name, config)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, session_id, device_id, device_name, json.dumps(default_config)))
                    
                    # Crear estado inicial
                    conn.execute('''
                        INSERT INTO user_state (user_id)
                        VALUES (?)
                    ''', (user_id,))
                    
                    config = default_config
                    print(f"➕ Nuevo usuario registrado: {user_id[:12]}...")
                
                conn.commit()
            
            return user_id, session_id, config
            
        except Exception as e:
            print(f"❌ Error registrando usuario: {e}")
            raise
    
    def update_user_config(self, user_id: str, config: Dict) -> bool:
        """Actualiza la configuración del usuario"""
        try:
            print(f"🔧 Intentando actualizar config para {user_id[:12]}... con: {config}")
            
            with self.get_db_connection() as conn:
                # Verificar que el usuario existe
                current = conn.execute(
                    "SELECT config FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
                
                if not current:
                    print(f"❌ Usuario no encontrado: {user_id[:12]}...")
                    # Intentar crear el usuario si no existe
                    default_config = {
                        "email_notifications": False,
                        "patent_notifications": False,
                        "papers_notifications": False,
                        "patent_keywords": [],
                        "papers_keywords": [],
                        "papers_categories": ["cs.AI", "cs.LG", "cs.CV"],
                        "email_check_interval": 300,
                        "patent_check_interval": 3600,
                        "papers_check_interval": 1800,
                        "device_name": "Web Device",
                        "max_papers_per_check": 5,
                        "max_patents_per_check": 3
                    }
                    
                    # Crear usuario básico
                    conn.execute('''
                        INSERT OR IGNORE INTO users (user_id, session_id, device_id, device_name, config)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, str(uuid.uuid4()), 'web_device', 'Web Device', json.dumps(default_config)))
                    
                    # Crear estado inicial
                    conn.execute('''
                        INSERT OR IGNORE INTO user_state (user_id)
                        VALUES (?)
                    ''', (user_id,))
                    
                    conn.commit()
                    
                    # Obtener la configuración recién creada
                    current = conn.execute(
                        "SELECT config FROM users WHERE user_id = ?", 
                        (user_id,)
                    ).fetchone()
                
                if current:
                    try:
                        current_config = json.loads(current['config'])
                        print(f"📋 Config actual: {current_config}")
                        
                        # Actualizar con los nuevos valores
                        current_config.update(config)
                        print(f"📋 Config nueva: {current_config}")
                        
                        # Guardar la configuración actualizada
                        conn.execute(
                            "UPDATE users SET config = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                            (json.dumps(current_config), user_id)
                        )
                        conn.commit()
                        
                        print(f"✅ Configuración actualizada para {user_id[:12]}...")
                        return True
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Error decodificando JSON config: {e}")
                        return False
                else:
                    print(f"❌ No se pudo crear/encontrar usuario: {user_id[:12]}...")
                    return False
                    
        except Exception as e:
            print(f"❌ Error updating user config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_user_config(self, user_id: str) -> Dict:
        """Obtiene la configuración del usuario"""
        try:
            with self.get_db_connection() as conn:
                result = conn.execute(
                    "SELECT config FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
                
                if result:
                    return json.loads(result['config'])
                return {}
        except Exception as e:
            print(f"❌ Error getting user config: {e}")
            return {}
    
    def add_notification(self, user_id: str, notification_type: str, title: str, message: str, data: Dict = None):
        """Añade una notificación para un usuario específico"""
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO notifications (user_id, notification_type, title, message, data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, notification_type, title, message, json.dumps(data or {})))
                conn.commit()
                print(f"📨 Notificación añadida para {user_id[:8]}: {title}")
        except Exception as e:
            print(f"❌ Error añadiendo notificación: {e}")
    
    def get_pending_notifications(self, user_id: str) -> List[Dict]:
        """Obtiene notificaciones pendientes para un usuario"""
        try:
            with self.get_db_connection() as conn:
                results = conn.execute('''
                    SELECT id, notification_type, title, message, data, created_at
                    FROM notifications 
                    WHERE user_id = ? AND delivered = FALSE
                    ORDER BY created_at DESC
                    LIMIT 20
                ''', (user_id,)).fetchall()
                
                notifications = []
                notification_ids = []
                
                for row in results:
                    notifications.append({
                        'id': row['id'],
                        'type': row['notification_type'],
                        'title': row['title'],
                        'message': row['message'],
                        'data': json.loads(row['data'] or '{}'),
                        'timestamp': row['created_at']
                    })
                    notification_ids.append(row['id'])
                
                # Marcar como entregadas
                if notification_ids:
                    placeholders = ','.join(['?' for _ in notification_ids])
                    conn.execute(f'''
                        UPDATE notifications 
                        SET delivered = TRUE 
                        WHERE id IN ({placeholders})
                    ''', notification_ids)
                    conn.commit()
                    print(f"✅ {len(notifications)} notificaciones entregadas a {user_id[:8]}")
                
                return notifications
        except Exception as e:
            print(f"❌ Error getting notifications: {e}")
            return []
    
    def get_active_users(self, hours: int = 24) -> List[str]:
        """Obtiene usuarios activos en las últimas X horas"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            with self.get_db_connection() as conn:
                results = conn.execute('''
                    SELECT user_id, config 
                    FROM users 
                    WHERE last_active > ?
                ''', (cutoff,)).fetchall()
                
                active_users = []
                for row in results:
                    config = json.loads(row['config'])
                    if (config.get('email_notifications') or 
                        config.get('patent_notifications') or 
                        config.get('papers_notifications')):
                        active_users.append(row['user_id'])
                
                return active_users
        except Exception as e:
            print(f"❌ Error getting active users: {e}")
            return []
    
    def start_background_monitoring(self):
        """Inicia el monitoreo en background para todos los usuarios"""
        if self.background_thread and self.background_thread.is_alive():
            print("⚠️ Sistema de monitoreo ya está ejecutándose")
            return False
        
        self.running = True
        self.background_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.background_thread.start()
        print("🚀 Sistema de notificaciones multi-usuario iniciado")
        return True
    
    def stop_background_monitoring(self):
        """Detiene el monitoreo en background"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        print("⏹️ Sistema de notificaciones detenido")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo en background"""
        print("🔄 Iniciando loop de monitoreo...")
        
        while self.running:
            try:
                active_users = self.get_active_users(hours=6)
                if len(active_users) > 0:
                    print(f"🔄 Verificando {len(active_users)} usuarios activos...")
                
                for user_id in active_users:
                    if not self.running:  # Check if should stop
                        break
                        
                    try:
                        config = self.get_user_config(user_id)
                        
                        # Verificar patentes si está habilitado
                        if config.get('patent_notifications') and config.get('patent_keywords'):
                            try:
                                new_patents = self.check_patents_sync(user_id, config)
                                for patent in new_patents:
                                    if not self.running:
                                        break
                                    self.add_notification(
                                        user_id, 'patent', patent['title'],
                                        patent['message'], patent['data']
                                    )
                            except Exception as e:
                                print(f"❌ Error checking patents for user {user_id[:8]}: {e}")
                        
                        # Verificar papers científicos si está habilitado
                        if config.get('papers_notifications') and (config.get('papers_keywords') or config.get('papers_categories')):
                            try:
                                new_papers = self.check_papers_sync(user_id, config)
                                for paper in new_papers:
                                    if not self.running:
                                        break
                                    self.add_notification(
                                        user_id, 'paper', paper['title'],
                                        paper['message'], paper['data']
                                    )
                            except Exception as e:
                                print(f"❌ Error checking papers for user {user_id[:8]}: {e}")
                        
                        # Pequeña pausa entre usuarios
                        if self.running:
                            time.sleep(1)
                        
                    except Exception as e:
                        print(f"❌ Error processing user {user_id[:8]}: {e}")
                        continue
                
                # Limpiar notificaciones antiguas (más de 7 días)
                if self.running:
                    self.cleanup_old_notifications()
                
                # Esperar antes del siguiente ciclo (5 minutos)
                for _ in range(300):  # 300 segundos = 5 minutos
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                if self.running:
                    time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def check_patents_sync(self, user_id: str, config: Dict) -> List[Dict]:
        """Versión síncrona del check de patentes"""
        try:
            keywords = config.get('patent_keywords', [])
            if not keywords:
                return []
            
            new_patents = []
            
            # Obtener estado del usuario
            state = self.get_user_state(user_id)
            since_date = datetime.now() - timedelta(hours=24)
            
            if state.get('last_patent_check'):
                try:
                    since_date = datetime.fromisoformat(state['last_patent_check'])
                except:
                    pass
            
            max_patents = config.get('max_patents_per_check', 3)
            
            # Usar API simplificada para demostración
            # En producción, usar USPTO API real
            for keyword in keywords[:3]:
                try:
                    # Simulación de búsqueda de patentes
                    # En producción aquí iría la búsqueda real en USPTO
                    simulated_patents = self._simulate_patent_search(keyword, since_date)
                    
                    for patent in simulated_patents[:2]:
                        new_patents.append({
                            'title': f'🔬 Nueva patente: {keyword}',
                            'message': patent['title'][:150] + "...",
                            'data': patent
                        })
                        
                        if len(new_patents) >= max_patents:
                            break
                    
                    if len(new_patents) >= max_patents:
                        break
                    
                except Exception as e:
                    print(f"❌ Error checking patent for keyword {keyword}: {e}")
                    continue
            
            # Actualizar estado si hay resultados
            if new_patents:
                state['last_patent_check'] = datetime.now().isoformat()
                state['patent_count'] = state.get('patent_count', 0) + len(new_patents)
                self.save_user_state(user_id, state)
                print(f"🔬 {len(new_patents)} nuevas patentes para usuario {user_id[:8]}")
            
            return new_patents
            
        except Exception as e:
            print(f"❌ Error in sync patent check: {e}")
            return []
    
    def _simulate_patent_search(self, keyword: str, since_date: datetime) -> List[Dict]:
        """Simula búsqueda de patentes para demostración"""
        # En producción, esto sería una llamada real a la API de USPTO
        # Usar URLs reales que funcionen
        patent_id = f"20240{str(hash(keyword))[-6:]}"
        simulated_results = [
            {
                'title': f'Method and System for {keyword.title()} Processing',
                'app_number': f'US{patent_id}',
                'app_date': datetime.now().strftime('%Y-%m-%d'),
                'keyword': keyword,
                'inventors': ['John Doe', 'Jane Smith'],
                # URL real de Google Patents (funciona mejor)
                'url': f'https://patents.google.com/patent/US{patent_id}A1/en'
            }
        ]
        
        # Solo devolver si es "reciente"
        if datetime.now() > since_date:
            return simulated_results
        return []
    
    def check_papers_sync(self, user_id: str, config: Dict) -> List[Dict]:
        """Versión síncrona del check de papers científicos"""
        try:
            keywords = config.get('papers_keywords', [])
            categories = config.get('papers_categories', ['cs.AI'])
            
            if not keywords and not categories:
                return []
            
            new_papers = []
            
            # Obtener estado del usuario
            state = self.get_user_state(user_id)
            since_date = datetime.now() - timedelta(hours=24)
            
            if state.get('last_papers_check'):
                try:
                    since_date = datetime.fromisoformat(state['last_papers_check'])
                except:
                    pass
            
            max_papers = config.get('max_papers_per_check', 5)
            
            # Buscar por keywords en arXiv
            if keywords:
                for keyword in keywords[:3]:
                    if not self.running:
                        break
                        
                    try:
                        papers = self.search_arxiv(keyword, max_results=3)
                        for paper in papers:
                            if self.is_paper_new(paper, since_date):
                                new_papers.append({
                                    'title': f'📚 Nuevo paper: {keyword}',
                                    'message': paper['title'][:150] + "...",
                                    'data': {
                                        'title': paper['title'],
                                        'authors': paper['authors'],
                                        'abstract': paper['abstract'][:300] + "...",
                                        'published': paper['published'],
                                        'url': paper['url'],
                                        'keyword': keyword,
                                        'category': paper.get('category', 'Unknown')
                                    }
                                })
                                
                                if len(new_papers) >= max_papers:
                                    break
                        
                        if self.running:
                            time.sleep(1)
                        
                        if len(new_papers) >= max_papers:
                            break
                            
                    except Exception as e:
                        print(f"❌ Error searching papers for keyword {keyword}: {e}")
                        continue
            
            # Buscar por categorías si no se alcanzó el límite
            if len(new_papers) < max_papers and categories and self.running:
                for category in categories[:2]:
                    if not self.running:
                        break
                        
                    try:
                        papers = self.search_arxiv_by_category(category, max_results=2)
                        for paper in papers:
                            if self.is_paper_new(paper, since_date):
                                new_papers.append({
                                    'title': f'🔬 Nuevo paper en {category}',
                                    'message': paper['title'][:150] + "...",
                                    'data': {
                                        'title': paper['title'],
                                        'authors': paper['authors'],
                                        'abstract': paper['abstract'][:300] + "...",
                                        'published': paper['published'],
                                        'url': paper['url'],
                                        'category': category
                                    }
                                })
                                
                                if len(new_papers) >= max_papers:
                                    break
                        
                        if self.running:
                            time.sleep(1)
                        
                        if len(new_papers) >= max_papers:
                            break
                            
                    except Exception as e:
                        print(f"❌ Error searching papers for category {category}: {e}")
                        continue
            
            # Actualizar estado si hay resultados
            if new_papers:
                state['last_papers_check'] = datetime.now().isoformat()
                state['papers_count'] = state.get('papers_count', 0) + len(new_papers)
                self.save_user_state(user_id, state)
                print(f"📚 {len(new_papers)} nuevos papers para usuario {user_id[:8]}")
            
            return new_papers
            
        except Exception as e:
            print(f"❌ Error in sync papers check: {e}")
            return []
    
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """Busca papers en arXiv por query"""
        try:
            base_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parsear XML
            root = ET.fromstring(response.content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom',
                        'arxiv': 'http://arxiv.org/schemas/atom'}
            
            papers = []
            for entry in root.findall('atom:entry', namespace):
                try:
                    title = entry.find('atom:title', namespace)
                    title = title.text.strip().replace('\n', ' ') if title is not None else "Sin título"
                    
                    authors = []
                    for author in entry.findall('atom:author', namespace):
                        name = author.find('atom:name', namespace)
                        if name is not None:
                            authors.append(name.text.strip())
                    
                    abstract = entry.find('atom:summary', namespace)
                    abstract = abstract.text.strip().replace('\n', ' ') if abstract is not None else "Sin resumen"
                    
                    published = entry.find('atom:published', namespace)
                    published = published.text.strip() if published is not None else ""
                    
                    url = entry.find('atom:id', namespace)
                    url = url.text.strip() if url is not None else ""
                    
                    # Obtener categoría principal
                    category = entry.find('arxiv:primary_category', namespace)
                    category = category.get('term') if category is not None else "Unknown"
                    
                    papers.append({
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'published': published,
                        'url': url,
                        'category': category
                    })
                    
                except Exception as e:
                    print(f"❌ Error parsing paper entry: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
            return []
    
    def search_arxiv_by_category(self, category: str, max_results: int = 5) -> List[Dict]:
        """Busca papers en arXiv por categoría"""
        try:
            base_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'cat:{category}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parsear XML (mismo código que search_arxiv)
            root = ET.fromstring(response.content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom',
                        'arxiv': 'http://arxiv.org/schemas/atom'}
            
            papers = []
            for entry in root.findall('atom:entry', namespace):
                try:
                    title = entry.find('atom:title', namespace)
                    title = title.text.strip().replace('\n', ' ') if title is not None else "Sin título"
                    
                    authors = []
                    for author in entry.findall('atom:author', namespace):
                        name = author.find('atom:name', namespace)
                        if name is not None:
                            authors.append(name.text.strip())
                    
                    abstract = entry.find('atom:summary', namespace)
                    abstract = abstract.text.strip().replace('\n', ' ') if abstract is not None else "Sin resumen"
                    
                    published = entry.find('atom:published', namespace)
                    published = published.text.strip() if published is not None else ""
                    
                    url = entry.find('atom:id', namespace)
                    url = url.text.strip() if url is not None else ""
                    
                    papers.append({
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'published': published,
                        'url': url,
                        'category': category
                    })
                    
                except Exception as e:
                    print(f"❌ Error parsing paper entry: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv by category: {e}")
            return []
    
    def is_paper_new(self, paper: Dict, since_date: datetime) -> bool:
        """Verifica si un paper es nuevo basado en la fecha de publicación"""
        try:
            published_str = paper.get('published', '')
            if not published_str:
                return True
            
            # Parsear fecha de arXiv (formato: 2024-01-01T10:00:00Z)
            paper_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            paper_date = paper_date.replace(tzinfo=None)
            
            return paper_date > since_date
            
        except Exception as e:
            print(f"❌ Error parsing paper date: {e}")
            return True
    
    def get_user_state(self, user_id: str) -> Dict:
        """Obtiene el estado de un usuario"""
        try:
            with self.get_db_connection() as conn:
                result = conn.execute('''
                    SELECT last_email_check, last_patent_check, last_papers_check, 
                           email_count, patent_count, papers_count
                    FROM user_state WHERE user_id = ?
                ''', (user_id,)).fetchone()
                
                if result:
                    return {
                        'last_email_check': result['last_email_check'],
                        'last_patent_check': result['last_patent_check'],
                        'last_papers_check': result['last_papers_check'],
                        'email_count': result['email_count'] or 0,
                        'patent_count': result['patent_count'] or 0,
                        'papers_count': result['papers_count'] or 0
                    }
                return {
                    'last_email_check': None,
                    'last_patent_check': None,
                    'last_papers_check': None,
                    'email_count': 0,
                    'patent_count': 0,
                    'papers_count': 0
                }
        except Exception as e:
            print(f"❌ Error getting user state: {e}")
            return {
                'last_email_check': None,
                'last_patent_check': None,
                'last_papers_check': None,
                'email_count': 0,
                'patent_count': 0,
                'papers_count': 0
            }
    
    def save_user_state(self, user_id: str, state: Dict):
        """Guarda el estado de un usuario"""
        try:
            with self.get_db_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_state 
                    (user_id, last_email_check, last_patent_check, last_papers_check, 
                     email_count, patent_count, papers_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    state.get('last_email_check'),
                    state.get('last_patent_check'),
                    state.get('last_papers_check'),
                    state.get('email_count', 0),
                    state.get('patent_count', 0),
                    state.get('papers_count', 0)
                ))
                conn.commit()
        except Exception as e:
            print(f"❌ Error saving user state: {e}")
    
    def cleanup_old_notifications(self, days: int = 7):
        """Limpia notificaciones antiguas"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            with self.get_db_connection() as conn:
                result = conn.execute(
                    "DELETE FROM notifications WHERE created_at < ? AND delivered = TRUE",
                    (cutoff,)
                )
                if result.rowcount > 0:
                    print(f"🧹 Limpiadas {result.rowcount} notificaciones antiguas")
                conn.commit()
        except Exception as e:
            print(f"❌ Error cleaning up notifications: {e}")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Obtiene estadísticas del usuario"""
        try:
            with self.get_db_connection() as conn:
                # Contar notificaciones por tipo
                stats = conn.execute('''
                    SELECT notification_type, COUNT(*) as count
                    FROM notifications 
                    WHERE user_id = ? 
                    GROUP BY notification_type
                ''', (user_id,)).fetchall()
                
                # Estado del usuario
                state = self.get_user_state(user_id)
                config = self.get_user_config(user_id)
                
                notification_counts = {row['notification_type']: row['count'] for row in stats}
                
                return {
                    'config': config,
                    'state': state,
                    'total_notifications': sum(notification_counts.values()),
                    'notification_counts': notification_counts,
                    'user_id': user_id,
                    'device_name': config.get('device_name', 'Desconocido')
                }
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {
                'config': {},
                'state': {},
                'total_notifications': 0,
                'notification_counts': {},
                'user_id': user_id,
                'device_name': 'Desconocido'
            }
    
    def _get_current_timestamp(self) -> str:
        """Helper para obtener timestamp actual"""
        return datetime.now().isoformat()

# Instancia global del sistema multi-usuario
multi_user_system = MultiUserNotificationSystem()