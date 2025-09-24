from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

def run(query: str) -> str:
    query = query.strip()
    if not query:
        return "ERROR: Debes escribir algo para buscar."
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=CSE_ID, num=5).execute()
        items = res.get("items", [])
        if not items:
            return "No se encontraron resultados."

        resultados = []
        for i, item in enumerate(items):
            title = item.get("title", "Sin título")
            link = item.get("link", "")
            snippet = item.get("snippet", "Sin descripción")
            resultados.append(f"{i+1}. {title} - {link} - {snippet}")
        return "\n".join(resultados)
    except Exception as e:
        return f"ERROR al buscar: {e}"
