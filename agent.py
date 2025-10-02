import importlib
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Cargar variables del archivo .env
load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
try:
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception:
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Función para obtener el mapeo desde un archivo JSON
def obtener_mapeo(nombre_mapeo: str) -> str:
    try:
        mapeo_path = os.path.join("mappings_docs", nombre_mapeo)
        print(f"📝 Buscando archivo en: {mapeo_path}")
        
        with open(mapeo_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        return json.dumps(data, indent=4)
    
    except FileNotFoundError:
        return f"❌ Error: El mapeo {nombre_mapeo} no se encuentra disponible en la carpeta 'mappings_docs'."
    except json.JSONDecodeError:
        return "❌ Error al leer el archivo de mapeo. Verifique el formato."

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
    "ayudas_manager": "tools.ayudas_manager"
}

def ask_gemini_for_tool(prompt: str) -> str:
    prompt_lower = prompt.lower().strip()
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUGGING ask_gemini_for_tool")
    print(f"📝 Prompt original: '{prompt}'")
    print(f"📝 Prompt lower: '{prompt_lower}'")
    print(f"{'='*60}\n")

    # ============================================================
    # 1. DETECTAR URLs PRIMERO
    # ============================================================
    url_pattern = r"(https?://[^\s]+)"
    if re.match(url_pattern, prompt.strip()):
        print("✅ DETECTADO: URL → web_open")
        return "web_open"
    
    # ============================================================
    # 2. DETECTAR OPERACIONES MATEMÁTICAS
    # ============================================================
    math_pattern = r"^[0-9\s\+\-\*/\(\)\.]+$"
    if re.match(math_pattern, prompt_lower):
        print(f"✅ DETECTADO: operación matemática → calculator")
        return "calculator"
    
    # ============================================================
    # 3. DETECTAR CÓDIGO CON ||
    # ============================================================
    if "||" in prompt:
        print(f"✅ MATCH: formato || → save_code")
        return "save_code"
    
    # ============================================================
    # 4. COMANDOS ESPECÍFICOS POR HERRAMIENTA
    # ============================================================
    
    # DOCUMENT_FILLER - Los más específicos primero
    document_commands = [
        "analizar:",
        "rellenar:",
        "rellenar auto:",
        "usar plantilla:",
        "crear ejemplo datos:",
        "convertir a json:",
        "ver mapeo:",
        "crear mapeo:",
        "listar plantillas",
        "listar datos",
        "listar mapeos",
    ]
    
    print(f"📄 Verificando DOCUMENT_FILLER...")
    for cmd in document_commands:
        if prompt_lower.startswith(cmd) or prompt_lower == cmd:
            print(f"✅ MATCH: '{cmd}' → document_filler")
            return "document_filler"
    
    # RMN_SPECTRUM_CLEANER
    rmn_commands = [
        "limpiar:",
        "comparar:",
        "exportar:",
        "listar espectros",
    ]
    
    print(f"🧪 Verificando RMN_SPECTRUM_CLEANER...")
    for cmd in rmn_commands:
        if prompt_lower.startswith(cmd) or prompt_lower == cmd:
            print(f"✅ MATCH: '{cmd}' → rmn_spectrum_cleaner")
            return "rmn_spectrum_cleaner"
    
    # AYUDAS_MANAGER
    ayudas_commands = [
        "ayudas buscar",
        "ayudas filtrar",
        "ayudas activar",
    ]
    
    print(f"💶 Verificando AYUDAS_MANAGER...")
    for cmd in ayudas_commands:
        if prompt_lower.startswith(cmd) or prompt_lower == cmd:
            print(f"✅ MATCH: '{cmd}' → ayudas_manager")
            return "ayudas_manager"
    
    # NOTIFICATIONS
    notification_commands = [
        "status",
        "debug",
        "resumen",
        "test",
        "listar notificaciones",
        "listar papers",
        "listar patentes",
        "listar emails",
        "activar emails",
        "activar patentes",
        "activar papers",
        "keywords patentes:",
        "keywords papers:",
        "borrar notificaciones",
    ]
    
    print(f"🔔 Verificando NOTIFICATIONS...")
    for cmd in notification_commands:
        if prompt_lower.startswith(cmd) or prompt_lower == cmd:
            print(f"✅ MATCH: '{cmd}' → notifications")
            return "notifications"
    
    # CODE_GEN
    codegen_keywords = ["generar", "genera", "crear codigo", "escribe codigo"]
    if any(k in prompt_lower for k in codegen_keywords):
        print(f"✅ MATCH: generación código → code_gen")
        return "code_gen"
    
    # ============================================================
    # 5. DETECCIÓN POR PALABRAS CLAVE (CONTEXTO)
    # ============================================================
    
    # Palabras clave que sugieren document_filler
    if any(word in prompt_lower for word in ["plantilla", "plantillas", "mapeo", "rellenar", "documento"]):
        print(f"✅ KEYWORD: documento/plantilla → document_filler")
        return "document_filler"
    
    # Palabras clave que sugieren rmn_spectrum_cleaner
    if any(word in prompt_lower for word in ["espectro", "espectros", "rmn", "nmr", "savgol", "gaussian", "línea base", "snr", "ppm"]):
        print(f"✅ KEYWORD: espectro/rmn → rmn_spectrum_cleaner")
        return "rmn_spectrum_cleaner"
    
    # Palabras clave que sugieren ayudas_manager
    if any(word in prompt_lower for word in ["subvención", "subvenciones", "beca", "becas", "convocatoria", "financiación", "ayuda"]):
        print(f"✅ KEYWORD: ayudas/subvenciones → ayudas_manager")
        return "ayudas_manager"
    
    # ============================================================
    # 6. FALLBACK: Preguntamos a Gemini
    # ============================================================
    
    print(f"\n⚠️ NO HAY MATCH DIRECTO → Preguntando a Gemini...")
    
    tools_list = ", ".join(TOOLS.keys())
    question = f"""Analiza este comando del usuario: "{prompt}"

Herramientas disponibles: {tools_list}

REGLAS ESTRICTAS:
- Si menciona "plantillas", "plantilla", "datos", "mapeo", "rellenar", "documento" → document_filler
- Si menciona "espectros", "espectro", "RMN", "NMR" → rmn_spectrum_cleaner
- Si menciona "ayudas", "subvenciones", "becas", "convocatoria" → ayudas_manager
- Si menciona "notificaciones", "papers", "patentes", "emails" → notifications
- Si menciona "buscar", "búsqueda", "web" → web_search
- Si es una operación matemática → calculator
- Si pide generar código → code_gen
- Si pide guardar una nota → note

Responde SOLO con el nombre exacto de la herramienta (sin puntos, comillas ni explicaciones)."""
    
    try:
        response = model.generate_content(question)
        result = response.text.strip().lower().replace('"', '').replace("'", '').replace('.', '').replace(',', '')
        print(f"🤖 Gemini eligió: '{result}'")
        
        if result in TOOLS:
            return result
        
        # Si Gemini responde algo no válido, buscar en la respuesta
        for tool in TOOLS.keys():
            if tool in result:
                print(f"✅ Encontrado '{tool}' en respuesta de Gemini")
                return tool
        
        print(f"⚠️ Gemini devolvió algo inválido: '{result}' → usando web_search como fallback")
        return "web_search"
        
    except Exception as e:
        print(f"❌ Error de Gemini: {e} → usando web_search como fallback")
        return "web_search"


def use_tool(tool_name: str, data: str) -> str:
    # Caso especial para ver mapeos
    if tool_name == "document_filler" and "ver mapeo:" in data.lower():
        nombre_mapeo = data.split(":", 1)[1].strip()
        return obtener_mapeo(nombre_mapeo)
    
    if tool_name not in TOOLS:
        return f"❌ No existe la herramienta '{tool_name}'"
    
    try:
        module = importlib.import_module(TOOLS[tool_name])
        return module.run(data)
    except Exception as e:
        return f"❌ ERROR al usar la herramienta {tool_name}: {e}"


def agent_loop():
    print("🤖 Agente inteligente con Gemini listo para ayudarte.")
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        user_input = input("🧠 Tú: ")
        if user_input.lower().strip() == "salir":
            print("👋 Hasta luego")
            break
        
        tool = ask_gemini_for_tool(user_input)
        print(f"🔧 Herramienta: {tool}")
        result = use_tool(tool, user_input)
        print(f"📦 Resultado:\n{result}\n")


if __name__ == "__main__":
    agent_loop()