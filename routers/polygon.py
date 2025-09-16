# backend/routers/polygon.py (VERSÃO FINAL COM BACKGROUND TASKS)

import io
import os
import zipfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
import pandas as pd
from polygon import RESTClient
from dotenv import load_dotenv

from .common import RequestData, analisar_tecnica_gatilho_universal

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
router = APIRouter(prefix="/polygon", tags=["Polygon.io (Forex)"])
REPORTS_DIR = "reports"

# --- MAPAS E FUNÇÃO DE BUSCA (sem alterações) ---
POLYGON_TIMESPAN_MAP = {"1m": "minute", "5m": "minute", "15m": "minute", "30m": "minute", "1h": "hour", "D": "day"}
POLYGON_MULTIPLIER_MAP = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 1, "D": 1}

def fetch_polygon_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    if not POLYGON_API_KEY: raise HTTPException(status_code=500, detail="Chave da API da Polygon.io não configurada.")
    if len(asset) != 6: raise HTTPException(status_code=400, detail=f"Formato de ativo inválido: '{asset}'.")
    
    polygon_ticker = f"C:{asset.upper()}"
    timespan = POLYGON_TIMESPAN_MAP.get(interval)
    multiplier = POLYGON_MULTIPLIER_MAP.get(interval)
    if not timespan: raise HTTPException(status_code=400, detail=f"Intervalo '{interval}' não suportado.")

    print(f"Buscando Polygon.io: {polygon_ticker}, {multiplier} {timespan}")
    try:
        client = RESTClient(POLYGON_API_KEY)
        aggs = client.get_aggs(ticker=polygon_ticker, multiplier=multiplier, timespan=timespan, from_=start_date_str, to=end_date_str, limit=50000)
        if not aggs: return pd.DataFrame()
        
        df = pd.DataFrame(aggs)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume', 'timestamp': 'Open_Time'}, inplace=True)
        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']].sort_values('Open_Time')
    except Exception as e:
        if "you have reached your request limit" in str(e): raise HTTPException(status_code=429, detail="Limite de chamadas da API da Polygon.io excedido.")
        print(f"Erro ao buscar dados da Polygon.io para {asset}: {e}")
        return pd.DataFrame()

# --- FUNÇÕES DE TRABALHO EM SEGUNDO PLANO ---

def do_polygon_extraction(data: RequestData):
    """Trabalho pesado para o extrator de dados da Polygon.io."""
    print(f"BACKGROUND: Iniciando extração da Polygon.io para: {data.assets}")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    zip_filename = f"extrator_polygon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_polygon_data(asset.upper(), interval, data.start_date, data.end_date)
                if not df.empty:
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    filename = f"FOREX_{asset.upper()}_{interval}_{data.start_date}_a_{data.end_date}.csv"
                    zip_file.writestr(filename, csv_buffer.getvalue())
    print(f"BACKGROUND: Extração da Polygon.io concluída. Salvo em: {zip_filepath}")

def do_polygon_analysis(data: RequestData):
    """Trabalho pesado para a análise 4e9 da Polygon.io."""
    print(f"BACKGROUND: Iniciando análise 4e9 da Polygon.io para {data.assets[0]}")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    asset = data.assets[0]
    df_historico = fetch_polygon_data(asset, '1m', data.start_date, data.end_date)
    if df_historico.empty: return

    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty: return

    zip_filename = f"analise_4e9_polygon_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)
    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    html_output = f"<html><body><h1>Relatório 4e9 para {asset}</h1><pre>{pd.Series(stats).to_string()}</pre>{df_analise.to_html(index=False)}</body></html>"

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"analise_{asset}_M1.csv", df_analise.to_csv(index=False))
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)
    print(f"BACKGROUND: Análise 4e9 da Polygon.io concluída. Salvo em: {zip_filepath}")

# --- ENDPOINTS ---

@router.post("/download-data/", summary="Inicia a extração de dados da Polygon.io em segundo plano")
async def endpoint_download_data_polygon(data: RequestData, background_tasks: BackgroundTasks):
    background_tasks.add_task(do_polygon_extraction, data)
    return {"message": f"Extração para {len(data.assets)} ativo(s) iniciada em segundo plano."}

@router.post("/analise-tecnica-gatilho/", summary="Inicia a análise 4e9 da Polygon.io em segundo plano")
async def endpoint_analise_gatilho_polygon(data: RequestData, background_tasks: BackgroundTasks):
    background_tasks.add_task(do_polygon_analysis, data)
    return {"message": f"Análise para {data.assets[0]} iniciada em segundo plano."}
