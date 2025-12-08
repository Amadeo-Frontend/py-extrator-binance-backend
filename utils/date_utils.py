from datetime import datetime
from fastapi import HTTPException


def parse_date(s: str) -> datetime:
    """
    Converte string 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM' para datetime.
    """
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            pass

    raise HTTPException(
        status_code=400,
        detail=f"Formato de data inválido: '{s}'. Use 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM'."
    )
