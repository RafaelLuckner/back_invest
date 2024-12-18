import streamlit as st
from data_collector import collect_stock_data, load_stock_data

# Configurações da página
st.set_page_config(
    page_title="Página Inicial",  
    page_icon=":chart_with_upwards_trend:",  
    layout="wide"
)

st.header("Seja bem-vindo!!")

# Função de carregamento de dados com cache
@st.cache_data
def load_data():
    return load_stock_data()

# Carregando dados
df = load_data()

if df.empty:
    st.markdown('Não foi possível carregar os dados. Clique no botão para coletar os dados.')

collecting_message = st.empty() 
# Adicionando um botão para coletar os dados
if st.button('Coletar Dados de Ações'):
    collecting_message.markdown('Coletando dados... Não navegue entre guias.  \n  \n**Pode levar alguns minutos**')
    # collecting_message.markdown('**Pode levar alguns minutos**')

    TICKERS = ["AAPL", "MSFT", "GOOGL", '^GSPC', "AMZN", 'VALE3.SA', 'BBAS3.SA', 'DOGE-USD','BTC-USD' ]
    collect_stock_data(TICKERS, period="1y")
    
    # Removendo a mensagem de "Coletando dados..." após a coleta ser concluída
    collecting_message.empty()
    
    st.success("Dados coletados com sucesso!")
    
    # Recarregar os dados após a coleta
    df = load_data()
st.markdown(f'Atualizado em {(df.iloc[-1]['Datetime']).strftime('%Y-%m-%d')}')

# Exibindo os dados (tabela)
if not df.empty:
    st.write(df)
else:
    st.markdown("Nenhum dado disponível para exibição.")

# Página explicativa
st.sidebar.title("Sobre o Site")

st.sidebar.markdown("""
    **Página de Backtest:**  
    -
    A página de **Backtest** permite testar estratégias de investimentos aplicando-as aos dados históricos das ações ou criptomoedas. Você pode simular como uma estratégia teria se comportado no passado, ajudando na tomada de decisões informadas sobre seus investimentos.
""")


st.sidebar.markdown("""
    **Página de Carteira:**  
    -
    A página de **Carteira** oferece uma visão geral dos ativos em que você está investido, com detalhes como quantidade, valor investido e preço médio. A funcionalidade de **atualizar dados** permite obter informações mais recentes sobre os ativos, garantindo que você tenha sempre os valores mais atualizados para tomar decisões precisas.
 """)

st.sidebar.markdown("""
    **Página de Monitoramento de Ações:**  
    -
    Na página de **Monitoramento de Ações**, você pode acompanhar o desempenho dos ativos de seu interesse em tempo real. O sistema atualiza os dados de mercado, permitindo que você visualize variações de preços, gráficos e outras métricas importantes. Ao **atualizar os dados**, você garante que as informações exibidas estão sempre precisas e em tempo real, refletindo as últimas movimentações do mercado.
""")



    
