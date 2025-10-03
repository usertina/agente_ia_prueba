# main.py - VERSIÓN OPTIMIZADA PARA RENDER
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import io
import json
from docx import Document
from tools.document_filler import document_filler

import schedule
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Imports locales
from agent import use_tool, ask_gemini_for_tool
from multi_user_notification_system import multi_user_system
from tools.rmn_spectrum_cleaner import rmn_cleaner

load_dotenv()

# ============= CONFIGURACIÓN DE LA APLICACIÓN =============

app = FastAPI(title="Agente Gemini", version="2.0.0")

# CORS para Render (permitir todas las origins en desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominio exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Headers de seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# ============= CONFIGURACIÓN DE DIRECTORIOS =============

DIRECTORIES = {
    "CODE_DIR": "code",
    "NOTES_DIR": "notes",
    "TEMPLATES_DIR": "templates_docs",
    "DATA_DIR": "data_docs",
    "OUTPUT_DIR": "output_docs",
    "RMN_INPUT_DIR": "rmn_spectra/input",
    "RMN_OUTPUT_DIR": "rmn_spectra/output",
    "RMN_PLOTS_DIR": "rmn_spectra/plots",
    "CACHE_DIR": "cache"
}

# Crear todos los directorios necesarios
for dir_path in DIRECTORIES.values():
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# ============= FUNCIONES HELPER (UTILITIES) =============

class Utils:
    """Utilidades compartidas para evitar duplicación"""
    
    @staticmethod
    def clean_nan_for_json(obj):
        """Limpia NaN/Inf para serialización JSON segura"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: Utils.clean_nan_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Utils.clean_nan_for_json(v) for v in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)
        elif hasattr(obj, 'item'):  # numpy types
            return Utils.clean_nan_for_json(obj.item())
        return obj
    
    @staticmethod
    def get_client_info(request: Request) -> dict:
        """Extrae información del cliente - Compatible con Render y proxies"""
        # En Render, la IP real viene en X-Forwarded-For
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Tomar la primera IP de la lista (cliente original)
            ip = forwarded_for.split(",")[0].strip()
        elif request.headers.get("x-real-ip"):
            # Fallback a X-Real-IP
            ip = request.headers.get("x-real-ip")
        else:
            # Último fallback
            ip = request.client.host if request.client else "unknown"
        
        user_agent = request.headers.get("user-agent", "unknown")
        
        return {
            "ip": ip,
            "user_agent": user_agent,
        }
    
    @staticmethod
    def get_current_user_id(request: Request) -> str:
        """Obtiene el user_id único del usuario actual"""
        client_info = Utils.get_client_info(request)
        return multi_user_system.generate_user_id(
            client_info["ip"], 
            client_info["user_agent"]
        )
    
    @staticmethod
    def format_file_info(file_path: str) -> dict:
        """Formatea información de archivo de manera consistente"""
        try:
            stats = os.stat(file_path)
            return {
                'name': os.path.basename(file_path),
                'size': stats.st_size,
                'modified': stats.st_mtime,
                'type': os.path.splitext(file_path)[1][1:]
            }
        except:
            return None

# ============= MANEJADORES DE COMANDOS =============

class CommandHandler:
    """Centraliza el manejo de comandos para evitar duplicación"""
    
    @staticmethod
    async def process_command(user_input: str, user_id: str) -> dict:
        """Procesa un comando y retorna respuesta estructurada"""
        user_input_strip = user_input.strip().lower()
        
        # ============================================================
        # COMANDOS EXACTOS Y ESPECÍFICOS (MÁXIMA PRIORIDAD)
        # ============================================================
        
        # Comandos de notas (exactos)
        if user_input_strip in ["leer", "borrar", "descargar", "contar"]:
            tool = "note"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # Comandos de notas con prefijo
        if user_input_strip.startswith("guardar:") or user_input_strip.startswith("buscar:"):
            tool = "note"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # ============================================================
        # COMANDOS DE DOCUMENTOS (ANTES QUE NOTIFICACIONES)
        # ============================================================
        
        if any(phrase in user_input_strip for phrase in [
            "listar plantillas",
            "listar datos", 
            "plantilla",
            "rellenar:",
            "analizar plantilla",
            "crear ejemplo datos",
            "usar plantilla:",
            "convertir a json"
        ]):
            tool = "document_filler"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # ============================================================
        # COMANDOS DE RMN (ANTES QUE NOTIFICACIONES)
        # ============================================================
        
        if any(phrase in user_input_strip for phrase in [
            "listar espectros",
            "limpiar:", "analizar:", "comparar:", "exportar:",
            "espectro", "espectros",
            "limpiar auto:",
            "métodos rmn"
        ]):
            tool = "rmn_spectrum_cleaner"
            from tools.rmn_spectrum_cleaner import rmn_cleaner
            result = rmn_cleaner.run(user_input)
            return {"tool": tool, "result": result}
        
        # ============================================================
        # COMANDOS DE NOTIFICACIONES (SOLO MUY ESPECÍFICOS)
        # ============================================================
        
        # Solo comandos exactos o muy específicos de notificaciones
        if (user_input_strip in ["status", "debug", "test", "probar", "resumen", "start", "iniciar", "stop", "detener"]) or \
        any(phrase in user_input_strip for phrase in [
            "listar notificaciones",
            "listar papers",
            "listar patentes", 
            "listar emails",
            "activar emails",
            "activar patentes",
            "activar papers",
            "desactivar emails",
            "desactivar patentes",
            "desactivar papers"
        ]) or \
        user_input_strip.startswith("keywords") or \
        user_input_strip.startswith("categories:") or \
        user_input_strip.startswith("borrar notif"):
            
            tool = "notifications"
            import tools.notifications as notif_tool
            notif_tool.set_current_user_id(user_id)
            result = notif_tool.run(user_input)
            return {"tool": tool, "result": result}
        
        # ============================================================
        # COMANDOS DE GENERACIÓN DE CÓDIGO
        # ============================================================
        
        if any(keyword in user_input_strip for keyword in ["generar", "genera", "crear codigo"]):
            tool = "code_gen"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # ============================================================
        # FALLBACK: Usar ask_gemini_for_tool
        # ============================================================

        # Si no coincide con ningún comando específico, usar el sistema de detección
        tool = ask_gemini_for_tool(user_input).lower().strip()  # normalizar a minúsculas
        print(f"🔧 Gemini eligió herramienta: {tool}")

        # Diccionario de herramientas que necesitan user_id
        tool_mapping = {
            "notifications": "notifications",
            "ayudas_manager": "ayudas_manager",
            "patents": "patents_manager",
            "papers": "papers_manager"
        }

        if tool in tool_mapping:
            mod_name = tool_mapping[tool]
            mod = __import__(f"tools.{mod_name}", fromlist=["run"])
            if tool == "notifications":
                mod.set_current_user_id(user_id)
            
            result = mod.run(user_input, user_id)
            return {"tool": tool, "result": result}


        # Si no está en la lista de herramientas especiales, usar use_tool genérico
        result = use_tool(tool, user_input)
        return {"tool": tool, "result": result}
                
# ============= SERVICE WORKER =============

@app.get("/sw.js")
async def service_worker():
    """Sirve el Service Worker desde la raíz para registro correcto"""
    return FileResponse(
        "static/sw.js", 
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache"
        }
    )

# ============= GESTORES DE ARCHIVOS =============

class FileManager:
    """Centraliza operaciones de archivos para evitar duplicación"""
    
    @staticmethod
    async def upload_file(file: UploadFile, directory: str, allowed_extensions: list) -> dict:
        """Maneja upload genérico de archivos"""
        try:
            file_extension = '.' + file.filename.split('.')[-1].lower()
            
            if file_extension not in allowed_extensions:
                return {
                    "success": False,
                    "error": f"Formato no soportado. Use: {', '.join(allowed_extensions)}"
                }
            
            file_path = os.path.join(directory, file.filename)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return {
                "success": True,
                "message": f"Archivo {file.filename} subido correctamente",
                "filename": file.filename,
                "location": f"{directory}/{file.filename}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def list_files(directory: str, extensions: list) -> list:
        """Lista archivos de un directorio con extensiones específicas"""
        files = []
        if not os.path.exists(directory):
            return files
            
        for filename in os.listdir(directory):
            if any(filename.endswith(ext) for ext in extensions):
                file_path = os.path.join(directory, filename)
                file_info = Utils.format_file_info(file_path)
                if file_info:
                    files.append(file_info)
        
        return files
    
    @staticmethod
    async def delete_file(directory: str, filename: str) -> dict:
        """Elimina un archivo de manera segura"""
        try:
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return {"success": True, "message": f"{filename} eliminado correctamente"}
            else:
                return {"success": False, "error": f"No se encontró {filename}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============= ENDPOINTS PRINCIPALES =============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal con auto-registro de usuario"""
    try:
        client_info = Utils.get_client_info(request)
        device_info = {
            'device_name': f'Web-{client_info["user_agent"][:20]}...',
            'device_id': f'web_{client_info["ip"].replace(".", "_")}'
        }
        
        user_id, session_id, config = multi_user_system.register_user(
            client_info["ip"], 
            client_info["user_agent"], 
            device_info
        )
        
        print(f"📱 Usuario registrado: {user_id[:12]}... desde {client_info['ip']}")
        
    except Exception as e:
        print(f"⚠️ Error registrando usuario: {e}")
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask")
async def ask(request: Request, user_input: str = Form(...)):
    """Endpoint principal para procesar comandos del usuario"""
    user_id = Utils.get_current_user_id(request)
    print(f"🔄 Procesando comando '{user_input}' para usuario {user_id[:12]}...")
    
    try:
        # Procesar comando
        command_result = await CommandHandler.process_command(user_input, user_id)
        
        # Limpiar resultado de NaN
        result = command_result["result"]
        if isinstance(result, dict):
            result = Utils.clean_nan_for_json(result)
        
        # Determinar tipo de respuesta
        if isinstance(result, dict) and "type" in result:
            result_type = result["type"]
        elif isinstance(result, list):
            result_type = "list"
        elif isinstance(result, dict) and "url" in result:
            result_type = "open_url"
        else:
            result_type = "text"
        
        return JSONResponse({
            "result_type": result_type,
            "result_data": result,
            "input": user_input,
            "tool": command_result["tool"]
        })
        
    except Exception as e:
        print(f"❌ Error procesando comando: {e}")
        return JSONResponse({
            "result_type": "error",
            "result_data": f"Error: {str(e)}",
            "input": user_input,
            "tool": "error"
        }, status_code=500)

# ============= ENDPOINTS DE ARCHIVOS =============

@app.get("/files")
async def get_files():
    """Lista archivos guardados de código y notas"""
    try:
        code_files = FileManager.list_files(
            DIRECTORIES["CODE_DIR"], 
            ['.py', '.js', '.html', '.css', '.txt']
        )
        
        notes_path = os.path.join(DIRECTORIES["NOTES_DIR"], "notas.txt")
        notes_exist = os.path.exists(notes_path)
        notes_count = 0
        
        if notes_exist:
            try:
                with open(notes_path, "r", encoding="utf-8") as f:
                    notes_count = len([line for line in f if line.strip()])
            except:
                pass
        
        return JSONResponse({
            "code_files": [f['name'] for f in code_files],
            "notes_exist": notes_exist,
            "notes_count": notes_count
        })
    except Exception as e:
        return JSONResponse({
            "code_files": [],
            "notes_exist": False,
            "notes_count": 0,
            "error": str(e)
        })

# ============= ENDPOINTS DE DOCUMENTOS =============

@app.post("/upload/template")
async def upload_template(file: UploadFile = File(...)):
    """Sube plantilla de documento"""
    try:
        result = await FileManager.upload_file(
            file, 
            DIRECTORIES["TEMPLATES_DIR"],
            ['.docx', '.txt', '.pdf']
        )
        
        if result["success"]:
            result["next_step"] = f"Analiza la plantilla con: 'analizar: {file.filename}'"
        
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/files/documents")
async def get_document_files():
    """Obtiene lista de archivos de documentos (FILTRADO - sin archivos del sistema)"""
    try:
        templates = FileManager.list_files(
            DIRECTORIES["TEMPLATES_DIR"],
            ['.docx', '.txt', '.pdf']
        )
        
        # Obtener TODOS los archivos de datos
        all_data_files = FileManager.list_files(
            DIRECTORIES["DATA_DIR"],
            ['.json', '.csv', '.xlsx', '.txt']
        )
        
        # FILTRAR archivos que empiezan con _ (archivos del sistema)
        data_files = [f for f in all_data_files if not f['name'].startswith('_')]
        
        output_files = FileManager.list_files(
            DIRECTORIES["OUTPUT_DIR"],
            ['.docx', '.txt', '.pdf']
        )
        
        return JSONResponse({
            "templates": templates,
            "data_files": data_files,
            "output_files": output_files,
            "total": len(templates) + len(data_files) + len(output_files)
        })
    except Exception as e:
        return JSONResponse({
            "templates": [],
            "data_files": [],
            "output_files": [],
            "total": 0,
            "error": str(e)
        })

@app.post("/fill/template")
async def fill_template(template_filename: str = Form(...)):
    """
    Rellena plantilla automáticamente y devuelve información completa del archivo generado
    """
    try:
        # Usar el sistema completo de document_filler
        result = document_filler.auto_fill_with_database(template_filename)
        
        # Si el resultado es un string (error o mensaje)
        if isinstance(result, str):
            success = "✅" in result or "éxito" in result.lower() or "generado" in result.lower()
            
            # Intentar extraer el nombre del archivo del mensaje
            output_filename = None
            if success:
                import re
                match = re.search(r'Archivo:\s*([^\n]+\.(?:docx|txt|pdf))', result)
                if match:
                    output_filename = match.group(1).strip()
            
            return JSONResponse({
                "success": success,
                "message": result,
                "output_file": output_filename,
                "template": template_filename,
                "download_url": f"/download/output/{output_filename}" if output_filename else None
            })
        
        # Si es un diccionario (respuesta estructurada)
        if isinstance(result, dict):
            # Extraer información del mensaje si no está en el dict
            output_filename = result.get("output_file")
            
            if not output_filename and 'message' in result:
                import re
                match = re.search(r'Archivo:\s*([^\n]+\.(?:docx|txt|pdf))', result['message'])
                if match:
                    output_filename = match.group(1).strip()
            
            return JSONResponse({
                "success": True,
                "message": result.get("message", "✅ Documento generado exitosamente"),
                "output_file": output_filename,
                "template": template_filename,
                "statistics": {
                    "total_fields": result.get("total_campos", 0),
                    "from_database": result.get("desde_bd", 0),
                    "from_ai": result.get("desde_ia", 0)
                },
                "download_url": f"/download/output/{output_filename}" if output_filename else None
            })
        
        # Fallback
        return JSONResponse({
            "success": False,
            "message": "Error desconocido en el procesamiento",
            "template": template_filename
        }, status_code=500)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error en fill_template: {e}\n{error_trace}")
        
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": f"❌ Error procesando plantilla: {e}",
            "template": template_filename
        }, status_code=500)

@app.get("/master-data")
async def get_master_data():
    """Obtiene los datos maestros actuales del usuario"""
    try:
        return JSONResponse({
            "success": True,
            "data": document_filler.user_database
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/master-data")
async def update_master_data(data: dict):
    """Actualiza los datos maestros del usuario"""
    try:
        result = document_filler.update_master_database(data)
        
        return JSONResponse({
            "success": "✅" in result,
            "message": result
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/analyze/template")
async def analyze_template(template_filename: str):
    """Analiza qué campos necesita una plantilla"""
    try:
        result = document_filler.analyze_template(template_filename)
        
        return JSONResponse({
            "success": True,
            "analysis": result
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.delete("/delete/output/{filename}")
async def delete_output_file(filename: str):
    """Elimina documento generado"""
    file_path = os.path.join(DIRECTORIES["OUTPUT_DIR"], filename)
    
    if os.path.exists(file_path):
        result = await FileManager.delete_file(DIRECTORIES["OUTPUT_DIR"], filename)
        return JSONResponse(result, status_code=200 if result["success"] else 404)
    else:
        return JSONResponse({
            "success": False,
            "error": "El archivo no se encuentra."
        }, status_code=404)

@app.delete("/delete/template/{filename}")
async def delete_template(filename: str):
    """Elimina plantilla"""
    file_path = os.path.join(DIRECTORIES["TEMPLATES_DIR"], filename)
    
    if os.path.exists(file_path):
        result = await FileManager.delete_file(DIRECTORIES["TEMPLATES_DIR"], filename)
        return JSONResponse(result, status_code=200 if result["success"] else 404)
    else:
        return JSONResponse({
            "success": False,
            "error": f"El archivo '{filename}' no se encuentra en la carpeta de plantillas."
        }, status_code=404)

@app.delete("/delete/data/{filename}")
async def delete_data_file(filename: str):
    """Elimina archivo de datos (PROTEGIDO contra archivos maestros)"""
    
    # ✅ PROTECCIÓN: No permitir borrar archivos que empiecen con _
    if filename.startswith('_'):
        return JSONResponse({
            "success": False,
            "error": "❌ Este es un archivo del sistema y no puede ser eliminado."
        }, status_code=403)
    
    file_path = os.path.join(DIRECTORIES["DATA_DIR"], filename)
    
    if os.path.exists(file_path):
        result = await FileManager.delete_file(DIRECTORIES["DATA_DIR"], filename)
        return JSONResponse(result, status_code=200 if result["success"] else 404)
    else:
        return JSONResponse({
            "success": False,
            "error": "El archivo no se encuentra."
        }, status_code=404)

# ============= ENDPOINTS DE ESPECTROS RMN =============

@app.post("/upload/spectrum")
async def upload_spectrum(file: UploadFile = File(...)):
    """Sube espectro RMN"""
    result = await FileManager.upload_file(
        file,
        DIRECTORIES["RMN_INPUT_DIR"],
        ['.csv', '.txt', '.dat', '.asc', '.json']
    )
    
    if result["success"]:
        result["next_step"] = f"Analiza el espectro con: 'analizar: {file.filename}'"
    
    return JSONResponse(result)

@app.get("/files/spectra")
async def get_spectra_files():
    """Obtiene lista de archivos de espectros"""
    try:
        spectra = FileManager.list_files(
            DIRECTORIES["RMN_INPUT_DIR"],
            ['.csv', '.txt', '.dat', '.asc', '.json']
        )
        
        cleaned = FileManager.list_files(
            DIRECTORIES["RMN_OUTPUT_DIR"],
            ['.csv']
        )
        
        plots = FileManager.list_files(
            DIRECTORIES["RMN_PLOTS_DIR"],
            ['.png']
        )
        
        # Clasificar plots
        for plot in plots:
            plot['plot_type'] = 'analysis' if plot['name'].startswith('analysis_') else 'comparison'
        
        return JSONResponse({
            "spectra": spectra,
            "cleaned": cleaned,
            "plots": plots,
            "total": len(spectra) + len(cleaned) + len(plots)
        })
    except Exception as e:
        return JSONResponse({
            "spectra": [],
            "cleaned": [],
            "plots": [],
            "total": 0,
            "error": str(e)
        })

@app.delete("/delete/spectrum/{filename}")
async def delete_spectrum(filename: str):
    """Elimina espectro original"""
    result = await FileManager.delete_file(DIRECTORIES["RMN_INPUT_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

@app.delete("/delete/cleaned/{filename}")
async def delete_cleaned_spectrum(filename: str):
    """Elimina espectro limpio"""
    result = await FileManager.delete_file(DIRECTORIES["RMN_OUTPUT_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

@app.delete("/delete/plot/{filename}")
async def delete_plot(filename: str):
    """Elimina gráfico"""
    result = await FileManager.delete_file(DIRECTORIES["RMN_PLOTS_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

# ============= ENDPOINTS DE DESCARGA =============

class DownloadHandler:
    """Maneja todas las descargas de manera unificada"""
    
    @staticmethod
    async def download_file(directory: str, filename: str, category: str):
        """Descarga genérica de archivos"""
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                filename=filename,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        raise HTTPException(status_code=404, detail=f"No se encontró {category}: {filename}")

@app.get("/download/notes")
async def download_notes():
    """Descarga archivo de notas"""
    return await DownloadHandler.download_file(
        DIRECTORIES["NOTES_DIR"], 
        "notas.txt", 
        "las notas"
    )

@app.get("/download/code/{filename}")
async def download_code(filename: str):
    """Descarga archivo de código"""
    return await DownloadHandler.download_file(
        DIRECTORIES["CODE_DIR"],
        filename,
        "el archivo"
    )

@app.get("/download/template/{filename}")
async def download_template(filename: str):
    """Descarga plantilla"""
    return await DownloadHandler.download_file(
        DIRECTORIES["TEMPLATES_DIR"],
        filename,
        "la plantilla"
    )

@app.get("/download/data/{filename}")
async def download_data_file(filename: str):
    """Descarga archivo de datos"""
    return await DownloadHandler.download_file(
        DIRECTORIES["DATA_DIR"],
        filename,
        "el archivo de datos"
    )

@app.get("/download/output/{filename}")
async def download_output_file(filename: str):
    """Descarga documento generado"""
    return await DownloadHandler.download_file(
        DIRECTORIES["OUTPUT_DIR"],
        filename,
        "el documento"
    )

@app.get("/download/spectrum/{filename}")
async def download_spectrum(filename: str):
    """Descarga espectro original"""
    return await DownloadHandler.download_file(
        DIRECTORIES["RMN_INPUT_DIR"],
        filename,
        "el espectro"
    )

@app.get("/download/cleaned/{filename}")
async def download_cleaned_spectrum(filename: str):
    """Descarga espectro limpio"""
    return await DownloadHandler.download_file(
        DIRECTORIES["RMN_OUTPUT_DIR"],
        filename,
        "el espectro limpio"
    )

@app.get("/download/plot/{filename}")
async def download_plot(filename: str):
    """Descarga gráfico"""

    possible_filenames = [
        f"plots{filename[6:]}",  # si el nombre comienza con "analysis", reemplazarlo por "plots"
        filename  # la versión con "analysis"
    ]

    for possible_filename in possible_filenames:
        file_path = os.path.join(DIRECTORIES["RMN_PLOTS_DIR"], possible_filename)
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                filename=possible_filename,
                media_type="image/png",
                headers={"Content-Disposition": f"attachment; filename={possible_filename}"}
            )

    raise HTTPException(status_code=404, detail=f"No se encontró el gráfico: {filename}")
# ============= ENDPOINTS DE NOTIFICACIONES =============

@app.post("/notifications/register")
async def register_user(request: Request):
    """Registra usuario para notificaciones"""
    try:
        client_info = Utils.get_client_info(request)
        
        try:
            body = await request.json()
            device_info = body
        except:
            device_info = {
                'device_name': f'Web-{client_info["user_agent"][:20]}...',
                'device_id': f'web_{client_info["ip"].replace(".", "_")}'
            }
        
        user_id, session_id, config = multi_user_system.register_user(
            client_info["ip"],
            client_info["user_agent"],
            device_info
        )
        
        print(f"📱 Usuario registrado exitosamente: {user_id[:12]}...")
        
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "session_id": session_id,
            "config": config,
            "device_name": device_info.get('device_name', 'Dispositivo Desconocido')
        })
    except Exception as e:
        print(f"❌ Error registrando usuario: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/notifications/user/{user_id}")
async def get_user_notifications(request: Request, user_id: str):
    """Obtiene notificaciones pendientes de un usuario"""
    try:
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        notifications = multi_user_system.get_pending_notifications(user_id)
        
        return JSONResponse({
            "success": True,
            "notifications": notifications,
            "count": len(notifications),
            "user_id": user_id
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo notificaciones: {e}")
        return JSONResponse({
            "success": False,
            "notifications": [],
            "count": 0,
            "error": str(e)
        })

@app.post("/notifications/user/{user_id}/test")
async def send_test_notification(request: Request, user_id: str):
    """Envía notificación de prueba a un usuario"""
    try:
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        config = multi_user_system.get_user_config(user_id)
        device_name = config.get('device_name', 'tu dispositivo')
        
        multi_user_system.add_notification(
            user_id,
            'test',
            '🧪 Notificación de Prueba',
            f'El sistema funciona correctamente en {device_name}',
            {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id[:8],
                'device_name': device_name
            }
        )
        
        print(f"🧪 Notificación de prueba enviada a {user_id[:12]}...")
        
        return JSONResponse({
            "success": True,
            "message": "Notificación de prueba enviada"
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error enviando notificación de prueba: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error: {str(e)}"
        }, status_code=500)

# ============= NUEVOS ENDPOINTS PARA HISTORIAL DE NOTIFICACIONES =============

@app.get("/notifications/user/{user_id}/history")
async def get_notification_history(request: Request, user_id: str):
    """Obtiene el historial completo de notificaciones de un usuario"""
    try:
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Obtener todas las notificaciones (últimas 50)
        notifications = multi_user_system.get_all_notifications(user_id, limit=50, include_delivered=True)
        
        # Contar no leídas (asumiendo que delivered=False significa no leída)
        unread_count = len([n for n in notifications if not n.get('delivered', True)])
        
        return JSONResponse({
            "success": True,
            "notifications": notifications,
            "total": len(notifications),
            "unread_count": unread_count
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo historial: {e}")
        return JSONResponse({
            "success": False,
            "notifications": [],
            "total": 0,
            "unread_count": 0,
            "error": str(e)
        })

@app.post("/notifications/mark-read/{notification_id}")
async def mark_notification_read(request: Request, notification_id: int):
    """Marca una notificación como leída"""
    try:
        body = await request.json()
        user_id = body.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id requerido")
        
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Marcar como entregada/leída en la base de datos
        with multi_user_system.get_db_connection() as conn:
            # Verificar que la notificación pertenece al usuario
            notif = conn.execute(
                "SELECT id FROM notifications WHERE id = ? AND user_id = ?",
                (notification_id, user_id)
            ).fetchone()
            
            if not notif:
                raise HTTPException(status_code=404, detail="Notificación no encontrada")
            
            # Marcar como leída
            conn.execute(
                "UPDATE notifications SET delivered = TRUE WHERE id = ?",
                (notification_id,)
            )
            conn.commit()
        
        return JSONResponse({
            "success": True,
            "message": "Notificación marcada como leída"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marcando como leída: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/notifications/mark-all-read")
async def mark_all_notifications_read(request: Request):
    """Marca todas las notificaciones de un usuario como leídas"""
    try:
        body = await request.json()
        user_id = body.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id requerido")
        
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        with multi_user_system.get_db_connection() as conn:
            result = conn.execute(
                "UPDATE notifications SET delivered = TRUE WHERE user_id = ? AND delivered = FALSE",
                (user_id,)
            )
            conn.commit()
            count = result.rowcount
        
        return JSONResponse({
            "success": True,
            "message": f"{count} notificaciones marcadas como leídas"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error marcando todas como leídas: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/notifications/clear-history")
async def clear_notification_history(request: Request):
    """Limpia el historial de notificaciones de un usuario"""
    try:
        body = await request.json()
        user_id = body.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id requerido")
        
        current_user_id = Utils.get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        count = multi_user_system.delete_all_notifications(user_id)
        
        return JSONResponse({
            "success": True,
            "message": f"{count} notificaciones eliminadas"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error limpiando historial: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# ============= ENDPOINTS AUXILIARES =============

@app.get("/view/code/{filename}")
async def view_code(filename: str):
    """Ver contenido de archivo de código"""
    file_path = os.path.join(DIRECTORIES["CODE_DIR"], filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return JSONResponse({
                "filename": filename,
                "content": content,
                "size": os.path.getsize(file_path)
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {e}")
    raise HTTPException(status_code=404, detail=f"No se encontró el archivo {filename}")

@app.get("/view/notes")
async def view_notes():
    """Ver contenido de notas"""
    file_path = os.path.join(DIRECTORIES["NOTES_DIR"], "notas.txt")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n') if content else []
            notes_count = len([line for line in lines if line.strip()])
            return JSONResponse({
                "content": content,
                "notes_count": notes_count,
                "size": os.path.getsize(file_path)
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer las notas: {e}")
    raise HTTPException(status_code=404, detail="No hay notas guardadas")

@app.get("/check/notes")
async def check_notes():
    """Verifica si existe el archivo de notas y cuenta las líneas"""
    try:
        # Usar la ruta correcta desde DIRECTORIES
        notes_path = os.path.join(DIRECTORIES["NOTES_DIR"], "notas.txt")
        
        if os.path.exists(notes_path):
            with open(notes_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n') if content else []
                # Contar líneas no vacías como notas
                notes_count = len([line for line in lines if line.strip()])
            
            return JSONResponse({
                'exists': True,
                'count': notes_count,
                'size': os.path.getsize(notes_path)
            })
        else:
            return JSONResponse({
                'exists': False,
                'count': 0
            })
            
    except Exception as e:
        print(f"❌ Error verificando notas: {e}")
        return JSONResponse({
            'error': str(e),
            'exists': False,
            'count': 0
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    try:
        return JSONResponse({
            "status": "healthy",
            "notifications_system": "active" if multi_user_system.running else "inactive",
            "active_users": len(multi_user_system.get_active_users(hours=24)),
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/debug/user")
async def debug_user_info(request: Request):
    """Debug: Ver información del usuario detectado - Útil para troubleshooting en Render"""
    try:
        client_info = Utils.get_client_info(request)
        user_id = Utils.get_current_user_id(request)
        
        # Verificar si el usuario existe en BD
        with multi_user_system.get_db_connection() as conn:
            user_exists = conn.execute(
                "SELECT user_id, device_name, created_at, last_active FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        
        return JSONResponse({
            "client_ip": client_info["ip"],
            "user_agent": client_info["user_agent"][:100],
            "generated_user_id": user_id,
            "user_exists_in_db": bool(user_exists),
            "user_details": dict(user_exists) if user_exists else None,
            "all_headers": dict(request.headers),
            "forwarded_for": request.headers.get("x-forwarded-for"),
            "real_ip": request.headers.get("x-real-ip")
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "client_ip": "unknown",
            "user_agent": "unknown"
        }, status_code=500)

# ============= EVENTOS DE CICLO DE VIDA =============

@app.on_event("startup")
async def startup_event():
    """Inicializar el sistema al arrancar"""
    try:
        print("=" * 60)
        print("🚀 INICIANDO AGENTE GEMINI")
        print("=" * 60)
        
        # Inicializar base de datos
        multi_user_system.init_database()
        print("✅ Base de datos inicializada")
        
        # Verificar directorios
        for name, path in DIRECTORIES.items():
            if os.path.exists(path):
                print(f"✅ {name}: {path}")
            else:
                os.makedirs(path, exist_ok=True)
                print(f"📁 {name} creado: {path}")
        
        # Iniciar monitoreo de notificaciones en background
        success = multi_user_system.start_background_monitoring()
        if success:
            print("🔔 Sistema de notificaciones multi-usuario iniciado")
        else:
            print("⚠️ Sistema de notificaciones ya estaba ejecutándose")
        
        # Información del entorno
        port = int(os.environ.get("PORT", 8000))
        is_render = os.environ.get("RENDER", False)
        
        print("=" * 60)
        print(f"📦 Versión: 2.0.0")
        print(f"🌍 Entorno: {'Render' if is_render else 'Local'}")
        print(f"🔌 Puerto: {port}")
        print(f"📁 Directorios: {len(DIRECTORIES)}")
        print(f"🔧 Herramientas: 10+")
        print("=" * 60)
        print("✅ APLICACIÓN LISTA")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error iniciando sistema: {e}")
        import traceback
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    """Detener el sistema al cerrar"""
    try:
        print("\n" + "=" * 60)
        print("⏹️ DETENIENDO AGENTE GEMINI")
        print("=" * 60)
        
        # Detener monitoreo de notificaciones
        multi_user_system.stop_background_monitoring()
        print("🔔 Sistema de notificaciones detenido")
        
        # Guardar estadísticas finales
        active_users = len(multi_user_system.get_active_users(hours=24))
        print(f"📊 Usuarios activos últimas 24h: {active_users}")
        
        print("=" * 60)
        print("👋 APLICACIÓN CERRADA CORRECTAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"⚠️ Error deteniendo sistema: {e}")

# ============= PUNTO DE ENTRADA PRINCIPAL =============

if __name__ == "__main__":
    """Punto de entrada para ejecutar la aplicación"""
    
    # Configuración de puerto y host
    port = int(os.environ.get("PORT", 3000))
    host = "0.0.0.0"  # Importante para Render
    
    # Detectar entorno
    is_production = os.environ.get("RENDER", False) or os.environ.get("PRODUCTION", False)
    
    # Información de inicio
    print("\n" + "=" * 60)
    print("🤖 AGENTE GEMINI - SISTEMA INTELIGENTE")
    print("=" * 60)
    print(f"🚀 Iniciando servidor...")
    print(f"🌍 Entorno: {'Producción (Render)' if is_production else 'Desarrollo'}")
    print(f"🔌 Host: {host}")
    print(f"📍 Puerto: {port}")
    print(f"📍 URL local: http://localhost:{port}")
    print(f"🔔 Notificaciones: Habilitadas")
    print(f"📁 Directorios: {', '.join(DIRECTORIES.keys())}")
    print("=" * 60 + "\n")
    
    # Configuración de uvicorn según entorno
    if is_production:
        # Configuración para producción (Render)
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,  # No reload en producción
            log_level="info",
            access_log=True,
            workers=1  # Render usa 1 worker por defecto
        )
    else:
        # Configuración para desarrollo local
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,  # Hot reload en desarrollo
            log_level="debug",
            access_log=True
        )