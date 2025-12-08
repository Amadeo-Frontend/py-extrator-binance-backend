import io
import os
import zipfile
from datetime import datetime
import pandas as pd
from alpha_vantage.foreignexchange import ForeignExchange
from core.config import settings
from models.forex_schemas import RequestData
from utils.gatilho_4e9 import analisar_tecnica_gatilho_universal


API_KEY = settings.ALPHA_VANTAGE_API_KEY
REPORTS_DIR = "reports"


# ---------------------------------------------------------
# FUNÇÃO ORIGINAL: fetch de Alpha Vantage
# ---------------------------------------------------------
def fetch_av(asset: str, interval: str) -> pd.DataFrame:
    if not API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY não configurada.")

    if len(asset) != 6:
        return pd.DataFrame()

    fx = ForeignExchange(key=API_KEY, output_format="pandas")

    from_symbol = asset[:3].upper()
    to_symbol = asset[3:].upper()

    try:
        if interval == "D":
            data, _ = fx.get_fx_daily(from_symbol, to_symbol, outputsize="full")
        else:
            data, _ = fx.get_fx_intraday(
                from_symbol, to_symbol, interval=interval, outputsize="full"
            )

        df = data.copy()
        df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume",
        }, inplace=True)

        df.index.name = "Open_Time"
        df.reset_index(inplace=True)
        df["Resultado"] = df.apply(lambda r: "Call" if r["Close"] >= r["Open"] else "Put", axis=1)

        return df[["Open_Time", "Open", "High", "Low", "Close", "Volume", "Resultado"]]

    except Exception as e:
        print("Erro AlphaVantage:", e)
        return pd.DataFrame()


# ---------------------------------------------------------
def run_extraction(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    zip_filename = f"extrator_alphavantage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_av(asset, interval)
                if df.empty:
                    continue
                buff = io.StringIO()
                df.to_csv(buff, index=False)
                zipf.writestr(f"{asset}_{interval}.csv", buff.getvalue())

    print("AlphaVantage ZIP criado:", zip_filepath)


# ---------------------------------------------------------
def run_analysis(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    asset = data.assets[0]

    df = fetch_av(asset, "1m")
    if df.empty:
        print("Sem dados para análise AV (provavelmente plano gratuito).")
        return

    analise = analisar_tecnica_gatilho_universal(df)
    if analise.empty:
        print("Nenhuma oportunidade detectada.")
        return

    zip_filename = f"analise_4e9_av_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    stats = analise["Resultado_Final"].value_counts(normalize=True).mul(100).round(2).to_dict()
    html = (
        f"<html><body><h1>Análise {asset}</h1>"
        f"<pre>{pd.Series(stats).to_string()}</pre>"
        f"{analise.to_html(index=False)}</body></html>"
    )

    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        zipf.writestr("resultado.csv", analise.to_csv(index=False))
        zipf.writestr("relatorio.html", html)

    print("Análise AV gerada:", zip_filepath)
