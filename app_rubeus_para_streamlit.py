import streamlit as st
import requests
import pandas as pd
import io
from requests.auth import HTTPBasicAuth
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path=r".env")

# Obter as variáveis de ambiente
login = os.getenv('login')
senha = os.getenv('senha')
url_registros = os.getenv('URL_REGISTROS')
url_contatos = os.getenv('URL_CONTATOS')

# Verificar se as variáveis foram carregadas corretamente
if not login or not senha or not url_registros or not url_contatos:
    st.error("Erro ao carregar variáveis de ambiente. Verifique o arquivo .env.")
else:
    st.success("Variáveis de ambiente carregadas com sucesso!")

# Função para baixar e converter CSV para DataFrame
def baixar_csv_para_df(url):
    try:
        response = requests.get(url, auth=HTTPBasicAuth(login, senha))
        response.raise_for_status()
        csv_content = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content), low_memory=False)
        return df
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro HTTP: {http_err}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    except Exception as err:
        st.error(f"Erro inesperado: {err}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

# Carregar DataFrames
df_registros = baixar_csv_para_df(url_registros)
df_contatos = baixar_csv_para_df(url_contatos)

# Função para realizar o merge com verificação de colunas
def merge_com_colunas_customizadas(df_contatos, df_registros):
    # Verificar se as colunas necessárias existem
    if 'id' not in df_contatos.columns:
        st.error("A coluna 'id' não está presente no DataFrame de contatos.")
        return pd.DataFrame()  # Retorna um DataFrame vazio
    if 'pessoa' not in df_registros.columns:
        st.error("A coluna 'pessoa' não está presente no DataFrame de registros.")
        return pd.DataFrame()  # Retorna um DataFrame vazio

    # Realizar o merge
    merged_df = pd.merge(df_contatos, df_registros, how='left', left_on='id', right_on='pessoa')

    # Renomear colunas duplicadas
    new_columns = []
    for col in merged_df.columns:
        if col in df_contatos.columns and col in df_registros.columns:
            new_columns.append(f"{col}_contatos" if col in df_contatos.columns else f"{col}_registros")
        else:
            new_columns.append(col)
    merged_df.columns = new_columns
    return merged_df

# Botão para recarregar dados com efeito de carregamento
if st.button('🔄 Atualizar consultas'):
    with st.spinner('Atualizando os dados...'):
        df_registros = baixar_csv_para_df(url_registros)
        df_contatos = baixar_csv_para_df(url_contatos)
    st.success('Dados atualizados com sucesso!')

# Título e linha divisória para a seção
st.header("Lista de Leads por Processo 📋")
st.markdown("---") 

# Realizar o merge
df_merge = merge_com_colunas_customizadas(df_contatos, df_registros)

if not df_merge.empty:
    # Criar a lista de processos disponíveis
    opcoes_de_processos = df_merge['processoNome'].unique().tolist()

    # Seção interativa para selecionar o processo com caixa destacada
    st.subheader("🔍 Selecione um processo para visualizar os leads associados")
    processo_procurado = st.selectbox("Selecione o processo:", opcoes_de_processos)

    # Filtrar e contar pessoas no processo selecionado
    df_processado = df_merge[df_merge['processoNome'] == processo_procurado]
    num_pessoas_associadas = df_processado['id_contatos'].nunique()

    # Exibir os resultados em um formato mais destacado
    st.info(f"Total de pessoas associadas ao processo **{processo_procurado}**: {num_pessoas_associadas}")
    st.dataframe(df_processado[['id_contatos', 'nome']], use_container_width=True)

    # Seção para visualização de leads por processo seletivo
    st.header("Lista de Leads por Processo Seletivo ")
    st.markdown("---")

    # Criar a lista de Processos Seletivos disponíveis
    opcoes_de_ps = df_merge['processoSeletivoNome'].unique().tolist()

    # Seção interativa para selecionar o processo com caixa destacada
    st.subheader('🔍 Selecione um Processo Seletivo para visualizar os leads associados')
    ps_procurado = st.selectbox('Selecione o Processo Seletivo:', opcoes_de_ps)

    # Filtrar e contar pessoas no processo seletivo selecionado
    df_processado_ps = df_merge[df_merge['processoSeletivoNome'] == ps_procurado]
    num_pessoas_associadas_ao_ps = df_processado_ps['id_contatos'].nunique()

    # Exibir os resultados em um formato mais destacado
    st.info(f'Total de pessoas associadas ao PS **{ps_procurado}**: {num_pessoas_associadas_ao_ps}')
    st.dataframe(df_processado_ps[['id_contatos', 'nome']], use_container_width=True)

    # Seção para filtrar e exibir 'Inscrito Parcial' e 'Inscrito' com base no processo seletivo selecionado
    st.header(f"Visualização do Processo Seletivo: {ps_procurado}")
    st.markdown("---")

    # Filtrar para 'Inscrito Parcial' e 'Inscrito'
    df_inscrito_parcial = df_processado_ps[df_processado_ps['etapaNome'] == 'Inscrito parcial']
    df_inscrito = df_processado_ps[df_processado_ps['etapaNome'] == 'Inscrito']

    # Layout em duas colunas para visualização dos filtros
    col1, col2 = st.columns(2)

    # Coluna 1: Exibir os dados para 'Inscrito Parcial'
    with col1:
        st.subheader("Inscrito Parcial")
        st.write(f"Total de pessoas em 'Inscrito Parcial': {df_inscrito_parcial['id_contatos'].nunique()}")
        st.dataframe(df_inscrito_parcial[['id_contatos', 'nome']], use_container_width=True)

    # Coluna 2: Exibir os dados para 'Inscrito'
    with col2:
        st.subheader("Inscrito")
        st.write(f"Total de pessoas em 'Inscrito': {df_inscrito['id_contatos'].nunique()}")
        st.dataframe(df_inscrito[['id_contatos', 'nome']], use_container_width=True)

    # Verificação de similaridade de nomes entre as etapas
    st.header("Verificação de Nomes Semelhantes entre Etapas")
    st.markdown("---")

    # Criar uma lista para armazenar os resultados
    resultados_nomes_semelhantes = [
        (nome_parcial, nome, fuzz.ratio(nome_parcial, nome))
        for nome_parcial in df_inscrito_parcial['nome'].tolist()
        for nome in df_inscrito['nome'].tolist()
        if fuzz.ratio(nome_parcial, nome) > 98
    ]

    # Exibir resultados
    if resultados_nomes_semelhantes:
        st.success("Nomes semelhantes encontrados com mais de 98% de similaridade:")
        df_resultados = pd.DataFrame(resultados_nomes_semelhantes, columns=['Nome Inscrito Parcial', 'Nome Inscrito', 'Similaridade'])
        st.dataframe(df_resultados, use_container_width=True)
    else:
        st.warning("Nenhum nome semelhante encontrado entre as etapas 'Inscrito Parcial' e 'Inscrito'.")

    # Seção para leads com 0 ou 1 processo
    st.header("Leads com 0 ou 1 Processo ⚙️")
    st.markdown("---")

    # Contar quantidade de processos por pessoa
    df_merge['qtd_processos'] = df_merge.groupby('nome')['processoNome'].transform('nunique')
    df_merge = df_merge.reset_index(drop=True)

    # Função para filtrar pessoas por número de processos
    def filtrar_por_processos(df, num_processos):
        return df[df['qtd_processos'] == num_processos]

    # Botões para mostrar leads com 0 ou 1 processos
    if st.button("Mostrar Leads com 0 Processos"):
        leads_zero_processos = filtrar_por_processos(df_merge, 0)
        st.success(f"Total de Leads com 0 processos: {leads_zero_processos['nome'].nunique()}")
        st.dataframe(leads_zero_processos[['nome']], use_container_width=True)

    if st.button("Mostrar Leads com 1 Processo"):
        leads_um_processo = filtrar_por_processos(df_merge, 1)
        st.success(f"Total de Leads com 1 processo: {leads_um_processo['nome'].nunique()}")
        st.dataframe(leads_um_processo[['nome']], use_container_width=True)

# Exibir informações adicionais
st.sidebar.title("Informações Adicionais")
st.sidebar.info("Este painel mostra a associação de leads com processos e processos seletivos, incluindo a identificação de nomes semelhantes entre etapas e leads com 0 ou 1 processo.")
