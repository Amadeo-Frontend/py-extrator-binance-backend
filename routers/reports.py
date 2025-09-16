# backend/routers/reports.py

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

REPORTS_DIR = "reports"

# Garante que o diretório de relatórios exista ao iniciar
os.makedirs(REPORTS_DIR, exist_ok=True)

@router.get("/", summary="Lista todos os relatórios gerados")
def list_reports() -> List[str]:
    """
    Verifica a pasta 'reports' no servidor e retorna uma lista com os nomes
    dos arquivos .zip disponíveis para download.
    """
    try:
        # Lista apenas arquivos .zip e os ordena do mais novo para o mais antigo
        files = sorted(
            [f for f in os.listdir(REPORTS_DIR) if f.endswith('.zip')],
            key=lambda f: os.path.getmtime(os.path.join(REPORTS_DIR, f)),
            reverse=True
        )
        return files
    except Exception as e:
        print(f"Erro ao listar relatórios: {e}")
        return []

@router.get("/{filename}", summary="Baixa um relatório específico")
def download_report(filename: str):
    """
    Fornece o download de um arquivo específico da pasta 'reports'.
    O frontend deve garantir que o nome do arquivo é válido.
    """
    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    
    # Usa FileResponse para enviar o arquivo para o usuário
    return FileResponse(path=filepath, media_type='application/zip', filename=filename)
