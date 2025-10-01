import importlib
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Cargar variables del archivo .env
load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Herramientas disponibles
TOOLS = {
    "note": "tools.note",
    "save_code": "tools.save_code",
    "web_search": "tools.web_search",
    "calculator": "tools.calculator",
    "web_open": "tools.web_open",
    "code_gen": "tools.code_gen",
    "notifications": "tools.notifications",
    "document_filler": "tools.document_filler",
    "rmn_spectrum_cleaner": "tools.rmn_spectrum_cleaner",
    "ayudas_manager": "tools.ayudas_manager"  # Nueva herramienta
}

def ask_gemini_for_tool(prompt: str) -> str:
    prompt_lower = prompt.lower().strip()
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUGGING ask_gemini_for_tool")
    print(f"📝 Prompt original: '{prompt}'")
    print(f"📝 Prompt lower: '{prompt_lower}'")
    print(f"{'='*60}\n")

    # URLs
    url_pattern = r"(https?://[^\s]+)"
    if re.match(url_pattern, prompt.strip()):
        print("✅ DETECTADO: URL → web_open")
        return "web_open"
    
    # ============================================================
    # COMANDOS EXACTOS (DICCIONARIO)
    # ============================================================
    
    exact_commands = {
        "listar espectros": "rmn_spectrum_cleaner",
        "listar plantillas": "document_filler",
        "listar datos": "document_filler",
        "status": "notifications",
        "debug": "notifications",
        "resumen": "notifications",
        "test": "notifications",
        "ayudas buscar": "ayudas_manager",
    }
    
    print(f"🔍 Verificando comandos exactos...")
    if prompt_lower in exact_commands:
        result = exact_commands[prompt_lower]
        print(f"✅ MATCH EXACTO: '{prompt_lower}' → {result}")
        return result
    else:
        print(f"❌ No hay match exacto para: '{prompt_lower}'")
    
    # ============================================================
    # DETECCIÓN POR FRASES (ORDEN ESTRICTO)
    # ============================================================
    
    print(f"\n🔍 Verificando frases específicas...\n")
    
    # 1. DOCUMENTOS
    document_phrases = [
        "listar plantillas", "listar datos",
        "plantilla", "plantillas",
        "rellenar:", "analizar plantilla",
        "crear ejemplo datos", "usar plantilla:",
        "convertir a json"
    ]
    
    print(f"📄 Verificando DOCUMENTOS...")
    for phrase in document_phrases:
        if phrase in prompt_lower:
            print(f"✅ MATCH: '{phrase}' encontrada → document_filler")
            return "document_filler"
    print(f"❌ No match en documentos")
    
    # 2. RMN
    rmn_phrases = [
        "listar espectros",
        "espectro", "espectros",
        "analizar:", "limpiar:", "comparar:", "exportar:",
        "savgol", "gaussian", "mediana",
        "línea base", "snr", "ppm"
    ]
    
    print(f"🧪 Verificando RMN...")
    for phrase in rmn_phrases:
        if phrase in prompt_lower:
            print(f"✅ MATCH: '{phrase}' encontrada → rmn_spectrum_cleaner")
            return "rmn_spectrum_cleaner"
    print(f"❌ No match en RMN")
    
    # 3. AYUDAS
    ayudas_phrases = [
        "ayudas buscar", "ayudas filtrar", "ayudas activar",
        "subvención", "subvenciones", "beca", "becas",
        "convocatoria", "financiación"
    ]
    
    print(f"💶 Verificando AYUDAS...")
    for phrase in ayudas_phrases:
        if phrase in prompt_lower:
            print(f"✅ MATCH: '{phrase}' encontrada → ayudas_manager")
            return "ayudas_manager"
    print(f"❌ No match en ayudas")
    
    # 4. NOTIFICACIONES (solo muy específicas)
    notification_phrases = [
        "listar notificaciones",
        "listar papers", "listar patentes", "listar emails",
        "activar emails", "activar patentes", "activar papers",
        "keywords patentes:", "keywords papers:",
        "borrar notificaciones"
    ]
    
    print(f"🔔 Verificando NOTIFICACIONES...")
    for phrase in notification_phrases:
        if phrase in prompt_lower:
            print(f"✅ MATCH: '{phrase}' encontrada → notifications")
            return "notifications"
    print(f"❌ No match en notificaciones")
    
    # 5. CÓDIGO
    if any(k in prompt_lower for k in ["generar", "genera", "crear codigo"]):
        print(f"✅ MATCH: generación código → code_gen")
        return "code_gen"
    
    if "||" in prompt:
        print(f"✅ MATCH: formato || → save_code")
        return "save_code"
    
    # ============================================================
    # FALLBACK: Gemini
    # ============================================================
    
    print(f"\n⚠️ NO HAY MATCH → Preguntando a Gemini...")
    
    tools_list = ", ".join(TOOLS.keys())
    question = f"""Comando del usuario: "{prompt}"

Herramientas: {tools_list}

Si menciona "plantillas" o "datos" → document_filler
Si menciona "espectros" o "RMN" → rmn_spectrum_cleaner
Si menciona "ayudas" o "subvenciones" → ayudas_manager
Si menciona "notificaciones" o "papers" → notifications

Responde SOLO el nombre de la herramienta."""
    
    try:
        response = model.generate_content(question)
        result = response.text.strip().lower().replace('"', '').replace("'", '').replace('.', '')
        print(f"🤖 Gemini eligió: {result}")
        
        if result in TOOLS:
            return result
        else:
            print(f"⚠️ Gemini devolvió inválido: {result} → usando notifications")
            return "notifications"  # Fallback
            
    except Exception as e:
        print(f"❌ Error Gemini: {e} → usando notifications")
        return "notifications"


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