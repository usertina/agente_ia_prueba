import os
import shutil
from datetime import datetime

NOTES_DIR = "notes"
os.makedirs(NOTES_DIR, exist_ok=True)
NOTES_FILE = os.path.join(NOTES_DIR, "notas.txt")

def run(text: str) -> str:
    text_lower = text.strip().lower()

    # Leer notas
    if text_lower == "leer":
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
            return contenido if contenido else "No hay notas guardadas todavía."
        except FileNotFoundError:
            return "No hay notas guardadas todavía."
        except Exception as e:
            return f"ERROR al leer notas: {e}"

    # Guardar nota
    elif text_lower.startswith("guardar:"):
        nota = text.split(":", 1)[1].strip()
        if not nota:
            return "Debes escribir algo después de 'guardar:'."
        try:
            # Agregar timestamp a cada nota
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nota_con_fecha = f"[{timestamp}] {nota}"
            
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(nota_con_fecha + "\n")
            return f"✅ Nota guardada: {nota}"
        except Exception as e:
            return f"ERROR al guardar nota: {e}"

    # Borrar notas
    elif text_lower == "borrar":
        try:
            if os.path.exists(NOTES_FILE):
                os.remove(NOTES_FILE)
            return "🗑️ Todas las notas han sido borradas."
        except Exception as e:
            return f"ERROR al borrar notas: {e}"

    # Descargar/exportar (ahora funciona remotamente)
    elif text_lower == "descargar":
        try:
            if not os.path.exists(NOTES_FILE):
                return "No hay notas guardadas todavía."
            
            # En lugar de crear un archivo local, indicamos que se puede descargar
            return "DOWNLOAD_FILE:notes|/download/notes|mis_notas.txt"
            
        except Exception as e:
            return f"ERROR al preparar descarga: {e}"

    # Contar notas
    elif text_lower == "contar":
        try:
            if not os.path.exists(NOTES_FILE):
                return "No hay notas guardadas todavía."
            
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            total_notas = len([line for line in lines if line.strip()])
            return f"📊 Tienes {total_notas} notas guardadas."
            
        except Exception as e:
            return f"ERROR al contar notas: {e}"

    # Buscar en notas
    elif text_lower.startswith("buscar:"):
        termino = text.split(":", 1)[1].strip()
        if not termino:
            return "Debes escribir un término de búsqueda después de 'buscar:'."
        
        try:
            if not os.path.exists(NOTES_FILE):
                return "No hay notas guardadas todavía."
                
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            resultados = []
            for i, line in enumerate(lines, 1):
                if termino.lower() in line.lower():
                    resultados.append(f"{i}. {line.strip()}")
            
            if resultados:
                return f"🔍 Encontradas {len(resultados)} coincidencias:\n\n" + "\n".join(resultados)
            else:
                return f"🔍 No se encontraron notas que contengan '{termino}'."
                
        except Exception as e:
            return f"ERROR al buscar en notas: {e}"

    else:
        return (
            "📝 Comandos de notas disponibles:\n\n"
            "• guardar: tu nota → para guardar una nueva nota\n"
            "• leer → para ver todas las notas\n" 
            "• buscar: término → para buscar en las notas\n"
            "• contar → para saber cuántas notas tienes\n"
            "• borrar → para borrar todas las notas\n"
            "• descargar → para descargar archivo con todas las notas"
        )