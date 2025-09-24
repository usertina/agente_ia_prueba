from datetime import datetime
import json
from typing import Dict
import os
import sys

# Agregar el directorio raíz al path para importar multi_user_notification_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from multi_user_notification_system import multi_user_system
except ImportError:
    multi_user_system = None

# Variable global para almacenar el user_id actual
_current_user_id = None

def set_current_user_id(user_id: str):
    """Establece el user_id actual desde main.py"""
    global _current_user_id
    _current_user_id = user_id

def get_current_user_id():
    """Obtiene el user_id actual"""
    global _current_user_id
    if _current_user_id:
        return _current_user_id
    # Fallback para desarrollo
    return "user_temp_123"

def run(command: str) -> str:
    """
    Herramienta para gestionar notificaciones de emails, patentes y papers científicos.
    
    Comandos disponibles:
    - config: configurar notificaciones
    - status: ver estado actual
    - start: iniciar monitoreo
    - stop: detener monitoreo
    - test: probar notificaciones
    - activar: activar tipos específicos de notificaciones
    - keywords: configurar palabras clave
    - categories: configurar categorías de papers
    """
    
    if not multi_user_system:
        return "❌ Error: Sistema de notificaciones no disponible"
    
    command = command.strip().lower()
    user_id = get_current_user_id()
    
    print(f"🔧 Notifications tool - User ID: {user_id}, Command: {command}")
    
    # Ver estado actual
    if command == "status":
        try:
            stats = multi_user_system.get_user_stats(user_id)
            config = stats['config']
            state = stats['state']
            
            result = "📊 **Estado de Notificaciones:**\n\n"
            result += f"🆔 Usuario: {user_id[:12]}...\n"
            result += f"📱 Dispositivo: {config.get('device_name', 'Desconocido')}\n\n"
            
            result += "**Configuración Actual:**\n"
            result += f"📧 Emails: {'✅ Activado' if config.get('email_notifications') else '❌ Desactivado'}\n"
            result += f"🔬 Patentes: {'✅ Activado' if config.get('patent_notifications') else '❌ Desactivado'}\n"
            result += f"📚 Papers: {'✅ Activado' if config.get('papers_notifications') else '❌ Desactivado'}\n\n"
            
            if config.get('patent_keywords'):
                result += f"🔍 Keywords patentes: {', '.join(config['patent_keywords'])}\n"
            
            if config.get('papers_keywords'):
                result += f"📖 Keywords papers: {', '.join(config['papers_keywords'])}\n"
            
            if config.get('papers_categories'):
                result += f"📂 Categorías papers: {', '.join(config['papers_categories'])}\n\n"
            
            result += "**Estadísticas:**\n"
            result += f"📧 Emails verificados: {state.get('email_count', 0)}\n"
            result += f"🔬 Patentes encontradas: {state.get('patent_count', 0)}\n"
            result += f"📚 Papers encontrados: {state.get('papers_count', 0)}\n"
            result += f"📊 Total notificaciones: {stats.get('total_notifications', 0)}\n"
            
            if state.get('last_patent_check'):
                result += f"⏰ Última verificación patentes: {state['last_patent_check'][:19]}\n"
            if state.get('last_papers_check'):
                result += f"⏰ Última verificación papers: {state['last_papers_check'][:19]}\n"
            
            return result
            
        except Exception as e:
            print(f"Error en status: {e}")
            return f"❌ Error obteniendo estado: {e}"
    
    # Debug - mostrar información del usuario
    elif command == "debug":
        try:
            print(f"🔍 Debug para usuario: {user_id}")
            
            # Verificar que el usuario existe en la BD
            with multi_user_system.get_db_connection() as conn:
                user_exists = conn.execute(
                    "SELECT user_id, config FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
            
            if not user_exists:
                return f"❌ **Usuario no encontrado en la base de datos**\n\nUser ID: {user_id}\n\nIntenta recargar la página para registrarte correctamente."
            
            config = multi_user_system.get_user_config(user_id)
            active_users = multi_user_system.get_active_users(hours=24)
            
            result = f"🔍 **Debug Information:**\n\n"
            result += f"**Usuario:**\n"
            result += f"• User ID: {user_id}\n"
            result += f"• Existe en BD: {'✅ Sí' if user_exists else '❌ No'}\n"
            result += f"• Configuración cargada: {'✅ Sí' if config else '❌ No'}\n"
            result += f"• Es activo: {'✅ Sí' if user_id in active_users else '❌ No'}\n\n"
            
            result += f"**Sistema:**\n"
            result += f"• Usuarios activos: {len(active_users)}\n"
            result += f"• Sistema ejecutándose: {'✅ Sí' if multi_user_system.running else '❌ No'}\n\n"
            
            if config:
                result += f"**Configuración actual:**\n"
                result += f"• Emails: {'✅' if config.get('email_notifications') else '❌'}\n"
                result += f"• Patentes: {'✅' if config.get('patent_notifications') else '❌'}\n"
                result += f"• Papers: {'✅' if config.get('papers_notifications') else '❌'}\n"
                
                if config.get('patent_keywords'):
                    result += f"• Keywords patentes: {', '.join(config['patent_keywords'])}\n"
                if config.get('papers_keywords'):
                    result += f"• Keywords papers: {', '.join(config['papers_keywords'])}\n"
                if config.get('papers_categories'):
                    result += f"• Categorías papers: {', '.join(config['papers_categories'])}\n"
            else:
                result += "**❌ No hay configuración disponible**\n"
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error en debug: {e}"
    
    # Activar notificaciones específicas
    elif command == "activar emails":
        try:
            print(f"🔧 Activando emails para {user_id[:12]}...")
            config = {"email_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            if success:
                print(f"✅ Emails activados para {user_id[:12]}")
                return "✅ Notificaciones de email activadas.\n\n📧 Nota: Requiere configuración adicional de Gmail API."
            else:
                print(f"❌ Error activando emails para {user_id[:12]}")
                return "❌ Error al activar notificaciones de email. Intenta con 'debug' para más información."
        except Exception as e:
            print(f"❌ Excepción activando emails: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error: {e}"
    
    elif command == "activar patentes":
        try:
            print(f"🔧 Activando patentes para {user_id[:12]}...")
            config = {"patent_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            if success:
                print(f"✅ Patentes activadas para {user_id[:12]}")
                return "✅ Notificaciones de patentes activadas.\n\n🔍 Usa 'keywords patentes: término1, término2' para configurar búsquedas."
            else:
                print(f"❌ Error activando patentes para {user_id[:12]}")
                return "❌ Error al activar notificaciones de patentes. Intenta con 'debug' para más información."
        except Exception as e:
            print(f"❌ Excepción activando patentes: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error: {e}"
    
    elif command == "activar papers":
        try:
            print(f"🔧 Activando papers para {user_id[:12]}...")
            config = {"papers_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            if success:
                print(f"✅ Papers activados para {user_id[:12]}")
                return "✅ Notificaciones de papers científicos activadas.\n\n📚 Usa 'keywords papers: término1, término2' para búsquedas específicas."
            else:
                print(f"❌ Error activando papers para {user_id[:12]}")
                return "❌ Error al activar notificaciones de papers. Intenta con 'debug' para más información."
        except Exception as e:
            print(f"❌ Excepción activando papers: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error: {e}"
    
    # Configurar keywords para patentes
    elif command.startswith("keywords patentes:"):
        try:
            keywords_str = command.split(":", 1)[1].strip()
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            if not keywords:
                return "❌ Debes proporcionar al menos una palabra clave.\nEjemplo: 'keywords patentes: inteligencia artificial, blockchain'"
            
            config = {"patent_keywords": keywords, "patent_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            
            if success:
                return f"✅ Keywords de patentes configuradas: {', '.join(keywords)}\n\n🔬 Notificaciones de patentes activadas automáticamente."
            else:
                return "❌ Error al configurar keywords de patentes"
        except Exception as e:
            return f"❌ Error: {e}"
    
    # Configurar keywords para papers
    elif command.startswith("keywords papers:"):
        try:
            keywords_str = command.split(":", 1)[1].strip()
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            if not keywords:
                return "❌ Debes proporcionar al menos una palabra clave.\nEjemplo: 'keywords papers: machine learning, neural networks'"
            
            config = {"papers_keywords": keywords, "papers_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            
            if success:
                return f"✅ Keywords de papers configuradas: {', '.join(keywords)}\n\n📚 Notificaciones de papers activadas automáticamente."
            else:
                return "❌ Error al configurar keywords de papers"
        except Exception as e:
            return f"❌ Error: {e}"
    
    # Configurar categorías de papers
    elif command.startswith("categories:"):
        try:
            categories_str = command.split(":", 1)[1].strip()
            categories = [c.strip() for c in categories_str.split(",") if c.strip()]
            
            if not categories:
                return get_categories_help()
            
            # Validar categorías
            valid_categories = validate_categories(categories)
            if not valid_categories:
                return "❌ Categorías inválidas.\n\n" + get_categories_help()
            
            config = {"papers_categories": valid_categories, "papers_notifications": True}
            success = multi_user_system.update_user_config(user_id, config)
            
            if success:
                return f"✅ Categorías de papers configuradas: {', '.join(valid_categories)}\n\n📚 Notificaciones de papers activadas automáticamente."
            else:
                return "❌ Error al configurar categorías de papers"
        except Exception as e:
            return f"❌ Error: {e}"
    
    # Probar notificaciones
    elif command == "test" or command == "probar":
        try:
            # Asegurarse de que el usuario está registrado
            config = multi_user_system.get_user_config(user_id)
            device_name = config.get('device_name', 'Dispositivo Desconocido')
            
            # Crear diferentes tipos de notificaciones de prueba
            test_notifications = [
                {
                    'type': 'test',
                    'title': '🧪 Notificación de Prueba - Sistema',
                    'message': f'Sistema funcionando correctamente en {device_name}',
                    'data': {
                        'test': True, 
                        'timestamp': multi_user_system._get_current_timestamp(),
                        'user_id': user_id[:8],
                        'device_name': device_name,
                        'url': 'https://github.com'
                    }
                },
                {
                    'type': 'paper',
                    'title': '📚 Notificación de Prueba - Paper Científico',
                    'message': 'Attention Is All You Need: A groundbreaking paper on transformer architecture...',
                    'data': {
                        'test': True,
                        'title': 'Attention Is All You Need',
                        'authors': ['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar'],
                        'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
                        'published': multi_user_system._get_current_timestamp(),
                        'url': 'https://arxiv.org/abs/1706.03762',
                        'keyword': 'test',
                        'category': 'cs.AI'
                    }
                },
                {
                    'type': 'patent',
                    'title': '🔬 Notificación de Prueba - Patente',
                    'message': 'Neural Network Processing Method: A new approach to artificial intelligence processing...',
                    'data': {
                        'test': True,
                        'title': 'Neural Network Processing Method',
                        'app_number': 'US20240TEST',
                        'app_date': datetime.now().strftime('%Y-%m-%d'),
                        'keyword': 'test',
                        'inventors': ['Test Inventor', 'Demo Creator'],
                        'url': 'https://patents.uspto.gov/patent/search'
                    }
                }
            ]
            
            # Enviar todas las notificaciones de prueba
            for notif in test_notifications:
                multi_user_system.add_notification(
                    user_id,
                    notif['type'],
                    notif['title'],
                    notif['message'],
                    notif['data']
                )
            
            return f"✅ {len(test_notifications)} notificaciones de prueba enviadas para usuario {user_id[:8]}.\n\n📱 Deberías verlas en tu navegador. Puedes hacer click en ellas para abrir los enlaces.\n\n🔗 Tipos enviados:\n• Sistema (GitHub)\n• Paper científico (arXiv)\n• Patente (USPTO)"
        except Exception as e:
            print(f"Error en test notification: {e}")
            return f"❌ Error enviando notificación de prueba: {e}"
    
    # Comandos de control del sistema
    elif command == "start" or command == "iniciar":
        return (
            "🚀 **El sistema de monitoreo se ejecuta automáticamente en el servidor.**\n\n"
            "✅ Verificaciones activas para usuarios configurados:\n"
            "• 📧 Emails: Cada 5 minutos (si está configurado Gmail API)\n"
            "• 🔬 Patentes: Cada hora\n"
            "• 📚 Papers: Cada 30 minutos\n\n"
            "💡 Solo usuarios con notificaciones activadas son monitoreados.\n"
            "📱 Las notificaciones llegan automáticamente a tu dispositivo."
        )
    
    elif command == "stop" or command == "detener":
        try:
            # Desactivar todas las notificaciones del usuario
            config = {
                "email_notifications": False,
                "patent_notifications": False,
                "papers_notifications": False
            }
            success = multi_user_system.update_user_config(user_id, config)
            
            if success:
                return "⏹️ Notificaciones desactivadas para tu dispositivo.\n\n📱 Ya no recibirás alertas automáticas."
            else:
                return "❌ Error al desactivar notificaciones"
        except Exception as e:
            return f"❌ Error: {e}"
    
    else:
        return get_main_help()

def get_main_help():
    return (
        "🔔 **Sistema de Notificaciones Inteligentes**\n\n"
        "**Tipos de Notificaciones:**\n"
        "📧 **Emails** - Gmail API (requiere configuración)\n"
        "🔬 **Patentes** - USPTO (Estados Unidos)\n"
        "📚 **Papers Científicos** - arXiv (matemáticas, física, CS, etc.)\n\n"
        "**Comandos Principales:**\n\n"
        "**Activación:**\n"
        "• `activar emails` - Activar notificaciones de email\n"
        "• `activar patentes` - Activar notificaciones de patentes\n"
        "• `activar papers` - Activar notificaciones de papers\n\n"
        "**Configuración:**\n"
        "• `keywords patentes: AI, blockchain` - Buscar patentes específicas\n"
        "• `keywords papers: machine learning, AI` - Buscar papers específicos\n"
        "• `categories: cs.AI, cs.LG, physics.gen-ph` - Categorías de arXiv\n\n"
        "**Información:**\n"
        "• `status` - Ver estado actual y estadísticas\n"
        "• `test` - Enviar notificación de prueba\n"
        "• `debug` - Información de depuración\n"
        "• `stop` - Desactivar todas las notificaciones\n\n"
        "**Ejemplo de Configuración Completa:**\n"
        "1. `activar patentes`\n"
        "2. `keywords patentes: inteligencia artificial, blockchain`\n"
        "3. `activar papers`\n"
        "4. `keywords papers: neural networks, deep learning`\n"
        "5. `categories: cs.AI, cs.LG, cs.CV`\n"
        "6. `test`"
    )

def get_categories_help():
    return (
        "📚 **Categorías de arXiv Disponibles:**\n\n"
        "**Computer Science:**\n"
        "• `cs.AI` - Inteligencia Artificial\n"
        "• `cs.LG` - Machine Learning\n"
        "• `cs.CV` - Computer Vision\n"
        "• `cs.CL` - Procesamiento de Lenguaje Natural\n"
        "• `cs.RO` - Robótica\n"
        "• `cs.CR` - Criptografía y Seguridad\n\n"
        "**Física:**\n"
        "• `physics.gen-ph` - Física General\n"
        "• `cond-mat` - Materia Condensada\n"
        "• `quant-ph` - Física Cuántica\n\n"
        "**Matemáticas:**\n"
        "• `math.GM` - Matemáticas Generales\n"
        "• `math.ST` - Estadística\n\n"
        "**Medicina/Biología:**\n"
        "• `q-bio.BM` - Biomoléculas\n"
        "• `q-bio.GN` - Genómica\n\n"
        "**Ejemplo:**\n"
        "`categories: cs.AI, cs.LG, cs.CV, physics.gen-ph`"
    )

def validate_categories(categories):
    """Valida que las categorías sean válidas de arXiv"""
    valid_cats = {
        # Computer Science
        'cs.ai', 'cs.lg', 'cs.cv', 'cs.cl', 'cs.ro', 'cs.cr', 'cs.db', 'cs.dc',
        'cs.ds', 'cs.gt', 'cs.hc', 'cs.ir', 'cs.it', 'cs.lo', 'cs.ms', 'cs.ne',
        'cs.ni', 'cs.oh', 'cs.os', 'cs.pf', 'cs.pl', 'cs.sc', 'cs.sd', 'cs.se',
        'cs.si', 'cs.sy',
        # Physics
        'physics.gen-ph', 'cond-mat', 'quant-ph', 'hep-ph', 'hep-th', 'gr-qc',
        'astro-ph', 'nucl-th', 'physics.atom-ph', 'physics.bio-ph',
        # Math
        'math.gm', 'math.st', 'math.pr', 'math.na', 'math.oc', 'math.co',
        # Biology
        'q-bio.bm', 'q-bio.gn', 'q-bio.mn', 'q-bio.nc', 'q-bio.pe', 'q-bio.qm',
        # Economics
        'econ.em', 'econ.th',
        # Statistics
        'stat.ap', 'stat.co', 'stat.ml', 'stat.th'
    }
    
    validated = []
    for cat in categories:
        cat_lower = cat.lower().strip()
        if cat_lower in valid_cats:
            validated.append(cat_lower)
        else:
            # Intentar encontrar coincidencias parciales
            matches = [v for v in valid_cats if cat_lower in v or v in cat_lower]
            if matches:
                validated.append(matches[0])
    
    return list(set(validated))  # Remover duplicados