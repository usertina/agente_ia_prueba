# main.py - VERSIÓN LIMPIA SIN DUPLICADOS
import math
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import schedule
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Imports locales
from agent import use_tool, ask_gemini_for_tool
from multi_user_notification_system import multi_user_system
from scheduler_ayudas import check_new_ayudas
from tools.rmn_spectrum_cleaner import rmn_cleaner

load_dotenv()

# ============= CONFIGURACIÓN DE LA APLICACIÓN =============

app = FastAPI(title="Agente Gemini", version="2.0.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============= CONFIGURACIÓN DE DIRECTORIOS =============

DIRECTORIES = {
    "CODE_DIR": "code",
    "NOTES_DIR": "notes",
    "TEMPLATES_DIR": "templates_docs",
    "DATA_DIR": "data_docs",
    "OUTPUT_DIR": "output_docs",
    "RMN_INPUT_DIR": "rmn_spectra/input",
    "RMN_OUTPUT_DIR": "rmn_spectra/output",
    "RMN_PLOTS_DIR": "rmn_spectra/plots"
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
        """Extrae información del cliente de la request"""
        return {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
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
        
        # Comandos de notas
        if user_input_strip in ["leer", "borrar", "descargar", "contar"] or \
           user_input_strip.startswith("guardar:") or user_input_strip.startswith("buscar:"):
            tool = "note"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # Comandos de notificaciones
        elif any(keyword in user_input_strip for keyword in [
            "status", "start", "stop", "iniciar", "detener", "test", "probar",
            "activar emails", "activar patentes", "activar papers", "debug"
        ]) or user_input_strip.startswith("keywords") or user_input_strip.startswith("categories:"):
            tool = "notifications"
            import tools.notifications as notif_tool
            notif_tool.set_current_user_id(user_id)
            result = notif_tool.run(user_input)
            return {"tool": tool, "result": result}
        
        # Comandos de generación de código
        elif any(keyword in user_input_strip for keyword in ["generar", "genera", "crear codigo"]):
            tool = "code_gen"
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}
        
        # Comandos RMN
        elif any(cmd in user_input_strip for cmd in ["limpiar:", "analizar:", "comparar:", "exportar:"]):
            tool = "rmn_spectrum_cleaner"
            result = rmn_cleaner.run(user_input)
            return {"tool": tool, "result": result}
        
        # Usar Gemini para elegir herramienta
        else:
            tool = ask_gemini_for_tool(user_input)
            print(f"🔧 Gemini eligió herramienta: {tool}")
            
            if tool == "notifications":
                import tools.notifications as notif_tool
                notif_tool.set_current_user_id(user_id)
            
            result = use_tool(tool, user_input)
            return {"tool": tool, "result": result}

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

# ============= SCHEDULER DE TAREAS =============

def start_ayudas_scheduler():
    """Ejecuta el scheduler de ayudas en background"""
    schedule.every(6).hours.do(check_new_ayudas)
    schedule.every().day.at("09:00").do(check_new_ayudas)
    schedule.every().day.at("14:00").do(check_new_ayudas)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# ============= ENDPOINTS PRINCIPALES =============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal con auto-registro de usuario"""
    try:
        client_info = Utils.get_client_info(request)
        device_info = {
            'device_name': f'Web-{client_info["user_agent"][:20]}...'
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
    result = await FileManager.upload_file(
        file, 
        DIRECTORIES["TEMPLATES_DIR"],
        ['.docx', '.txt', '.pdf']
    )
    
    if result["success"]:
        result["next_step"] = f"Analiza la plantilla con: 'analizar: {file.filename}'"
    
    return JSONResponse(result)

@app.post("/upload/data")
async def upload_data(file: UploadFile = File(...)):
    """Sube archivo de datos"""
    result = await FileManager.upload_file(
        file,
        DIRECTORIES["DATA_DIR"],
        ['.json', '.csv', '.xlsx', '.txt']
    )
    
    if result["success"]:
        result["next_step"] = f"Usa: 'rellenar: plantilla.docx con {file.filename}'"
    
    return JSONResponse(result)

@app.get("/files/documents")
async def get_document_files():
    """Obtiene lista de archivos de documentos"""
    try:
        templates = FileManager.list_files(
            DIRECTORIES["TEMPLATES_DIR"],
            ['.docx', '.txt', '.pdf']
        )
        
        data_files = FileManager.list_files(
            DIRECTORIES["DATA_DIR"],
            ['.json', '.csv', '.xlsx', '.txt']
        )
        
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

@app.delete("/delete/template/{filename}")
async def delete_template(filename: str):
    """Elimina plantilla"""
    result = await FileManager.delete_file(DIRECTORIES["TEMPLATES_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

@app.delete("/delete/data/{filename}")
async def delete_data_file(filename: str):
    """Elimina archivo de datos"""
    result = await FileManager.delete_file(DIRECTORIES["DATA_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

@app.delete("/delete/output/{filename}")
async def delete_output_file(filename: str):
    """Elimina documento generado"""
    result = await FileManager.delete_file(DIRECTORIES["OUTPUT_DIR"], filename)
    return JSONResponse(result, status_code=200 if result["success"] else 404)

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
    file_path = os.path.join(DIRECTORIES["RMN_PLOTS_DIR"], filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            filename=filename,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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

# ============= EVENTOS DE CICLO DE VIDA =============

@app.on_event("startup")
async def startup_event():
    """Inicializar el sistema al arrancar"""
    try:
        # Inicializar base de datos
        multi_user_system.init_database()
        
        # Iniciar scheduler de ayudas en thread separado
        ayudas_thread = threading.Thread(
            target=start_ayudas_scheduler,
            daemon=True
        )
        ayudas_thread.start()
        print("💶 Scheduler de ayudas iniciado")
        
        # Iniciar monitoreo de notificaciones en background
        success = multi_user_system.start_background_monitoring()
        if success:
            print("🚀 Sistema de notificaciones multi-usuario iniciado correctamente")
        else:
            print("⚠️ Sistema de notificaciones ya estaba ejecutándose")
            
        print(f"✅ Aplicación iniciada - Versión 2.0.0")
        print(f"📁 Directorios creados: {len(DIRECTORIES)}")
        print(f"🔧 Herramientas disponibles: 10+")
        
    except Exception as e:
        print(f"❌ Error iniciando sistema: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Detener el sistema al cerrar"""
    try:
        # Detener monitoreo de notificaciones
        multi_user_system.stop_background_monitoring()
        print("⏹️ Sistema de notificaciones detenido correctamente")
        print("👋 Aplicación cerrada correctamente")
        
    except Exception as e:
        print(f"⚠️ Error deteniendo sistema: {e}")

# ============= PUNTO DE ENTRADA PRINCIPAL =============

if __name__ == "__main__":
    """Punto de entrada para ejecutar la aplicación"""
    
    # Configuración de puerto y host
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Importante para Render
    
    # Información de inicio
    print("=" * 60)
    print("🤖 AGENTE GEMINI - SISTEMA INTELIGENTE")
    print("=" * 60)
    print(f"🚀 Iniciando servidor en http://{host}:{port}")
    print(f"📍 Acceso local: http://localhost:{port}")
    print(f"🔔 Sistema de notificaciones: Habilitado")
    print(f"📁 Directorios configurados: {', '.join(DIRECTORIES.keys())}")
    print("=" * 60)
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Cambiar a False en producción
        log_level="info"
    )