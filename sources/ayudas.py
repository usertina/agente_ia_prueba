from datetime import datetime

def check_ayudas(region, since_date):
    """Simula scraping de ayudas/subvenciones"""
    # Aquí se integraría el scraper real del BOE o del Gobierno Vasco
    notifications = []
    fake_ayuda = {
        "type": "ayudas",
        "title": f"💶 Nueva ayuda en {region}",
        "message": "Subvención para proyectos de innovación en Vizcaya",
        "data": {
            "region": region,
            "importe": "10.000€",
            "fecha_limite": "2025-12-31",
            "url": "https://www.euskadi.eus/ayuda/12345"
        }
    }
    notifications.append(fake_ayuda)
    return notifications
