import os

CODE_DIR = "code"
os.makedirs(CODE_DIR, exist_ok=True)

def run(data: str) -> str:
    if "||" not in data:
        return "Formato correcto: nombre_archivo||contenido"
    name, content = data.split("||", 1)
    file_path = os.path.join(CODE_DIR, name.strip())
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        return f"Código guardado en {file_path}"
    except Exception as e:
        return f"ERROR: {e}"
