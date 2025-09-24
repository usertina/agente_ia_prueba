import importlib
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Cargar variables del archivo .env
load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Herramientas disponibles
TOOLS = {
    "note": "tools.note",
    "save_code": "tools.save_code",
    "web_search": "tools.web_search",
    "calculator": "tools.calculator",
    "web_open": "tools.web_open",
    "code_gen": "tools.code_gen",
    "notifications": "tools.notifications",
    "document_filler": "tools.document_filler"
}

def ask_gemini_for_tool(prompt: str) -> str:
    prompt_lower = prompt.lower()  # <-- definir al inicio
    
    # Si el prompt es una URL, usar web_open automáticamente
    url_pattern = r"(https?://[^\s]+)"
    if re.match(url_pattern, prompt.strip()):
        return "web_open"
    
    # Palabras clave de generación de código
    code_gen_keywords = [
        "generar", "genera", "crear", "crea", "escribir", "escribe",
        "codigo", "código", "script", "programa", "función", "funcion",
        "algoritmo", "clase", "app", "aplicación", "aplicacion"
    ]

    # Palabras clave de notificaciones
    notification_keywords = [
        "notificacion", "notificación", "alerta", "avisar", "aviso",
        "email", "correo", "patente", "paper", "papers", "científico",
        "monitoreo", "notificar", "activar", "keywords", "categories",
        "status", "estado", "test", "probar"
    ]

    # Palabras clave de documentos
    document_keywords = [
        "plantilla", "rellenar", "documento", "formulario",
        "listar plantillas", "listar datos", "analizar",
        "crear ejemplo", "ayuda", "subvencion", "subvención",
        "document_filler", "plantillas", "datos", "rellenar:"
    ]

    # Revisar documentos PRIMERO (antes que notificaciones para evitar conflictos)
    if any(keyword in prompt_lower for keyword in document_keywords):
        return "document_filler"

    # Revisar notificaciones
    if any(keyword in prompt_lower for keyword in notification_keywords):
        return "notifications"

    # Revisar generación de código
    if any(keyword in prompt_lower for keyword in code_gen_keywords):
        if "||" not in prompt or prompt_lower.startswith("generar") or prompt_lower.startswith("genera"):
            return "code_gen"

    # Revisar guardar código existente
    if "||" in prompt and not any(keyword in prompt_lower for keyword in code_gen_keywords):
        return "save_code"

    # Preguntar a Gemini si no aplica ninguna regla
    tools_list = ", ".join(TOOLS.keys())
    question = (
        f"Elige una de estas herramientas: {tools_list}, "
        f"para resolver: {prompt}. "
        f"Si necesita generar/crear código usa 'code_gen'. "
        f"Si es para guardar código existente usa 'save_code'. "
        f"Si es para documentos/plantillas usa 'document_filler'. "
        f"Responde SOLO con el nombre exacto de la herramienta."
    )
    response = model.generate_content(question)
    return response.text.strip().lower()


def use_tool(tool_name: str, data: str) -> str:
    if tool_name not in TOOLS:
        return f"No existe la herramienta {tool_name}"
    try:
        module = importlib.import_module(TOOLS[tool_name])
        return module.run(data)
    except Exception as e:
        return f"ERROR al usar la herramienta {tool_name}: {e}"


def agent_loop():
    print("🤖 Agente inteligente con Gemini listo para ayudarte.")
    print("Escribe 'salir' para terminar.\n")

    while True:
        user_input = input("🧠 Tú: ")
        if user_input.lower().strip() == "salir":
            print("Hasta luego 👋")
            break

        tool = ask_gemini_for_tool(user_input)
        print(f"🔧 Gemini eligió la herramienta: {tool}")
        result = use_tool(tool, user_input)
        print("📦 Resultado:", result)