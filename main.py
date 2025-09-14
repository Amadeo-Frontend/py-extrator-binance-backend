# backend/main.py (VERSÃO CORRIGIDA E FINAL)

import io
import zipfile
import pandas as pd
from datetime import datetime, timedelta # Importa timedelta
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from binance.client import Client
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

# --- Modelo de Dados (Pydantic) ---
class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1)
    intervals: List[str] = Field(..., min_length=1)
    start_date: str
    end_date: str

# --- Configuração da API ---
app = FastAPI(
    title="API de Análise e Extração de Dados da Binance",
    description="Uma API com duas funções: um extrator de dados genérico e um analisador de técnica de trading específica."
)

# --- Configuração do CORS ---
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
    """Busca dados históricos para um único ativo e intervalo, garantindo dias completos."""
    client = Client()

    ### MUDANÇA 1: Garantir que o dia final seja totalmente incluído ###
    # Converte a string da data final para um objeto datetime
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    # Adiciona um dia para garantir que todos os dados do último dia selecionado sejam incluídos
    end_date_inclusive = (end_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Buscando: {asset}, Intervalo: {interval}, de {start_date} até o fim de {end_date}")

    try:
        # Usa a data final ajustada na chamada da API
        klines = client.get_historical_klines(asset, interval, start_date, end_date_inclusive)
        if not klines: return pd.DataFrame()

        columns = ['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore']
        df = pd.DataFrame(klines, columns=columns)

        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)
        
        # Filtra para garantir que não pegamos dados do dia seguinte
        df = df[df['Open_Time'] < end_date_inclusive]
        
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

    while i < len(df):
        vela_atual = df.iloc[i]
        minuto_atual = vela_atual['Open_Time'].minute

        ### MUDANÇA 2: Remove a condição 'and ultimo_resultado_foi_loss' ###
        # Agora, a análise acontece em TODAS as velas de gatilho.
        if minuto_atual in minutos_gatilho:
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
            
            # Pula para a próxima vela após a vela de gatilho para evitar reanálise
            i += 1
            continue
        i += 1
    return pd.DataFrame(resultados)

# --- ENDPOINTS DA API (sem alterações aqui) ---

@app.get("/", summary="Verifica o status da API")
def read_root():
    return {"status": "API online. Use os endpoints /download-data/ ou /analise-tecnica-gatilho/."}

@app.post("/download-data/", summary="Extrator de Dados Genérico")
async def endpoint_download_data(data: RequestData):
    # ... (código deste endpoint permanece o mesmo)
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
    # ... (código deste endpoint permanece o mesmo)
    asset = data.assets[0]
    df_historico = fetch_binance_data(asset, '1m', data.start_date, data.end_date)
    if df_historico.empty:
        raise HTTPException(status_code=404, detail=f"Nenhum dado de 1 minuto encontrado para {asset} no período.")
    df_analise = analisar_tecnica_gatilho(df_historico)
    if df_analise.empty:
        raise HTTPException(status_code=404, detail="Nenhum gatilho válido encontrado para a análise no período fornecido.")
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
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        csv_buffer = io.StringIO()
        df_analise.to_csv(csv_buffer, index=False)
        zip_file.writestr(f"analise_{asset}_M1.csv", csv_buffer.getvalue())
        zip_file.writestr(f"relatorio_{asset}_M1.html", html_output)
    zip_buffer.seek(0)
    download_filename = f"analise_gatilho_{asset}_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return StreamingResponse(zip_buffer, media_type="application/x-zip-compressed", headers={"Content-Disposition": f"attachment; filename={download_filename}"})
