import schedule
import time
from datetime import datetime, timedelta
from sources.ayudas_real import AyudasScraper
from multi_user_notification_system import multi_user_system

def check_new_ayudas():
    """Verifica nuevas ayudas para todos los usuarios activos"""
    print(f"🔍 Verificando ayudas - {datetime.now()}")
    
    scraper = AyudasScraper()
    active_users = multi_user_system.get_active_users(hours=24)
    
    for user_id in active_users:
        config = multi_user_system.get_user_config(user_id)
        
        if config.get('ayudas_notifications'):
            region = config.get('region', 'Euskadi')
            categories = config.get('ayudas_categories', [])
            
            # Obtener ayudas
            ayudas = scraper.get_all_ayudas(region, datetime.now() - timedelta(days=1))
            
            # Filtrar por categorías de interés
            if categories:
                ayudas = [a for a in ayudas 
                         if any(cat in a.get('categorias', []) for cat in categories)]
            
            # Crear notificaciones
            for ayuda in ayudas[:5]:  # Máximo 5 por usuario
                multi_user_system.add_notification(
                    user_id,
                    'ayudas',
                    f"💶 {ayuda['titulo'][:100]}",
                    f"{ayuda['entidad']} - {ayuda.get('importe', 'Consultar')}",
                    {
                        'url': ayuda['url'],
                        'fecha_limite': ayuda.get('fecha_limite'),
                        'categorias': ayuda.get('categorias', [])
                    }
                )
    
    print(f"✅ Verificación completada - {len(active_users)} usuarios procesados")

# Programar tareas
schedule.every(6).hours.do(check_new_ayudas)
schedule.every().day.at("09:00").do(check_new_ayudas)
schedule.every().day.at("14:00").do(check_new_ayudas)

if __name__ == "__main__":
    print("🚀 Scheduler de ayudas iniciado")
    
    # Ejecutar una vez al iniciar
    check_new_ayudas()
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)