import io
import os
import zipfile
from datetime import datetime
import pandas as pd
from polygon import RESTClient
from core.config import settings

from models.forex_schemas import RequestData
from utils.gatilho_4e9 import analisar_tecnica_gatilho_universal


POLYGON_API_KEY = settings.POLYGON_API_KEY
REPORTS_DIR = "reports"

POLYGON_TIMESPAN_MAP = {"1m": "minute", "5m": "minute", "15m": "minute", "30m": "minute", "1h": "hour", "D": "day"}
POLYGON_MULTIPLIER_MAP = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 1, "D": 1}


# ------------------------------------------------
def fetch_polygon(asset: str, interval: str, start: str, end: str) -> pd.DataFrame:
    if not POLYGON_API_KEY:
        raise Exception("POLYGON_API_KEY não configurada.")

    ticker = f"C:{asset.upper()}"
    client = RESTClient(POLYGON_API_KEY)

    try:
        multiplier = POLYGON_MULTIPLIER_MAP[interval]
        timespan = POLYGON_TIMESPAN_MAP[interval]

        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=multiplier,
            timespan=timespan,
            from_=start,
            to=end,
            limit=50000
        )

        if not aggs:
            return pd.DataFrame()

        df = pd.DataFrame(aggs)
        df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "timestamp": "Open_Time",
        }, inplace=True)

        df["Open_Time"] = pd.to_datetime(df["Open_Time"], unit="ms")
        df["Resultado"] = df.apply(lambda r: "Call" if r["Close"] >= r["Open"] else "Put", axis=1)

        return df[["Open_Time", "Open", "High", "Low", "Close", "Volume", "Resultado"]]

    except Exception as e:
        print("Erro POLYGON:", e)
        return pd.DataFrame()


# ------------------------------------------------
def run_extraction(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    zip_filename = f"extrator_polygon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_polygon(asset, interval, data.start_date, data.end_date)
                if df.empty:
                    continue
                buff = io.StringIO()
                df.to_csv(buff, index=False)
                zipf.writestr(f"{asset}_{interval}.csv", buff.getvalue())

    print("Extração Polygon concluída:", zip_filepath)


# ------------------------------------------------
def run_analysis(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    asset = data.assets[0]

    df = fetch_polygon(asset, "1m", data.start_date, data.end_date)
    if df.empty:
        print("Nenhum dado Polygon para análise.")
        return

    df_analise = analisar_tecnica_gatilho_universal(df)

    zip_filename = f"analise_4e9_polygon_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    stats = df_analise["Resultado_Final"].value_counts(normalize=True).mul(100).round(2).to_dict()

    html_output = (
        f"<html><body><h1>Relatório {asset}</h1>"
        f"<pre>{pd.Series(stats).to_string()}</pre>"
        f"{df_analise.to_html(index=False)}</body></html>"
    )

    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        zipf.writestr("resultado.csv", df_analise.to_csv(index=False))
        zipf.writestr("relatorio.html", html_output)

    print("Análise Polygon concluída:", zip_filepath)
