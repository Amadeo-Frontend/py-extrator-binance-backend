# backend/routers/binance.py (VERSÃO FINAL COM BACKGROUND TASKS PARA TUDO)

import io
import os
import zipfile
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks
import pandas as pd
from binance.client import Client

# Importa os modelos e funções comuns
from .common import RequestData, analisar_tecnica_gatilho_universal

router = APIRouter(
    prefix="/binance",
    tags=["Binance (Cripto)"]
)
client_binance = Client()

# --- FUNÇÕES DE LÓGICA (sem alterações) ---

def fetch_binance_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
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

@router.get("/available-assets/", summary="Lista todos os ativos USDT da Binance")
def get_available_assets():
    try:
        exchange_info = client_binance.get_exchange_info()
        symbols = sorted([s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')])
        return {"assets": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível buscar a lista de ativos da Binance: {e}")

# --- FUNÇÕES DE TRABALHO (PARA BACKGROUND) ---

def do_extraction_and_zip(data: RequestData):
    """Função de trabalho para o extrator genérico."""
    print(f"BACKGROUND: Iniciando extração para {len(data.assets)} ativos.")
    
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Usa um nome de arquivo que identifica a fonte e o tipo
    zip_filename = f"extrator_binance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)

    found_data = False
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
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
        print(f"BACKGROUND: Nenhum dado encontrado para a extração. Removendo arquivo zip vazio.")
        os.remove(zip_filepath) # Remove o arquivo zip se ele estiver vazio
        return

    print(f"BACKGROUND: Extração concluída. Salvo em: {zip_filepath}")

def do_analysis_and_zip(data: RequestData):
    """Função de trabalho para a análise de gatilho."""
    print(f"BACKGROUND: Iniciando análise 4e9 para {data.assets[0]}")
    asset = data.assets[0]
    df_historico = fetch_binance_data(asset, '1m', data.start_date, data.end_date)
    
    if df_historico.empty:
        print(f"BACKGROUND: Nenhum dado encontrado para {asset}. Abortando análise.")
        return

    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty:
        print(f"BACKGROUND: Nenhum gatilho encontrado para {asset}. Abortando análise.")
        return

    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Usa um nome de arquivo que identifica a fonte e o tipo
    zip_filename = f"analise_4e9_binance_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)

    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    html_output = (
        f"<html><body><h1>Relatório para {asset}</h1><pre>{pd.Series(stats).to_string()}</pre>{df_analise.to_html(index=False)}</body></html>"
    )

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"analise_{asset}_M1.csv", df_analise.to_csv(index=False))
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)
    
    print(f"BACKGROUND: Análise 4e9 para {asset} concluída. Salvo em: {zip_filepath}")

# --- ENDPOINTS COM BACKGROUND TASKS ---

@router.post("/download-data/", summary="Inicia a extração de dados da Binance em segundo plano")
async def endpoint_download_data(data: RequestData, background_tasks: BackgroundTasks):
    # Adiciona a função de trabalho à fila
    background_tasks.add_task(do_extraction_and_zip, data)
    # Retorna uma resposta IMEDIATA
    return {"message": f"Extração para {len(data.assets)} ativo(s) iniciada em segundo plano."}

@router.post("/analise-tecnica-gatilho/", summary="Inicia a análise de gatilho para Binance em segundo plano")
async def endpoint_analise_gatilho_binance(data: RequestData, background_tasks: BackgroundTasks):
    # Adiciona a função de trabalho à fila
    background_tasks.add_task(do_analysis_and_zip, data)
    # Retorna uma resposta IMEDIATA
    return {"message": f"Análise para {data.assets[0]} iniciada em segundo plano."}
