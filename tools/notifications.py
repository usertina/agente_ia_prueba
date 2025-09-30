from datetime import datetime
import json
import os
import sys

# Agregar el directorio raíz al path para importar multi_user_notification_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from multi_user_notification_system import multi_user_system
except ImportError:
    multi_user_system = None
    print("⚠️ Warning: multi_user_notification_system no disponible")

# Variable global para almacenar el user_id actual
_current_user_id = None

def set_current_user_id(user_id: str):
    """Establece el user_id actual desde main.py"""
    global _current_user_id
    _current_user_id = user_id
    print(f"🔑 User ID establecido en notifications.py: {user_id[:12]}...")

def get_current_user_id():
    """Obtiene el user_id actual"""
    global _current_user_id
    if _current_user_id:
        return _current_user_id
    # Fallback para desarrollo
    print("⚠️ Warning: user_id no establecido, usando fallback")
    return "user_temp_fallback"

def run(command: str) -> str:
    """
    Herramienta para gestionar notificaciones de emails, patentes, papers y ayudas.
    """
    
    if not multi_user_system:
        return "❌ Error: Sistema de notificaciones no disponible"
    
    command = command.strip().lower()
    user_id = get_current_user_id()
    
    print(f"🔧 Notifications tool - User ID: {user_id[:12]}..., Command: {command}")

    # Comandos principales
    if command == "status":
        return _handle_status(user_id)
    elif command == "debug":
        return _handle_debug(user_id)
    elif command == "resumen":
        return _handle_resumen(user_id)
    elif command.startswith("listar"):
        return _handle_listar(user_id, command)
    elif command.startswith("borrar"):
        return _handle_borrar(user_id, command)
    elif command.startswith("activar"):
        return _handle_activar(user_id, command)
    elif command.startswith("desactivar"):
        return _handle_desactivar(user_id, command)
    elif command.startswith("keywords patentes:"):
        return _handle_keywords_patentes(user_id, command)
    elif command.startswith("keywords papers:"):
        return _handle_keywords_papers(user_id, command)
    elif command.startswith("categories:"):
        return _handle_categories(user_id, command)
    elif command in ["test", "probar"]:
        return _handle_test(user_id)
    elif command in ["start", "iniciar"]:
        return _handle_start(user_id)
    elif command in ["stop", "detener"]:
        return _handle_stop(user_id)
    else:
        return get_main_help()

# -----------------------------------------------
# Handlers internos
# -----------------------------------------------

def _handle_status(user_id: str) -> str:
    """Muestra el estado completo del sistema de notificaciones"""
    try:
        stats = multi_user_system.get_user_stats(user_id)
        config = stats.get('config', {})
        state = stats.get('state', {})

        result = "📊 **ESTADO DE NOTIFICACIONES**\n\n"
        result += f"🆔 Usuario: {user_id[:12]}...\n"
        result += f"📱 Dispositivo: {config.get('device_name', 'Desconocido')}\n\n"

        result += "**⚙️ Configuración Actual:**\n"
        result += f"📧 Emails: {'✅ Activado' if config.get('email_notifications') else '❌ Desactivado'}\n"
        result += f"🔬 Patentes: {'✅ Activado' if config.get('patent_notifications') else '❌ Desactivado'}\n"
        result += f"📚 Papers: {'✅ Activado' if config.get('papers_notifications') else '❌ Desactivado'}\n"
        result += f"💶 Ayudas: {'✅ Activado' if config.get('ayudas_notifications') else '❌ Desactivado'}\n\n"

        # Mostrar keywords si existen
        if config.get('patent_keywords'):
            result += f"🔍 Keywords patentes: {', '.join(config['patent_keywords'])}\n"
        if config.get('papers_keywords'):
            result += f"📖 Keywords papers: {', '.join(config['papers_keywords'])}\n"
        if config.get('papers_categories'):
            result += f"📂 Categorías papers: {', '.join(config['papers_categories'])}\n"
        if config.get('region'):
            result += f"🗺️ Región ayudas: {config['region']}\n"
        
        if any([config.get('patent_keywords'), config.get('papers_keywords'), 
                config.get('papers_categories'), config.get('region')]):
            result += "\n"

        result += "**📊 Estadísticas:**\n"
        result += f"📧 Emails verificados: {state.get('email_count', 0)}\n"
        result += f"🔬 Patentes encontradas: {state.get('patent_count', 0)}\n"
        result += f"📚 Papers encontrados: {state.get('papers_count', 0)}\n"
        result += f"💶 Ayudas encontradas: {state.get('ayudas_count', 0)}\n"
        result += f"📊 Total notificaciones: {stats.get('total_notifications', 0)}\n\n"

        # Última verificación
        last_checks = []
        if state.get('last_patent_check'):
            last_checks.append(f"🔬 Patentes: {state['last_patent_check'][:19]}")
        if state.get('last_papers_check'):
            last_checks.append(f"📚 Papers: {state['last_papers_check'][:19]}")
        if state.get('last_email_check'):
            last_checks.append(f"📧 Emails: {state['last_email_check'][:19]}")
        if state.get('last_ayudas_check'):
            last_checks.append(f"💶 Ayudas: {state['last_ayudas_check'][:19]}")
        
        if last_checks:
            result += "**⏰ Última verificación:**\n"
            for check in last_checks:
                result += f"• {check}\n"
            result += "\n"

        result += "💡 **Comandos útiles:**\n"
        result += "• `activar papers` - Activar tipo de notificación\n"
        result += "• `keywords papers: AI, ML` - Configurar keywords\n"
        result += "• `listar` - Ver notificaciones recientes\n"
        result += "• `test` - Enviar notificación de prueba"

        return result
    except Exception as e:
        print(f"❌ Error en status: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error obteniendo estado: {e}"

def _handle_debug(user_id: str) -> str:
    """Información de debug completa"""
    try:
        # Verificar usuario en BD
        with multi_user_system.get_db_connection() as conn:
            user_exists = conn.execute(
                "SELECT user_id, config, created_at, last_active FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()

        config = multi_user_system.get_user_config(user_id)
        active_users = multi_user_system.get_active_users(hours=24)

        result = f"🔍 **DEBUG INFORMATION**\n\n"
        result += f"**👤 Usuario:**\n"
        result += f"• User ID: {user_id}\n"
        result += f"• Existe en BD: {'✅ Sí' if user_exists else '❌ No'}\n"
        
        if user_exists:
            user_dict = dict(user_exists)
            result += f"• Creado: {user_dict.get('created_at', 'N/A')[:19]}\n"
            result += f"• Última actividad: {user_dict.get('last_active', 'N/A')[:19]}\n"
        
        result += f"• Configuración cargada: {'✅ Sí' if config else '❌ No'}\n"
        result += f"• Es activo (24h): {'✅ Sí' if user_id in active_users else '❌ No'}\n\n"

        result += f"**🌐 Sistema:**\n"
        result += f"• Usuarios activos (24h): {len(active_users)}\n"
        result += f"• Sistema ejecutándose: {'✅ Sí' if multi_user_system.running else '❌ No'}\n"
        result += f"• Base de datos: {multi_user_system.db_file}\n\n"

        if config:
            result += f"**⚙️ Configuración actual:**\n"
            result += f"• Emails: {'✅' if config.get('email_notifications') else '❌'}\n"
            result += f"• Patentes: {'✅' if config.get('patent_notifications') else '❌'}\n"
            result += f"• Papers: {'✅' if config.get('papers_notifications') else '❌'}\n"
            result += f"• Ayudas: {'✅' if config.get('ayudas_notifications') else '❌'}\n"
            
            if config.get('patent_keywords'):
                result += f"• Keywords patentes: {', '.join(config['patent_keywords'][:3])}{'...' if len(config['patent_keywords']) > 3 else ''}\n"
            if config.get('papers_keywords'):
                result += f"• Keywords papers: {', '.join(config['papers_keywords'][:3])}{'...' if len(config['papers_keywords']) > 3 else ''}\n"
            if config.get('papers_categories'):
                result += f"• Categorías papers: {', '.join(config['papers_categories'][:3])}\n"
            if config.get('region'):
                result += f"• Región: {config['region']}\n"
        else:
            result += "**❌ No hay configuración disponible**\n"
        
        result += "\n💡 Si hay problemas, contacta al administrador con esta información."

        return result
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error en debug: {e}\n{error_trace}")
        return f"❌ Error en debug: {e}\n\nVer logs del servidor para más detalles."
    
def _handle_resumen(user_id: str) -> str:
    """Mostrar resumen de notificaciones"""
    try:
        summary = multi_user_system.get_notification_summary(user_id)
        
        result = f"📊 **RESUMEN DE NOTIFICACIONES**\n\n"
        result += f"📈 **Total:** {summary['total']} notificaciones\n\n"
        
        if summary['by_type']:
            result += "**📋 Por tipo:**\n"
            for notif_type, counts in summary['by_type'].items():
                emoji = {
                    "papers": "📚", 
                    "patents": "🔬", 
                    "emails": "📧", 
                    "ayudas": "💶", 
                    "test": "🧪"
                }.get(notif_type, "📄")
                
                result += f"{emoji} **{notif_type.capitalize()}:** {counts['total']} total"
                if counts['pending'] > 0:
                    result += f" ({counts['pending']} pendientes)"
                result += f" | {counts['delivered']} entregadas\n"
        else:
            result += "📭 No hay notificaciones registradas.\n"
        
        result += f"\n💡 **Comandos útiles:**\n"
        result += f"• `listar` - Ver las notificaciones\n"
        result += f"• `listar [tipo]` - Filtrar por tipo\n"
        result += f"• `borrar todo` - Eliminar todas"
        
        return result
    except Exception as e:
        print(f"❌ Error en resumen: {e}")
        return f"❌ Error obteniendo resumen: {e}"

def _handle_listar(user_id: str, command: str) -> str:
    """Listar notificaciones"""
    try:
        parts = command.split()
        limit = 10  # por defecto
        notif_type = None
        
        # Parsear parámetros: "listar 20" o "listar papers" o "listar papers 15"
        if len(parts) > 1:
            if parts[1].isdigit():
                limit = min(int(parts[1]), 50)  # Máximo 50
            else:
                notif_type = parts[1]
                if len(parts) > 2 and parts[2].isdigit():
                    limit = min(int(parts[2]), 50)
        
        if notif_type:
            notifications = multi_user_system.get_notifications_by_type(user_id, notif_type, limit)
            title = f"📋 **Últimas {len(notifications)} notificaciones de '{notif_type}':**"
        else:
            notifications = multi_user_system.get_all_notifications(user_id, limit)
            title = f"📋 **Últimas {len(notifications)} notificaciones:**"
        
        if not notifications:
            return "📭 No hay notificaciones para mostrar.\n\n💡 Activa notificaciones con: `activar papers`"
        
        result = title + "\n\n"
        
        for i, notif in enumerate(notifications, 1):
            status = "✅" if notif["delivered"] else "🆕"
            date_str = notif["created_at"][:19].replace("T", " ")
            
            # Emoji según tipo
            emoji = {
                "papers": "📚",
                "patents": "🔬", 
                "emails": "📧",
                "ayudas": "💶",
                "test": "🧪"
            }.get(notif['type'], "📄")
            
            result += f"**{i}.** {status} {emoji} `{notif['type']}` - {date_str}\n"
            result += f"   📌 **{notif['title']}**\n"
            
            # Truncar mensaje largo
            message = notif['message']
            if len(message) > 100:
                message = message[:100] + '...'
            result += f"   💬 {message}\n"
            result += f"   🆔 ID: {notif['id']}\n\n"
        
        result += f"💡 **Comandos útiles:**\n"
        result += f"• `borrar {notifications[0]['id']}` - Borrar notificación específica\n"
        result += f"• `borrar todo` - Borrar todas\n"
        result += f"• `resumen` - Ver resumen por tipos"
        
        return result
    except Exception as e:
        print(f"❌ Error listando: {e}")
        return f"❌ Error listando notificaciones: {e}"

def _handle_borrar(user_id: str, command: str) -> str:
    """Borrar notificaciones"""
    try:
        parts = command.split()
        
        if len(parts) < 2:
            return "❌ Especifica qué borrar:\n• `borrar [ID]` - Borrar una\n• `borrar todo` - Borrar todas\n• `borrar [tipo]` - Borrar por tipo"
        
        target = parts[1].lower()
        
        if target == "todo":
            count = multi_user_system.delete_all_notifications(user_id)
            return f"🗑️ Se eliminaron **{count}** notificaciones."
        
        elif target.isdigit():
            notification_id = int(target)
            success = multi_user_system.delete_notification(user_id, notification_id)
            if success:
                return f"✅ Notificación **#{notification_id}** eliminada correctamente."
            else:
                return f"❌ No se encontró la notificación **#{notification_id}**."
        
        else:
            # Borrar por tipo
            count = multi_user_system.delete_all_notifications(user_id, target)
            if count > 0:
                return f"🗑️ Se eliminaron **{count}** notificaciones de tipo **'{target}'**."
            else:
                return f"📭 No hay notificaciones de tipo **'{target}'** para eliminar."
        
    except Exception as e:
        print(f"❌ Error borrando: {e}")
        return f"❌ Error borrando notificaciones: {e}"

def _handle_activar(user_id: str, command: str) -> str:
    """Activar notificaciones"""
    try:
        parts = command.split()
        if len(parts) < 2:
            return "❌ Especifica qué activar:\n• `activar emails`\n• `activar patentes`\n• `activar papers`\n• `activar ayudas`"
        
        tipo = parts[1].lower()
        
        config_map = {
            "emails": {"email_notifications": True},
            "email": {"email_notifications": True},
            "patentes": {"patent_notifications": True},
            "patents": {"patent_notifications": True},
            "papers": {"papers_notifications": True},
            "ayudas": {"ayudas_notifications": True},
            "subvenciones": {"ayudas_notifications": True}
        }
        
        if tipo not in config_map:
            return f"❌ Tipo '{tipo}' no válido.\n\nUsa: `activar emails`, `activar patentes`, `activar papers` o `activar ayudas`"

        success = multi_user_system.update_user_config(user_id, config_map[tipo])
        
        if success:
            emoji = {"emails": "📧", "email": "📧", "patentes": "🔬", "patents": "🔬", "papers": "📚", "ayudas": "💶", "subvenciones": "💶"}
            return f"✅ Notificaciones de **{tipo}** activadas {emoji.get(tipo, '🔔')}\n\n💡 Configura keywords con:\n• `keywords {tipo}: palabra1, palabra2`"
        
        return "❌ Error al actualizar la configuración"
        
    except Exception as e:
        print(f"❌ Error activando: {e}")
        return f"❌ Error en activar: {e}"

def _handle_desactivar(user_id: str, command: str) -> str:
    """Desactivar notificaciones"""
    try:
        parts = command.split()
        if len(parts) < 2:
            return "❌ Especifica qué desactivar:\n• `desactivar emails`\n• `desactivar patentes`\n• `desactivar papers`\n• `desactivar ayudas`"
        
        tipo = parts[1].lower()
        
        config_map = {
            "emails": {"email_notifications": False},
            "email": {"email_notifications": False},
            "patentes": {"patent_notifications": False},
            "patents": {"patent_notifications": False},
            "papers": {"papers_notifications": False},
            "ayudas": {"ayudas_notifications": False},
            "subvenciones": {"ayudas_notifications": False}
        }
        
        if tipo not in config_map:
            return f"❌ Tipo '{tipo}' no válido.\n\nUsa: `desactivar emails`, `desactivar patentes`, `desactivar papers` o `desactivar ayudas`"

        success = multi_user_system.update_user_config(user_id, config_map[tipo])
        
        if success:
            return f"⏹️ Notificaciones de **{tipo}** desactivadas."
        
        return "❌ Error al actualizar la configuración"
        
    except Exception as e:
        print(f"❌ Error desactivando: {e}")
        return f"❌ Error en desactivar: {e}"

def _handle_keywords_patentes(user_id: str, command: str) -> str:
    """Configurar keywords de patentes"""
    try:
        keywords = [k.strip() for k in command.split(":", 1)[1].split(",") if k.strip()]
        
        if not keywords:
            return "❌ No se especificaron keywords.\n\nEjemplo: `keywords patentes: AI, robotics, machine learning`"
        
        config = {
            "patent_keywords": keywords, 
            "patent_notifications": True
        }
        
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return f"✅ Keywords de patentes configuradas:\n• {', '.join(keywords)}\n\n🔔 Notificaciones de patentes activadas automáticamente."
        
        return "❌ Error al configurar keywords de patentes"
        
    except Exception as e:
        print(f"❌ Error en keywords patentes: {e}")
        return f"❌ Error: {e}"

def _handle_keywords_papers(user_id: str, command: str) -> str:
    """Configurar keywords de papers"""
    try:
        keywords = [k.strip() for k in command.split(":", 1)[1].split(",") if k.strip()]
        
        if not keywords:
            return "❌ No se especificaron keywords.\n\nEjemplo: `keywords papers: neural networks, deep learning, NLP`"
        
        config = {
            "papers_keywords": keywords,
            "papers_notifications": True
        }
        
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return f"✅ Keywords de papers configuradas:\n• {', '.join(keywords)}\n\n🔔 Notificaciones de papers activadas automáticamente."
        
        return "❌ Error al configurar keywords de papers"
        
    except Exception as e:
        print(f"❌ Error en keywords papers: {e}")
        return f"❌ Error: {e}"

def _handle_categories(user_id: str, command: str) -> str:
    """Configurar categorías de arXiv"""
    try:
        categories = [c.strip() for c in command.split(":", 1)[1].split(",") if c.strip()]
        
        if not categories:
            return "❌ No se especificaron categorías.\n\n" + get_categories_help()
        
        valid_categories = validate_categories(categories)
        
        if not valid_categories:
            return "❌ Categorías inválidas.\n\n" + get_categories_help()
        
        config = {
            "papers_categories": valid_categories,
            "papers_notifications": True
        }
        
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return f"✅ Categorías de papers configuradas:\n• {', '.join(valid_categories)}\n\n🔔 Notificaciones de papers activadas automáticamente."
        
        return "❌ Error al configurar categorías de papers"
        
    except Exception as e:
        print(f"❌ Error en categories: {e}")
        return f"❌ Error: {e}"

def _handle_test(user_id: str) -> str:
    """Enviar notificación de prueba"""
    try:
        config = multi_user_system.get_user_config(user_id)
        device_name = config.get('device_name', 'tu dispositivo')

        multi_user_system.add_notification(
            user_id,
            'test',
            '🧪 Notificación de Prueba',
            f'El sistema funciona correctamente en {device_name}',
            {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id[:8],
                'device_name': device_name
            }
        )
        
        print(f"🧪 Notificación de prueba enviada a {user_id[:12]}...")
        
        return f"✅ **Notificación de prueba enviada**\n\n💡 Deberías recibirla en unos segundos.\n\nSi no la recibes:\n• Verifica permisos del navegador\n• Usa `debug` para más información"
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return f"❌ Error enviando notificación de prueba: {e}"

def _handle_start(user_id: str) -> str:
    """Iniciar monitoreo"""
    return (
        "🚀 **El sistema de monitoreo se ejecuta automáticamente en el servidor.**\n\n"
        "💡 Solo usuarios con notificaciones activadas son monitoreados.\n\n"
        "📊 Para ver tu estado: `status`"
    )

def _handle_stop(user_id: str) -> str:
    """Detener notificaciones del usuario"""
    try:
        config = {
            "email_notifications": False,
            "patent_notifications": False,
            "papers_notifications": False,
            "ayudas_notifications": False
        }
        
        success = multi_user_system.update_user_config(user_id, config)
        
        if success:
            return "⏹️ **Todas las notificaciones desactivadas** para tu dispositivo.\n\n💡 Para reactivar: `activar [tipo]`"
        
        return "❌ Error al desactivar notificaciones"
        
    except Exception as e:
        print(f"❌ Error en stop: {e}")
        return f"❌ Error: {e}"

# -----------------------------------------------
# Ayudas y validaciones
# -----------------------------------------------

def get_main_help():
    """Ayuda principal"""
    return """
🔔 **SISTEMA DE NOTIFICACIONES INTELIGENTES**

**📋 Comandos disponibles:**

**Estado y configuración:**
- `status` - Ver estado completo
- `debug` - Información de depuración
- `resumen` - Resumen de notificaciones

**Gestión de notificaciones:**
- `listar [n]` - Ver últimas n notificaciones (default: 10)
- `listar [tipo]` - Filtrar por tipo (papers, patents, emails, ayudas)
- `listar [tipo] [n]` - Combinar filtro y cantidad
- `borrar [ID]` - Eliminar notificación específica
- `borrar todo` - Eliminar todas
- `borrar [tipo]` - Eliminar por tipo

**Activación:**
- `activar emails` - Activar notificaciones de emails
- `activar patentes` - Activar notificaciones de patentes
- `activar papers` - Activar notificaciones de papers científicos
- `activar ayudas` - Activar notificaciones de ayudas/subvenciones
- `desactivar [tipo]` - Desactivar tipo específico

**Configuración:**
- `keywords patentes: AI, robotics` - Configurar keywords de patentes
- `keywords papers: neural networks, ML` - Configurar keywords de papers
- `categories: cs.AI, cs.LG` - Configurar categorías de arXiv

**Utilidades:**
- `test` - Enviar notificación de prueba
- `stop` - Desactivar todas las notificaciones

**💡 Ejemplos de uso:**
activar papers
keywords papers: machine learning, AI
categories: cs.AI, cs.LG
listar papers 5
    """
def get_categories_help():
    """Ayuda de categorías"""
    return """
📚 **CATEGORÍAS DE ARXIV DISPONIBLES:**

**Computer Science:**
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `cs.CL` - Computation and Language
- `cs.NE` - Neural and Evolutionary Computing

**Physics:**
- `physics.gen-ph` - General Physics

**Mathematics:**
- `math.GM` - General Mathematics

**Ejemplo:**
`categories: cs.AI, cs.LG, cs.CV`
    """

def validate_categories(categories):
    """Valida categorías de arXiv"""
    valid_cats = {
        'cs.ai', 'cs.lg', 'cs.cv', 'cs.cl', 'cs.ne',
        'physics.gen-ph', 'math.gm'
    }
    return [c.lower() for c in categories if c.lower() in valid_cats]