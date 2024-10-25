# pages/2_Visao_Resumos.py
import streamlit as st
import requests
import pandas as pd
import io
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Adicione o conteúdo específico da Visão Resumos aqui.
st.title("Visão Resumos")
st.write("Esta é a página de Visão Resumos. O conteúdo será diferente da página Visão Geral.")

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter as variáveis de ambiente
login = os.getenv('login')
senha = os.getenv('senha')
url_atividades = os.getenv('URL_ATIVIDADES')

# Função para baixar e converter CSV para DataFrame
def baixar_csv_para_df(url):
    try:
        response = requests.get(url, auth=HTTPBasicAuth(login, senha))  # type: ignore
        response.raise_for_status()
        csv_content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content), low_memory=False)
        return df
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro HTTP: {http_err}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    except Exception as err:
        st.error(f"Erro inesperado: {err}")
        return pd.DataFrame()

# Carregar DataFrames
df_atividades = baixar_csv_para_df(url_atividades)

# Sidebar para recarregar dados
if st.button('🔄 Atualizar consultas'):
    with st.spinner('Atualizando os dados...'):
        df_atividades = baixar_csv_para_df(url_atividades)
    st.success('Dados atualizados com sucesso!')

st.header("🔍 Pesquisa por resumo")
st.markdown("---")

# Input para receber a descrição
pesquisa_resumo = st.text_input("Informe a descrição para resumo")

# Realiza a pesquisa e retorna as linhas associadas
if pesquisa_resumo:
    # Filtrar o DataFrame pela coluna 'contato'
    resultados = df_atividades[df_atividades['contato'].str.contains(pesquisa_resumo, case=False, na=False, regex=False)]

    # Verifica se há resultados e exibe
    if not resultados.empty:
        st.success("Resultados encontrados:")
        st.dataframe(resultados[['contato', 'descricao', 'razaoOportunidadeNome', 'pessoaNome', 'cursoNome', 'processoSeletivoNome', 'etapaNome', 'responsavelNome']], use_container_width=True)
        
        # Gerar gráfico de barras para o campo 'responsavelNome'
        st.header("📊 Total de atendimento por vendedor")
        st.markdown("---")
        
        # Contar a quantidade de vezes que cada 'responsavelNome' aparece nos resultados filtrados
        contagem_responsaveis = resultados['responsavelNome'].value_counts()
        
        # Verifica se existem dados para gerar o gráfico
        if not contagem_responsaveis.empty:
            # Ordenar a contagem em ordem decrescente
            contagem_responsaveis = contagem_responsaveis.sort_values(ascending=True)  # Corrigido para decrescente

            # Configurar o gráfico
            plt.figure(figsize=(10, 6))  # Aumentar a largura e altura
            colors = sns.color_palette("viridis", len(contagem_responsaveis))  # Usar uma paleta de cores
            contagem_responsaveis.plot(kind='barh', color=colors, edgecolor='black')  # Adicionando bordas para as barras
            plt.title('Atendimentos por vendedor de acordo com o resumo acima', fontsize=15, fontweight='bold')
            plt.xlabel('Quantidade de Ocorrências', fontsize=13)
            plt.ylabel('Responsável', fontsize=14)
            plt.xticks(rotation=0, fontsize=11)  # Ajustar a rotação e tamanho da fonte
            plt.yticks(fontsize=11)  # Tamanho da fonte dos rótulos do eixo y
            plt.grid(axis='x', linestyle='--', alpha=0.7)  # Adicionar grade horizontal
            
            # Adicionar anotações nos gráficos
            for index, value in enumerate(contagem_responsaveis):
                plt.text(value + 4, index, str(value), va='center', fontsize=11)  # Aumenta o espaço entre a barra e o número

            st.pyplot(plt)  # type: ignore
    else:
        # Mensagem amigável quando não há resultados
        st.warning("Nenhum resultado encontrado para a descrição fornecida. Tente usar termos diferentes ou verifique a ortografia.")

st.header("📋 Top 10 Principais Objeções")
st.markdown("---")

# Criar um DataFrame para armazenar os resultados com contagem
resultados_objeções = pd.DataFrame(columns=['objecaoNome', 'pessoa'])

# Contar total geral de objeções
total_objeções = df_atividades['objecaoNome'].value_counts().head(10)  # Limitar a 10 objeções

# Exibir total geral de objeções
col1, col2 = st.columns(2)  # Cria duas colunas

with col1:
    st.subheader("Top 10 Total Geral de Objeções")
    # Reseta o índice e começa a contagem a partir de 1
    total_df = total_objeções.reset_index().rename(columns={'index': 'objecaoNome', 'objecaoNome': 'Total'})
    total_df.index += 1  # Iniciar contagem a partir de 1
    st.dataframe(total_df, use_container_width=True)

with col2:
    st.subheader("Top 10 Objeções Encontradas")

    # Input para receber a descrição
    # pesquisa_objeção = st.text_input("Informe a descrição para pesquisa de objeções")
    pesquisa_objeção = pesquisa_resumo

    if pesquisa_objeção:
        # Filtrar o DataFrame pela coluna 'objecaoNome' e pelo resumo
        resultados_objeções = df_atividades[df_atividades['contato'].str.contains(pesquisa_objeção, case=False, na=False, regex=False)]

        # Verifica se há resultados e exibe
        if not resultados_objeções.empty:
     # Contar a quantidade de vezes que cada 'objecaoNome' aparece nos resultados filtrados
            contagem_objeções = resultados_objeções['objecaoNome'].value_counts()

            # Obter o Top 10 objeções
            top_10_objeções = contagem_objeções.head(10).reset_index().rename(columns={'index': 'objecaoNome', 'objecaoNome': 'Total'})
            top_10_objeções.index += 1  # Iniciar contagem a partir de 1

            # Exibir o Top 10
            st.dataframe(top_10_objeções, use_container_width=True)
    else:
        # Mensagem amigável quando não há resultados
        st.warning("Nenhuma objeção encontrada para a descrição fornecida. Tente usar termos diferentes ou verifique a ortografia.")

