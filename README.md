🤖 Agente Inteligente Gemini
Un agente autónomo con IA que utiliza el modelo Google Gemini para ejecutar comandos y realizar tareas.
Cuenta con una interfaz web moderna (modo claro y oscuro) y un conjunto de herramientas para aumentar su funcionalidad.

📂 Estructura del proyecto
ia_agent/
│── agent.py          # Lógica principal del agente que elige la herramienta
│── main.py           # Servidor FastAPI para manejar peticiones y la interfaz
│── .env              # Variables de entorno y API keys
│── requirements.txt  # Dependencias del proyecto
│
├── templates/
│   └── index.html    # Plantilla HTML de la interfaz
│
├── static/
│   ├── style.css     # Estilos CSS para el modo claro y oscuro
│   └── script.js     # Lógica de la interfaz (temas, animaciones)
│
├── notes/            # Carpeta para guardar notas
├── code/             # Carpeta para guardar archivos de código
│
├── tools/
│   ├── note.py       # Herramienta para guardar y leer notas
│   ├── save_code.py  # Herramienta para guardar código
│   ├── web_search.py # Herramienta para buscar en la web
│   ├── web_open.py   # Herramienta para abrir enlaces
│   └── calculator.py # Herramienta para realizar cálculos
│
└── README.md         # Este archivo

⚙️ Configuración inicial
# 1️⃣ Crear entorno virtual
python -m venv agent-env

# 2️⃣ Activar entorno en Windows
.gent-env\Scriptsctivate

# 2️⃣ Activar entorno en Mac/Linux
source agent-env/bin/activate

# 3️⃣ Instalar dependencias
pip install -r requirements.txt

📦 Dependencias principales
fastapi
uvicorn
requests
python-dotenv
jinja2

🔐 Variables de entorno
GEMINI_API_KEY=tu_api_key_gemini
GOOGLE_CSE_API_KEY=tu_api_key_google_cse
GOOGLE_CSE_ID=tu_cse_id

🔑 Cómo conseguir las API Keys
### Gemini
1. Accede a Google Cloud Console.
2. Activa Gemini API.
3. Genera tu GEMINI_API_KEY en la sección de credenciales.

### Google Custom Search (CSE)
1. Activa Custom Search API.
2. Crea un motor de búsqueda programable.
3. Copia GOOGLE_CSE_ID y GOOGLE_CSE_API_KEY.

🛠 Funcionalidades del agente
# 📝 Notas
guardar: tu nota   # Guarda una nueva nota
leer               # Muestra todas las notas
borrar             # Elimina todas las notas
descargar          # Exporta las notas a un archivo de texto

# 💻 Guardar código
nombre_archivo||contenido_del_codigo

# 🧮 Calculadora
2 + 2 * (3 - 1)   # Devuelve 6

# 🔍 Búsqueda en la web
# Devuelve los 5 resultados principales con título, enlace y descripción.

# 🌐 Abrir enlaces
# Abre una URL directamente en el navegador.

🚀 Ejecutar localmente
uvicorn main:app --reload
http://127.0.0.1:8000

📌 Tecnologías usadas
🐍 Python 3
⚡ FastAPI (backend)
🎨 HTML, CSS, JavaScript (frontend con modo oscuro)
🔑 Google Gemini API
🔍 Google Custom Search API

