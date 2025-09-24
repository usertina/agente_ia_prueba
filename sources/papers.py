from datetime import datetime
import requests, xml.etree.ElementTree as ET

def check_papers(keywords, categories, since_date, max_results=5):
    """Busca papers en arXiv y devuelve notificaciones"""
    notifications = []
    base_url = "http://export.arxiv.org/api/query"
    namespace = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    for keyword in keywords[:3]:
        params = {"search_query": f"all:{keyword}", "start": 0, "max_results": max_results, "sortBy": "submittedDate", "sortOrder": "descending"}
        try:
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for entry in root.findall("atom:entry", namespace):
                title = entry.find("atom:title", namespace).text.strip()
                published = entry.find("atom:published", namespace).text.strip()
                published_date = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(tzinfo=None)
                if published_date > since_date:
                    notifications.append({
                        "type": "papers",
                        "title": f"📚 Nuevo paper: {keyword}",
                        "message": title[:150] + "...",
                        "data": {"title": title, "published": published}
                    })
        except Exception as e:
            print(f"❌ Error buscando papers: {e}")
            continue

    return notifications
