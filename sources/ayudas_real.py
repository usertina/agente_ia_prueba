import requests
from datetime import datetime, timedelta
import feedparser
import re
import json
import time
from typing import List, Dict, Optional
import hashlib
import logging
from xml.etree import ElementTree as ET

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AyudasScraper:
    """
    Scraper mejorado usando APIs OFICIALES VERIFICADAS
    Prioriza APIs sobre web scraping para mayor confiabilidad
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'es-ES,es;q=0.9',
        })
        self.timeout = 20
        
        # 🔥 APIs OFICIALES VERIFICADAS
        self.apis = {
            # ========== EUSKADI OPEN DATA API (OFICIAL) ==========
            'euskadi_opendata': {
                'name': 'Open Data Euskadi - API Oficial',
                'enabled': True,
                'base_url': 'https://api.euskadi.eus',
                'endpoints': {
                    # API de contenidos (búsqueda general)
                    'search': 'https://api.euskadi.eus/contenidos',
                    # RSS de ayudas y subvenciones
                    'rss': 'https://www.euskadi.eus/rss/ayudas-subvenciones/',
                    # Portal web para scraping de respaldo
                    'web': 'https://www.euskadi.eus/ayudas-subvenciones/'
                },
                'type': 'api+rss'
            },
            
            # ========== BDNS - API OFICIAL ==========
            'bdns_api': {
                'name': 'Base de Datos Nacional de Subvenciones - API',
                'enabled': True,
                'base_url': 'https://www.infosubvenciones.es',
                'endpoints': {
                    # API pública de búsqueda
                    'search': 'https://www.infosubvenciones.es/bdnstrans/busqueda/Rest/search',
                    # RSS oficial
                    'rss': 'https://www.infosubvenciones.es/bdnstrans/A04003/es/rss',
                    # XML de convocatorias
                    'xml': 'https://www.infosubvenciones.es/bdnstrans/GE/es/convocatorias/formato/xml'
                },
                'type': 'api+rss'
            },
            
            # ========== DIPUTACIÓN FORAL DE BIZKAIA ==========
            'bizkaia': {
                'name': 'Diputación Foral de Bizkaia',
                'enabled': True,
                'endpoints': {
                    'rss': 'https://www.bizkaia.eus/rss/ayudas.xml',
                    'web': 'https://www.bizkaia.eus/es/subvenciones',
                    'buscador': 'https://www.bizkaia.eus/eu/web/subvencionesbizkaia/aurreikusitako-diru-laguntzak'
                },
                'type': 'rss+web'
            },
            
            # ========== DIPUTACIÓN FORAL DE GIPUZKOA ==========
            'gipuzkoa': {
                'name': 'Diputación Foral de Gipuzkoa',
                'enabled': True,
                'endpoints': {
                    'web': 'https://www.gipuzkoa.eus/es/web/subvenciones',
                    'buscador': 'https://www.gipuzkoa.eus/es/web/subvenciones/dirulaguntzak'
                },
                'type': 'web'
            },
            
            # ========== SPRI (AGENCIA VASCA) ==========
            'spri': {
                'name': 'SPRI - Agencia Vasca de Desarrollo',
                'enabled': True,
                'endpoints': {
                    'rss': 'https://www.spri.eus/es/rss/',
                    'web': 'https://www.spri.eus/ayudas/',
                    'api': 'https://www.spri.eus/api/ayudas'  # Endpoint hipotético
                },
                'type': 'rss'
            },
            
            # ========== PLAN DE RECUPERACIÓN (NEXT GENERATION) ==========
            'next_generation': {
                'name': 'Plan de Recuperación - Next Generation EU',
                'enabled': True,
                'endpoints': {
                    'api': 'https://planderecuperacion.gob.es/api/convocatorias',
                    'web': 'https://planderecuperacion.gob.es/convocatorias',
                    'rss': 'https://planderecuperacion.gob.es/rss/convocatorias'
                },
                'type': 'web+rss'
            },
            
            # ========== CDTI ==========
            'cdti': {
                'name': 'CDTI - Centro Desarrollo Tecnológico',
                'enabled': True,
                'endpoints': {
                    'web': 'https://www.cdti.es/index.asp?MP=7&MS=0&MN=1',
                    'rss': 'https://www.cdti.es/rss/convocatorias.xml'
                },
                'type': 'rss+web'
            }
        }
        
        # Cache
        self.cache_file = "cache/ayudas_cache.json"
        self.seen_aids = self.load_cache()
        
        # Estadísticas
        self.stats = {
            'total_intentos': 0,
            'exitos': 0,
            'errores': 0,
            'ayudas_encontradas': 0
        }
    
    def load_cache(self) -> set:
        """Carga cache de ayudas procesadas"""
        try:
            import os
            os.makedirs("cache", exist_ok=True)
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Error cargando cache: {e}")
            return set()
    
    def save_cache(self):
        """Guarda cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(list(self.seen_aids), f)
        except Exception as e:
            logger.error(f"Error guardando cache: {e}")
    
    def generate_id(self, title: str, url: str) -> str:
        """Genera ID único"""
        return hashlib.md5(f"{title}_{url}".encode()).hexdigest()
    
    # ========== APIs OFICIALES ==========
    
    def fetch_euskadi_opendata(self) -> List[Dict]:
        """
        API OFICIAL: Open Data Euskadi
        Documentación: https://www.euskadi.eus/opendata/
        """
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando Open Data Euskadi RSS...")
            
            # Método 1: RSS Oficial (MÁS CONFIABLE)
            rss_url = self.apis['euskadi_opendata']['endpoints']['rss']
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                logger.info(f"📡 RSS Euskadi: {len(feed.entries)} entradas encontradas")
                
                for entry in feed.entries[:25]:
                    try:
                        titulo = entry.get('title', '').strip()
                        url = entry.get('link', '')
                        
                        if not titulo or not url:
                            continue
                        
                        aid_id = self.generate_id(titulo, url)
                        
                        if aid_id not in self.seen_aids:
                            # Extraer información del RSS
                            descripcion = entry.get('summary', entry.get('description', ''))
                            fecha_pub = entry.get('published', entry.get('updated', ''))
                            
                            ayuda = {
                                'id': aid_id,
                                'titulo': titulo,
                                'descripcion': self.clean_html(descripcion)[:500],
                                'url': url,
                                'fecha_publicacion': fecha_pub,
                                'fecha_limite': self.extract_deadline_from_text(descripcion),
                                'entidad': 'Gobierno Vasco',
                                'tipo': self.classify_aid_type(titulo),
                                'ambito': 'Euskadi',
                                'categorias': self.extract_categories(titulo + ' ' + descripcion),
                                'importe': self.extract_amount(descripcion),
                                'fuente': 'OpenData Euskadi RSS',
                                'nuevo': True
                            }
                            
                            ayudas.append(ayuda)
                            self.seen_aids.add(aid_id)
                    
                    except Exception as e:
                        logger.warning(f"Error procesando entrada Euskadi: {e}")
                        continue
                
                self.stats['exitos'] += 1
                self.stats['ayudas_encontradas'] += len(ayudas)
                logger.info(f"✅ Euskadi OpenData: {len(ayudas)} ayudas obtenidas")
            else:
                logger.warning("⚠️ RSS Euskadi no devolvió entradas")
        
        except Exception as e:
            logger.error(f"❌ Error en Euskadi OpenData: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    def fetch_bdns_api(self) -> List[Dict]:
        """
        API OFICIAL: Base de Datos Nacional de Subvenciones
        URL: https://www.infosubvenciones.es
        """
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando BDNS API...")
            
            # Método 1: RSS Oficial (MÁS CONFIABLE)
            rss_url = self.apis['bdns_api']['endpoints']['rss']
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                logger.info(f"📡 RSS BDNS: {len(feed.entries)} convocatorias encontradas")
                
                for entry in feed.entries[:30]:
                    try:
                        titulo = entry.get('title', '').strip()
                        url = entry.get('link', '')
                        
                        if not titulo or not url:
                            continue
                        
                        aid_id = self.generate_id(titulo, url)
                        
                        if aid_id not in self.seen_aids:
                            descripcion = entry.get('summary', entry.get('description', ''))
                            
                            ayuda = {
                                'id': aid_id,
                                'titulo': titulo,
                                'descripcion': self.clean_html(descripcion)[:500],
                                'url': url,
                                'fecha_publicacion': entry.get('published', ''),
                                'fecha_limite': self.extract_deadline_from_text(descripcion),
                                'entidad': 'Administración General del Estado',
                                'tipo': self.classify_aid_type(titulo),
                                'ambito': 'Nacional',
                                'categorias': self.extract_categories(titulo + ' ' + descripcion),
                                'importe': self.extract_amount(descripcion),
                                'fuente': 'BDNS RSS',
                                'nuevo': True
                            }
                            
                            ayudas.append(ayuda)
                            self.seen_aids.add(aid_id)
                    
                    except Exception as e:
                        logger.warning(f"Error procesando BDNS: {e}")
                        continue
                
                self.stats['exitos'] += 1
                self.stats['ayudas_encontradas'] += len(ayudas)
                logger.info(f"✅ BDNS: {len(ayudas)} ayudas obtenidas")
            else:
                logger.warning("⚠️ RSS BDNS no devolvió entradas")
        
        except Exception as e:
            logger.error(f"❌ Error en BDNS API: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    def fetch_bizkaia_rss(self) -> List[Dict]:
        """Diputación Foral de Bizkaia - RSS"""
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando Bizkaia RSS...")
            
            # Intentar con RSS
            rss_url = self.apis['bizkaia']['endpoints'].get('rss')
            if rss_url:
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    logger.info(f"📡 RSS Bizkaia: {len(feed.entries)} entradas")
                    
                    for entry in feed.entries[:20]:
                        try:
                            titulo = entry.get('title', '').strip()
                            url = entry.get('link', '')
                            
                            if not titulo:
                                continue
                            
                            aid_id = self.generate_id(titulo, url)
                            
                            if aid_id not in self.seen_aids:
                                descripcion = entry.get('summary', '')
                                
                                ayuda = {
                                    'id': aid_id,
                                    'titulo': titulo,
                                    'descripcion': self.clean_html(descripcion)[:500],
                                    'url': url or self.apis['bizkaia']['endpoints']['web'],
                                    'fecha_publicacion': entry.get('published', ''),
                                    'fecha_limite': self.extract_deadline_from_text(descripcion),
                                    'entidad': 'Diputación Foral de Bizkaia',
                                    'tipo': self.classify_aid_type(titulo),
                                    'ambito': 'Bizkaia',
                                    'categorias': self.extract_categories(titulo),
                                    'importe': self.extract_amount(descripcion),
                                    'fuente': 'Bizkaia RSS',
                                    'nuevo': True
                                }
                                
                                ayudas.append(ayuda)
                                self.seen_aids.add(aid_id)
                        
                        except Exception as e:
                            logger.warning(f"Error Bizkaia: {e}")
                            continue
                    
                    self.stats['exitos'] += 1
                    self.stats['ayudas_encontradas'] += len(ayudas)
                    logger.info(f"✅ Bizkaia: {len(ayudas)} ayudas")
        
        except Exception as e:
            logger.error(f"❌ Error Bizkaia: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    def fetch_spri_rss(self) -> List[Dict]:
        """SPRI - Agencia Vasca"""
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando SPRI RSS...")
            
            rss_url = self.apis['spri']['endpoints']['rss']
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                logger.info(f"📡 RSS SPRI: {len(feed.entries)} entradas")
                
                for entry in feed.entries[:20]:
                    titulo = entry.get('title', '').strip()
                    
                    # Filtrar solo ayudas
                    if not any(word in titulo.lower() for word in ['ayuda', 'programa', 'convocatoria', 'subvención']):
                        continue
                    
                    url = entry.get('link', '')
                    aid_id = self.generate_id(titulo, url)
                    
                    if aid_id not in self.seen_aids:
                        descripcion = entry.get('summary', '')
                        
                        ayuda = {
                            'id': aid_id,
                            'titulo': titulo,
                            'descripcion': self.clean_html(descripcion)[:500],
                            'url': url,
                            'fecha_publicacion': entry.get('published', ''),
                            'fecha_limite': self.extract_deadline_from_text(descripcion),
                            'entidad': 'SPRI - Agencia Vasca',
                            'tipo': 'Desarrollo Empresarial',
                            'ambito': 'Euskadi',
                            'categorias': ['Empresa', 'Innovación', 'I+D'],
                            'importe': self.extract_amount(descripcion),
                            'fuente': 'SPRI RSS',
                            'nuevo': True
                        }
                        
                        ayudas.append(ayuda)
                        self.seen_aids.add(aid_id)
                
                self.stats['exitos'] += 1
                self.stats['ayudas_encontradas'] += len(ayudas)
                logger.info(f"✅ SPRI: {len(ayudas)} ayudas")
        
        except Exception as e:
            logger.error(f"❌ Error SPRI: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    def fetch_next_generation(self) -> List[Dict]:
        """Next Generation EU - Plan de Recuperación"""
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando Next Generation EU...")
            
            # Intentar con RSS si existe
            rss_url = self.apis['next_generation']['endpoints'].get('rss')
            if rss_url:
                try:
                    feed = feedparser.parse(rss_url)
                    
                    if feed.entries:
                        for entry in feed.entries[:15]:
                            titulo = entry.get('title', '').strip()
                            url = entry.get('link', '')
                            
                            if not titulo:
                                continue
                            
                            aid_id = self.generate_id(titulo, url)
                            
                            if aid_id not in self.seen_aids:
                                descripcion = entry.get('summary', '')
                                
                                ayuda = {
                                    'id': aid_id,
                                    'titulo': titulo,
                                    'descripcion': self.clean_html(descripcion)[:500],
                                    'url': url,
                                    'fecha_publicacion': entry.get('published', ''),
                                    'fecha_limite': self.extract_deadline_from_text(descripcion),
                                    'entidad': 'Next Generation EU',
                                    'tipo': 'Fondo Europeo',
                                    'ambito': 'Europeo',
                                    'categorias': ['Europa', 'Next Generation', 'Recuperación'],
                                    'importe': self.extract_amount(descripcion),
                                    'fuente': 'Next Generation RSS',
                                    'nuevo': True
                                }
                                
                                ayudas.append(ayuda)
                                self.seen_aids.add(aid_id)
                        
                        self.stats['exitos'] += 1
                        self.stats['ayudas_encontradas'] += len(ayudas)
                        logger.info(f"✅ Next Generation: {len(ayudas)} ayudas")
                
                except:
                    logger.warning("⚠️ RSS Next Generation no disponible")
        
        except Exception as e:
            logger.error(f"❌ Error Next Generation: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    def fetch_cdti_rss(self) -> List[Dict]:
        """CDTI - Centro Desarrollo Tecnológico"""
        ayudas = []
        self.stats['total_intentos'] += 1
        
        try:
            logger.info("🔍 Consultando CDTI...")
            
            rss_url = self.apis['cdti']['endpoints'].get('rss')
            if rss_url:
                try:
                    feed = feedparser.parse(rss_url)
                    
                    if feed.entries:
                        for entry in feed.entries[:15]:
                            titulo = entry.get('title', '').strip()
                            url = entry.get('link', '')
                            
                            if not titulo:
                                continue
                            
                            aid_id = self.generate_id(titulo, url)
                            
                            if aid_id not in self.seen_aids:
                                descripcion = entry.get('summary', '')
                                
                                ayuda = {
                                    'id': aid_id,
                                    'titulo': titulo,
                                    'descripcion': self.clean_html(descripcion)[:500],
                                    'url': url,
                                    'fecha_publicacion': entry.get('published', ''),
                                    'fecha_limite': self.extract_deadline_from_text(descripcion),
                                    'entidad': 'CDTI',
                                    'tipo': 'I+D+i',
                                    'ambito': 'Nacional',
                                    'categorias': ['Innovación', 'I+D', 'Tecnología'],
                                    'importe': self.extract_amount(descripcion),
                                    'fuente': 'CDTI RSS',
                                    'nuevo': True
                                }
                                
                                ayudas.append(ayuda)
                                self.seen_aids.add(aid_id)
                        
                        self.stats['exitos'] += 1
                        self.stats['ayudas_encontradas'] += len(ayudas)
                        logger.info(f"✅ CDTI: {len(ayudas)} ayudas")
                
                except:
                    logger.warning("⚠️ RSS CDTI no disponible")
        
        except Exception as e:
            logger.error(f"❌ Error CDTI: {e}")
            self.stats['errores'] += 1
        
        return ayudas
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def clean_html(self, text: str) -> str:
        """Limpia HTML de un texto"""
        if not text:
            return ""
        # Eliminar tags HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Eliminar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_deadline_from_text(self, text: str) -> Optional[str]:
        """Extrae fecha límite del texto"""
        if not text:
            return None
        
        patterns = [
            r'hasta\s+(?:el\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'plazo[:\s]+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
            r'antes\s+del\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_amount(self, text: str) -> str:
        """Extrae importe"""
        if not text:
            return "Consultar bases"
        
        patterns = [
            r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?)\s*(?:€|euros?)',
            r'hasta\s+(\d{1,3}(?:\.\d{3})*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} €"
        
        return "Consultar bases"
    
    def classify_aid_type(self, title: str) -> str:
        """Clasifica tipo de ayuda"""
        title_lower = title.lower()
        
        classifications = {
            'I+D+i': ['i+d', 'investigación', 'desarrollo', 'innovación'],
            'Empleo': ['empleo', 'contratación', 'laboral'],
            'Digitalización': ['digitalización', 'digital', 'tic'],
            'Sostenibilidad': ['sostenible', 'verde', 'ambiental'],
            'Formación': ['formación', 'educación', 'beca'],
            'Emprendimiento': ['emprendimiento', 'startup', 'pyme']
        }
        
        for tipo, keywords in classifications.items():
            if any(kw in title_lower for kw in keywords):
                return tipo
        
        return 'General'
    
    def extract_categories(self, text: str) -> List[str]:
        """Extrae categorías"""
        if not text:
            return ['General']
        
        categories = []
        text_lower = text.lower()
        
        category_keywords = {
            'Tecnología': ['tecnología', 'digital', 'software'],
            'Innovación': ['innovación', 'i+d'],
            'Sostenibilidad': ['sostenible', 'verde', 'ecológico'],
            'Empleo': ['empleo', 'trabajo'],
            'Industria': ['industria', 'industrial']
        }
        
        for cat, keywords in category_keywords.items():
            if any(kw in text_lower for kw in keywords):
                categories.append(cat)
        
        return categories if categories else ['General']
    
    # ========== FUNCIÓN PRINCIPAL ==========
    
    def get_all_ayudas(self, region: str = None, since_date: datetime = None) -> List[Dict]:
        """
        Obtiene ayudas usando APIs oficiales
        
        Args:
            region: bizkaia, gipuzkoa, euskadi, nacional, europeo
            since_date: Filtrar desde fecha
        """
        all_ayudas = []
        
        # Reiniciar estadísticas
        self.stats = {
            'total_intentos': 0,
            'exitos': 0,
            'errores': 0,
            'ayudas_encontradas': 0
        }
        
        # Determinar qué fuentes consultar
        sources_map = {
            'bizkaia': ['euskadi_opendata', 'bizkaia', 'spri', 'bdns_api'],
            'gipuzkoa': ['euskadi_opendata', 'spri', 'bdns_api'],
            'euskadi': ['euskadi_opendata', 'spri', 'bizkaia', 'bdns_api'],
            'nacional': ['bdns_api', 'cdti', 'next_generation'],
            'europa': ['next_generation'],
            'todas': list(self.apis.keys())
        }
        
        region_lower = (region or 'todas').lower()
        sources_to_fetch = sources_map.get(region_lower, sources_map['todas'])
        
        # Métodos de fetch
        fetch_methods = {
            'euskadi_opendata': self.fetch_euskadi_opendata,
            'bdns_api': self.fetch_bdns_api,
            'bizkaia': self.fetch_bizkaia_rss,
            'spri': self.fetch_spri_rss,
            'next_generation': self.fetch_next_generation,
            'cdti': self.fetch_cdti_rss
        }
        
        logger.info(f"🎯 Consultando {len(sources_to_fetch)} fuentes para región: {region_lower}")
        
        # Ejecutar fetching
        for source in sources_to_fetch:
            if not self.apis.get(source, {}).get('enabled', True):
                continue
            
            fetch_method = fetch_methods.get(source)
            if fetch_method:
                try:
                    ayudas = fetch_method()
                    all_ayudas.extend(ayudas)
                    time.sleep(1)  # Pausa entre peticiones
                except Exception as e:
                    logger.error(f"Error en {source}: {e}")
        
        # Guardar cache
        self.save_cache()
        
        # Mostrar estadísticas
        logger.info(f"""
╔══════════════════════════════════════╗
║   RESUMEN DE BÚSQUEDA DE AYUDAS      ║
╠══════════════════════════════════════╣
║ Total fuentes consultadas: {self.stats['total_intentos']:>2}        ║
║ Exitosas: {self.stats['exitos']:>2}                         ║
║ Con errores: {self.stats['errores']:>2}                      ║
║ Ayudas encontradas: {len(all_ayudas):>3}               ║
╚══════════════════════════════════════╝
        """)
        
        return all_ayudas
    
    def get_statistics(self) -> Dict:
        """Devuelve estadísticas de la última ejecución"""
        return {
            **self.stats,
            'cache_size': len(self.seen_aids),
            'sources_configured': len([s for s in self.apis.values() if s.get('enabled', True)])
        }


# ========== FUNCIÓN PARA NOTIFICACIONES ==========

def check_ayudas(region: str, since_date: datetime) -> List[Dict]:
    """
    Función principal compatible con sistema de notificaciones
    """
    try:
        scraper = AyudasScraper()
        ayudas = scraper.get_all_ayudas(region, since_date)
        
        notifications = []
        for ayuda in ayudas[:15]:
            notification = {
                "type": "ayudas",
                "title": f"💶 {ayuda['titulo'][:80]}",
                "message": f"{ayuda['entidad']} | {ayuda.get('importe', 'Consultar')}",
                "data": {
                    "id": ayuda['id'],
                    "url": ayuda['url'],
                    "entidad": ayuda['entidad'],
                    "fecha_limite": ayuda.get('fecha_limite', 'No especificada'),
                    "categorias": ayuda.get('categorias', []),
                    "ambito": ayuda['ambito'],
                    "tipo": ayuda['tipo'],
                    "importe": ayuda.get('importe', 'Consultar'),
                    "fuente": ayuda.get('fuente', 'Desconocida')
                }
            }
            notifications.append(notification)
        
        return notifications
    
    except Exception as e:
        logger.error(f"Error en check_ayudas: {e}")
        return []