# backend/routers/common.py

from datetime import datetime
from typing import List
import pandas as pd
from pydantic import BaseModel, Field
from fastapi import HTTPException

# --- MODELOS DE DADOS (PYDANTIC) ---
class RequestData(BaseModel):
    assets: List[str] = Field(..., min_length=1)
    intervals: List[str] = Field(..., min_length=1)
    start_date: str
    end_date: str

class TVForexQuery(BaseModel):
    symbol: str = Field(..., description="Par forex no formato 'EURUSD' (sem /)")
    exchange: str | None = Field(default=None, description="Exchange do TradingView (ex: 'FX_IDC' ou 'OANDA').")

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
