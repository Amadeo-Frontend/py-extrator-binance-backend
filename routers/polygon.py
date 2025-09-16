# backend/routers/polygon.py (VERSÃO CORRIGIDA)

import io
import os
import zipfile
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from polygon import RESTClient
from dotenv import load_dotenv

# Importe os modelos de dados e funções auxiliares do arquivo common.py
from .common import RequestData, analisar_tecnica_gatilho_universal

load_dotenv()

# --- CONFIGURAÇÃO DO CLIENTE POLYGON.IO ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

router = APIRouter(
    prefix="/polygon",
    tags=["Polygon.io (Forex)"]
)

# --- MAPA DE INTERVALOS E FUNÇÃO DE BUSCA ---

# Mapeia nossos intervalos para os da Polygon.io
POLYGON_TIMESPAN_MAP = {
    "1m": "minute", "5m": "minute", "15m": "minute", "30m": "minute", "1h": "hour", "D": "day"
}
POLYGON_MULTIPLIER_MAP = {
    "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 1, "D": 1
}

def fetch_polygon_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """
    Busca dados históricos de Forex da API da Polygon.io.
    """
    if not POLYGON_API_KEY:
        raise HTTPException(status_code=500, detail="Chave da API da Polygon.io não configurada no servidor.")

    if len(asset) != 6:
        raise HTTPException(status_code=400, detail=f"Formato de ativo inválido para Forex: '{asset}'. Use 6 caracteres, como 'EURUSD'.")
    
    # Polygon usa o formato C:EURUSD para Forex
    polygon_ticker = f"C:{asset.upper()}"
    
    timespan = POLYGON_TIMESPAN_MAP.get(interval)
    multiplier = POLYGON_MULTIPLIER_MAP.get(interval)

    if not timespan:
        raise HTTPException(status_code=400, detail=f"Intervalo '{interval}' não suportado. Use 1m, 5m, 15m, 30m, 1h ou D.")

    print(f"Buscando Polygon.io: {polygon_ticker}, Multiplicador: {multiplier}, Timespan: {timespan}")

    try:
        # --- CORREÇÃO APLICADA AQUI ---
        # Instancia o cliente diretamente, sem o 'with'
        client = RESTClient(POLYGON_API_KEY)

        aggs = client.get_aggs(
            ticker=polygon_ticker,
            multiplier=multiplier,
            timespan=timespan,
            from_=start_date_str,
            to=end_date_str,
            limit=50000 # Limite máximo de barras por chamada
        )

        if not aggs:
            return pd.DataFrame()

        # Converte a resposta para um DataFrame do Pandas
        df = pd.DataFrame(aggs)
        
        # Renomeia as colunas para o nosso padrão universal
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'timestamp': 'Open_Time'
        }, inplace=True)

        # Converte o timestamp (que vem em milissegundos) para datetime
        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        
        # Calcula o resultado (Call/Put)
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        
        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']].sort_values('Open_Time')

    except Exception as e:
        # Trata erros comuns da API da Polygon
        error_message = str(e)
        if "you have reached your request limit" in error_message:
            raise HTTPException(status_code=429, detail="Limite de chamadas da API da Polygon.io excedido (5 chamadas/minuto no plano gratuito).")
        print(f"Erro ao buscar dados da Polygon.io para {asset}: {e}")
        return pd.DataFrame()

# --- ENDPOINT DE EXTRAÇÃO DE DADOS ---
@router.post("/download-data/", summary="Extrator de Dados de Forex (Polygon.io)")
async def endpoint_download_data_polygon(data: RequestData):
    zip_buffer = io.BytesIO()
    found_data = False
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_polygon_data(asset.upper(), interval, data.start_date, data.end_date)
                if not df.empty:
                    found_data = True
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    filename = f"FOREX_{asset.upper()}_{interval}_{data.start_date}_a_{data.end_date}.csv"
                    zip_file.writestr(filename, csv_buffer.getvalue())
    
    if not found_data:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os parâmetros fornecidos na Polygon.io.")
    
    zip_buffer.seek(0)
    download_filename = f"polygon_forex_data_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})

# --- ENDPOINT DA TÉCNICA 4 E 9 ---
@router.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho para Forex (Polygon.io)")
async def endpoint_analise_gatilho_polygon(data: RequestData):
    asset = data.assets[0]
    df_historico = fetch_polygon_data(asset, '1m', data.start_date, data.end_date)
    
    if df_historico.empty:
        raise HTTPException(status_code=404, detail=f"Nenhum dado de 1 minuto encontrado para {asset} no período na Polygon.io.")
    
    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty:
        raise HTTPException(status_code=404, detail="Nenhum gatilho válido encontrado para a análise no período fornecido.")
    
    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    
    html_output = (
        f"<html><head><title>Análise 4e9 - {asset}</title></head><body>"
        f"<h1>Relatório de Análise 4e9 (Forex - Polygon.io)</h1><h2>Ativo: {asset}</h2>"
        f"<p>Período: {data.start_date} a {data.end_date}</p>"
        f"<h3>Estatísticas</h3><pre>{pd.Series(stats).to_string()}</pre>"
        f"<h3>Detalhes</h3>{df_analise.to_html(index=False)}"
        f"</body></html>"
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"analise_4e9_{asset}_M1.csv", df_analise.to_csv(index=False))
        zip_file.writestr(f"relatorio_4e9_{asset}_M1.html", html_output)
    
    zip_buffer.seek(0)
    download_filename = f"analise_4e9_polygon_{asset}_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})
