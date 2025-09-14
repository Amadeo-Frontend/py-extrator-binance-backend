# backend/main.py

import io
import zipfile
import pandas as pd
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from binance.client import Client

# --- Modelo de Dados (Pydantic) ---
# Define a estrutura dos dados que o front-end vai enviar.
class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1, description="Lista de ativos, ex: ['BTCUSDT', 'ETHUSDT']")
    intervals: List[str] = Field(..., min_length=1, description="Lista de timeframes, ex: ['1m', '5m']")
    start_date: str = Field(..., description="Data de início no formato YYYY-MM-DD")
    end_date: str = Field(..., description="Data de fim no formato YYYY-MM-DD")

# --- Configuração da API ---
app = FastAPI(
    title="API de Extração de Dados Históricos da Binance",
    description="Uma API para buscar dados de velas da Binance e retorná-los como um arquivo ZIP."
)

# --- Configuração do CORS (Cross-Origin Resource Sharing) ---
# Define quais front-ends (origens) podem fazer requisições para esta API.
# É uma medida de segurança crucial.
origins = [
    # A URL exata do seu aplicativo em produção na Vercel
    "https://nextjs-extrator-binance-frontend.vercel.app",
    # A URL para desenvolvimento local
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"], # Permite apenas os métodos que usamos
    allow_headers=["*"],
 )

# --- Lógica de Extração ---
def fetch_binance_data(asset: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Busca dados históricos para um único ativo e intervalo."""
    client = Client() # Não precisa de API Key para dados públicos
    print(f"Buscando: {asset}, Intervalo: {interval}, de {start_date} a {end_date}")

    try:
        klines = client.get_historical_klines(asset, interval, start_date, end_date)
        
        if not klines:
            return pd.DataFrame()

        columns = [
            'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 
            'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume', 
            'Taker_Buy_Quote_Asset_Volume', 'Ignore'
        ]
        df = pd.DataFrame(klines, columns=columns)

        # --- Processamento dos Dados ---
        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        
        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)

        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']]

    except Exception as e:
        print(f"Erro ao buscar dados para {asset} ({interval}): {e}")
        return pd.DataFrame()

# --- Endpoints da API ---
@app.post("/download-data/")
async def generate_and_download_data(data: RequestData):
    """
    Recebe as configurações, busca os dados, cria arquivos CSV,
    compacta em um ZIP e retorna para download.
    """
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
        raise HTTPException(
            status_code=404, 
            detail="Nenhum dado encontrado para os parâmetros fornecidos. Verifique os nomes dos ativos e o período."
        )

    zip_buffer.seek(0)
    download_filename = f"binance_data_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment; filename={download_filename}"
        }
    )

@app.get("/", summary="Verifica o status da API")
def read_root():
    """Endpoint raiz que retorna um status de 'online'."""
    return {"status": "API online. Use o endpoint POST /download-data/ para extrair dados."}

