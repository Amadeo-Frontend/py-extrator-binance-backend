import io
import os
import zipfile
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client

from models.forex_schemas import RequestData
from utils.gatilho_4e9 import analisar_tecnica_gatilho_universal


client_binance = Client()
REPORTS_DIR = "reports"


# -----------------------------------------------------
# FUNÇÃO ORIGINAL: buscar dados da Binance
# -----------------------------------------------------
def fetch_binance_data(asset: str, interval: str, start_date_str: str, end_date_str: str) -> pd.DataFrame:
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date_inclusive = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')

    try:
        klines = client_binance.get_historical_klines(asset, interval, start_date_str, end_date_inclusive)
        if not klines:
            return pd.DataFrame()

        columns = [
            'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades',
            'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume',
            'Ignore'
        ]

        df = pd.DataFrame(klines, columns=columns)
        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        df = df[df['Open_Time'] < pd.to_datetime(end_date_inclusive)]

        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)

        df['Resultado'] = df.apply(lambda row: 'Call' if row['Close'] >= row['Open'] else 'Put', axis=1)

        return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Resultado']]

    except Exception as e:
        print(f"Erro ao buscar dados Binance ({asset}, {interval}): {e}")
        return pd.DataFrame()



# -----------------------------------------------------
# FUNÇÃO ORIGINAL: extrator com ZIP (background)
# -----------------------------------------------------
def run_extraction(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    zip_filename = f"extrator_binance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    found = False

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for asset in data.assets:
            for interval in data.intervals:
                df = fetch_binance_data(asset.upper(), interval, data.start_date, data.end_date)
                if not df.empty:
                    found = True
                    buff = io.StringIO()
                    df.to_csv(buff, index=False)
                    zip_file.writestr(f"{asset}_{interval}.csv", buff.getvalue())

    if not found:
        os.remove(zip_filepath)
        print("Nenhum dado encontrado — arquivo removido.")
    else:
        print(f"ZIP salvo em: {zip_filepath}")



# -----------------------------------------------------
# FUNÇÃO ORIGINAL: análise 4e9
# -----------------------------------------------------
def run_analysis(data: RequestData):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    asset = data.assets[0]
    df = fetch_binance_data(asset, '1m', data.start_date, data.end_date)

    if df.empty:
        print(f"Sem dados para análise: {asset}")
        return

    df_analise = analisar_tecnica_gatilho_universal(df)
    if df_analise.empty:
        print("Sem gatilhos encontrados.")
        return

    zip_filename = f"analise_4e9_binance_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(REPORTS_DIR, zip_filename)

    stats = df_analise["Resultado_Final"].value_counts(normalize=True).mul(100).round(2).to_dict()

    html_output = (
        f"<html><body><h1>Relatório para {asset}</h1>"
        f"<pre>{pd.Series(stats).to_string()}</pre>"
        f"{df_analise.to_html(index=False)}</body></html>"
    )

    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("resultado.csv", df_analise.to_csv(index=False))
        zip_file.writestr("relatorio.html", html_output)

    print(f"Análise concluída: {zip_filepath}")
