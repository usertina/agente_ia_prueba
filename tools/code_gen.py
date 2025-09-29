import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

CODE_DIR = "code"
os.makedirs(CODE_DIR, exist_ok=True)

def run(prompt: str) -> str:
    """
    Genera código basado en una descripción y lo guarda automáticamente.
    
    Formatos soportados:
    1. "generar: descripción del código" -> genera y guarda con nombre automático
    2. "archivo.py||generar: descripción" -> genera y guarda con nombre específico
    3. "archivo.py||descripción del código" -> genera y guarda con nombre específico
    4. "descripción del código" -> solo genera sin guardar
    """
    
    if not prompt.strip():
        return "ERROR: Debes proporcionar una descripción para generar código."
    
    # Determinar si hay un nombre de archivo específico
    filename = None
    description = prompt.strip()
    
    # Caso: archivo.py||descripción
    if "||" in prompt:
        parts = prompt.split("||", 1)
        filename = parts[0].strip()
        description = parts[1].strip()
    
    # Limpiar la descripción si empieza con "generar:"
    if description.lower().startswith("generar:"):
        description = description[8:].strip()
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Prompt mejorado para generar código más específico
        enhanced_prompt = f"""
        Genera código limpio y funcional para la siguiente descripción:
        {description}
        
        Instrucciones:
        - Solo devuelve el código, sin explicaciones adicionales
        - Incluye comentarios en español cuando sea necesario
        - Asegúrate de que el código sea funcional y siga buenas prácticas
        - Si es Python, incluye las importaciones necesarias al inicio
        """
        
        response = model.generate_content(enhanced_prompt)
        generated_code = response.text.strip()
        
        # Limpiar el código generado (remover markdown si existe)
        if generated_code.startswith("```"):
            lines = generated_code.split('\n')
            # Remover primera línea si es ```python o similar
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remover última línea si es ```
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            generated_code = '\n'.join(lines)
        
        # Generar nombre automático si no se especificó uno
        if not filename:
            # Crear nombre basado en el contenido y timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if "python" in description.lower() or "script" in description.lower():
                filename = f"codigo_generado_{timestamp}.py"
            elif "html" in description.lower() or "web" in description.lower():
                filename = f"codigo_generado_{timestamp}.html"
            elif "css" in description.lower():
                filename = f"codigo_generado_{timestamp}.css"
            elif "js" in description.lower() or "javascript" in description.lower():
                filename = f"codigo_generado_{timestamp}.js"
            else:
                filename = f"codigo_generado_{timestamp}.txt"
        
        # Guardar el archivo (siempre guardamos si se usa code_gen)
        file_path = os.path.join(CODE_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        
        return f"✅ Código generado y guardado en {filename}\n\nPreview:\n{generated_code[:200]}{'...' if len(generated_code) > 200 else ''}"
        
    except Exception as e:
        return f"ERROR al generar código: {e}"

def extraer_nombre_sugerido(descripcion: str) -> str:
    """
    Intenta extraer un nombre de archivo apropiado de la descripción.
    """
    descripcion_lower = descripcion.lower()
    
    # Palabras clave para diferentes tipos de archivos
    if any(palabra in descripcion_lower for palabra in ["calculadora", "calc"]):
        return "calculadora.py"
    elif any(palabra in descripcion_lower for palabra in ["juego", "game"]):
        return "juego.py"
    elif any(palabra in descripcion_lower for palabra in ["web", "html", "pagina"]):
        return "pagina.html"
    elif any(palabra in descripcion_lower for palabra in ["api", "servidor", "server"]):
        return "servidor.py"
    elif any(palabra in descripcion_lower for palabra in ["bot", "chatbot"]):
        return "bot.py"
    else:
        return None
