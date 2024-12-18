import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from data_collector import load_stock_data

df = load_stock_data()

st.set_page_config(
    page_title="Monitoramento",  
    page_icon="🔍",  
    layout="wide"
)

st.header("Monitoramento de Ações")
st.markdown("Acompanhe a variação das ações desde 2000.")

if "monitor_tickers" not in st.session_state:
    st.session_state.monitor_tickers = ["AAPL", "MSFT"]

monitor_tickers = st.multiselect("Escolha as ações para monitorar:", df['Ticker'].unique(), default=st.session_state.monitor_tickers)

min_date = df['Datetime'].min().date()
max_date = df['Datetime'].max().date()

if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = (min_date, max_date)  

st.sidebar.markdown(
    "<h4 style='font-size:18px;'>Selecione o intervalo de datas:</h4>",
    unsafe_allow_html=True
)

selected_dates = st.sidebar.slider(
    "",
    min_date, max_date,
    st.session_state.selected_dates
)

start_date, end_date = selected_dates
st.write(f"Intervalo selecionado: {start_date} até {end_date}")

df_filtered = df[(df['Datetime'] >= pd.to_datetime(start_date)) & (df['Datetime'] <= pd.to_datetime(end_date))]

for ticker in monitor_tickers:
    ticker_data = df_filtered[df_filtered['Ticker'] == ticker]
    
    ticker_data['Variation'] = ticker_data['Close'].pct_change() * 100  # Variação em %

    fig = px.line(ticker_data, x='Datetime', y='Close', title=f"Preço de Fechamento - {ticker}")
    st.plotly_chart(fig, use_container_width=True)

    last_row = ticker_data.iloc[-1]
    st.markdown(f"**Resultado do {ticker} no final do dia**")
    st.markdown(f"Preço de Fechamento: {last_row['Close']:.2f}")
    st.markdown(f"Variação do Dia: {last_row['Variation']:.2f}%")

st.markdown("### Dados das Ações")
st.dataframe(df_filtered)

