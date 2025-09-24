import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from docx import Document
import PyPDF2
from docx2pdf import convert
import mammoth
import pandas as pd
from pathlib import Path

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Directorios
TEMPLATES_DIR = "templates_docs"
DATA_DIR = "data_docs"
OUTPUT_DIR = "output_docs"
for dir_path in [
        TEMPLATES_DIR,
        DATA_DIR,
        OUTPUT_DIR,
]:
    os.makedirs(dir_path, exist_ok=True)


class DocumentFiller:

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.supported_template_formats = ['.docx', '.txt', '.pdf']
        self.supported_data_formats = ['.json', '.csv', '.xlsx', '.txt']

    def run(self, prompt: str) -> str:
        """
        Procesa comandos para rellenar documentos.
        
        Comandos disponibles:
        - "listar plantillas" - Lista plantillas disponibles
        - "listar datos" - Lista archivos de datos disponibles
        - "rellenar: plantilla.docx con datos.json" - Rellena documento
        - "analizar: plantilla.docx" - Analiza campos de una plantilla
        - "crear ejemplo datos: plantilla.docx" - Crea JSON de ejemplo
        """

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


    def convert_to_json(self, filename: str) -> str:
        """
        Convierte archivos CSV, XLSX, TXT o DOCX a JSON en data_docs.
        Para TXT/DOCX intenta extraer pares clave=valor o marcadores automáticamente.
        """
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            return f"❌ No se encontró el archivo: {filename}"

        data = {}

        try:
            if filename.endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            elif filename.endswith('.csv'):
                df = pd.read_csv(path)
                if len(df) > 0:
                    data = df.iloc[0].to_dict()

            elif filename.endswith('.xlsx'):
                df = pd.read_excel(path)
                if len(df) > 0:
                    data = df.iloc[0].to_dict()

            elif filename.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            data[key.strip()] = value.strip()
                        elif ':' in line:
                            key, value = line.strip().split(':', 1)
                            data[key.strip()] = value.strip()

            elif filename.endswith('.docx'):
                doc = Document(path)
                text_content = []
                for paragraph in doc.paragraphs:
                    text_content.append(paragraph.text)
                full_text = "\n".join(text_content)

                import re
                # Buscar patrones clave=valor o clave: valor
                for match in re.findall(r'(\w+)\s*[:=]\s*(.+)', full_text):
                    key, value = match
                    data[key.strip()] = value.strip()

                # También extraer marcadores {{campo}} y crear placeholders si no hay valor
                marcadores = re.findall(r'\{\{(\w+)\}\}', full_text)
                for marcador in marcadores:
                    if marcador not in data:
                        data[marcador] = f"[COMPLETAR_{marcador.upper()}]"

        except Exception as e:
            return f"❌ Error procesando el archivo: {e}"

        if not data:
            return "❌ No se pudieron extraer datos del archivo"

        # Guardar JSON
        json_name = f"{filename.split('.')[0]}.json"
        json_path = os.path.join(DATA_DIR, json_name)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Preview de los primeros campos
        preview = "\n".join(
            [f"{k}: {v}" for i, (k, v) in enumerate(data.items()) if i < 10])
        if len(data) > 10:
            preview += "\n…"

        return f"✅ Archivo convertido a JSON: {json_name}\n📁 Ubicación: {DATA_DIR}/{json_name}\n\n📋 Preview:\n{preview}"

    def show_help(self) -> str:
        """Muestra la ayuda del sistema"""
        return """
📄 **SISTEMA DE RELLENADO DE DOCUMENTOS**

**Comandos disponibles:**

1️⃣ **Gestión de archivos:**
   • listar plantillas
   • listar datos
   • usar plantilla: nombre_archivo
    - Copia una plantilla
      predeterminada a tus plantillas


2️⃣ **Análisis de plantillas:**
   • analizar: plantilla.docx
     - Detecta los campos a rellenar 
       en una plantilla
   • crear ejemplo datos: plantilla.docx 
   - Genera un archivo JSON de ejemplo con los campos


3️⃣ **Rellenado de documentos:**
   • rellenar: plantilla.docx con datos.json 
    - Rellena una plantilla con los datos
   • rellenar: solicitud_ayuda.docx con empresa_datos.json
    - También funciona con CSV o XLSX

**📁 Estructura de carpetas:**
   • templates_docs/ - Coloca aquí tus plantillas
     (.docx, .txt, .pdf)
   • templates_docs/defaults/ - Plantillas predeterminadas que puedes copiar con 'usar plantilla:
   • data_docs/ - Coloca aquí tus datos (.json, .csv, .xlsx)
   • output_docs/ - Los documentos rellenados se guardan aquí

**🔤 Marcadores en plantillas:**
   • {{nombre_empresa}} - Campo simple
   • {{fecha}} - Se rellena automáticamente con fecha actual
   • {{#lista}}{{item}}{{/lista}} - Para listas/repeticiones

**💡 Flujo recomendado:**
   1. Si quieres usar una plantilla predeterminada: 'usar plantilla: nombre_archivo'
   2. Analiza la plantilla: "analizar: mi_plantilla.docx"
   3. Crea datos de ejemplo: "crear ejemplo datos: mi_plantilla.docx"
   4. Edita el archivo JSON generado con tus datos reales
   5. Rellena: "rellenar: mi_plantilla.docx con mis_datos.json"

**🎯 Perfecto para:**
   • Solicitudes de ayudas/subvenciones
   • Contratos repetitivos
   • Formularios oficiales
   • Documentación empresarial
        """

    def copy_default_template(self, filename: str) -> str:
        src = os.path.join(TEMPLATES_DIR, "defaults", filename)
        dst = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(src):
            return f"❌ La plantilla {filename} no existe en defaults"
        if not os.path.exists(dst):
            import shutil
            shutil.copy(src, dst)
            return f"✅ Plantilla {filename} copiada a tus plantillas"
        return f"⚠️ Plantilla {filename} ya existe en tus plantillas"

    def list_templates(self) -> str:
        """Lista las plantillas disponibles, incluyendo las predeterminadas"""
        try:
            templates = []

            # Plantillas subidas por el usuario
            for file in os.listdir(TEMPLATES_DIR):
                file_path = os.path.join(TEMPLATES_DIR, file)
                if os.path.isfile(file_path) and any(
                        file.endswith(ext)
                        for ext in self.supported_template_formats):
                    size = os.path.getsize(file_path)
                    modified = datetime.fromtimestamp(
                        os.path.getmtime(file_path))
                    templates.append({
                        'name':
                        file,
                        'size':
                        f"{size/1024:.1f} KB",
                        'modified':
                        modified.strftime("%Y-%m-%d %H:%M"),
                        'is_default':
                        False
                    })

            # Plantillas predeterminadas
            defaults_dir = os.path.join(TEMPLATES_DIR, "defaults")
            if os.path.exists(defaults_dir):
                for file in os.listdir(defaults_dir):
                    file_path = os.path.join(defaults_dir, file)
                    if os.path.isfile(file_path) and any(
                            file.endswith(ext)
                            for ext in self.supported_template_formats):
                        size = os.path.getsize(file_path)
                        modified = datetime.fromtimestamp(
                            os.path.getmtime(file_path))
                        templates.append({
                            'name':
                            file,
                            'size':
                            f"{size/1024:.1f} KB",
                            'modified':
                            modified.strftime("%Y-%m-%d %H:%M"),
                            'is_default':
                            True
                        })

            if not templates:
                return f"""
    📁 **No hay plantillas disponibles**

    Para empezar:
    1. Coloca tus archivos plantilla en: {TEMPLATES_DIR}/
    2. Formatos soportados: {', '.join(self.supported_template_formats)}
    3. Usa marcadores como {{{{nombre}}}}, {{{{empresa}}}} en tus plantillas
                """

            # Generar listado en texto
            result = "📄 **PLANTILLAS DISPONIBLES:**\n\n"
            for i, template in enumerate(templates, 1):
                result += f"{i}. **{template['name']}**"
                if template['is_default']:
                    result += " (Predeterminada)"
                result += f"\n   📊 Tamaño: {template['size']}\n"
                result += f"   📅 Modificado: {template['modified']}\n\n"

            result += "💡 **Siguiente paso:** usar plantilla: nombre_plantilla.txt\n" "**Por último:** analizar: nombre_plantilla.txt"
            return result

        except Exception as e:
            return f"❌ Error listando plantillas: {e}"

    def list_data_files(self) -> str:
        """Lista los archivos de datos disponibles"""
        try:
            data_files = []
            for file in os.listdir(DATA_DIR):
                if any(
                        file.endswith(ext)
                        for ext in self.supported_data_formats):
                    file_path = os.path.join(DATA_DIR, file)
                    size = os.path.getsize(file_path)
                    modified = datetime.fromtimestamp(
                        os.path.getmtime(file_path))
                    data_files.append({
                        'name':
                        file,
                        'size':
                        f"{size/1024:.1f} KB",
                        'modified':
                        modified.strftime("%Y-%m-%d %H:%M"),
                        'type':
                        file.split('.')[-1].upper()
                    })

            if not data_files:
                return f"""
📁 **No hay archivos de datos disponibles**

Para empezar:
1. Coloca tus archivos de datos en: {DATA_DIR}/
2. Formatos soportados: {', '.join(self.supported_data_formats)}
3. O crea datos de ejemplo: 'crear ejemplo datos: plantilla.docx'
                """

            result = "📊 **ARCHIVOS DE DATOS DISPONIBLES:**\n\n"
            for i, data_file in enumerate(data_files, 1):
                result += f"{i}. **{data_file['name']}** ({data_file['type']})\n"
                result += f"   📊 Tamaño: {data_file['size']}\n"
                result += f"   📅 Modificado: {data_file['modified']}\n\n"

            return result

        except Exception as e:
            return f"❌ Error listando datos: {e}"

    def analyze_template(self, filename: str) -> str:
        """Analiza una plantilla para identificar campos"""
        try:
            file_path = os.path.join(TEMPLATES_DIR, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró la plantilla: {filename}"

            # Extraer texto según el formato
            text_content = self.extract_text_from_file(file_path)

            # Usar Gemini para analizar los campos
            analysis_prompt = f"""
Analiza el siguiente documento plantilla y identifica todos los campos que necesitan ser rellenados.

Busca:
1. Marcadores como {{campo}}, [campo], _campo_, o espacios en blanco obvios
2. Campos típicos de formularios (nombre, empresa, fecha, dirección, etc.)
3. Campos específicos del contexto (número de expediente, cuantía, etc.)

Texto del documento:
{text_content[:2000]}

Devuelve una lista JSON con los campos identificados y su descripción.
Formato: {{"campos": [{{"nombre": "nombre_campo", "descripcion": "Descripción del campo", "tipo": "texto/numero/fecha"}}]}}
            """

            response = self.model.generate_content(analysis_prompt)

            # Intentar extraer JSON de la respuesta
            try:
                # Buscar JSON en la respuesta
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    campos_info = json.loads(json_match.group())
                else:
                    # Si no hay JSON válido, crear estructura básica
                    campos_info = {"campos": []}
            except:
                campos_info = {"campos": []}

            # También buscar marcadores directamente en el texto
            import re
            marcadores = re.findall(r'\{\{(\w+)\}\}', text_content)
            marcadores.extend(re.findall(r'\[(\w+)\]', text_content))
            marcadores.extend(re.findall(r'_(\w+)_', text_content))

            # Combinar campos encontrados
            campos_encontrados = set()
            for campo in campos_info.get("campos", []):
                campos_encontrados.add(campo["nombre"])

            for marcador in marcadores:
                if marcador not in campos_encontrados:
                    campos_info["campos"].append({
                        "nombre": marcador,
                        "descripcion": f"Campo {marcador}",
                        "tipo": "texto"
                    })

            # Formatear resultado
            result = f"🔍 **ANÁLISIS DE PLANTILLA: {filename}**\n\n"

            if campos_info["campos"]:
                result += "📋 **Campos identificados:**\n\n"
                for i, campo in enumerate(campos_info["campos"], 1):
                    result += f"{i}. **{campo['nombre']}**\n"
                    result += f"   📝 {campo['descripcion']}\n"
                    result += f"   🏷️ Tipo: {campo['tipo']}\n\n"

                result += f"💡 **Siguiente paso:** Crea datos de ejemplo con 'crear ejemplo datos: {filename}'\n"
            else:
                result += "⚠️ No se identificaron campos automáticamente.\n"
                result += "Revisa que tu plantilla tenga marcadores como {{campo}} o [campo]\n"

            return result

        except Exception as e:
            return f"❌ Error analizando plantilla: {e}"

    def create_example_data(self, filename: str) -> str:
        """Crea un archivo JSON de ejemplo basado en una plantilla"""
        try:
            # Primero analizar la plantilla
            file_path = os.path.join(TEMPLATES_DIR, filename)
            if not os.path.exists(file_path):
                return f"❌ No se encontró la plantilla: {filename}"

            text_content = self.extract_text_from_file(file_path)

            # Buscar marcadores
            import re
            marcadores = set()
            marcadores.update(re.findall(r'\{\{(\w+)\}\}', text_content))
            marcadores.update(re.findall(r'\[(\w+)\]', text_content))
            marcadores.update(re.findall(r'_(\w+)_', text_content))

            # Crear datos de ejemplo
            ejemplo_datos = {}
            ejemplo_datos[
                "_info"] = f"Datos de ejemplo para {filename} - Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ejemplo_datos["fecha"] = datetime.now().strftime("%Y-%m-%d")

            # Datos típicos de empresa/persona
            datos_tipicos = {
                "nombre": "Juan Pérez García",
                "empresa": "Innovaciones Tech SL",
                "cif": "B12345678",
                "nif": "12345678A",
                "direccion": "Calle Mayor, 123",
                "ciudad": "Madrid",
                "cp": "28001",
                "telefono": "911234567",
                "email": "info@innovacionestech.com",
                "importe": "50000",
                "cuantia": "50000",
                "proyecto": "Desarrollo de plataforma digital innovadora",
                "descripcion":
                "Descripción detallada del proyecto o actividad",
                "representante": "Juan Pérez García",
                "cargo": "Director General",
                "expediente": "EXP/2024/001",
                "numero": "001",
                "año": "2024"
            }

            # Asignar valores a los marcadores encontrados
            for marcador in marcadores:
                if marcador.lower() in datos_tipicos:
                    ejemplo_datos[marcador] = datos_tipicos[marcador.lower()]
                else:
                    # Generar valor basado en el nombre del campo
                    ejemplo_datos[marcador] = f"[COMPLETAR_{marcador.upper()}]"

            # Guardar archivo JSON
            json_filename = f"datos_ejemplo_{filename.split('.')[0]}.json"
            json_path = os.path.join(DATA_DIR, json_filename)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ejemplo_datos, f, indent=2, ensure_ascii=False)

            result = f"✅ **ARCHIVO DE DATOS CREADO: {json_filename}**\n\n"
            result += f"📁 Ubicación: {DATA_DIR}/{json_filename}\n\n"
            result += "📋 **Campos incluidos:**\n"

            for campo, valor in ejemplo_datos.items():
                if campo != "_info":
                    result += f"• {campo}: {valor}\n"

            result += f"\n💡 **Siguiente paso:**\n"
            result += f"1. Edita el archivo JSON con tus datos reales\n"
            result += f"2. Usa: 'rellenar: {filename} con {json_filename}'\n"

            return result

        except Exception as e:
            return f"❌ Error creando datos de ejemplo: {e}"

    def fill_document(self, command: str) -> str:
        """Rellena un documento con los datos proporcionados"""
        try:
            # Parsear comando: "plantilla.docx con datos.json"
            if " con " not in command:
                return "❌ Formato incorrecto. Usa: 'rellenar: plantilla.docx con datos.json'"

            parts = command.split(" con ")
            template_name = parts[0].strip()
            data_name = parts[1].strip()

            # Verificar archivos
            template_path = os.path.join(TEMPLATES_DIR, template_name)
            data_path = os.path.join(DATA_DIR, data_name)

            if not os.path.exists(template_path):
                return f"❌ No se encontró la plantilla: {template_name}"

            if not os.path.exists(data_path):
                return f"❌ No se encontró el archivo de datos: {data_name}"

            # Cargar datos
            data = self.load_data(data_path)
            if not data:
                return f"❌ No se pudieron cargar los datos de: {data_name}"

            # Procesar según el tipo de plantilla
            output_name = f"{template_name.split('.')[0]}_rellenado_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if template_name.endswith('.docx'):
                return self.fill_docx(template_path, data, output_name)
            elif template_name.endswith('.txt'):
                return self.fill_txt(template_path, data, output_name)
            else:
                return f"❌ Formato de plantilla no soportado: {template_name}"

        except Exception as e:
            return f"❌ Error rellenando documento: {e}"

    def extract_text_from_file(self, file_path: str) -> str:
        """Extrae texto de diferentes formatos de archivo"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_path.endswith('.docx'):
                doc = Document(file_path)
                text = []
                for paragraph in doc.paragraphs:
                    text.append(paragraph.text)
                return '\n'.join(text)

            elif file_path.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = []
                    for page in reader.pages:
                        text.append(page.extract_text())
                    return '\n'.join(text)

            return ""
        except Exception as e:
            return f"Error extrayendo texto: {e}"

    def load_data(self, data_path: str) -> dict:
        """Carga datos de diferentes formatos"""
        try:
            if data_path.endswith('.json'):
                with open(data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            elif data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
                # Convertir primera fila a diccionario
                if len(df) > 0:
                    return df.iloc[0].to_dict()
                return {}

            elif data_path.endswith('.xlsx'):
                df = pd.read_excel(data_path)
                if len(df) > 0:
                    return df.iloc[0].to_dict()
                return {}

            elif data_path.endswith('.txt'):
                # Formato clave=valor, si no, intentamos separar por tabulaciones o comas
                data = {}
                with open(data_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                        elif '\t' in line:
                            key, value = line.split('\t', 1)
                        elif ',' in line:
                            key, value = line.split(',', 1)
                        else:
                            continue
                        data[key.strip()] = value.strip()
                return data

            return {}
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return {}

    def fill_docx(self, template_path: str, data: dict,
                  output_name: str) -> str:
        """Rellena un documento DOCX"""
        try:
            doc = Document(template_path)

            # Agregar fecha actual si no está en los datos
            if 'fecha' not in data:
                data['fecha'] = datetime.now().strftime("%Y-%m-%d")

            replacements = 0

            # Reemplazar en párrafos
            for paragraph in doc.paragraphs:
                for key, value in data.items():
                    if key.startswith('_'):  # Saltar metadatos
                        continue

                    patterns = [f'{{{{{key}}}}}', f'[{key}]', f'_{key}_']
                    for pattern in patterns:
                        if pattern in paragraph.text:
                            paragraph.text = paragraph.text.replace(
                                pattern, str(value))
                            replacements += 1

            # Reemplazar en tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in data.items():
                            if key.startswith('_'):
                                continue

                            patterns = [
                                f'{{{{{key}}}}}', f'[{key}]', f'_{key}_'
                            ]
                            for pattern in patterns:
                                if pattern in cell.text:
                                    cell.text = cell.text.replace(
                                        pattern, str(value))
                                    replacements += 1

            # Guardar documento rellenado
            output_path = os.path.join(OUTPUT_DIR, f"{output_name}.docx")
            doc.save(output_path)

            result = f"✅ **DOCUMENTO RELLENADO EXITOSAMENTE**\n\n"
            result += f"📄 **Archivo:** {output_name}.docx\n"
            result += f"📁 **Ubicación:** {OUTPUT_DIR}/\n"
            result += f"🔄 **Reemplazos realizados:** {replacements}\n\n"

            if replacements == 0:
                result += "⚠️ **Advertencia:** No se realizaron reemplazos. Verifica que:\n"
                result += "• Los marcadores en la plantilla coincidan con los datos\n"
                result += "• Usa formato {{campo}}, [campo] o _campo_\n"
            else:
                result += "💡 **El documento está listo para usar**\n"

            return result

        except Exception as e:
            return f"❌ Error procesando DOCX: {e}"

    def fill_txt(self, template_path: str, data: dict,
                 output_name: str) -> str:
        """Rellena un documento de texto"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Agregar fecha actual si no está en los datos
            if 'fecha' not in data:
                data['fecha'] = datetime.now().strftime("%Y-%m-%d")

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

            # Guardar archivo rellenado
            output_path = os.path.join(OUTPUT_DIR, f"{output_name}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result = f"✅ **DOCUMENTO RELLENADO EXITOSAMENTE**\n\n"
            result += f"📄 **Archivo:** {output_name}.txt\n"
            result += f"📁 **Ubicación:** {OUTPUT_DIR}/\n"
            result += f"🔄 **Reemplazos realizados:** {replacements}\n\n"

            if replacements == 0:
                result += "⚠️ **Advertencia:** No se realizaron reemplazos. Verifica que:\n"
                result += "• Los marcadores en la plantilla coincidan con los datos\n"
                result += "• Usa formato {{campo}}, [campo] o _campo_\n"

            return result

        except Exception as e:
            return f"❌ Error procesando TXT: {e}"


# Instancia global
document_filler = DocumentFiller()


def run(prompt: str) -> str:
    """Función principal de la herramienta"""
    return document_filler.run(prompt)
