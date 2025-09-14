# backend/main.py
import io
import zipfile
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from binance.client import Client

class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1)
    intervals: List[str] = Field(..., min_length=1)
    start_date: str
    end_date: str

app = FastAPI(title="API de Extração de Dados Históricos da Binance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
 )

def fetch_binance_data(asset: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
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

@app.post("/download-data/")
async def generate_and_download_data(data: RequestData):
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
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={download_filename}"}
    )

@app.get("/")
def read_root():
    return {"status": "API online. Use o endpoint POST /download-data/."}
