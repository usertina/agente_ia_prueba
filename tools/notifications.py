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
    """
    
    if not multi_user_system:
        return "❌ Error: Sistema de notificaciones no disponible"
    
    command = command.strip().lower()
    user_id = get_current_user_id()
    
    print(f"🔧 Notifications tool - User ID: {user_id}, Command: {command}")

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
    elif command.startswith("keywords patentes:"):
        return _handle_keywords_patentes(user_id, command)
    elif command.startswith("keywords papers:"):
        return _handle_keywords_papers(user_id, command)
    elif command.startswith("categories:"):
        return _handle_categories(user_id, command)
    elif command in ["test", "probar"]:
        return _handle_test(user_id)
    elif command in ["start", "iniciar"]:
        return _handle_start()
    elif command in ["stop", "detener"]:
        return _handle_stop(user_id)
    else:
        return get_main_help()

# -----------------------------------------------
# Handlers internos
# -----------------------------------------------

def _handle_status(user_id: str) -> str:
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

def _handle_debug(user_id: str) -> str:
    try:
        with multi_user_system.get_db_connection() as conn:
            user_exists = conn.execute(
                "SELECT user_id, config FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()

        if not user_exists:
            return f"❌ **Usuario no encontrado en la base de datos**\n\nUser ID: {user_id}"

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
    
def _handle_resumen(user_id: str) -> str:
    """Mostrar resumen de notificaciones"""
    try:
        summary = multi_user_system.get_notification_summary(user_id)
        
        result = f"📊 **Resumen de Notificaciones:**\n\n"
        result += f"📈 **Total:** {summary['total']} notificaciones\n\n"
        
        if summary['by_type']:
            result += "**Por tipo:**\n"
            for notif_type, counts in summary['by_type'].items():
                emoji = {"papers": "📚", "patents": "🔬", "emails": "📧", "ayudas": "💰", "test": "🧪"}.get(notif_type, "📄")
                result += f"{emoji} **{notif_type}:** {counts['total']} total"
                if counts['pending'] > 0:
                    result += f" ({counts['pending']} pendientes)"
                result += "\n"
        else:
            result += "📭 No hay notificaciones registradas.\n"
        
        result += f"\n💡 Usa `listar` para ver las notificaciones o `listar [tipo]` para filtrar por tipo."
        
        return result
    except Exception as e:
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
                limit = int(parts[1])
            else:
                notif_type = parts[1]
                if len(parts) > 2 and parts[2].isdigit():
                    limit = int(parts[2])
        
        if notif_type:
            notifications = multi_user_system.get_notifications_by_type(user_id, notif_type, limit)
            title = f"📋 **Últimas {len(notifications)} notificaciones de tipo '{notif_type}':**"
        else:
            notifications = multi_user_system.get_all_notifications(user_id, limit)
            title = f"📋 **Últimas {len(notifications)} notificaciones:**"
        
        if not notifications:
            return "📭 No hay notificaciones para mostrar."
        
        result = title + "\n\n"
        
        for i, notif in enumerate(notifications, 1):
            status = "✅" if notif["delivered"] else "🆕"
            date_str = notif["created_at"][:19].replace("T", " ")
            result += f"**{i}.** {status} `{notif['type']}` - {date_str}\n"
            result += f"   📌 **{notif['title']}**\n"
            result += f"   💬 {notif['message'][:100]}{'...' if len(notif['message']) > 100 else ''}\n"
            result += f"   🆔 ID: {notif['id']}\n\n"
        
        result += f"💡 **Comandos útiles:**\n"
        result += f"• `borrar {notifications[0]['id']}` - Borrar notificación específica\n"
        result += f"• `borrar todo` - Borrar todas las notificaciones\n"
        result += f"• `resumen` - Ver resumen por tipos"
        
        return result
    except Exception as e:
        return f"❌ Error listando notificaciones: {e}"

def _handle_borrar(user_id: str, command: str) -> str:
    """Borrar notificaciones"""
    try:
        parts = command.split()
        
        if len(parts) < 2:
            return "❌ Especifica qué borrar: `borrar [ID]`, `borrar todo`, `borrar [tipo]`"
        
        target = parts[1].lower()
        
        if target == "todo":
            count = multi_user_system.delete_all_notifications(user_id)
            return f"🗑️ Se eliminaron {count} notificaciones."
        
        elif target.isdigit():
            notification_id = int(target)
            success = multi_user_system.delete_notification(user_id, notification_id)
            if success:
                return f"✅ Notificación {notification_id} eliminada."
            else:
                return f"❌ No se encontró la notificación {notification_id}."
        
        else:
            # Borrar por tipo
            count = multi_user_system.delete_all_notifications(user_id, target)
            return f"🗑️ Se eliminaron {count} notificaciones de tipo '{target}'."
        
    except Exception as e:
        return f"❌ Error borrando notificaciones: {e}"


def _handle_activar(user_id: str, command: str) -> str:
    try:
        tipo = command.split(" ")[1]
        config_map = {
            "emails": {"email_notifications": True},
            "patentes": {"patent_notifications": True},
            "papers": {"papers_notifications": True}
        }
        if tipo not in config_map:
            return "❌ Tipo de notificación inválido. Usa 'emails', 'patentes' o 'papers'."

        success = multi_user_system.update_user_config(user_id, config_map[tipo])
        if success:
            return f"✅ Notificaciones de {tipo} activadas."
        return "❌ Error al actualizar la configuración"
    except Exception as e:
        return f"❌ Error en activar: {e}"

def _handle_keywords_patentes(user_id: str, command: str) -> str:
    try:
        keywords = [k.strip() for k in command.split(":", 1)[1].split(",") if k.strip()]
        config = {"patent_keywords": keywords, "patent_notifications": True}
        success = multi_user_system.update_user_config(user_id, config)
        if success:
            return f"✅ Keywords de patentes configuradas: {', '.join(keywords)}"
        return "❌ Error al configurar keywords de patentes"
    except Exception as e:
        return f"❌ Error: {e}"

def _handle_keywords_papers(user_id: str, command: str) -> str:
    try:
        keywords = [k.strip() for k in command.split(":", 1)[1].split(",") if k.strip()]
        config = {"papers_keywords": keywords, "papers_notifications": True}
        success = multi_user_system.update_user_config(user_id, config)
        if success:
            return f"✅ Keywords de papers configuradas: {', '.join(keywords)}"
        return "❌ Error al configurar keywords de papers"
    except Exception as e:
        return f"❌ Error: {e}"

def _handle_categories(user_id: str, command: str) -> str:
    try:
        categories = [c.strip() for c in command.split(":", 1)[1].split(",") if c.strip()]
        valid_categories = validate_categories(categories)
        if not valid_categories:
            return "❌ Categorías inválidas.\n\n" + get_categories_help()
        config = {"papers_categories": valid_categories, "papers_notifications": True}
        success = multi_user_system.update_user_config(user_id, config)
        if success:
            return f"✅ Categorías de papers configuradas: {', '.join(valid_categories)}"
        return "❌ Error al configurar categorías de papers"
    except Exception as e:
        return f"❌ Error: {e}"

def _handle_test(user_id: str) -> str:
    try:
        config = multi_user_system.get_user_config(user_id)
        device_name = config.get('device_name', 'Despositivo Desconocido')

        test_notifications = [
            {
                'type': 'test',
                'title': '🧪 Notificación de Prueba - Sistema',
                'message': f'Sistema funcionando correctamente en {device_name}',
                'data': {'test': True, 'timestamp': multi_user_system._get_current_timestamp()}
            }
        ]

        for notif in test_notifications:
            multi_user_system.add_notification(
                user_id,
                notif['type'],
                notif['title'],
                notif['message'],
                notif['data']
            )
        return f"✅ Notificación de prueba enviada para usuario {user_id[:8]}"
    except Exception as e:
        return f"❌ Error enviando notificación de prueba: {e}"

def _handle_start() -> str:
    return (
        "🚀 **El sistema de monitoreo se ejecuta automáticamente en el servidor.**\n"
        "💡 Solo usuarios con notificaciones activadas son monitoreados."
    )

def _handle_stop(user_id: str) -> str:
    try:
        config = {
            "email_notifications": False,
            "patent_notifications": False,
            "papers_notifications": False
        }
        success = multi_user_system.update_user_config(user_id, config)
        if success:
            return "⏹️ Notificaciones desactivadas para tu dispositivo."
        return "❌ Error al desactivar notificaciones"
    except Exception as e:
        return f"❌ Error: {e}"

# -----------------------------------------------
# Ayudas y validaciones
# -----------------------------------------------

def get_main_help():
    return (
        "🔔 **Sistema de Notificaciones Inteligentes**\n"
        "• `status` - Ver estado\n"
        "• `debug` - Depuración\n"
        "• `activar emails|patentes|papers`\n"
        "• `keywords patentes: ...`\n"
        "• `keywords papers: ...`\n"
        "• `categories: ...`\n"
        "• `test` - Notificación de prueba\n"
        "• `stop` - Detener notificaciones"
    )

def get_categories_help():
    return (
        "📚 **Categorías de arXiv Disponibles:** cs.AI, cs.LG, cs.CV, physics.gen-ph, math.GM"
    )

def validate_categories(categories):
    valid_cats = {'cs.ai','cs.lg','cs.cv','physics.gen-ph','math.gm'}
    return [c.lower() for c in categories if c.lower() in valid_cats]
