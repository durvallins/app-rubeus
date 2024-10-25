# app.py
import streamlit as st

st.set_page_config(page_title="Acompanhamento Rubeus", layout="wide")

# st.sidebar.header("Navegação")
st.title("Bem-vindo à Aplicação")

# Adicionando o GIF de abertura
st.write("Use a barra lateral para navegar entre as páginas.")

st.image("https://login.rubeus.com.br/assets/gifLogin.f20d0ea9.gif", 
         caption="Bem-vindo a página de acompanhamento!",
            width=400)

