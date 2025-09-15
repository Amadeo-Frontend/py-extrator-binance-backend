# teste_tv.py (Arquivo temporário apenas para diagnóstico)

from tvDatafeed import TvDatafeed
import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis do arquivo .env

username = os.getenv("TV_USERNAME")
password = os.getenv("TV_PASSWORD")

print("--- INICIANDO TESTE DE LOGIN DIRETO ---")
print(f"Usuário lido do .env: {username}")
print(f"Senha lida do .env: {'*' * len(password) if password else 'Nenhuma'}")

if not username or not password:
    print("\nERRO: Usuário ou senha não encontrados no arquivo .env.")
else:
    try:
        tv = TvDatafeed(username=username, password=password)
        print("\n>>> SUCESSO: Login na TvDatafeed funcionou! <<<")
        
        print("\nTentando buscar 1 candle de EUR/USD...")
        data = tv.get_hist(symbol='EURUSD', exchange='FX_IDC', interval='1H', n_bars=1)
        
        if data is not None and not data.empty:
            print("\n>>> SUCESSO FINAL: Dados foram buscados com sucesso! <<<")
            print(data)
        else:
            print("\nAVISO: Login funcionou, mas a busca de dados falhou.")

    except Exception as e:
        print(f"\n>>> FALHA: Ocorreu um erro. Detalhe: {e} <<<")

print("\n--- TESTE FINALIZADO ---")
