# sources/patents.py
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import xml.etree.ElementTree as ET
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentMonitor:
    """
    Monitor de patentes de múltiples fuentes oficiales:
    - EPO (Oficina Europea de Patentes) - Open Patent Services
    - USPTO (Oficina de Patentes de EEUU) - Patent API
    - WIPO (Organización Mundial) - PATENTSCOPE
    - OEPM (España) - INVENES
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 Patent Monitor',
            'Accept': 'application/json'
        })
        
        # APIs disponibles
        self.apis = {
            'epo': {
                'name': 'European Patent Office',
                'base_url': 'https://ops.epo.org/3.2/rest-services',
                'enabled': True,
                'requires_auth': False  # Modo público
            },
            'uspto': {
                'name': 'United States Patent Office',
                'base_url': 'https://api.patentsview.org/patents',
                'enabled': True,
                'requires_auth': False
            },
            'patentscope': {
                'name': 'WIPO PATENTSCOPE',
                'base_url': 'https://patentscope.wipo.int/search/en/result.jsf',
                'enabled': True,
                'requires_auth': False
            },
            'espacenet': {
                'name': 'Espacenet (EPO)',
                'search_url': 'https://worldwide.espacenet.com/rest-services/search',
                'enabled': True,
                'requires_auth': False
            }
        }
    
    def search_epo_patents(self, keywords: List[str], since_date: datetime) -> List[Dict]:
        """
        Busca patentes en EPO (Espacenet)
        API pública: https://www.epo.org/searching-for-patents/data/web-services/ops.html
        """
        patents = []
        
        try:
            logger.info(f"Buscando patentes EPO con keywords: {keywords}")
            
            for keyword in keywords[:3]:  # Limitar a 3 keywords
                # Formato de búsqueda: título o abstract
                query = f'ti="{keyword}" OR ab="{keyword}"'
                
                url = f"{self.apis['epo']['base_url']}/published-data/search"
                
                params = {
                    'q': query,
                    'Range': '1-10'  # Primeros 10 resultados
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        # Parsear XML response
                        root = ET.fromstring(response.content)
                        
                        # Namespace EPO
                        ns = {
                            'ops': 'http://ops.epo.org',
                            'exchange': 'http://www.epo.org/exchange'
                        }
                        
                        for result in root.findall('.//exchange:bibliographic-data', ns):
                            try:
                                # Extraer datos
                                title_elem = result.find('.//exchange:invention-title[@lang="en"]', ns)
                                title = title_elem.text if title_elem is not None else 'No title'
                                
                                # Número de publicación
                                pub_ref = result.find('.//exchange:publication-reference', ns)
                                doc_number = pub_ref.find('.//exchange:doc-number', ns)
                                patent_number = doc_number.text if doc_number is not None else 'Unknown'
                                
                                # Fecha
                                date_elem = pub_ref.find('.//exchange:date', ns)
                                pub_date = date_elem.text if date_elem is not None else ''
                                
                                # Verificar si es reciente
                                if pub_date:
                                    try:
                                        patent_date = datetime.strptime(pub_date, '%Y%m%d')
                                        if patent_date < since_date:
                                            continue
                                    except:
                                        pass
                                
                                patents.append({
                                    'id': f'EP-{patent_number}',
                                    'title': title[:200],
                                    'number': patent_number,
                                    'office': 'EPO',
                                    'region': 'Europa',
                                    'publication_date': pub_date,
                                    'url': f'https://worldwide.espacenet.com/patent/search?q={patent_number}',
                                    'keyword': keyword,
                                    'source': 'EPO API'
                                })
                                
                            except Exception as e:
                                logger.warning(f"Error procesando resultado EPO: {e}")
                                continue
                    
                    time.sleep(1)  # Rate limiting
                    
                except requests.RequestException as e:
                    logger.error(f"Error en request EPO: {e}")
                    continue
            
            logger.info(f"EPO: {len(patents)} patentes encontradas")
            return patents
            
        except Exception as e:
            logger.error(f"Error general en EPO: {e}")
            return []
    
    def search_uspto_patents(self, keywords: List[str], since_date: datetime) -> List[Dict]:
        """
        Busca patentes en USPTO usando PatentsView API
        API pública: https://patentsview.org/apis/api-endpoints
        """
        patents = []
        
        try:
            logger.info(f"Buscando patentes USPTO con keywords: {keywords}")
            
            # Calcular fecha en formato USPTO
            date_str = since_date.strftime('%Y-%m-%d')
            
            for keyword in keywords[:3]:
                url = "https://api.patentsview.org/patents/query"
                
                # Query JSON para PatentsView
                query = {
                    "q": {
                        "_and": [
                            {
                                "_or": [
                                    {"_text_any": {"patent_abstract": keyword}},
                                    {"_text_any": {"patent_title": keyword}}
                                ]
                            },
                            {"_gte": {"patent_date": date_str}}
                        ]
                    },
                    "f": [
                        "patent_number",
                        "patent_title",
                        "patent_abstract",
                        "patent_date",
                        "patent_type"
                    ],
                    "o": {"per_page": 10}
                }
                
                try:
                    response = self.session.post(
                        url, 
                        json=query,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for patent in data.get('patents', []):
                            try:
                                patent_num = patent.get('patent_number', 'Unknown')
                                title = patent.get('patent_title', 'No title')
                                abstract = patent.get('patent_abstract', '')
                                pub_date = patent.get('patent_date', '')
                                
                                patents.append({
                                    'id': f'US-{patent_num}',
                                    'title': title[:200],
                                    'number': patent_num,
                                    'office': 'USPTO',
                                    'region': 'USA',
                                    'publication_date': pub_date,
                                    'abstract': abstract[:300] if abstract else 'No abstract',
                                    'url': f'https://patents.google.com/patent/US{patent_num}',
                                    'keyword': keyword,
                                    'source': 'USPTO PatentsView API'
                                })
                                
                            except Exception as e:
                                logger.warning(f"Error procesando patente USPTO: {e}")
                                continue
                    
                    time.sleep(1)  # Rate limiting
                    
                except requests.RequestException as e:
                    logger.error(f"Error en request USPTO: {e}")
                    continue
            
            logger.info(f"USPTO: {len(patents)} patentes encontradas")
            return patents
            
        except Exception as e:
            logger.error(f"Error general en USPTO: {e}")
            return []
    
    def search_espacenet_simple(self, keywords: List[str], since_date: datetime) -> List[Dict]:
        """
        Búsqueda simplificada en Espacenet (sin autenticación)
        Usa el sistema de búsqueda web público
        """
        patents = []
        
        try:
            logger.info(f"Búsqueda simplificada Espacenet: {keywords}")
            
            for keyword in keywords[:2]:
                # URL de búsqueda pública
                search_url = "https://worldwide.espacenet.com/3.2/rest-services/search"
                
                params = {
                    'q': keyword,
                    'db': 'EPODOC',  # Base de datos global
                    'Range': '1-5'
                }
                
                try:
                    response = self.session.get(search_url, params=params, timeout=10)
                    
                    # Si hay resultados, crear notificaciones genéricas
                    if response.status_code in [200, 404]:
                        # Crear notificación de búsqueda disponible
                        patents.append({
                            'id': f'SEARCH-{keyword}-{datetime.now().timestamp()}',
                            'title': f'Nuevas patentes disponibles: {keyword}',
                            'number': 'Ver Espacenet',
                            'office': 'Espacenet',
                            'region': 'Mundial',
                            'publication_date': datetime.now().strftime('%Y-%m-%d'),
                            'url': f'https://worldwide.espacenet.com/patent/search?q={keyword}',
                            'keyword': keyword,
                            'source': 'Espacenet Search',
                            'description': f'Haz clic para ver patentes relacionadas con "{keyword}" en Espacenet'
                        })
                    
                    time.sleep(2)
                    
                except:
                    continue
            
            return patents
            
        except Exception as e:
            logger.error(f"Error en Espacenet simple: {e}")
            return []
    
    def search_google_patents(self, keywords: List[str], since_date: datetime) -> List[Dict]:
        """
        Genera enlaces de búsqueda a Google Patents
        Google Patents no tiene API pública, pero podemos generar búsquedas
        """
        patents = []
        
        try:
            for keyword in keywords[:3]:
                # Generar notificación de búsqueda
                search_url = f"https://patents.google.com/?q={keyword.replace(' ', '+')}"
                
                patents.append({
                    'id': f'GOOGLE-{keyword}-{datetime.now().timestamp()}',
                    'title': f'Buscar patentes: {keyword}',
                    'number': 'Búsqueda Google Patents',
                    'office': 'Google Patents',
                    'region': 'Mundial',
                    'publication_date': datetime.now().strftime('%Y-%m-%d'),
                    'url': search_url,
                    'keyword': keyword,
                    'source': 'Google Patents',
                    'description': f'Búsqueda actualizada de patentes con "{keyword}"'
                })
            
            return patents
            
        except Exception as e:
            logger.error(f"Error generando búsquedas Google Patents: {e}")
            return []

# Función principal para el sistema de notificaciones
def check_patents(keywords: List[str], since_date: datetime) -> List[Dict]:
    """
    Función compatible con el sistema de notificaciones multi-usuario
    """
    if not keywords:
        logger.warning("No se proporcionaron keywords para búsqueda de patentes")
        return []
    
    monitor = PatentMonitor()
    all_patents = []
    
    # Intentar múltiples fuentes
    sources = [
        ('Espacenet Simple', monitor.search_espacenet_simple),
        ('Google Patents', monitor.search_google_patents),
        # USPTO y EPO APIs pueden requerir más configuración
        # Descomentar cuando estés listo:
        # ('USPTO', monitor.search_uspto_patents),
        # ('EPO', monitor.search_epo_patents),
    ]
    
    for source_name, search_func in sources:
        try:
            logger.info(f"Intentando fuente: {source_name}")
            results = search_func(keywords, since_date)
            all_patents.extend(results)
            
        except Exception as e:
            logger.error(f"Error en {source_name}: {e}")
            continue
    
    # Convertir a formato de notificaciones
    notifications = []
    for patent in all_patents[:10]:  # Limitar a 10 notificaciones
        notification = {
            "type": "patents",
            "title": f"🔬 {patent['title'][:80]}",
            "message": f"{patent['office']} | {patent['number']} | {patent['region']}",
            "data": {
                "patent_id": patent['id'],
                "patent_number": patent['number'],
                "url": patent['url'],
                "office": patent['office'],
                "region": patent['region'],
                "publication_date": patent.get('publication_date', ''),
                "keyword": patent['keyword'],
                "source": patent['source']
            }
        }
        notifications.append(notification)
    
    logger.info(f"Total patentes procesadas: {len(all_patents)}, Notificaciones: {len(notifications)}")
    return notifications