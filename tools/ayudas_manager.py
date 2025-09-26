import json
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.ayudas_real import AyudasScraper
from multi_user_notification_system import multi_user_system

class AyudasManager:
    """
    Gestor de ayudas y subvenciones con comandos avanzados
    """
    
    def __init__(self):
        self.scraper = AyudasScraper()
    
    def run(self, command: str, user_id: str) -> str:
        """Procesa comandos de ayudas"""
        command = command.strip().lower()
        
        if command == "ayudas buscar":
            return self.search_ayudas(user_id)
        elif command.startswith("ayudas filtrar"):
            return self.filter_ayudas(command, user_id)
        elif command == "ayudas activar":
            return self.activate_notifications(user_id)
        elif command == "ayudas test":
            return self.test_scraping()
        elif command.startswith("ayudas region:"):
            return self.set_region(command, user_id)
        elif command.startswith("ayudas categorias:"):
            return self.set_categories(command, user_id)
        else:
            return self.show_help()
    
    def search_ayudas(self, user_id: str) -> str:
        """Busca ayudas actuales"""
        config = multi_user_system.get_user_config(user_id)
        region = config.get('region', 'Euskadi')
        
        ayudas = self.scraper.get_all_ayudas(region)
        
        if not ayudas:
            return "📭 No se encontraron ayudas nuevas"
        
        result = f"💶 **AYUDAS DISPONIBLES EN {region.upper()}**\n\n"
        
        for i, ayuda in enumerate(ayudas[:10], 1):
            result += f"**{i}. {ayuda['titulo']}**\n"
            result += f"   🏛️ {ayuda['entidad']}\n"
            result += f"   💰 Importe: {ayuda.get('importe', 'Consultar')}\n"
            result += f"   📅 Límite: {ayuda.get('fecha_limite', 'No especificado')}\n"
            result += f"   🔗 [Ver más]({ayuda['url']})\n"
            result += f"   🏷️ {', '.join(ayuda.get('categorias', ['General']))}\n\n"
        
        return result
    
    def filter_ayudas(self, command: str, user_id: str) -> str:
        """Filtra ayudas por criterios"""
        # Extraer filtro
        if ":" in command:
            filter_type = command.split(":")[1].strip()
        else:
            filter_type = "todas"
        
        config = multi_user_system.get_user_config(user_id)
        region = config.get('region', 'Euskadi')
        
        ayudas = self.scraper.get_all_ayudas(region)
        
        # Aplicar filtro
        if filter_type != "todas":
            ayudas = [a for a in ayudas if filter_type.lower() in a.get('tipo', '').lower() 
                     or any(filter_type.lower() in cat.lower() for cat in a.get('categorias', []))]
        
        if not ayudas:
            return f"📭 No se encontraron ayudas con filtro '{filter_type}'"
        
        result = f"🔍 **AYUDAS FILTRADAS: {filter_type.upper()}**\n\n"
        
        for i, ayuda in enumerate(ayudas[:5], 1):
            result += f"**{i}. {ayuda['titulo']}**\n"
            result += f"   Tipo: {ayuda['tipo']} | {ayuda['entidad']}\n"
            result += f"   🔗 {ayuda['url']}\n\n"
        
        return result
    
    def activate_notifications(self, user_id: str) -> str:
        """Activa notificaciones de ayudas"""
        config = {
            "ayudas_notifications": True,
            "ayudas_check_interval": 86400  # Una vez al día
        }
        
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return "✅ Notificaciones de ayudas activadas. Recibirás alertas diarias de nuevas subvenciones."
        else:
            return "❌ Error activando notificaciones"
    
    def set_region(self, command: str, user_id: str) -> str:
        """Configura la región para las ayudas"""
        region = command.split(":")[1].strip()
        
        valid_regions = ['euskadi', 'gipuzkoa', 'bizkaia', 'araba', 'nacional', 'todas']
        
        if region not in valid_regions:
            return f"❌ Región no válida. Opciones: {', '.join(valid_regions)}"
        
        config = {"region": region}
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return f"✅ Región configurada: {region}"
        else:
            return "❌ Error configurando región"
    
    def set_categories(self, command: str, user_id: str) -> str:
        """Configura categorías de interés"""
        categories = command.split(":")[1].strip().split(",")
        categories = [c.strip() for c in categories]
        
        config = {"ayudas_categories": categories}
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return f"✅ Categorías configuradas: {', '.join(categories)}"
        else:
            return "❌ Error configurando categorías"
    
    def test_scraping(self) -> str:
        """Prueba el sistema de scraping"""
        result = "🧪 **TEST DEL SISTEMA DE AYUDAS**\n\n"
        
        sources_status = {
            'Euskadi RSS': False,
            'Gipuzkoa API': False,
            'BDNS Estado': False,
            'SPRI': False
        }
        
        # Test Euskadi
        try:
            ayudas = self.scraper.scrape_euskadi_rss()
            if ayudas:
                sources_status['Euskadi RSS'] = True
        except:
            pass
        
        # Test Gipuzkoa
        try:
            ayudas = self.scraper.scrape_gipuzkoa_api()
            if ayudas:
                sources_status['Gipuzkoa API'] = True
        except:
            pass
        
        # Test Estado
        try:
            ayudas = self.scraper.scrape_estado_bdns()
            if ayudas:
                sources_status['BDNS Estado'] = True
        except:
            pass
        
        # Test SPRI
        try:
            ayudas = self.scraper.scrape_spri()
            if ayudas:
                sources_status['SPRI'] = True
        except:
            pass
        
        for source, status in sources_status.items():
            icon = "✅" if status else "❌"
            result += f"{icon} {source}: {'Funcionando' if status else 'Error'}\n"
        
        total_working = sum(sources_status.values())
        result += f"\n📊 **Resumen:** {total_working}/{len(sources_status)} fuentes operativas"
        
        return result
    
    def show_help(self) -> str:
        """Muestra ayuda del sistema"""
        return """
💶 **SISTEMA DE AYUDAS Y SUBVENCIONES**

**Comandos disponibles:**

- `ayudas buscar` - Buscar ayudas actuales
- `ayudas filtrar: [tipo]` - Filtrar por tipo/categoría
- `ayudas activar` - Activar notificaciones
- `ayudas region: [region]` - Configurar región
- `ayudas categorias: cat1, cat2` - Configurar intereses
- `ayudas test` - Probar sistema de scraping

**Regiones disponibles:**
- euskadi, gipuzkoa, bizkaia, araba, nacional, todas

**Categorías:**
- Tecnología, Innovación, Sostenibilidad
- Empleo, Formación, Industria
- Comercio, Turismo, Cultura, Social

**Ejemplo de uso:**
1. `ayudas region: gipuzkoa`
2. `ayudas categorias: tecnología, innovación`
3. `ayudas buscar`
4. `ayudas activar`
"""

# Instancia global
ayudas_manager = AyudasManager()

def run(prompt: str) -> str:
    """Función principal compatible con el sistema"""
    # Simular user_id si no está disponible
    # En producción, esto debería venir del contexto
    user_id = "user_default"
    
    # Si tenemos acceso al user_id real desde notifications
    try:
        from tools.notifications import get_current_user_id
        user_id = get_current_user_id()
    except:
        pass
    
    return ayudas_manager.run(prompt, user_id)