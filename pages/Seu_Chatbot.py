import os
import csv
import json
import ast
import toml
import streamlit as st

from groq import Groq
from dotenv import load_dotenv


st.title("Chat com LLaMA 3 usando Groq API")

# config = toml.load("senhas.toml")
# API_KEY = config['api_key']['GROQ_API_KEY']
API_KEY = st.secrets['api_key']['GROQ_API_KEY']

try:
    client = Groq(api_key=API_KEY)
except Exception as e:
    st.error(f"Erro ao configurar o cliente Groq: {str(e)}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Responda sempre em portugues."}
    ]

# Inicializar estado do campo de texto
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

MAX_CHARACTERS = 10000  # Limite de caracteres para o conteúdo do arquivo

def process_file(uploaded_file):
    try:
        # Identificar o tipo de arquivo pela extensão
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension == "csv":
            file_content = uploaded_file.read().decode("utf-8")
            reader = csv.reader(file_content.splitlines())
            content_as_text = "\n".join([", ".join(row) for row in reader])
        
        elif file_extension == "json":
            file_content = uploaded_file.read().decode("utf-8")
            json_data = json.loads(file_content)
            content_as_text = json.dumps(json_data, indent=2)
        
        elif file_extension == "py":
            file_content = uploaded_file.read().decode("utf-8")
            ast.parse(file_content)  # Garante que o código é válido
            content_as_text = file_content

        elif file_extension == "txt":
            file_content = uploaded_file.read().decode("utf-8")
            content_as_text = file_content
        
        else:
            st.error(f"Formato de arquivo não suportado: {file_extension}")
            return None
        
        # Verificar tamanho do conteúdo
        if len(content_as_text) > MAX_CHARACTERS:
            st.warning(f"O arquivo {uploaded_file.name} é muito extenso. Apenas os primeiros {MAX_CHARACTERS} caracteres foram considerados.")
            return content_as_text[:MAX_CHARACTERS]
        
        return content_as_text
    
    except Exception as e:
        st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {str(e)}")
        return None

def send_message(uploaded_files=None):
    if st.session_state.user_input:
        # Adicionar mensagem do usuário ao histórico
        user_message = st.session_state.user_input
        
        file_contents = []  # Lista para armazenar os conteúdos dos arquivos
        if uploaded_files:
            for uploaded_file in uploaded_files:
                processed_content = process_file(uploaded_file)
                if processed_content:
                    file_contents.append(f"\n\nArquivo: {uploaded_file.name}\n\n{processed_content}")
        
        # Atualizar o histórico com a mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": user_message})

        # Limpar o campo de entrada
        st.session_state.user_input = ""

        try:
            # Combinar a mensagem do usuário com os dados dos arquivos
            if file_contents:
                combined_message = user_message + "\n".join(file_contents)
                st.session_state.messages.append({"role": "user", "content": combined_message})

            # Realizar a consulta ao modelo com o histórico completo
            response = client.chat.completions.create(
                messages=st.session_state.messages,
                model="llama3-8b-8192",
                temperature=0.05
            )

            # Adicionar a resposta do assistente ao histórico
            assistant_message = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        except Exception as e:
            st.error(f"Erro ao consultar o modelo: {str(e)}")


# Entrada de texto e upload de múltiplos arquivos
uploaded_files = st.file_uploader("Anexe arquivos (opcional):",
                                type=["txt", "csv", "json", "py"],
                                accept_multiple_files=True,
                                help="Você pode anexar arquivos de texto, CSV, JSON ou Python.")

st.text_input(
    "Digite sua mensagem:",
    key="user_input",
    on_change=send_message,
    args=(uploaded_files,),
    placeholder="Escreva algo e pressione Enter...",
)

if len(st.session_state.messages) > 1:
    last_user_message = next((msg for msg in reversed(st.session_state.messages) if msg["role"] == "user"), None)
    last_assistant_message = next((msg for msg in reversed(st.session_state.messages) if msg["role"] == "assistant"), None)
    if last_user_message:
        st.write(f"**Usuário:** {last_user_message['content']}")
    if last_assistant_message:
        st.write(f"**LLaMA 3:** {last_assistant_message['content']}")

st.markdown("")
st.markdown("")

with st.expander("**Últimas mensagens:**"):
    with st.container(border = True, height=600):
        recent_messages = st.session_state.messages[-10:][::1]
        
        for msg in recent_messages:
            if msg["role"] == "user":
                st.write(f"**Usuário:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.write(f"**Assistente:** {msg['content']}")
                st.markdown("---")

st.markdown("")
st.markdown("")
