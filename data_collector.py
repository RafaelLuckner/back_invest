import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "stocks.csv")

def ensure_data_directory():
    """Garante que o diretório para armazenar dados existe."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(CSV_FILE):
        columns = ['Datetime', 'Close', 'Volume', 'variacao', 'Ticker', 'day']
        empty_df = pd.DataFrame(columns=columns)
        empty_df.to_csv(CSV_FILE, index=False)

def baixar_dados(ticker, start_date, end_date):
    data = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        interval="1d"
    )

    data = data.reset_index()
    data.columns = ['Datetime','Adj Close','Close','High',	'Low',	'Open',	'Volume']
    return data

    
def collect_stock_data(tickers, period="1d"):
    all_data = []  
    now = datetime.now()

    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    start_date = '2000-01-01'

    count = 0
    for acao in tickers:
        dados_diarios = baixar_dados(acao, start_date, end_date)
        dados_diarios['variacao'] = dados_diarios['Close'].pct_change()

        dados_diarios['variacao_acumulada'] = (1 + dados_diarios['variacao']).cumprod() - 1

        dados_diarios['variacao'] = dados_diarios['variacao'].apply(lambda x: round(x * 100, 4))  # Em %
        dados_diarios['variacao_acumulada'] = dados_diarios['variacao_acumulada'].apply(lambda x: round(x * 100, 4))  # Em %

        dados_diarios = dados_diarios.loc[:, ['Datetime', 'Close', 'Volume', 'variacao', 'variacao_acumulada']]
        dados_diarios['Ticker'] = acao.replace('.SA', '') 
        count = count + 1
        try:
            print(f'Coletados Dados Diarios da Ação {dados_diarios["Ticker"][0]}')
        except:
            return 
        print(f'Total de ações: {count}')
        
        all_data.append(dados_diarios)
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=False)
        combined_data['Datetime'] = pd.to_datetime(combined_data['Datetime'])
        combined_data['day'] = combined_data['Datetime'].dt.day

        combined_data.to_csv(CSV_FILE, index=False)
        print(f"Dados coletados e salvos em {CSV_FILE}.")
        return combined_data
    
    else:
        print("Nenhum dado coletado. Verifique os tickers e a conexão.")
        return pd.DataFrame()
def load_stock_data():
    """
    Carrega os dados do CSV.
    Certifique-se de que os dados já tenham sido coletados com collect_stock_data().
    """
    if not os.path.exists(CSV_FILE):
        ensure_data_directory()
    
    data = pd.read_csv(CSV_FILE, parse_dates=["Datetime"])
    
    return data

