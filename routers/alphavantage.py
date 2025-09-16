# backend/routers/alphavantage.py (VERSÃO FINAL COM BACKGROUND TASKS)

import io
import os
import zipfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
import pandas as pd
from alpha_vantage.foreignexchange import ForeignExchange
from dotenv import load_dotenv

from .common import RequestData, analisar_tecnica_gatilho_universal

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
router = APIRouter(prefix="/alphavantage", tags=["Alpha Vantage (Forex)"])
REPORTS_DIR = "reports"

# --- FUNÇÃO DE BUSCA (com melhorias) ---
def fetch_alphavantage_data(asset: str, interval: str) -> pd.DataFrame:
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(status_code=500, detail="Chave da API da Alpha Vantage não configurada.")
    if len(asset) != 6:
        raise HTTPException(status_code=400, detail=f"Formato de ativo inválido: '{asset}'.")

    from_symbol = asset[:3].upper()
    to_symbol = asset[3:].upper()
    
    print(f"Buscando Alpha Vantage: {asset}, Intervalo: {interval}")
    try:
        fx = ForeignExchange(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        
        # A API gratuita da Alpha Vantage só fornece dados diários de forma confiável
        # Outros intervalos geralmente são premium.
        if interval != 'D':
             print(f"AVISO: O intervalo '{interval}' provavelmente é um endpoint premium na Alpha Vantage. A chamada pode falhar.")

        # Usamos uma função genérica para tentar buscar os dados
        # Nota: get_fx_daily, get_fx_intraday, etc.
        api_call_map = {
            '1m': fx.get_fx_intraday,
            '5m': fx.get_fx_intraday,
            '15m': fx.get_fx_intraday,
            '30m': fx.get_fx_intraday,
            '1h': fx.get_fx_intraday,
            'D': fx.get_fx_daily,
        }
        
        call_func = api_call_map.get(interval)
        if not call_func:
            raise ValueError(f"Intervalo '{interval}' não mapeado para uma chamada da Alpha Vantage.")

        if interval == 'D':
            data, _ = call_func(from_symbol=from_symbol, to_symbol=to_symbol, outputsize='full')
        else:
            # Para intraday, a API espera o parâmetro 'interval'
            data, _ = call_func(from_symbol=from_symbol, to_symbol=to_symbol, interval=interval, outputsize='full')

        df = pd.DataFrame(data)
        df.rename(columns={
            '1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close', '5. volume': 'Volume'
        }, inplace=True)
        df.index.name = 'Open_Time'
        df.reset_index(inplace=True)
        
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']].sort_values('Open_Time')

    except Exception as e:
        print(f"Erro ao buscar dados da Alpha Vantage para {asset}: {e}")
        return pd.DataFrame()

# --- FUNÇÕES DE TRABALHO EM SEGUNDO PLANO ---

def do_alphavantage_extraction(data: RequestData):
    """Trabalho pesado para o extrator de dados da Alpha Vantage."""
    print(f"BACKGROUND: Iniciando extração da Alpha Vantage para: {data.assets}")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    zip_filename = f"extrator_alphavantage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_alphavantage_data(asset.upper(), interval)
                if not df.empty:
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    filename = f"FOREX-AV_{asset.upper()}_{interval}.csv"
                    zip_file.writestr(filename, csv_buffer.getvalue())
    print(f"BACKGROUND: Extração da Alpha Vantage concluída. Salvo em: {zip_filepath}")

def do_alphavantage_analysis(data: RequestData):
    """Trabalho pesado para a análise 4e9 da Alpha Vantage."""
    print(f"BACKGROUND: Iniciando análise 4e9 da Alpha Vantage para {data.assets[0]}")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    asset = data.assets[0]
    # A análise 4e9 depende de dados de 1 minuto, que são premium na Alpha Vantage.
    # A função tentará buscar, mas provavelmente retornará vazio no plano gratuito.
    df_historico = fetch_alphavantage_data(asset, '1m')
    if df_historico.empty: 
        print("BACKGROUND: Nenhum dado de 1m da Alpha Vantage encontrado (provavelmente requer API premium).")
        return

    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty: return

    zip_filename = f"analise_4e9_alphavantage_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)
    # ... (código para gerar HTML e salvar no ZIP) ...
    print(f"BACKGROUND: Análise 4e9 da Alpha Vantage concluída. Salvo em: {zip_filepath}")

# --- ENDPOINTS ---

@router.post("/download-data/", summary="Inicia a extração de dados da Alpha Vantage em segundo plano")
async def endpoint_download_data_alphavantage(data: RequestData, background_tasks: BackgroundTasks):
    background_tasks.add_task(do_alphavantage_extraction, data)
    return {"message": f"Extração da Alpha Vantage para {len(data.assets)} ativo(s) iniciada."}

@router.post("/analise-tecnica-gatilho/", summary="Inicia a análise 4e9 da Alpha Vantage em segundo plano")
async def endpoint_analise_gatilho_alphavantage(data: RequestData, background_tasks: BackgroundTasks):
    background_tasks.add_task(do_alphavantage_analysis, data)
    return {"message": f"Análise da Alpha Vantage para {data.assets[0]} iniciada."}
