def run(url: str) -> str:
    """
    Prepara una URL para ser abierta en el navegador del usuario.
    Funciona tanto en local como en dispositivos remotos.
    """
    url = url.strip()
    
    # Validar que sea una URL válida
    if not url.startswith(("http://", "https://")):
        # Si no tiene protocolo, agregar https por defecto
        if not url.startswith("www."):
            url = "https://" + url
        else:
            url = "https://" + url
    
    try:
        # En lugar de usar webbrowser.open(), devolvemos la URL
        # para que el frontend la maneje
        return f"OPEN_URL:{url}"
    except Exception as e:
        return f"ERROR al procesar la URL: {e}"