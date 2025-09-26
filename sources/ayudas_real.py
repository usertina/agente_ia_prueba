import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import feedparser
import re
import json
import time
from typing import List, Dict, Optional
import hashlib
from urllib.parse import urljoin

class AyudasScraper:
    """
    Scraper real para ayudas y subvenciones de múltiples fuentes oficiales
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Fuentes de datos reales
        self.sources = {
            'euskadi': {
                'name': 'Gobierno Vasco',
                'rss': 'https://www.euskadi.eus/rss/ayudas-subvenciones/',
                'web': 'https://www.euskadi.eus/ayudas-subvenciones/',
                'type': 'rss'
            },
            'gipuzkoa': {
                'name': 'Diputación Foral de Gipuzkoa',
                'web': 'https://www.gipuzkoa.eus/es/web/subvenciones',
                'api': 'https://www.gipuzkoa.eus/documents/2556071/2587785/subvenciones.json',
                'type': 'json_api'
            },
            'estado': {
                'name': 'Administración General del Estado',
                'web': 'https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias',
                'rss': 'https://www.infosubvenciones.es/bdnstrans/A04003/es/rss',
                'type': 'rss'
            },
            'europa': {
                'name': 'Fondos Europeos',
                'web': 'https://planderecuperacion.gob.es/convocatorias',
                'type': 'web_scraping'
            },
            'spri': {
                'name': 'SPRI - Agencia Vasca de Desarrollo',
                'web': 'https://www.spri.eus/ayudas/',
                'rss': 'https://www.spri.eus/feed/',
                'type': 'rss'
            }
        }
        
        # Cache para evitar duplicados
        self.cache_file = "cache/ayudas_cache.json"
        self.seen_aids = self.load_cache()
    
    def load_cache(self) -> set:
        """Carga IDs de ayudas ya procesadas"""
        try:
            import os
            os.makedirs("cache", exist_ok=True)
            with open(self.cache_file, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    
    def save_cache(self):
        """Guarda IDs de ayudas procesadas"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(list(self.seen_aids), f)
        except Exception as e:
            print(f"Error guardando cache: {e}")
    
    def generate_id(self, title: str, url: str) -> str:
        """Genera ID único para cada ayuda"""
        content = f"{title}_{url}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def scrape_euskadi_rss(self) -> List[Dict]:
        """Scraping del RSS del Gobierno Vasco"""
        ayudas = []
        try:
            feed = feedparser.parse(self.sources['euskadi']['rss'])
            
            for entry in feed.entries[:20]:  # Últimas 20 ayudas
                aid_id = self.generate_id(entry.title, entry.link)
                
                if aid_id not in self.seen_aids:
                    # Extraer fecha límite del contenido si existe
                    fecha_limite = self.extract_deadline(entry.get('summary', ''))
                    
                    ayuda = {
                        'id': aid_id,
                        'titulo': entry.title,
                        'descripcion': entry.get('summary', '')[:500],
                        'url': entry.link,
                        'fecha_publicacion': entry.get('published', ''),
                        'fecha_limite': fecha_limite,
                        'entidad': 'Gobierno Vasco',
                        'tipo': self.classify_aid_type(entry.title),
                        'ambito': 'Euskadi',
                        'categorias': self.extract_categories(entry.title + ' ' + entry.get('summary', '')),
                        'importe': self.extract_amount(entry.get('summary', '')),
                        'nuevo': True
                    }
                    ayudas.append(ayuda)
                    self.seen_aids.add(aid_id)
        
        except Exception as e:
            print(f"Error scraping Euskadi RSS: {e}")
        
        return ayudas
    
    def scrape_gipuzkoa_api(self) -> List[Dict]:
        """Scraping del API JSON de Gipuzkoa"""
        ayudas = []
        try:
            response = self.session.get(self.sources['gipuzkoa']['api'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('ayudas', [])[:20]:
                    aid_id = self.generate_id(
                        item.get('titulo', ''),
                        item.get('url', '')
                    )
                    
                    if aid_id not in self.seen_aids:
                        ayuda = {
                            'id': aid_id,
                            'titulo': item.get('titulo', ''),
                            'descripcion': item.get('descripcion', '')[:500],
                            'url': item.get('url', ''),
                            'fecha_publicacion': item.get('fecha_publicacion', ''),
                            'fecha_limite': item.get('fecha_fin', ''),
                            'entidad': 'Diputación Foral de Gipuzkoa',
                            'tipo': self.classify_aid_type(item.get('titulo', '')),
                            'ambito': 'Gipuzkoa',
                            'categorias': item.get('categorias', []),
                            'importe': item.get('dotacion', 'No especificado'),
                            'nuevo': True
                        }
                        ayudas.append(ayuda)
                        self.seen_aids.add(aid_id)
        
        except Exception as e:
            print(f"Error scraping Gipuzkoa API: {e}")
        
        return ayudas
    
    def scrape_estado_bdns(self) -> List[Dict]:
        """Scraping de la Base de Datos Nacional de Subvenciones"""
        ayudas = []
        try:
            # RSS de convocatorias estatales
            feed = feedparser.parse(self.sources['estado']['rss'])
            
            for entry in feed.entries[:15]:
                aid_id = self.generate_id(entry.title, entry.link)
                
                if aid_id not in self.seen_aids:
                    ayuda = {
                        'id': aid_id,
                        'titulo': entry.title,
                        'descripcion': entry.get('description', '')[:500],
                        'url': entry.link,
                        'fecha_publicacion': entry.get('published', ''),
                        'fecha_limite': self.extract_deadline(entry.get('description', '')),
                        'entidad': 'Administración General del Estado',
                        'tipo': self.classify_aid_type(entry.title),
                        'ambito': 'Nacional',
                        'categorias': self.extract_categories(entry.title),
                        'importe': self.extract_amount(entry.get('description', '')),
                        'nuevo': True
                    }
                    ayudas.append(ayuda)
                    self.seen_aids.add(aid_id)
        
        except Exception as e:
            print(f"Error scraping BDNS: {e}")
        
        return ayudas
    
    def scrape_europa_funds(self) -> List[Dict]:
        """Scraping de fondos europeos"""
        ayudas = []
        try:
            url = self.sources['europa']['web']
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar convocatorias (adaptar selectores según estructura real)
                convocatorias = soup.find_all('div', class_='convocatoria-item')[:10]
                
                for conv in convocatorias:
                    titulo_elem = conv.find('h3') or conv.find('h4')
                    if not titulo_elem:
                        continue
                    
                    titulo = titulo_elem.get_text(strip=True)
                    link_elem = conv.find('a')
                    url_ayuda = urljoin(url, link_elem['href']) if link_elem else url
                    
                    aid_id = self.generate_id(titulo, url_ayuda)
                    
                    if aid_id not in self.seen_aids:
                        descripcion = conv.find('p')
                        fecha = conv.find('span', class_='fecha')
                        
                        ayuda = {
                            'id': aid_id,
                            'titulo': titulo,
                            'descripcion': descripcion.get_text(strip=True)[:500] if descripcion else '',
                            'url': url_ayuda,
                            'fecha_publicacion': fecha.get_text(strip=True) if fecha else '',
                            'fecha_limite': self.extract_deadline(conv.get_text()),
                            'entidad': 'Fondos Europeos',
                            'tipo': 'Fondo Europeo',
                            'ambito': 'Europeo',
                            'categorias': ['Europa', 'Next Generation EU'],
                            'importe': self.extract_amount(conv.get_text()),
                            'nuevo': True
                        }
                        ayudas.append(ayuda)
                        self.seen_aids.add(aid_id)
        
        except Exception as e:
            print(f"Error scraping Europa: {e}")
        
        return ayudas
    
    def scrape_spri(self) -> List[Dict]:
        """Scraping de SPRI - Agencia Vasca"""
        ayudas = []
        try:
            feed = feedparser.parse(self.sources['spri']['rss'])
            
            for entry in feed.entries[:15]:
                # Filtrar solo ayudas (no noticias)
                if 'ayuda' in entry.title.lower() or 'programa' in entry.title.lower():
                    aid_id = self.generate_id(entry.title, entry.link)
                    
                    if aid_id not in self.seen_aids:
                        ayuda = {
                            'id': aid_id,
                            'titulo': entry.title,
                            'descripcion': entry.get('summary', '')[:500],
                            'url': entry.link,
                            'fecha_publicacion': entry.get('published', ''),
                            'fecha_limite': self.extract_deadline(entry.get('summary', '')),
                            'entidad': 'SPRI',
                            'tipo': 'Desarrollo Empresarial',
                            'ambito': 'Euskadi',
                            'categorias': ['Empresa', 'Innovación', 'I+D'],
                            'importe': self.extract_amount(entry.get('summary', '')),
                            'nuevo': True
                        }
                        ayudas.append(ayuda)
                        self.seen_aids.add(aid_id)
        
        except Exception as e:
            print(f"Error scraping SPRI: {e}")
        
        return ayudas
    
    # Métodos auxiliares
    
    def extract_deadline(self, text: str) -> Optional[str]:
        """Extrae fecha límite del texto"""
        patterns = [
            r'hasta el (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'fecha límite[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'plazo[:\s]+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'antes del (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_amount(self, text: str) -> str:
        """Extrae el importe de la ayuda del texto"""
        patterns = [
            r'(\d+\.?\d*)\s*€',
            r'(\d+\.?\d*)\s*euros?',
            r'hasta\s+(\d+\.?\d*)',
            r'máximo\s+de\s+(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return f"{amount} €"
        
        return "No especificado"
    
    def classify_aid_type(self, title: str) -> str:
        """Clasifica el tipo de ayuda según el título"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['i+d', 'investigación', 'desarrollo']):
            return 'I+D+i'
        elif any(word in title_lower for word in ['empleo', 'contratación', 'laboral']):
            return 'Empleo'
        elif any(word in title_lower for word in ['digitalización', 'digital', 'tecnología']):
            return 'Digitalización'
        elif any(word in title_lower for word in ['sostenible', 'verde', 'ambiental']):
            return 'Sostenibilidad'
        elif any(word in title_lower for word in ['formación', 'educación', 'beca']):
            return 'Formación'
        elif any(word in title_lower for word in ['emprendimiento', 'startup', 'empresa']):
            return 'Emprendimiento'
        else:
            return 'General'
    
    def extract_categories(self, text: str) -> List[str]:
        """Extrae categorías relevantes del texto"""
        categories = []
        text_lower = text.lower()
        
        category_keywords = {
            'Tecnología': ['tecnología', 'digital', 'software', 'tic'],
            'Innovación': ['innovación', 'i+d', 'investigación'],
            'Sostenibilidad': ['sostenible', 'verde', 'ambiental', 'ecológico'],
            'Empleo': ['empleo', 'contratación', 'trabajo'],
            'Formación': ['formación', 'educación', 'capacitación', 'beca'],
            'Industria': ['industria', 'industrial', 'manufactura'],
            'Comercio': ['comercio', 'exportación', 'internacional'],
            'Turismo': ['turismo', 'turístico', 'hostelería'],
            'Cultura': ['cultura', 'cultural', 'arte'],
            'Social': ['social', 'inclusión', 'discapacidad']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ['General']
    
    def get_all_ayudas(self, region: str = None, since_date: datetime = None) -> List[Dict]:
        """Obtiene todas las ayudas de todas las fuentes"""
        all_ayudas = []
        
        # Definir qué fuentes usar según región
        sources_to_use = []
        if region and region.lower() in ['euskadi', 'país vasco', 'pais vasco']:
            sources_to_use = ['euskadi', 'spri', 'gipuzkoa', 'estado', 'europa']
        elif region and region.lower() == 'gipuzkoa':
            sources_to_use = ['gipuzkoa', 'euskadi', 'spri', 'estado', 'europa']
        else:
            sources_to_use = list(self.sources.keys())
        
        # Scraping de cada fuente
        for source in sources_to_use:
            print(f"🔍 Scraping {source}...")
            
            if source == 'euskadi':
                all_ayudas.extend(self.scrape_euskadi_rss())
            elif source == 'gipuzkoa':
                all_ayudas.extend(self.scrape_gipuzkoa_api())
            elif source == 'estado':
                all_ayudas.extend(self.scrape_estado_bdns())
            elif source == 'europa':
                all_ayudas.extend(self.scrape_europa_funds())
            elif source == 'spri':
                all_ayudas.extend(self.scrape_spri())
            
            # Pequeña pausa para no sobrecargar
            time.sleep(1)
        
        # Filtrar por fecha si se especifica
        if since_date:
            filtered = []
            for ayuda in all_ayudas:
                try:
                    # Intentar parsear la fecha de publicación
                    pub_date_str = ayuda.get('fecha_publicacion', '')
                    if pub_date_str:
                        # Aquí necesitarías adaptar el parsing según el formato real
                        # Por ahora lo simplificamos
                        filtered.append(ayuda)
                except:
                    pass
            all_ayudas = filtered
        
        # Guardar cache
        self.save_cache()
        
        return all_ayudas


# Función principal para usar desde el sistema de notificaciones
def check_ayudas(region: str, since_date: datetime) -> List[Dict]:
    """
    Función principal que devuelve notificaciones de ayudas reales
    """
    scraper = AyudasScraper()
    ayudas = scraper.get_all_ayudas(region, since_date)
    
    notifications = []
    for ayuda in ayudas[:10]:  # Limitar a 10 notificaciones
        notification = {
            "type": "ayudas",
            "title": f"💶 Nueva ayuda: {ayuda['titulo'][:100]}",
            "message": f"{ayuda['entidad']} - {ayuda.get('importe', 'Consultar bases')}",
            "data": {
                "id": ayuda['id'],
                "url": ayuda['url'],
                "entidad": ayuda['entidad'],
                "fecha_limite": ayuda.get('fecha_limite', 'No especificada'),
                "categorias": ayuda.get('categorias', []),
                "ambito": ayuda['ambito'],
                "tipo": ayuda['tipo']
            }
        }
        notifications.append(notification)
    
    return notifications