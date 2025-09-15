# backend/main.py (VERSÃO ESTÁVEL SEM A BIBLIOTECA TVDATAFEED)

import io
import os
import zipfile
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from binance.client import Client
from fastapi import FastAPI, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import StreamingResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore

# Não precisamos mais do dotenv, pois a única autenticação era para a tvdatafeed
# from dotenv import load_dotenv
# load_dotenv()

# --- VERIFICAÇÃO E IMPORTAÇÃO DE DEPENDÊNCIAS OPCIONAIS ---
try:
    from tradingview_ta import TA_Handler, Interval # type: ignore
    _TV_AVAILABLE = True
except ImportError:
    _TV_AVAILABLE = False

# --- MODELOS DE DADOS (PYDANTIC) ---
class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1)
    intervals: List[str] = Field(..., min_length=1)
    start_date: str
    end_date: str

class TVForexQuery(BaseModel):
    symbol: str = Field(..., description="Par forex no formato 'EURUSD' (sem /)")
    exchange: str | None = Field(default=None, description="Exchange do TradingView (ex: 'FX_IDC' ou 'OANDA').")

# --- CONFIGURAÇÃO DA API E CLIENTES ---
app = FastAPI(
    title="API de Análise e Extração de Dados",
    description="Uma API com funções para extrair dados da Binance e obter resumos de análise do TradingView."
)

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

# Cliente da Binance, que funciona perfeitamente para dados públicos
client_binance = Client()

# --- FUNÇÕES AUXILIARES UNIVERSAIS ---
def parse_date(s: str) -> datetime:
    """Converte string 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM' para datetime."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            pass
    raise HTTPException(status_code=400, detail=f"Formato de data inválido: '{s}'. Use 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM'.")

def analisar_tecnica_gatilho_universal(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica a técnica de análise de velas de gatilho. Usada pela função da Binance."""
    if df.empty:
        return pd.DataFrame()
        
    df = df.sort_values(by='Open_Time').reset_index(drop=True)
    minutos_gatilho = {4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59}
    resultados = []
    i = 0
    while i < len(df):
        vela_atual = df.iloc[i]
        minuto_atual = pd.to_datetime(vela_atual['Open_Time']).minute

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
                'Horario_Gatilho': vela_gatilho['Open_Time'], 'Cor_Gatilho': cor_gatilho,
                'Sequencia_Esperada': ' → '.join(sequencia_operacoes), 'Resultado_Final': resultado_final_sequencia
            })
        i += 1
    return pd.DataFrame(resultados)

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

# --- ENDPOINTS DA API ---
@app.get("/", summary="Verifica o status da API")
def read_root():
    return {"status": "API online. Use os endpoints corretos."}

# --- ENDPOINTS BINANCE ---
@app.get("/available-assets/", summary="Lista todos os ativos USDT da Binance")
def get_available_assets():
    """Busca e retorna uma lista de todos os símbolos de trading que terminam com 'USDT' na Binance."""
    try:
        exchange_info = client_binance.get_exchange_info()
        symbols = sorted([s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')])
        return {"assets": symbols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível buscar a lista de ativos da Binance: {e}")

@app.post("/download-data/", summary="Extrator de Dados Genérico da Binance")
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

@app.post("/analise-tecnica-gatilho/", summary="Analisador de Técnica de Gatilho para Binance")
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

# --- ENDPOINTS TRADINGVIEW (APENAS OS FUNCIONAIS) ---
COMMON_FOREX = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "USDBRL"]

@app.get("/tradingview/forex/search", summary="Busca simples por pares forex (lista interna)")
def tv_search_forex(q: str):
    q = q.replace("/", "").upper().strip()
    results = [s for s in COMMON_FOREX if q in s]
    return {"query": q, "matches": results}

@app.post("/tradingview/forex/summary", summary="Resumo do TradingView para um par forex")
def tv_forex_summary(data: TVForexQuery):
    if not _TV_AVAILABLE:
        raise HTTPException(status_code=501, detail="A biblioteca 'tradingview-ta' não está instalada no ambiente.")
    symbol = data.symbol.replace("/", "").upper()
    exchanges = [data.exchange] if data.exchange else ["FX_IDC", "OANDA"]
    last_error = None
    for ex in exchanges:
        try:
            handler = TA_Handler(symbol=symbol, exchange=ex, screener="forex", interval=Interval.INTERVAL_1_MINUTE)
            analysis = handler.get_analysis()
            return {
                "symbol": symbol, "exchange": ex, "time": datetime.utcnow().isoformat() + "Z",
                "summary": analysis.summary, "oscillators": analysis.oscillators,
                "moving_averages": analysis.moving_averages, "indicators": analysis.indicators,
            }
        except Exception as e:
            last_error = str(e)
            continue
    raise HTTPException(status_code=400, detail=f"Não foi possível obter dados do TradingView para {symbol}. Último erro: {last_error}")

