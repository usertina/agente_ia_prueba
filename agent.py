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
    "document_filler": "tools.document_filler",
    "rmn_spectrum_cleaner": "tools.rmn_spectrum_cleaner",
    "ayudas_manager": "tools.ayudas_manager"  # Nueva herramienta
}

def ask_gemini_for_tool(prompt: str) -> str:
    prompt_lower = prompt.lower()  # <-- definir al inicio

    # Si el prompt es una URL, usar web_open automáticamente
    url_pattern = r"(https?://[^\s]+)"
    if re.match(url_pattern, prompt.strip()):
        return "web_open"
    
     # Detección específica por patrón de archivo científico
    scientific_file_patterns = [
        r'mz\d+.*\.csv',  # Archivos tipo MZ0031_algo.csv
        r'.*_array.*\.csv',  # Archivos con _array_
        r'.*_cut.*\.csv',    # Archivos con _cut
        r'.*pfos.*\.csv',    # Archivos con pfos
        r'.*pfas.*\.csv',    # Archivos con pfas
    ]
    
    for pattern in scientific_file_patterns:
        if re.search(pattern, prompt_lower) and any(cmd in prompt_lower for cmd in ["analizar", "limpiar", "comparar"]):
            return "rmn_spectrum_cleaner"
    
    # Si el prompt contiene "analizar:" seguido de .csv, probablemente es espectro
    if "analizar:" in prompt_lower and ".csv" in prompt_lower:
        return "rmn_spectrum_cleaner"

    # Palabras clave de generación de código
    code_gen_keywords = [
        "generar", "genera", "crear", "crea", "escribir", "escribe",
        "codigo", "código", "script", "programa", "función", "funcion",
        "algoritmo", "clase", "app", "aplicación", "aplicacion"
    ]

    # Palabras clave de notificaciones (completa)
    notification_keywords = [
        # Comandos de listado
        "listar", "listar 10", "listar 20", "listar papers", "listar patentes", "listar patents",
        "ver", "mostrar", "ver recientes", "últimas", "últimos", "recientes",
        # Comandos de gestión
        "resumen", "desglose", "borrar", "eliminar", "borrar papers", "eliminar papers",
        "borrar todo", "eliminar todo", "limpiar", "reset", "clear",
        # Tipos de notificación
        "papers", "patentes", "emails", "notificaciones", "tipo", "tipos",
        # Identificadores y referencias
        "ID", "id", "identificador", "ref", "referencia",
        # Acciones generales
        "gestionar", "administrar", "control", "verificar", "consultar",
        # Otros términos relacionados
        "notificacion", "notificación", "alerta", "avisar", "aviso",
        "email", "correo", "patente", "paper", "científico",
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

   # En agent.py, reemplaza la sección de rmn_keywords con esto:

    # Palabras clave de espectros RMN - EXPANDIDA
    rmn_keywords = [
        # RMN tradicional
        "rmn", "espectro", "espectros", "resonancia magnética", "resonancia magnetica",
        "ruido", "limpiar espectro", "filtrar", "savgol", "gaussian", "mediana",
        "wiener", "línea base", "linea base", "snr", "señal ruido",
        "ppm", "intensidad", "picos", "analizar espectro", "limpiar auto",
        "comparar espectro", "exportar espectro", "nmr", "spectrum", "noise",
        "baseline", "peaks", "chemical shift", "listar espectros",
    
        # Análisis químico y contaminantes - NUEVO
        "pfos", "pfas", "contaminante", "contaminantes", "array", "cutref",
        "cromatografia", "cromatografía", "espectrometria", "espectrometría",
        "masas", "gc-ms", "lc-ms", "hplc", "uplc", "mz",
    
        # Detección más específica para archivos de datos
        "_array_", "_cut", "_ref", "datos analíticos", "datos analiticos",
        "procesar datos", "limpiar datos", "filtrar datos"
    ]

    # Palabras clave de ayudas/subvenciones
    ayudas_keywords = [
        "ayudas", "ayuda", "subvención", "subvenciones", "subvencion",
        "beca", "becas", "financiación", "financiacion", "fondos",
        "convocatoria", "convocatorias", "euskadi", "gipuzkoa",
        "spri", "europea", "next generation", "bdns"
    ]
    
    if any(keyword in prompt_lower for keyword in ayudas_keywords):
        return "ayudas_manager"
    

    # Revisar espectros RMN PRIMERO (nueva herramienta)
    if any(keyword in prompt_lower for keyword in rmn_keywords):
        return "rmn_spectrum_cleaner"

    # Revisar documentos SEGUNDO (antes que notificaciones para evitar conflictos)
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
        f"Si es para espectros RMN o análisis químico usa 'rmn_spectrum_cleaner'. "
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