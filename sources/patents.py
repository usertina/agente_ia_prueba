from datetime import datetime

def check_patents(keywords, since_date, max_patents=3):
    """Simula búsqueda de patentes (en producción sería USPTO o Google Patents)"""
    notifications = []
    for keyword in keywords[:3]:
        patent_id = f"2025{str(hash(keyword))[-6:]}"
        notifications.append({
            "type": "patents",
            "title": f"🔬 Nueva patente: {keyword}",
            "message": f"Método para {keyword}",
            "data": {
                "id": patent_id,
                "url": f"https://patents.google.com/patent/US{patent_id}A1/en",
                "keyword": keyword,
                "date": datetime.now().isoformat()
            }
        })
        if len(notifications) >= max_patents:
            break
    return notifications
