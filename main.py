from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from agent import use_tool, ask_gemini_for_tool
from tools.web_search import run as web_search_run
from dotenv import load_dotenv
import os
from multi_user_notification_system import multi_user_system
from datetime import datetime
import asyncio
import shutil

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

CODE_DIR = "code"
NOTES_DIR = "notes"
os.makedirs(CODE_DIR, exist_ok=True)
os.makedirs(NOTES_DIR, exist_ok=True)

# Directorios para el sistema de documentos
TEMPLATES_DIR = "templates_docs"
DATA_DIR = "data_docs"
OUTPUT_DIR = "output_docs"

for dir_path in [TEMPLATES_DIR, DATA_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

@app.post("/upload/template")
async def upload_template(file: UploadFile = File(...)):
    """Subir plantilla de documento"""
    try:
        # Validar formato
        allowed_extensions = ['.docx', '.txt', '.pdf']
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato no soportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Guardar archivo
        file_path = os.path.join(TEMPLATES_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse({
            "success": True,
            "message": f"Plantilla {file.filename} subida correctamente",
            "filename": file.filename,
            "location": f"{TEMPLATES_DIR}/{file.filename}",
            "next_step": f"Analiza la plantilla con: 'analizar: {file.filename}'"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/upload/data")
async def upload_data(file: UploadFile = File(...)):
    """Subir archivo de datos"""
    try:
        # Validar formato
        allowed_extensions = ['.json', '.csv', '.xlsx', '.txt']
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato no soportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Guardar archivo
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse({
            "success": True,
            "message": f"Archivo de datos {file.filename} subido correctamente",
            "filename": file.filename,
            "location": f"{DATA_DIR}/{file.filename}",
            "next_step": f"Usa: 'rellenar: plantilla.docx con {file.filename}'"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/files/documents")
async def get_document_files():
    """Obtener lista de archivos de documentos"""
    try:
        templates = []
        data_files = []
        output_files = []
        
        # Listar plantillas
        if os.path.exists(TEMPLATES_DIR):
            for file in os.listdir(TEMPLATES_DIR):
                if any(file.endswith(ext) for ext in ['.docx', '.txt', '.pdf']):
                    file_path = os.path.join(TEMPLATES_DIR, file)
                    templates.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path),
                        'type': 'template'
                    })
        
        # Listar datos
        if os.path.exists(DATA_DIR):
            for file in os.listdir(DATA_DIR):
                if any(file.endswith(ext) for ext in ['.json', '.csv', '.xlsx', '.txt']):
                    file_path = os.path.join(DATA_DIR, file)
                    data_files.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path),
                        'type': 'data'
                    })
        
        # Listar documentos generados
        if os.path.exists(OUTPUT_DIR):
            for file in os.listdir(OUTPUT_DIR):
                file_path = os.path.join(OUTPUT_DIR, file)
                if os.path.isfile(file_path):
                    output_files.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path),
                        'type': 'output'
                    })
        
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


@app.get("/download/template/{filename}")
async def download_template(filename: str):
    """Descargar plantilla"""
    file_path = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            filename=filename, 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    raise HTTPException(status_code=404, detail=f"No se encontró la plantilla {filename}")


@app.get("/download/data/{filename}")
async def download_data_file(filename: str):
    """Descargar archivo de datos"""
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            filename=filename, 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    raise HTTPException(status_code=404, detail=f"No se encontró el archivo {filename}")


@app.get("/download/output/{filename}")
async def download_output_file(filename: str):
    """Descargar documento generado"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            filename=filename, 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    raise HTTPException(status_code=404, detail=f"No se encontró el documento {filename}")


@app.delete("/delete/template/{filename}")
async def delete_template(filename: str):
    """Eliminar plantilla"""
    try:
        file_path = os.path.join(TEMPLATES_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return JSONResponse({
                "success": True,
                "message": f"Plantilla {filename} eliminada correctamente"
            })
        else:
            raise HTTPException(status_code=404, detail=f"No se encontró la plantilla {filename}")
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.delete("/delete/data/{filename}")
async def delete_data_file(filename: str):
    """Eliminar archivo de datos"""
    try:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return JSONResponse({
                "success": True,
                "message": f"Archivo de datos {filename} eliminado correctamente"
            })
        else:
            raise HTTPException(status_code=404, detail=f"No se encontró el archivo {filename}")
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)    


@app.on_event("startup")
async def startup_event():
    """Inicializar el sistema al startup"""
    try:
        # Inicializar la base de datos
        multi_user_system.init_database()
        
        # Iniciar monitoreo en background
        success = multi_user_system.start_background_monitoring()
        if success:
            print("🚀 Sistema de notificaciones multi-usuario iniciado correctamente")
        else:
            print("⚠️ Sistema de notificaciones ya estaba ejecutándose")
    except Exception as e:
        print(f"❌ Error iniciando sistema de notificaciones: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Detener el sistema al shutdown"""
    try:
        multi_user_system.stop_background_monitoring()
        print("⏹️ Sistema de notificaciones detenido correctamente")
    except Exception as e:
        print(f"⚠️ Error deteniendo sistema: {e}")


def get_client_info(request: Request):
    """Extrae información del cliente"""
    return {
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
    }


def get_current_user_id(request: Request) -> str:
    """Obtiene el user_id del usuario actual"""
    client_info = get_client_info(request)
    user_id = multi_user_system.generate_user_id(client_info["ip"], client_info["user_agent"])
    return user_id


def web_search_formatted(query: str):
    """Wrapper para web_search que devuelve formato apropiado para la interfaz"""
    try:
        from googleapiclient.discovery import build
        API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
        CSE_ID = os.getenv("GOOGLE_CSE_ID")
        
        if not API_KEY or not CSE_ID:
            return [{"title": "Error", "link": "", "snippet": "Google Search API no configurado"}]
        
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=CSE_ID, num=5).execute()
        items = res.get("items", [])
        
        if not items:
            return []
        
        resultados = []
        for item in items:
            resultados.append({
                "title": item.get("title", "Sin título"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "Sin descripción")
            })
        return resultados
    except Exception as e:
        return [{"title": "Error", "link": "", "snippet": f"Error en la búsqueda: {e}"}]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal"""
    try:
        # Registrar usuario automáticamente
        client_info = get_client_info(request)
        device_info = {
            'device_name': f'Web-{request.headers.get("user-agent", "Unknown")[:20]}...'
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
    """Procesar comandos del usuario"""
    user_input_strip = user_input.strip().lower()
    current_user_id = get_current_user_id(request)
    
    print(f"🔄 Procesando comando '{user_input}' para usuario {current_user_id[:12]}...")

    try:
        # Manejar comandos de notas directamente
        if user_input_strip in ["leer", "borrar", "descargar", "contar"] or \
           user_input_strip.startswith("guardar:") or user_input_strip.startswith("buscar:"):
            tool = "note"
            result = use_tool(tool, user_input)

        # Manejar búsquedas web directamente
        elif user_input_strip.startswith("buscar "):
            tool = "web_search"
            query = user_input[7:].strip()
            result = web_search_formatted(query)
            return JSONResponse({
                "result_type": "list",
                "result_data": result,
                "input": user_input,
                "tool": tool
            })

        # Manejar notificaciones directamente - CORREGIDO
        elif any(keyword in user_input_strip for keyword in [
            "status", "start", "stop", "iniciar", "detener", "test", "probar",
            "activar emails", "activar patentes", "activar papers", "debug"
        ]) or \
            user_input_strip.startswith("keywords") or \
            user_input_strip.startswith("categories:"):

            tool = "notifications"
            
            # IMPORTANTE: Establecer el user_id antes de ejecutar la herramienta
            import tools.notifications as notif_tool
            notif_tool.set_current_user_id(current_user_id)

            try:
                result = notif_tool.run(user_input)
                print(f"✅ Resultado notificaciones: {result[:100]}...")
            except Exception as e:
                print(f"❌ Error en notifications tool: {e}")
                result = f"❌ Error en sistema de notificaciones: {e}"

        # Generación de código
        elif any(keyword in user_input_strip for keyword in ["generar", "genera", "crear codigo", "crear script", "escribir codigo"]):
            tool = "code_gen"
            result = use_tool(tool, user_input)

        # Usar Gemini para elegir la herramienta
        else:
            tool = ask_gemini_for_tool(user_input)
            print(f"🔧 Gemini eligió herramienta: {tool}")

            # Si Gemini eligió notificaciones, configurar user_id
            if tool == "notifications":
                import tools.notifications as notif_tool
                notif_tool.set_current_user_id(current_user_id)

            result = use_tool(tool, user_input)

        # Preparar respuesta
        if isinstance(result, list):
            return JSONResponse({
                "result_type": "list",
                "result_data": result,
                "input": user_input,
                "tool": tool
            })
        elif isinstance(result, dict) and "url" in result:
            return JSONResponse({
                "result_type": "open_url",
                "result_data": result.get("message", "Abriendo URL..."),
                "url": result["url"],
                "input": user_input,
                "tool": tool
            })
        else:
            return JSONResponse({
                "result_type": "text",
                "result_data": str(result),
                "input": user_input,
                "tool": tool
            })
            
    except Exception as e:
        print(f"❌ Error procesando comando: {e}")
        return JSONResponse({
            "result_type": "error",
            "result_data": f"Error: {str(e)}",
            "input": user_input,
            "tool": "error"
        }, status_code=500)


# -------------------- Archivos y Notas --------------------

@app.get("/files")
async def get_files():
    """Obtener lista de archivos guardados"""
    try:
        saved_code_files = [f for f in os.listdir(CODE_DIR) if os.path.isfile(os.path.join(CODE_DIR, f))] \
            if os.path.exists(CODE_DIR) else []
        notes_exist = os.path.exists(os.path.join(NOTES_DIR, "notas.txt"))
        notes_count = 0
        
        if notes_exist:
            try:
                with open(os.path.join(NOTES_DIR, "notas.txt"), "r", encoding="utf-8") as f:
                    lines = f.readlines()
                notes_count = len([line for line in lines if line.strip()])
            except:
                notes_count = 0
        
        return JSONResponse({
            "code_files": saved_code_files, 
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


@app.get("/download/notes")
async def download_notes():
    """Descargar archivo de notas"""
    file_path = os.path.join(NOTES_DIR, "notas.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="mis_notas.txt", media_type="text/plain",
                            headers={"Content-Disposition": "attachment; filename=mis_notas.txt"})
    raise HTTPException(status_code=404, detail="No hay notas guardadas")


@app.get("/download/code/{filename}")
async def download_code(filename: str):
    """Descargar archivo de código"""
    file_path = os.path.join(CODE_DIR, filename)
    if os.path.exists(file_path):
        media_type = "text/plain"
        if filename.endswith('.py'):
            media_type = "text/x-python"
        elif filename.endswith('.js'):
            media_type = "text/javascript"
        elif filename.endswith('.html'):
            media_type = "text/html"
        elif filename.endswith('.css'):
            media_type = "text/css"
        return FileResponse(file_path, filename=filename, media_type=media_type,
                            headers={"Content-Disposition": f"attachment; filename={filename}"})
    raise HTTPException(status_code=404, detail=f"No se encontró el archivo {filename}")


@app.get("/view/code/{filename}")
async def view_code(filename: str):
    """Ver contenido de archivo de código"""
    file_path = os.path.join(CODE_DIR, filename)
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
    file_path = os.path.join(NOTES_DIR, "notas.txt")
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


@app.post("/search/notes")
async def search_notes(query: str = Form(...)):
    """Buscar en notas"""
    file_path = os.path.join(NOTES_DIR, "notas.txt")
    if not os.path.exists(file_path):
        return JSONResponse({"results": [], "message": "No hay notas guardadas"})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        results = []
        for i, line in enumerate(lines, 1):
            if query.lower() in line.lower() and line.strip():
                results.append({
                    "line_number": i,
                    "content": line.strip(),
                    "preview": line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                })
        
        return JSONResponse({
            "results": results, 
            "total": len(results), 
            "query": query
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar en notas: {e}")

@app.delete("/delete/output/{filename}")
async def delete_output_file(filename: str):
    """Eliminar documento generado"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return JSONResponse({
                "success": True,
                "message": f"Documento generado {filename} eliminado correctamente"
            })
        else:
            raise HTTPException(status_code=404, detail=f"No se encontró el documento {filename}")
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# -------------------- Sistema de Notificaciones Multi-Usuario --------------------

@app.post("/notifications/register")
async def register_user(request: Request):
    """Registrar usuario para notificaciones"""
    try:
        client_info = get_client_info(request)
        device_info = {}
        
        try:
            body = await request.json()
            device_info = body
        except:
            # Si no hay JSON, usar valores por defecto
            device_info = {
                'device_name': f'Web-{request.headers.get("user-agent", "Unknown")[:20]}...',
                'device_id': f'web_{client_info["ip"].replace(".", "_")}'
            }
        
        user_id, session_id, config = multi_user_system.register_user(
            client_info["ip"], client_info["user_agent"], device_info
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
    """Obtener notificaciones pendientes para un usuario"""
    try:
        current_user_id = get_current_user_id(request)
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
    """Enviar notificación de prueba"""
    try:
        current_user_id = get_current_user_id(request)
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


@app.get("/notifications/debug/{user_id}")
async def debug_notifications(request: Request, user_id: str):
    """Información de debug para notificaciones"""
    try:
        current_user_id = get_current_user_id(request)
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

        # Información de debug
        config = multi_user_system.get_user_config(user_id)
        active_users = multi_user_system.get_active_users(hours=24)
        pending_notifications = multi_user_system.get_pending_notifications(user_id)

        debug_info = {
            "user_id": user_id,
            "config": config,
            "is_active": user_id in active_users,
            "active_users_count": len(active_users),
            "pending_notifications": len(pending_notifications),
            "notifications_enabled": any([
                config.get('email_notifications'),
                config.get('patent_notifications'), 
                config.get('papers_notifications')
            ]),
            "background_running": multi_user_system.running,
            "system_status": "🟢 Activo" if multi_user_system.running else "🔴 Inactivo"
        }

        return JSONResponse({"success": True, "debug_info": debug_info})

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/notifications")
async def get_notifications_legacy(request: Request):
    """Endpoint legacy para obtener notificaciones"""
    try:
        current_user_id = get_current_user_id(request)
        notifications = multi_user_system.get_pending_notifications(current_user_id)
        return JSONResponse({
            "notifications": notifications, 
            "count": len(notifications)
        })
    except Exception as e:
        return JSONResponse({
            "notifications": [], 
            "count": 0, 
            "error": str(e)
        })


# Endpoint para verificar el estado del sistema
@app.get("/health")
async def health_check():
    """Health check del sistema"""
    try:
        return JSONResponse({
            "status": "healthy",
            "notifications_system": "active" if multi_user_system.running else "inactive",
            "active_users": len(multi_user_system.get_active_users(hours=24)),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"  # Importante para Render
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"🔔 Sistema de notificaciones: {'Habilitado' if multi_user_system else 'Deshabilitado'}")
    
    uvicorn.run("main:app", host=host, port=port, reload=True)