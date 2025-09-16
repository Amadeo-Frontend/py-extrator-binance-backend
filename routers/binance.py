# backend/routers/binance.py (VERSÃO COM BACKGROUND TASKS)

import io
import zipfile
from datetime import datetime, timedelta
# 1. Importe o BackgroundTasks
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import pandas as pd
from binance.client import Client

from .common import RequestData, analisar_tecnica_gatilho_universal

# ... (código do router, cliente, etc.) ...
router = APIRouter(
    prefix="/binance",
    tags=["Binance (Cripto)"]
)
client_binance = Client()

# ... (função fetch_binance_data e get_available_assets continuam iguais) ...
def fetch_binance_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    # ... (sem alterações aqui) ...
    # (seu código atual para esta função)
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
    # ... (sem alterações aqui) ...
    try:
        exchange_info = client_binance.get_exchange_info()
        symbols = sorted([s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')])
        return {"assets": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível buscar a lista de ativos da Binance: {e}")


# --- MODIFICAÇÃO IMPORTANTE AQUI ---

# 2. Crie uma função de trabalho separada
def do_analysis_and_zip(data: RequestData):
    """Esta função faz o trabalho pesado e será executada em segundo plano."""
    print(f"BACKGROUND: Iniciando análise para {data.assets[0]}")
    asset = data.assets[0]
    df_historico = fetch_binance_data(asset, '1m', data.start_date, data.end_date)
    
    if df_historico.empty:
        print(f"BACKGROUND: Nenhum dado encontrado para {asset}. Abortando.")
        return

    df_analise = analisar_tecnica_gatilho_universal(df_historico)
    if df_analise.empty:
        print(f"BACKGROUND: Nenhum gatilho encontrado para {asset}. Abortando.")
        return

    # O resultado agora precisa ser salvo em um arquivo em vez de retornado
    # Por simplicidade, vamos salvar em uma pasta 'reports'
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    zip_filename = f"analise_gatilho_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)

    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    html_output = (
        f"<html><body><h1>Relatório para {asset}</h1><pre>{pd.Series(stats).to_string()}</pre>{df_analise.to_html(index=False)}</body></html>"
    )

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"analise_{asset}_M1.csv", df_analise.to_csv(index=False))
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)
    
    print(f"BACKGROUND: Análise para {asset} concluída. Salvo em: {zip_filepath}")


# 3. Modifique o endpoint para usar a tarefa em segundo plano
@router.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho para Binance")
async def endpoint_analise_gatilho_binance(data: RequestData, background_tasks: BackgroundTasks):
    # Adiciona a função de trabalho à fila
    background_tasks.add_task(do_analysis_and_zip, data)
    
    # Retorna uma resposta IMEDIATA
    return {"message": f"Análise para {data.assets[0]} iniciada em segundo plano. O resultado será gerado no servidor."}


# O endpoint de download-data continua igual por enquanto, pois ele é mais rápido
# e a expectativa do usuário é receber o download imediatamente.
@router.post("/download-data/", summary="Extrator de Dados Genérico da Binance")
async def endpoint_download_data(data: RequestData):
    # ... (código original do download-data) ...
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

