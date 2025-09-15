# backend/routers/binance.py

import io
import zipfile
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from binance.client import Client

# Importe os modelos de dados e funções auxiliares que este roteador precisa
from .common import RequestData, parse_date, analisar_tecnica_gatilho_universal

# Cliente da Binance, que funciona perfeitamente para dados públicos
client_binance = Client()

# Crie um roteador. É como uma "mini-FastAPI"
router = APIRouter(
    prefix="/binance",  # Adiciona /binance na frente de todas as rotas deste arquivo
    tags=["Binance"]    # Agrupa estes endpoints na documentação da API
)

# --- LÓGICA DE EXTRAÇÃO DE DADOS (BINANCE) ---
def fetch_binance_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    """Busca dados históricos da Binance para um único ativo e intervalo."""
    end_dt = parse_date(end_date_str)
    end_date_inclusive = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Buscando Binance: {asset}, Intervalo: {interval}, de {start_date_str} até {end_date_str}")

    try:
        klines = client_binance.get_historical_klines(asset, interval, start_date_str, end_date_inclusive)
        if not klines: return pd.DataFrame()

        columns = ['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore']
        df = pd.DataFrame(klines, columns=columns)

        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        df = df[df['Open_Time'] < pd.to_datetime(end_date_inclusive)]

        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        
        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']]
    except Exception as e:
        print(f"Erro ao buscar dados para {asset} ({interval}): {e}")
        return pd.DataFrame()

# --- ENDPOINTS DA BINANCE ---
@router.get("/available-assets/", summary="Lista todos os ativos USDT da Binance")
def get_available_assets():
    """Busca e retorna uma lista de todos os símbolos de trading que terminam com 'USDT' na Binance."""
    try:
        exchange_info = client_binance.get_exchange_info()
        symbols = sorted([s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')])
        return {"assets": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível buscar a lista de ativos da Binance: {e}")

@router.post("/download-data/", summary="Extrator de Dados Genérico da Binance")
async def endpoint_download_data(data: RequestData):
    zip_buffer = io.BytesIO()
    found_data = False
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_binance_data(asset.upper(), interval, data.start_date, data.end_date)
                if not df.empty:
                    found_data = True
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    filename = f"{asset.upper()}_{interval}_{data.start_date}_a_{data.end_date}.csv"
                    zip_file.writestr(filename, csv_buffer.getvalue())
    if not found_data:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para os parâmetros fornecidos.")
    zip_buffer.seek(0)
    download_filename = f"binance_data_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})

@router.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho para Binance")
async def endpoint_analise_gatilho_binance(data: RequestData):
    asset = data.assets[0]
    df_historico = fetch_binance_data(asset, '1m', data.start_date, data.end_date)
    if df_historico.empty:
        raise HTTPException(status_code=404, detail=f"Nenhum dado de 1 minuto encontrado para {asset} no período.")
    
    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty:
        raise HTTPException(status_code=404, detail="Nenhum gatilho válido encontrado para a análise no período fornecido.")
    
    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    
    html_output = (
        f"<html><head><meta charset='utf-8'><title>Análise de Gatilho - {asset}</title>"
        f"<style>body{{font-family:Arial,sans-serif;}} table{{border-collapse:collapse;width:100%;}} th,td{{border:1px solid #ddd;padding:8px;text-align:left;}} .styled-table th{{background-color:#f2f2f2;}}</style></head><body>"
        f"<h1>Relatório de Análise de Gatilho</h1><h2>Ativo: {asset}</h2>"
        f"<p>Período: {data.start_date} a {data.end_date}</p>"
        f"<p>Data de Geração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        f"<h3>Estatísticas de Resultado</h3><pre>{pd.Series(stats).to_string()}</pre>"
        f"<h3>Detalhes das Operações</h3>{df_analise.to_html(classes='styled-table', index=False, escape=False)}"
        f"</body></html>"
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"analise_{asset}_M1.csv", df_analise.to_csv(index=False))
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)
    
    zip_buffer.seek(0)
    download_filename = f"analise_gatilho_{asset}_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})
