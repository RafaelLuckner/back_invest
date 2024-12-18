import os
import numpy as np
import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from groq import Groq
from datetime import datetime

FILE_LANCAMENTO = "data/lancamentos.csv"

API_KEY = os.getenv("GROQ_API_KEY")

data_stocks = pd.read_csv('data/lancamentos.csv')

TICKERS = data_stocks['Ativo'].unique()

def carregar_carteira(lancamentos):
    df_fin = lancamentos.groupby('Ativo').agg(
                        Quantidade=('Quantidade', 'sum'),
                        Valor = ('Valor', 'sum'),
                        Média=('Preço', 'mean')
                        ).reset_index()
    df_fin.columns = ['Ativo', 'Quantidade', 'Valor', 'Preço Médio']
    return df_fin
    
def carregar_lancamentos():
    if os.path.exists(FILE_LANCAMENTO):
        df = pd.read_csv(FILE_LANCAMENTO)
        # Validar colunas
        colunas_esperadas = ['Ativo', 'Quantidade', 'Preço', 'Valor', 'Data de Compra']
        df = df[colunas_esperadas]
        return df
    return pd.DataFrame(columns=['Ativo', 'Quantidade', 'Preço', 'Valor', 'Data de Compra'])

def salvar_dados(data):
    data = data[['Ativo', 'Quantidade', 'Preço', 'Valor', 'Data de Compra']]
    data.to_csv(FILE_LANCAMENTO, index=False)

if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = carregar_lancamentos()

if "carteira" not in st.session_state:
    st.session_state.carteira = carregar_carteira(st.session_state.lancamentos)

def novo_lancamento(nome_ativo, quantidade, preco, data_compra):
    if quantidade <= 0 or preco <= 0:
        st.error("Quantidade e preço devem ser positivos.")
        return

    # Usando a data de compra fornecida pelo usuário
    data_compra_formatada = data_compra.strftime("%Y-%m-%d")  # Converte para o formato "YYYY-MM-DD"
    
    # Criar um novo registro para o ativo
    novo_registro = pd.DataFrame([
        [nome_ativo, quantidade, preco, quantidade * preco, data_compra_formatada]
    ], columns=['Ativo', 'Quantidade', 'Preço', 'Valor', 'Data de Compra'])

    # Copiar a carteira da sessão
    lancamentos = st.session_state.lancamentos.copy()

    lancamentos = pd.concat([lancamentos, novo_registro], ignore_index=True)

    # Atualizar a sessão com a nova carteira
    st.session_state.lancamentos = lancamentos
    salvar_dados(lancamentos)

def atualiza_lancamento(id_lancamento, novo_preco=None, nova_quantidade=None, novo_nome=None, nova_data = None, df_lancamentos = None ):
    if novo_preco is not None and novo_preco <= 0:
        st.error("O preço deve ser positivo.")
        return
    if nova_quantidade is not None and nova_quantidade < 0:
        st.error("A quantidade não pode ser negativa.")
        return

    if novo_preco is not None:
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Preço'] = novo_preco

    if nova_quantidade is not None:
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Quantidade'] = nova_quantidade

    if novo_nome is not None:
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Ativo'] = novo_nome

    if nova_data:
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Data de Compra'] = nova_data

    # Atualizar o valor e data de atualização
    df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Valor'] = (
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Quantidade'] * 
        df_lancamentos.loc[df_lancamentos['ID'] == id_lancamento, 'Preço']
    )
    st.session_state.lancamentos = df_lancamentos
    salvar_dados(df_lancamentos)

def remove_lancamento(id_ativo, df_lancamentos):
    df_lancamentos = df_lancamentos.loc[df_lancamentos['ID'] != id_ativo]
    st.session_state.lancamentos = df_lancamentos
    salvar_dados(df_lancamentos)

# layout streamlit
st.set_page_config(
    page_title="Carteira",  
    page_icon=":chart_with_upwards_trend:",  
    layout="wide" )

st.title("Carteira de Investimentos")

tab1, tab2, tab3, tab4 = st.tabs(["Visualizar Carteira", "Fazer Lançamento", "Atualizar/Remover Lançamento", "Assistente IA"])

with tab1:
    # Mostrar a planilha atual
    st.subheader("Carteira:")
    df_carteira = st.session_state.carteira.copy()

    st.dataframe(
        df_carteira,
        width=600, height=200,
        column_config={
            "Quantidade": st.column_config.NumberColumn(
                "Quantidade",
                help="Description",
                format=" %f ",
            ),
            "Valor": st.column_config.NumberColumn(
                "Valor Investido",
                help="Description",
                format="R$ %.2f",
            ),
            "Preço Médio": st.column_config.NumberColumn(
                "Preço Médio",
                help="Description",
                format="R$ %.2f",
            )
        },
        hide_index=True,
        )

    # Mostrar o valor total da carteira
    st.subheader("Valor total da carteira")
    st.write(f"R$ {st.session_state.carteira['Valor'].sum():.2f}")

    gaph1, gaph2 = st.tabs(["Crescimento da Carteira", "Distribuição de Ativos"])
    
    with gaph1:
        if 'lancamentos' not in st.session_state or st.session_state.lancamentos.empty:
            st.info("Adicione ativos para visualizar a composição da carteira.")
            st.stop()
        lancamentos = st.session_state.lancamentos.copy()
        # Seleção de opções
        tipo_grafico = st.radio("Escolha a escala do gráfico:", ("Anual", "Mensal", "Diário"))
        periodo_opcao = st.selectbox("Selecione o período:", ["Máximo", "Últimos 6 meses", "Últimos 12 meses", "Últimos 2 anos", "Últimos 5 anos"])
        data_fim = pd.Timestamp.today().date()

        # Conversão de datas
        lancamentos['Data de Compra'] = pd.to_datetime(lancamentos['Data de Compra'])

        # Determinar a data de início com base na seleção
        if periodo_opcao == "Últimos 6 meses":
            data_inicio = (pd.Timestamp.today() - pd.DateOffset(months=6)).date()
        elif periodo_opcao == "Últimos 12 meses":
            data_inicio = (pd.Timestamp.today() - pd.DateOffset(years= 1)).date()
        elif periodo_opcao == "Últimos 2 anos":
            data_inicio = (pd.Timestamp.today() - pd.DateOffset(years=2)).date()
        elif periodo_opcao == "Últimos 5 anos":
            data_inicio = (pd.Timestamp.today() - pd.DateOffset(years=5)).date()
        elif periodo_opcao == "Máximo":
            data_inicio = lancamentos['Data de Compra'].min().date()

        
        # Filtrar os lançamentos
        lancamentos = lancamentos[(lancamentos['Data de Compra'].dt.date >= data_inicio) & 
                                (lancamentos['Data de Compra'].dt.date <= data_fim)]

        if lancamentos.empty:
            st.warning("Nenhum lançamento encontrado no intervalo selecionado.")
            st.stop()

        # Agrupamento de dados e cálculo do valor acumulado
        lancamentos['dia'] = lancamentos['Data de Compra'].dt.date

        if tipo_grafico == "Diário":
            df_growth = lancamentos.groupby('dia').agg({'Valor': 'sum'}).reset_index()
        elif tipo_grafico == 'Mensal':
            lancamentos['mes'] = lancamentos['Data de Compra'].dt.to_period('M')
            df_growth = lancamentos.groupby('mes').agg({'Valor': 'sum'}).reset_index()
            df_growth['dia'] = df_growth['mes'].dt.start_time
        else:
            lancamentos['ano'] = lancamentos['Data de Compra'].dt.to_period('Y')
            df_growth = lancamentos.groupby('ano').agg({'Valor': 'sum'}).reset_index()
            df_growth['dia'] = df_growth['ano'].dt.start_time

        df_growth['Valor Acumulado'] = df_growth['Valor'].cumsum()

        # Reindexar para incluir todos os intervalos e preencher valores ausentes
        freq = {'Diário': 'D', 'Mensal': 'MS', 'Anual': 'YS'}[tipo_grafico]
        all_dates = pd.date_range(df_growth['dia'].min(), df_growth['dia'].max(), freq=freq)

        df_growth = df_growth.set_index('dia').reindex(all_dates).ffill().reset_index()
        df_growth = df_growth.rename(columns={'index': 'dia'})

        # Limitar o número de ticks no eixo X
        max_ticks = 6
        tick_step = max(1, len(df_growth) // max_ticks)
        tick_vals = df_growth['dia'][::tick_step]

        # Criando o gráfico de barras
        fig_growth = px.bar(df_growth, x='dia', y='Valor Acumulado', 
                            title=f"Crescimento do Valor Acumulado Investido - {tipo_grafico}",
                            labels={'Valor Acumulado': 'Valor Total Investido (R$)', 'dia': 'Data'})

        # Ajustando o layout
        fig_growth.update_layout(
            xaxis_title='',
            yaxis_title='Valor Total Investido Acumulado (R$)',
            showlegend=False,
            xaxis=dict(
                tickvals=tick_vals,
                tickformat="%d/%m/%Y" if tipo_grafico == "Diário" else "%m/%Y",
                tickmode='array',
            )
        )

        # Adicionando os valores nas barras
        fig_growth.update_traces(
            text=df_growth['Valor Acumulado'],
            textposition='inside',
            textfont=dict(size=12)
        )

        st.plotly_chart(fig_growth)

    with gaph2:
        if not st.session_state.carteira.empty:
            st.subheader("Composição da Carteira")
            carteira_agrupada = st.session_state.carteira.copy()

            # Criar o gráfico de pizza com Plotly
            fig = px.pie(
                carteira_agrupada,
                values='Valor',
                names='Ativo',
                title="Distribuição dos Ativos",
                hole=0,  # Sem formato de rosca
            )

            # Adicionar slider para controlar qual fatia será "expandida"
            selected_ativo = st.selectbox("Escolha o ativo para expandir:", carteira_agrupada['Ativo'])
            valor_investido = float(carteira_agrupada.loc[carteira_agrupada['Ativo'] == selected_ativo, 'Valor'])
            st.markdown(f'{selected_ativo} - Valor investido: R${valor_investido}')

            # Encontrar o índice da fatia selecionada
            ativo_index = carteira_agrupada[carteira_agrupada['Ativo'] == selected_ativo].index[0]

            # Atualizar o valor de pull para simular o zoom na fatia selecionada
            pull_values = [0.1 if i == ativo_index else 0 for i in range(len(carteira_agrupada))]

            # Configuração de interatividade e estilo
            fig.update_traces(
                textinfo='percent+label',  # Informações na fatia
                hoverinfo='label+value+percent',  # Informações no hover
                pull=pull_values,  # Simula o "zoom" na fatia selecionada
                marker=dict(
                    line=dict(color='#000000', width=0.1),  # Borda das fatias
                ),
            )

            # Configurar layout geral
            fig.update_layout(
                title_font_size=20,
                margin=dict(t=50, b=50, l=50, r=50),  # Margens do gráfico
                showlegend=True,
                legend_title_text="Ativos",
                hoverlabel=dict(font_size=12, font_family="Arial"),  # Estilo do hover
            )

            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig)
    
        else:
            st.info("Adicione ativos para visualizar a composição da carteira.")

with tab2:
    st.subheader("Fazer Lançamento")
    nome_ativo = st.selectbox("Selecione ou busque o ativo:", options=TICKERS)

    quantidade = st.number_input("Quantidade:", min_value=0.00, step=0.001)
    preco = st.number_input("Preço:", min_value=0.0, step=0.01)
    data_compra = st.date_input("Data de compra:", min_value=datetime(2000, 1, 1), max_value=datetime.today())

    if st.button("Adicionar"):
        if nome_ativo and quantidade > 0 and preco > 0:
            # Chama a função adiciona_ativo passando a data de compra
            novo_lancamento(nome_ativo, quantidade, preco, data_compra)
            st.success(f"Ativo {nome_ativo} adicionado com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos corretamente.")
            
with tab3:
    # Atualizar/Remover lancamento
    if not st.session_state.lancamentos.empty:
        st.subheader("Atualizar Lançamentos")

        # Mostrar lista de lancamentos com suas quantidades e preços
        lancamentos_att = st.session_state.lancamentos.copy()
        lancamentos_att['ID'] = lancamentos_att.index + 1
        lancamentos_disponiveis = lancamentos_att.iloc[::-1]
        lancamentos_disponiveis['Ativo'] = (" Lançamento: " + lancamentos_disponiveis['ID'].astype(str)+ 
                                                " | "+                lancamentos_disponiveis['Ativo'] + 
                                            " | Quantidade: " + lancamentos_disponiveis['Quantidade'].astype(str) + 
                                            " | Preço: R$ " + lancamentos_disponiveis['Preço'].astype(str) + 
                                            " | Data: "+lancamentos_disponiveis['Data de Compra']
                                            )

        ativo_atualizar = st.selectbox("Selecione o lançamento a atualizar", lancamentos_disponiveis['Ativo'].values)

        id_lancamento = int(ativo_atualizar.split(": ")[1].split(' | ')[0])

        # Criar abas para cada tipo de atualização
        with st.expander("Atualizar Quantidade"):
            st.markdown(f'Quantidade atual: {ativo_atualizar.split(" | ")[2].split(": ")[1]}')
            nova_quantidade = st.number_input("Nova quantidade:", min_value=0.00, step=0.01, key="atualizar_quantidade")
            if st.button("Atualizar Quantidade"):
                if nova_quantidade >= 0:
                    atualiza_lancamento(id_lancamento, nova_quantidade=nova_quantidade, df_lancamentos = lancamentos_att)
                    st.success("Quantidade atualizada com sucesso!")
                else:
                    st.error("Por favor, insira uma quantidade válida.")

        with st.expander("Atualizar Nome"):
            st.markdown(f'Nome atual: {ativo_atualizar.split(" | ")[1]}')
            novo_nome = st.text_input("Novo Nome:", max_chars=20, key="atualizar_nome")
            if st.button("Atualizar Nome"):
                if novo_nome:
                    atualiza_lancamento(id_lancamento, novo_nome=novo_nome, df_lancamentos = lancamentos_att)
                    st.success("Nome atualizado com sucesso!")
                else:
                    st.error("Por favor, insira um nome válido.")

        with st.expander("Atualizar Preço"):
            st.markdown(f'Preço atual: {ativo_atualizar.split(" | ")[3].split(": ")[1]}')
            novo_preco = st.number_input("Novo Preço:", min_value=0.0, step=0.001, key="atualizar_preco")
            if st.button("Atualizar Preço"):
                if novo_preco > 0:
                    atualiza_lancamento(id_lancamento, novo_preco=novo_preco, df_lancamentos = lancamentos_att)
                    st.success("Preço atualizado com sucesso!")
                else:
                    st.error("Por favor, insira um preço válido.")

        with st.expander("Atualizar Data"):
            data_lanc = ativo_atualizar.split(" | ")[4].split(": ")[1]
            st.markdown(f'Data atual: {data_lanc}')
            nova_data = st.date_input(label = "Nova data:", value = data_lanc)
            if st.button("Atualizar Data"):
                if nova_data:
                    atualiza_lancamento(id_lancamento, nova_data=nova_data, df_lancamentos = lancamentos_att)
                    st.success("Data atualizada com sucesso!")
                else:
                    st.error("Por favor, insira uma data.")

        with st.expander("Remover Lançamento"):
            if st.button("Remover Lançamento"):
                remove_lancamento(id_lancamento, df_lancamentos=lancamentos_att)
                st.success("Ativo removido com sucesso!")
    else:
        st.info("Adicione ativos à lançamentos para atualizá-los.")

def atualizar_contexto(df):
    if "message" not in st.session_state:
        st.session_state.message = []

    # Gerar o texto da tabela com os dados atualizados
    descricao_colunas = """
                        As colunas representam os seguintes dados:
                        - 'Ativo': O nome do ativo financeiro (exemplo: PETR4, VALE3).
                        - 'Quantidade': A quantidade de unidades do ativo que o cliente possui.
                        - 'Preço Médio': O preço médio do ativo no momento da última atualização.
                        - 'Valor': O valor total investido no ativo (Quantidade * Preço).
                        - 'Última Atualização': A data e hora da última atualização dos dados.
                        """
    
    cuidados =  """
                        Responda em no máximo 50 palavras.
                        Nunca realize recomendações de investimento.
                        Você irá ajudar pessoas leigas a aprenderem a investir.
                        Se não souber a resposta, diga: "Desculpe, não tenho informações suficientes para fornecer uma resposta precisa. Procure fontes confiáveis."
                        Seja claro e objetivo, nunca invente informações.
                """
    
    contexto = f"""Siga essas regras:
                {cuidados}

                Descrição dos dados:
                {descricao_colunas}

                Tabela da carteira do usuário:
                {df.to_string(index=False)}
                """

    # Atualizar a mensagem do tipo 'system' no histórico
    st.session_state.message = [
        msg for msg in st.session_state.message if msg["role"] != "system"
    ]
    st.session_state.message.insert(0, {"role": "system", "content": contexto})

carteira_agrupada = st.session_state.carteira.copy()
atualizar_contexto(carteira_agrupada)

with tab4:

    st.title("Pergunte sobre investimentos")

    try:
        client = Groq(api_key=API_KEY)
    except Exception as e:
        st.error(f"Erro ao configurar o cliente Groq: {str(e)}")
        st.stop()

    if "message" not in st.session_state:
        st.session_state.message = [
            {
            "role": "system",
            "content": (
                "Responda em no máximo 10 palavras, focando em precisão."

            ),}
        ]
    
    if "user_input" not in st.session_state:
     st.session_state.user_input = ""

  
    def send_message():
        if st.session_state.user_input:
            user_message = st.session_state.user_input

            st.session_state.message.append({"role": "user", "content": user_message})

            st.session_state.user_input = ""

            try:
                response = client.chat.completions.create(
                    messages=st.session_state.message,
                    model="llama3-8b-8192",
                    temperature=0.05,
                    max_tokens=1000
                )
                assistant_message = response.choices[0].message.content
                st.session_state.message.append({"role": "assistant", "content": assistant_message})
            except Exception as e:
                st.error(f"Erro ao consultar o modelo: {str(e)}")

    with st.container(border = True):
        st.text_input(
        "Digite sua pergunta:",
        key="user_input",
        on_change=send_message(),
        help = 'Meta AI Llama3-8b-8192 ',
        placeholder="Escreva algo e pressione Enter...",)

        if len(st.session_state.message) > 1:
            last_user_message = next((msg for msg in reversed(st.session_state.message) if msg["role"] == "user"), None)
            last_assistant_message = next((msg for msg in reversed(st.session_state.message) if msg["role"] == "assistant"), None)
            
            if last_user_message:
                st.markdown(f"**Usuário:** {last_user_message['content']}")
            if last_assistant_message:
                st.markdown(f"**Assistente:** {last_assistant_message['content']}")
        
    st.markdown("")
    st.markdown("")

    
    with st.expander("**Últimas mensagens:**"):
        with st.container(border = True, height=600):
            recent_messages = st.session_state.message[-10:][::1]
            
            for msg in recent_messages:
                if msg["role"] == "user":
                    st.write(f"**Usuário:** {msg['content']}")
                elif msg["role"] == "assistant":
                    st.write(f"**Assistente:** {msg['content']}")

                    st.markdown("---")

    st.markdown("")
    st.markdown("")


    st.write("Sempre confira os dados:")
    carteira_agrupada