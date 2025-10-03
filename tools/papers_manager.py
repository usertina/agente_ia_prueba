# tools/papers_manager.py
from datetime import datetime, timedelta
import tools.papers_manager as papers

def run(command: str, user_id: str):
    """
    Wrapper para integración con CommandHandler.
    `command` se puede usar para filtrar keywords si quieres.
    """
    # Para simplificar, usamos keywords de ejemplo
    keywords = command.replace("papers", "").strip().split(",")
    if not keywords or keywords == [""]:
        keywords = ["quantum sensor", "quantum dot", "PFAS detection"]
    
    # Buscar papers desde los últimos 7 días
    since_date = datetime.now() - timedelta(days=7)
    results = papers.check_papers(keywords, categories=[], since_date=since_date, max_results=5)
    
    if not results:
        return "📭 No se encontraron papers nuevos"
    
    output = f"📚 **PAPERS RECIENTES**\n\n"
    for i, paper in enumerate(results, 1):
        output += f"**{i}. {paper['title']}**\n"
        output += f"   📝 {paper['message']}\n"
        output += f"   📅 Publicado: {paper['data']['published']}\n\n"
    
    return output
