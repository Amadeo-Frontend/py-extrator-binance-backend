# backend/main.py

import io
import zipfile
import pandas as pd
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from binance.client import Client
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

# --- Modelo de Dados (Pydantic) ---
# Define a estrutura dos dados que o front-end pode enviar.
class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1, description="Lista de ativos, ex: ['BTCUSDT', 'ETHUSDT']")
    intervals: List[str] = Field(..., min_length=1, description="Lista de timeframes, ex: ['1m', '5m']")
    start_date: str = Field(..., description="Data de início no formato YYYY-MM-DD")
    end_date: str = Field(..., description="Data de fim no formato YYYY-MM-DD")

# --- Configuração da API ---
app = FastAPI(
    title="API de Análise e Extração de Dados da Binance",
    description="Uma API com duas funções: um extrator de dados genérico e um analisador de técnica de trading específica."
)

# --- Configuração do CORS ---
# Define quais front-ends podem fazer requisições para esta API.
origins = [
    "https://nextjs-extrator-binance-frontend.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
 )

# --- LÓGICA DE EXTRAÇÃO DE DADOS (Função Auxiliar) ---
def fetch_binance_data(asset: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Busca dados históricos para um único ativo e intervalo."""
    client = Client()
    print(f"Buscando: {asset}, Intervalo: {interval}, de {start_date} a {end_date}")

    try:
        klines = client.get_historical_klines(asset, interval, start_date, end_date)
        if not klines: return pd.DataFrame()

        columns = ['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore']
        df = pd.DataFrame(klines, columns=columns)

        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']]
    except Exception as e:
        print(f"Erro ao buscar dados para {asset} ({interval}): {e}")
        return pd.DataFrame()

# --- LÓGICA DA TÉCNICA DE GATILHO (Função Auxiliar) ---
def analisar_tecnica_gatilho(df: pd.DataFrame):
    """Aplica a técnica de análise de velas de gatilho e sequências de martingale."""
    df = df.sort_values(by='Open_Time').reset_index(drop=True)
    minutos_gatilho = {4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59}
    resultados = []
    i = 0
    ultimo_resultado_foi_loss = True

    while i < len(df):
        vela_atual = df.iloc[i]
        minuto_atual = vela_atual['Open_Time'].minute

        if minuto_atual in minutos_gatilho and ultimo_resultado_foi_loss:
            if i + 4 >= len(df):
                i += 1
                continue

            vela_gatilho = vela_atual
            cor_gatilho = vela_gatilho['Resultado']
            sequencia_operacoes = ['Put', 'Put', 'Call', 'Call'] if cor_gatilho == 'Call' else ['Call', 'Call', 'Put', 'Put']
            
            resultado_final_sequencia = "LOSS"
            if df.iloc[i+1]['Resultado'] == sequencia_operacoes[0]: resultado_final_sequencia = "WIN"
            elif df.iloc[i+2]['Resultado'] == sequencia_operacoes[1]: resultado_final_sequencia = "WIN GALE 1"
            elif df.iloc[i+3]['Resultado'] == sequencia_operacoes[2]: resultado_final_sequencia = "WIN GALE 2"
            elif df.iloc[i+4]['Resultado'] == sequencia_operacoes[3]: resultado_final_sequencia = "WIN GALE 3"

            resultados.append({
                'Horario_Gatilho': vela_gatilho['Open_Time'],
                'Cor_Gatilho': cor_gatilho,
                'Sequencia_Esperada': ' → '.join(sequencia_operacoes),
                'Resultado_Final': resultado_final_sequencia
            })

            ultimo_resultado_foi_loss = (resultado_final_sequencia == "LOSS")
            i += 5
            continue
        i += 1
    return pd.DataFrame(resultados)

# --- ENDPOINTS DA API ---

@app.get("/", summary="Verifica o status da API")
def read_root():
    """Endpoint raiz que retorna um status de 'online'."""
    return {"status": "API online. Use os endpoints /download-data/ ou /analise-tecnica-gatilho/."}

@app.post("/download-data/", summary="Extrator de Dados Genérico")
async def endpoint_download_data(data: RequestData):
    """Recebe configurações, busca dados e retorna um ZIP com arquivos CSV."""
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

@app.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho")
async def endpoint_analise_gatilho(data: RequestData):
    """Busca dados de M1, aplica a análise da técnica de gatilho e retorna um ZIP com CSV e HTML."""
    asset = data.assets[0]
    df_historico = fetch_binance_data(asset, '1m', data.start_date, data.end_date)

    if df_historico.empty:
        raise HTTPException(status_code=404, detail=f"Nenhum dado de 1 minuto encontrado para {asset} no período.")

    df_analise = analisar_tecnica_gatilho(df_historico)

    if df_analise.empty:
        raise HTTPException(status_code=404, detail="Nenhum gatilho válido encontrado para a análise no período fornecido.")

    # Geração do HTML
    stats = df_analise['Resultado_Final'].value_counts(normalize=True).mul(100).round(2).to_dict()
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template_gatilho.html')
    html_output = template.render(
        asset=asset,
        start_date=data.start_date,
        end_date=data.end_date,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stats=stats,
        table=df_analise.to_html(classes='styled-table', index=False, escape=False)
    )

    # Geração do ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        csv_buffer = io.StringIO()
        df_analise.to_csv(csv_buffer, index=False)
        zip_file.writestr(f"analise_{asset}_M1.csv", csv_buffer.getvalue())
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)

    zip_buffer.seek(0)
    download_filename = f"analise_gatilho_{asset}_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})
