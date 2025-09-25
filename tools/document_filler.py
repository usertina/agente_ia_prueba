import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from docx import Document
import PyPDF2
import mammoth
import pandas as pd
from pathlib import Path

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Directorios
TEMPLATES_DIR = "templates_docs"
DATA_DIR = "data_docs"
OUTPUT_DIR = "output_docs"
for dir_path in [TEMPLATES_DIR, DATA_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

class DocumentFiller:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.supported_template_formats = ['.docx', '.txt', '.pdf']
        self.supported_data_formats = ['.json', '.csv', '.xlsx', '.txt']

    def run(self, prompt: str) -> str:
        """Procesa comandos para rellenar documentos."""
        prompt = prompt.strip().lower()

        if "listar plantillas" in prompt:
            return self.list_templates()
        elif "listar datos" in prompt:
            return self.list_data_files()
        elif prompt.startswith("rellenar:"):
            return self.fill_document(prompt[9:].strip())
        elif prompt.startswith("analizar:"):
            return self.analyze_template(prompt[9:].strip())
        elif prompt.startswith("crear ejemplo datos:"):
            return self.create_example_data(prompt[20:].strip())
        elif prompt.startswith("usar plantilla:"):
            filename = prompt[15:].strip()
            copy_result = self.copy_default_template(filename)
            templates_result = self.list_templates()
            return f"{copy_result}\n\n{templates_result}"
        elif prompt.startswith("convertir a json:"):
            filename = prompt[len("convertir a json:"):].lstrip(": ").strip()
            return self.convert_to_json(filename)
        else:
            return self.show_help()

    def extract_text_from_file(self, file_path: str) -> str:
        """Extrae texto de diferentes formatos con codificación UTF-8"""
        try:
            if file_path.endswith('.txt'):
                # CORRECCIÓN: Forzar UTF-8 y manejar errores
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            return f.read()
                    except UnicodeDecodeError:
                        continue
                # Si ninguna codificación funciona, usar errors='replace'
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()

            elif file_path.endswith('.docx'):
                try:
                    doc = Document(file_path)
                    text = []
                    for paragraph in doc.paragraphs:
                        text.append(paragraph.text)
                    return '\n'.join(text)
                except Exception as docx_error:
                    return f"Error procesando DOCX: {docx_error}"

            elif file_path.endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = []
                        for page in reader.pages:
                            text.append(page.extract_text())
                        return '\n'.join(text)
                except Exception as pdf_error:
                    return f"Error procesando PDF: {pdf_error}"

            return ""
        except Exception as e:
            return f"Error extrayendo texto: {e}"

    def load_data(self, data_path: str) -> dict:
        """Carga datos con codificación UTF-8 correcta"""
        try:
            if data_path.endswith('.json'):
                # CORRECCIÓN: Forzar UTF-8
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(data_path, 'r', encoding=encoding) as f:
                            return json.load(f)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                # Fallback con manejo de errores
                with open(data_path, 'r', encoding='utf-8', errors='replace') as f:
                    return json.load(f)

            elif data_path.endswith('.csv'):
                df = pd.read_csv(data_path, encoding='utf-8')
                if len(df) > 0:
                    return df.iloc[0].to_dict()
                return {}

            elif data_path.endswith('.xlsx'):
                df = pd.read_excel(data_path)
                if len(df) > 0:
                    return df.iloc[0].to_dict()
                return {}

            elif data_path.endswith('.txt'):
                data = {}
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(data_path, 'r', encoding=encoding) as f:
                            for line in f:
                                line = line.strip()
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                elif '\t' in line:
                                    key, value = line.split('\t', 1)
                                elif ',' in line:
                                    key, value = line.split(',', 1)
                                elif ':' in line:
                                    key, value = line.split(':', 1)
                                else:
                                    continue
                                data[key.strip()] = value.strip()
                        return data
                    except UnicodeDecodeError:
                        continue
                return data

            return {}
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return {}

    def fill_txt(self, template_path: str, data: dict, output_name: str) -> str:
        """Rellena un documento de texto con codificación UTF-8 correcta"""
        try:
            # CORRECCIÓN: Leer con múltiples encodings
            content = ""
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(template_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                # Fallback con manejo de errores
                with open(template_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

            # Agregar fecha actual si no está en los datos
            if 'fecha' not in data:
                data['fecha'] = datetime.now().strftime("%d/%m/%Y")

            replacements = 0

            # Reemplazar marcadores
            for key, value in data.items():
                if key.startswith('_'):  # Saltar metadatos
                    continue

                patterns = [f'{{{{{key}}}}}', f'[{key}]', f'_{key}_']
                for pattern in patterns:
                    if pattern in content:
                        content = content.replace(pattern, str(value))
                        replacements += 1

            # CORRECCIÓN: Guardar con UTF-8 explícito
            output_path = os.path.join(OUTPUT_DIR, f"{output_name}.txt")
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)

            result = f"✅ **DOCUMENTO RELLENADO EXITOSAMENTE**\n\n"
            result += f"📄 **Archivo:** {output_name}.txt\n"
            result += f"📁 **Ubicación:** {OUTPUT_DIR}/\n"
            result += f"🔄 **Reemplazos realizados:** {replacements}\n\n"

            if replacements == 0:
                result += "⚠️ **Advertencia:** No se realizaron reemplazos. Verifica que:\n"
                result += "• Los marcadores en la plantilla coincidan con los datos\n"
                result += "• Usa formato {{campo}}, [campo] o _campo_\n"
            else:
                result += "💡 **El documento está listo para usar**\n"
                result += f"🔧 **Codificación:** UTF-8 (acentos corregidos)\n"

            return result

        except Exception as e:
            return f"❌ Error procesando TXT: {e}"

    def create_example_data(self, filename: str) -> str:
        """Crea un archivo JSON de ejemplo con codificación UTF-8"""
        try:
            file_path = os.path.join(TEMPLATES_DIR, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró la plantilla: {filename}"

            text_content = self.extract_text_from_file(file_path)
            
            if not text_content or "Error" in text_content:
                return f"❌ No se pudo extraer el contenido de: {filename}"

            # Buscar marcadores
            import re
            marcadores = set()
            marcadores.update(re.findall(r'\{\{(\w+)\}\}', text_content))
            marcadores.update(re.findall(r'\[(\w+)\]', text_content))
            marcadores.update(re.findall(r'_(\w+)_', text_content))

            # Crear datos de ejemplo con acentos correctos
            ejemplo_datos = {}
            ejemplo_datos["_info"] = f"Datos de ejemplo para {filename} - Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ejemplo_datos["fecha"] = datetime.now().strftime("%d/%m/%Y")

            # CORRECCIÓN: Datos con acentos correctos
            datos_tipicos = {
                "nombre": "Juan Pérez García",
                "empresa": "Innovaciones Tech SL",
                "mi_empresa": "Fundación Educación Global",
                "direccion_empresa": "Calle Mayor, 123",
                "ciudad_codigo": "Madrid, 28001",
                "empresa_destinataria": "Tech Solutions S.A.",
                "direccion_destinataria": "Avenida Innovación 45", 
                "ciudad_destinataria": "Madrid, 28010",
                "proyecto_necesidad": "el programa de becas para estudiantes en riesgo de exclusión",
                "objetivo": "ofrecer oportunidades educativas a jóvenes con talento",
                "resultado_esperado": "impactar positivamente a más de 100 estudiantes este año",
                "tipo_apoyo": "financiero, material educativo o asesoría técnica",
                "documentos_adjuntos": "el plan de acción y el presupuesto estimado",
                "nombre_representante": "María López",
                "cargo_representante": "Directora Ejecutiva",
                "contacto_representante": "mlopez@fundacioneducacion.org",
                "telefono": "911234567",
                "email": "info@innovacionestech.com",
                "importe": "50000",
                "descripcion": "Descripción detallada del proyecto"
            }

            # Asignar valores a los marcadores encontrados
            for marcador in marcadores:
                if marcador.lower() in datos_tipicos:
                    ejemplo_datos[marcador] = datos_tipicos[marcador.lower()]
                else:
                    ejemplo_datos[marcador] = f"[COMPLETAR_{marcador.upper()}]"

            # Si no se encontraron marcadores, usar estructura básica
            if not marcadores:
                for key, value in datos_tipicos.items():
                    ejemplo_datos[key] = value

            # CORRECCIÓN: Guardar JSON con UTF-8 y ensure_ascii=False
            json_filename = f"datos_ejemplo_{filename.split('.')[0]}.json"
            json_path = os.path.join(DATA_DIR, json_filename)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ejemplo_datos, f, indent=2, ensure_ascii=False)

            result = f"✅ **ARCHIVO DE DATOS CREADO: {json_filename}**\n\n"
            result += f"📁 Ubicación: {DATA_DIR}/{json_filename}\n"
            result += f"🔧 Codificación: UTF-8 (con acentos correctos)\n\n"
            result += "📋 **Campos incluidos:**\n"

            for campo, valor in ejemplo_datos.items():
                if campo != "_info":
                    result += f"• {campo}: {valor}\n"

            result += f"\n💡 **Siguiente paso:**\n"
            result += f"1. Edita el archivo JSON con tus datos reales\n"
            result += f"2. Usa: `rellenar: {filename} con {json_filename}`\n"

            return result

        except Exception as e:
            return f"❌ Error creando datos de ejemplo: {e}"

    # [Resto de métodos sin cambios - manteniendo las demás funciones igual]
    def show_help(self) -> str:
        return """
📄 **SISTEMA DE RELLENADO DE DOCUMENTOS**

**Comandos disponibles:**

1️⃣ **Gestión de archivos:**
   • listar plantillas
   • listar datos
   • usar plantilla: nombre_archivo

2️⃣ **Análisis de plantillas:**
   • analizar: plantilla.docx
   • crear ejemplo datos: plantilla.docx 

3️⃣ **Rellenado de documentos:**
   • rellenar: plantilla.txt con datos.json 

**🔧 Codificación UTF-8:**
   • Todos los archivos se procesan con UTF-8
   • Acentos y caracteres especiales preservados
   • Compatible con texto en español

**💡 Flujo recomendado:**
   1. "analizar: mi_plantilla.txt"
   2. "crear ejemplo datos: mi_plantilla.txt"
   3. Edita el archivo JSON generado
   4. "rellenar: mi_plantilla.txt con mis_datos.json"
        """

    def list_templates(self) -> str:
        """Lista las plantillas disponibles"""
        try:
            templates = []

            if os.path.exists(TEMPLATES_DIR):
                for file in os.listdir(TEMPLATES_DIR):
                    file_path = os.path.join(TEMPLATES_DIR, file)
                    if (os.path.isfile(file_path) and 
                        any(file.endswith(ext) for ext in self.supported_template_formats) and
                        file != "defaults"):
                        try:
                            size = os.path.getsize(file_path)
                            modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                            templates.append({
                                'name': file,
                                'size': f"{size/1024:.1f} KB",
                                'modified': modified.strftime("%Y-%m-%d %H:%M"),
                                'is_default': False
                            })
                        except Exception as e:
                            continue

            defaults_dir = os.path.join(TEMPLATES_DIR, "defaults")
            if os.path.exists(defaults_dir):
                for file in os.listdir(defaults_dir):
                    file_path = os.path.join(defaults_dir, file)
                    if (os.path.isfile(file_path) and 
                        any(file.endswith(ext) for ext in self.supported_template_formats)):
                        try:
                            size = os.path.getsize(file_path)
                            modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                            templates.append({
                                'name': file,
                                'size': f"{size/1024:.1f} KB",
                                'modified': modified.strftime("%Y-%m-%d %H:%M"),
                                'is_default': True
                            })
                        except Exception as e:
                            continue

            if not templates:
                return f"📁 **No hay plantillas disponibles**\n\nPara empezar:\n1. Coloca tus archivos plantilla en: {TEMPLATES_DIR}/"

            result = "📄 **PLANTILLAS DISPONIBLES:**\n\n"
            
            user_templates = [t for t in templates if not t['is_default']]
            default_templates = [t for t in templates if t['is_default']]
            
            if user_templates:
                result += "👤 **Tus plantillas:**\n"
                for i, template in enumerate(user_templates, 1):
                    result += f"{i}. **{template['name']}**\n"
                    result += f"   📊 Tamaño: {template['size']}\n"
                    result += f"   📅 Modificado: {template['modified']}\n\n"
            
            if default_templates:
                result += "🏭 **Plantillas predeterminadas:**\n"
                for i, template in enumerate(default_templates, 1):
                    result += f"{i}. **{template['name']}**\n"
                    result += f"   📊 Tamaño: {template['size']}\n"
                    result += f"   📅 Modificado: {template['modified']}\n"
                    result += "   💡 Usa: `usar plantilla: " + template['name'] + "`\n\n"

            result += "\n**Siguiente paso:** `analizar: nombre_plantilla.txt`"
            return result

        except Exception as e:
            return f"❌ Error listando plantillas: {e}"

    def list_data_files(self) -> str:
        """Lista los archivos de datos disponibles"""
        try:
            data_files = []
            
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR, exist_ok=True)
                
            for file in os.listdir(DATA_DIR):
                if any(file.endswith(ext) for ext in self.supported_data_formats):
                    file_path = os.path.join(DATA_DIR, file)
                    try:
                        size = os.path.getsize(file_path)
                        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                        data_files.append({
                            'name': file,
                            'size': f"{size/1024:.1f} KB",
                            'modified': modified.strftime("%Y-%m-%d %H:%M"),
                            'type': file.split('.')[-1].upper()
                        })
                    except Exception as e:
                        continue

            if not data_files:
                return f"📁 **No hay archivos de datos disponibles**\n\nPara empezar:\n1. Coloca tus archivos de datos en: {DATA_DIR}/"

            result = "📊 **ARCHIVOS DE DATOS DISPONIBLES:**\n\n"
            for i, data_file in enumerate(data_files, 1):
                result += f"{i}. **{data_file['name']}** ({data_file['type']})\n"
                result += f"   📊 Tamaño: {data_file['size']}\n"
                result += f"   📅 Modificado: {data_file['modified']}\n\n"

            return result

        except Exception as e:
            return f"❌ Error listando datos: {e}"

    def copy_default_template(self, filename: str) -> str:
        """Copia una plantilla predeterminada"""
        defaults_dir = os.path.join(TEMPLATES_DIR, "defaults")
        src = os.path.join(defaults_dir, filename)
        dst = os.path.join(TEMPLATES_DIR, filename)
        
        if not os.path.exists(src):
            return f"❌ La plantilla {filename} no existe en defaults"
        if os.path.exists(dst):
            return f"⚠️ Plantilla {filename} ya existe en tus plantillas"
        
        try:
            import shutil
            shutil.copy(src, dst)
            return f"✅ Plantilla {filename} copiada a tus plantillas"
        except Exception as e:
            return f"❌ Error copiando plantilla: {e}"

    def analyze_template(self, filename: str) -> str:
        """Analiza una plantilla para identificar campos"""
        try:
            file_path = os.path.join(TEMPLATES_DIR, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró la plantilla: {filename}"

            text_content = self.extract_text_from_file(file_path)
            
            if not text_content or "Error" in text_content:
                return f"❌ No se pudo extraer el contenido de: {filename}"

            import re
            marcadores = re.findall(r'\{\{(\w+)\}\}', text_content)
            marcadores.extend(re.findall(r'\[(\w+)\]', text_content))
            marcadores.extend(re.findall(r'_(\w+)_', text_content))

            result = f"🔍 **ANÁLISIS DE PLANTILLA: {filename}**\n\n"

            if marcadores:
                result += "📋 **Campos identificados:**\n\n"
                for i, campo in enumerate(set(marcadores), 1):
                    result += f"{i}. **{campo}**\n"

                result += f"\n💡 **Siguiente paso:** `crear ejemplo datos: {filename}`\n"
            else:
                result += "⚠️ No se identificaron campos automáticamente.\n"
                result += "Revisa que tu plantilla tenga marcadores como {{campo}} o [campo]\n"

            return result

        except Exception as e:
            return f"❌ Error analizando plantilla: {e}"

    def fill_document(self, command: str) -> str:
        """Rellena un documento con los datos proporcionados"""
        try:
            if " con " not in command:
                return "❌ Formato incorrecto. Usa: `rellenar: plantilla.txt con datos.json`"

            parts = command.split(" con ")
            template_name = parts[0].strip()
            data_name = parts[1].strip()

            template_path = os.path.join(TEMPLATES_DIR, template_name)
            data_path = os.path.join(DATA_DIR, data_name)

            if not os.path.exists(template_path):
                return f"❌ No se encontró la plantilla: {template_name}"

            if not os.path.exists(data_path):
                return f"❌ No se encontró el archivo de datos: {data_name}"

            data = self.load_data(data_path)
            if not data:
                return f"❌ No se pudieron cargar los datos de: {data_name}"

            output_name = f"{template_name.split('.')[0]}_rellenado_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if template_name.endswith('.docx'):
                return self.fill_docx(template_path, data, output_name)
            elif template_name.endswith('.txt'):
                return self.fill_txt(template_path, data, output_name)
            else:
                return f"❌ Formato de plantilla no soportado: {template_name}"

        except Exception as e:
            return f"❌ Error rellenando documento: {e}"

    def fill_docx(self, template_path: str, data: dict, output_name: str) -> str:
        """Rellena un documento DOCX con codificación correcta"""
        try:
            doc = Document(template_path)

            if 'fecha' not in data:
                data['fecha'] = datetime.now().strftime("%d/%m/%Y")

            replacements = 0

            for paragraph in doc.paragraphs:
                for key, value in data.items():
                    if key.startswith('_'):
                        continue

                    patterns = [f'{{{{{key}}}}}', f'[{key}]', f'_{key}_']
                    for pattern in patterns:
                        if pattern in paragraph.text:
                            paragraph.text = paragraph.text.replace(pattern, str(value))
                            replacements += 1

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in data.items():
                            if key.startswith('_'):
                                continue

                            patterns = [f'{{{{{key}}}}}', f'[{key}]', f'_{key}_']
                            for pattern in patterns:
                                if pattern in cell.text:
                                    cell.text = cell.text.replace(pattern, str(value))
                                    replacements += 1

            output_path = os.path.join(OUTPUT_DIR, f"{output_name}.docx")
            doc.save(output_path)

            result = f"✅ **DOCUMENTO RELLENADO EXITOSAMENTE**\n\n"
            result += f"📄 **Archivo:** {output_name}.docx\n"
            result += f"📁 **Ubicación:** {OUTPUT_DIR}/\n"
            result += f"🔄 **Reemplazos realizados:** {replacements}\n"
            result += f"🔧 **Codificación:** UTF-8 (acentos preservados)\n\n"

            if replacements == 0:
                result += "⚠️ **Advertencia:** No se realizaron reemplazos.\n"
            else:
                result += "💡 **El documento está listo para usar**\n"

            return result

        except Exception as e:
            return f"❌ Error procesando DOCX: {e}"

    def convert_to_json(self, filename: str) -> str:
        """Convierte archivos a JSON con codificación UTF-8"""
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return f"❌ No se encontró el archivo: {filename}"

        data = {}

        try:
            if filename.endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            elif filename.endswith('.csv'):
                df = pd.read_csv(path, encoding='utf-8')
                if len(df) > 0:
                    data = df.iloc[0].to_dict()

            elif filename.endswith('.xlsx'):
                df = pd.read_excel(path)
                if len(df) > 0:
                    data = df.iloc[0].to_dict()

            elif filename.endswith('.txt'):
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            for line in f:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    data[key.strip()] = value.strip()
                                elif ':' in line:
                                    key, value = line.strip().split(':', 1)
                                    data[key.strip()] = value.strip()
                        break
                    except UnicodeDecodeError:
                        continue

        except Exception as e:
            return f"❌ Error procesando el archivo: {e}"

        if not data:
            return "❌ No se pudieron extraer datos del archivo"

        json_name = f"{filename.split('.')[0]}.json"
        json_path = os.path.join(DATA_DIR, json_name)
        
        # CORRECCIÓN: Guardar con UTF-8 y ensure_ascii=False
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        preview = "\n".join([f"{k}: {v}" for i, (k, v) in enumerate(data.items()) if i < 10])
        if len(data) > 10:
            preview += "\n…"

        return f"✅ Archivo convertido a JSON: {json_name}\n📁 Ubicación: {DATA_DIR}/{json_name}\n🔧 Codificación: UTF-8\n\n📋 Preview:\n{preview}"


# Instancia global
document_filler = DocumentFiller()

def run(prompt: str) -> str:
    """Función principal de la herramienta"""
    return document_filler.run(prompt)