# backend/routers/alphavantage.py (VERSÃO COM TIMEFRAME)

import io
import os
import zipfile
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from alpha_vantage.foreignexchange import ForeignExchange
from dotenv import load_dotenv

from .common import RequestData, analisar_tecnica_gatilho_universal

load_dotenv()

AV_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

router = APIRouter(
    prefix="/alphavantage",
    tags=["Alpha Vantage (Forex)"]
)

# --- MAPA DE INTERVALOS E FUNÇÃO DE BUSCA ATUALIZADA ---

# Mapeia nossos intervalos para os da Alpha Vantage
AV_INTERVAL_MAP = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "60min",
    "D": "daily"
}

def fetch_alphavantage_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    if not AV_API_KEY:
        raise HTTPException(status_code=500, detail="Chave da API da Alpha Vantage não configurada no servidor.")

    if len(asset) != 6:
        raise HTTPException(status_code=400, detail=f"Formato de ativo inválido para Forex: '{asset}'. Use 6 caracteres, como 'EURUSD'.")
    
    from_symbol = asset[:3]
    to_symbol = asset[3:]
    
    av_interval = AV_INTERVAL_MAP.get(interval)
    if not av_interval:
        raise HTTPException(status_code=400, detail=f"Intervalo '{interval}' não é suportado pela Alpha Vantage. Use 1m, 5m, 15m, 30m, 1h ou D.")

    print(f"Buscando Alpha Vantage: {asset}, Intervalo: {av_interval}")

    try:
        fx = ForeignExchange(key=AV_API_KEY, output_format='pandas')
        
        # Lógica para escolher a função correta da API
        if av_interval == 'daily':
            data, _ = fx.get_currency_exchange_daily(from_symbol=from_symbol, to_symbol=to_symbol, outputsize='full')
        else:
            # NOTA: A API gratuita para intraday é muito limitada (geralmente poucos dias de dados)
            data, _ = fx.get_currency_exchange_intraday(from_symbol=from_symbol, to_symbol=to_symbol, interval=av_interval, outputsize='full')

        if data.empty:
            return pd.DataFrame()

        data.rename(columns={'1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close'}, inplace=True)
        data['Volume'] = 0
        data['Open_Time'] = pd.to_datetime(data.index) # Converte o índice para uma coluna de data/hora
        
        # Filtra o DataFrame pelo período solicitado
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
        data = data[(data['Open_Time'].dt.date >= start_dt.date()) & (data['Open_Time'].dt.date <= end_dt.date())]

        data['Resultado'] = data.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        
        return data[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']].sort_values('Open_Time')

    except Exception as e:
        error_message = str(e)
        if "Our standard API call frequency is 5 calls per minute and 500 calls per day" in error_message:
            raise HTTPException(status_code=429, detail="Limite de chamadas da API da Alpha Vantage excedido. Tente novamente mais tarde.")
        print(f"Erro ao buscar dados da Alpha Vantage para {asset}: {e}")
        return pd.DataFrame()

# --- ENDPOINT DE EXTRAÇÃO DE DADOS (ATUALIZADO) ---
@router.post("/download-data/", summary="Extrator de Dados de Forex (Alpha Vantage)")
async def endpoint_download_data_av(data: RequestData):
    zip_buffer = io.BytesIO()
    found_data = False
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals: # Agora iteramos sobre os intervalos
                df = fetch_alphavantage_data(asset.upper(), interval, data.start_date, data.end_date)
                if not df.empty:
                    found_data = True
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    # Nome do arquivo agora inclui o intervalo
                    filename = f"FOREX_{asset.upper()}_{interval}_{data.start_date}_a_{data.end_date}.csv"
                    zip_file.writestr(filename, csv_buffer.getvalue())
    
    if not found_data:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os parâmetros fornecidos na Alpha Vantage.")
    
    zip_buffer.seek(0)
    download_filename = f"alphavantage_forex_data_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})

# --- ENDPOINT DA TÉCNICA 4 E 9 (AGORA FUNCIONAL, MAS COM DADOS LIMITADOS) ---
@router.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho para Forex (Alpha Vantage)")
async def endpoint_analise_gatilho_av(data: RequestData):
    asset = data.assets[0]
    # A técnica 4e9 precisa de dados de 1 minuto
    df_historico = fetch_alphavantage_data(asset, '1m', data.start_date, data.end_date)
    
    if df_historico.empty:
        raise HTTPException(status_code=404, detail=f"Nenhum dado de 1 minuto encontrado para {asset} no período. A API gratuita da Alpha Vantage é limitada para dados intraday.")
    
    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty:
        raise HTTPException(status_code=404, detail="Nenhum gatilho válido encontrado para a análise no período fornecido.")
    
    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    
    html_output = (
        f"<html><head><title>Análise 4e9 - {asset}</title></head><body>"
        f"<h1>Relatório de Análise 4e9 (Forex)</h1><h2>Ativo: {asset}</h2>"
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
    download_filename = f"analise_4e9_forex_{asset}_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})
