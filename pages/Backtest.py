import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from data_collector import load_stock_data
import os
from dotenv import load_dotenv

def calcular_variacao_anual(df):
    df_ano = df.groupby('Year').agg(
        inicial=('Close', 'first'),
        final=('Close', 'last')).reset_index()
    df_ano['Percentual_Variacao'] = ((df_ano['final'] / df_ano['inicial']) - 1) * 100
    return df_ano[['Year', 'Percentual_Variacao']]

def calcular_variacao_percentual(df):
    df = df.sort_values(by="Datetime")  
    df["Percentual_Crescimento"] = (df["Close"] / df["Close"].iloc[0] - 1) * 100  # Variação percentual
    return df

senha = os.getenv("GROQ_API_KEY")


st.set_page_config(
    page_title="Backtest",  
    page_icon=":chart_with_upwards_trend:",  
    layout="wide")

st.header("Backtest de Múltiplos Ativos")
st.markdown("Compare o investimento em vários ativos ao mesmo tempo.")

df = load_stock_data()

monitor_tickers = st.multiselect("Escolha as ações para análise:", df["Ticker"].unique(), default=["MSFT", "AAPL"])
st.markdown('')
investment = st.number_input("Valor inicial do investimento por Ativo:", min_value=1.0, step=100.0, value=1000.0)

min_date = df['Datetime'].min().date()
max_date = df['Datetime'].max().date()
st.markdown('')

selected_dates = st.slider(
    "Selecione o intervalo de datas:",
    min_date, max_date,
    (min_date, max_date))

start_date, end_date = selected_dates

df_filtered = df[(df['Datetime'] >= pd.to_datetime(start_date)) & (df['Datetime'] <= pd.to_datetime(end_date))]
tickers = set(monitor_tickers).intersection(df_filtered['Ticker'].unique())
sem_dados = set(monitor_tickers).symmetric_difference(tickers)

df_filtered = df_filtered[df_filtered['Ticker'].isin(tickers)]

if df_filtered.empty:
    st.info('Nenhum valor encontrado para os filtros aplicados. Verifique as opções selecionadas.')
else:
    if len(sem_dados)==1 :
        frase = f'{str(sem_dados).replace("'", '').replace('{','').replace('}','')}'
        st.info(f'Sem dados para {frase} neste período.')
    elif len(sem_dados)==2 :
        frase = f'{str(sem_dados).replace("'", '').replace('{','').replace('}','').replace(',', ' e ')}'
        st.info(f'Sem dados para {frase} neste período.')
    elif len(sem_dados)>2:
        ultimo_elemento = list(sem_dados)[-1]
        frase = f'{str(sem_dados).replace("'", '').replace('{','').replace(', '+ str(ultimo_elemento)+'}',' e '+ultimo_elemento)}'
        st.info(f'Sem dados para {frase} neste período.')



tab1, tab2 = st.tabs(['Resultados', 'Gráficos de Comparação'])

with tab1:
    if not df_filtered.empty:
        if monitor_tickers:
            st.header("Tabela de Retornos",
                    help="""
                Ticker: Código do ativo no mercado financeiro.  
        Preço Inicial: Preço do ativo no início do período.  
        Data Inicial: Data do primeiro registro de preço no período.  
        Preço Final : Preço do ativo no final do período.  
        Ganho: Valor total de retorno obtido.  
        Retorno (%): Porcentagem de crescimento ou queda da ação no período.
            """)
            results = []
            for ticker in tickers:
                df_filtered2 = df_filtered[df_filtered["Ticker"] == ticker]
                
                # Verifica os preços de abertura e fechamento para o cálculo de retorno
                initial_price = float(df_filtered2.iloc[0]["Close"])
                initial_date = (df_filtered2.iloc[0]["Datetime"]).strftime("%Y-%m-%d")
                final_price = float(df_filtered2.iloc[-1]["Close"])
                
                # Calcula o retorno em reais e em porcentagem
                profit = (final_price - initial_price) / initial_price * investment
                profit_percentage = (final_price - initial_price) / initial_price * 100
                
                results.append({
                    "Ticker": ticker,
                    "Data Inicial": initial_date,
                    "Preço Inicial": initial_price,
                    "Preço Final": final_price,
                    "Ganho": round(profit,2),
                    "Retorno (%)": round(profit_percentage,2)
                })
            results_df = pd.DataFrame(results)
            st.dataframe(
                    results_df,
                    width=600,
                    column_config={
                        "Preço Inicial": st.column_config.NumberColumn(
                            help="Description",
                            format=" %.4f ",
                        ),
                        "Preço Final": st.column_config.NumberColumn(
                            help="Description",
                            format=" %.2f",
                        ),
                        "Ganho": st.column_config.NumberColumn(
                            help="Description",
                            format=" %.2f",
                        ),
                        "Retorno (%)": st.column_config.NumberColumn(
                            help="Description",
                            format=" %.2f",
                        )
                    },
                    hide_index=True)

            st.markdown("---")

            df_filtered['Year'] = df_filtered['Datetime'].dt.year

            tabela_variacao = pd.concat([
                calcular_variacao_anual(df_filtered[df_filtered['Ticker'] == ticker]).set_index('Year').rename(
                                columns={'Percentual_Variacao': ticker}) for ticker in monitor_tickers], axis=1)

            tabela_variacao = tabela_variacao.fillna(0)  

            tabela_variacao = tabela_variacao.round(2)  

            for col in tabela_variacao.columns:
                if col != 'Year':  
                    tabela_variacao[col] = tabela_variacao[col].apply(lambda x: f"{'+' if x > 0 else ''}{x}%")

            st.subheader("Percentual de Crescimento por Ano",
                        help ="Esta tabela mostra a variação percentual anual de cada ativo. Para os anos em que não há dados disponíveis, os valores foram substituídos por 0.")

            tabela_variacao.index = pd.to_datetime(tabela_variacao.index, format='%Y').strftime('%Y')
            tabela_variacao = tabela_variacao.sort_index(ascending=False)
            tabela_variacao.rename_axis('Ano',inplace=True)
            st.dataframe(tabela_variacao.style.applymap(
                lambda x: 'color: green' if isinstance(x, str) and x.startswith('+') else 
                        ('color: red' if isinstance(x, str) and x.startswith('-') else ''),
                subset=tabela_variacao.columns[0:]  # Aplicar cor nas colunas de variação percentual
            ))

with tab2:
    if not df_filtered.empty:
            if monitor_tickers:
                df_filtered['Datetime'] = pd.to_datetime(df_filtered['Datetime'])

                df_filtered = df_filtered[df_filtered["Ticker"].isin(tickers)]

                df_percentual = pd.concat([calcular_variacao_percentual(df_filtered[df_filtered['Ticker'] == ticker]) 
                                            for ticker in tickers])

                st.markdown("")
                st.markdown("")
                st.subheader("Percentual de Crescimento Acumulado")
                fig = px.line(
                    df_percentual,
                    x="Datetime",
                    y="Percentual_Crescimento",
                    color="Ticker",  
                    labels={"Percentual_Crescimento": "Variação Percentual (%)", "Datetime": ""}
                )
                
                fig.update_traces(
                    line=dict(width=3),  # Espessura da linha
                )
                
                st.plotly_chart(fig, use_container_width=True)


