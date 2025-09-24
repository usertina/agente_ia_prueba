from datetime import datetime

def check_emails(user_id, since_date):
    """Simula revisión de correos electrónicos"""
    # En producción aquí iría conexión IMAP/SMTP
    return [{
        "type": "emails",
        "title": "📧 Nuevo correo",
        "message": "Has recibido un email de contacto@empresa.com",
        "data": {
            "from": "contacto@empresa.com",
            "subject": "Oferta de colaboración",
            "date": datetime.now().isoformat()
        }
    }]
