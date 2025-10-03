# tools/patents_manager.py
from datetime import datetime, timedelta
from sources.patents import check_patents

def run(command: str, user_id: str):
    """
    Wrapper para integración con CommandHandler.
    `command` se puede usar para filtrar keywords si quieres.
    """
    keywords = command.replace("patents", "").strip().split(",")
    if not keywords or keywords == [""]:
        keywords = ["quantum sensor", "PFAS detection", "water quality sensor"]
    
    since_date = datetime.now() - timedelta(days=30)
    results = check_patents(keywords, since_date=since_date)
    
    if not results:
        return "📭 No se encontraron patentes nuevas"
    
    output = f"🔬 **PATENTES RECIENTES**\n\n"
    for i, patent in enumerate(results, 1):
        output += f"**{i}. {patent['title']}**\n"
        output += f"   📝 {patent['message']}\n"
        output += f"   🔗 {patent['data']['url']}\n\n"
    
    return output
