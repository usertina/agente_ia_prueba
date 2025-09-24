def run(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"ERROR: {e}"
