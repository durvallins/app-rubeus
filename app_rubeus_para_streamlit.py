import streamlit as st
import requests
import pandas as pd
import io
from fuzzywuzzy import fuzz
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter as variáveis de ambiente
login = os.getenv('login')
senha = os.getenv('senha')
url_registros = os.getenv('URL_REGISTROS')
url_contatos = os.getenv('URL_CONTATOS')

###################################################################

# Verificar se as variáveis foram carregadas corretamente
if not login or not senha or not url_registros or not url_contatos:
    st.error("Erro ao carregar variáveis de ambiente. Verifique o arquivo .env.")
    st.stop()

# Função para baixar e converter CSV para DataFrame
def baixar_csv_para_df(url):
    try:
        response = requests.get(url, auth=HTTPBasicAuth(login, senha)) # type: ignore
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
df_registros = baixar_csv_para_df(url_registros)
df_contatos = baixar_csv_para_df(url_contatos)

###################################################################

# Verificar se os DataFrames foram carregados e se as colunas existem
if df_registros.empty or df_contatos.empty:
    st.error("Erro ao carregar DataFrames. Verifique as URLs e suas autenticações.")
    st.stop()

if 'id' not in df_contatos.columns:
    st.error("A coluna 'id' não está presente no DataFrame de contatos.")
    st.stop()

if 'pessoa' not in df_registros.columns:
    st.error("A coluna 'pessoa' não está presente no DataFrame de registros.")
    st.stop()

###################################################################

# Função para realizar o merge e renomear colunas duplicadas
def merge_com_colunas_customizadas(df_contatos, df_registros):
    merged_df = pd.merge(df_contatos, df_registros, how='left', left_on='id', right_on='pessoa')

    # Renomear colunas duplicadas
    merged_df = merged_df.rename(columns={'id_x': 'id'})
    
    new_columns = []
    for col in merged_df.columns:
        if col in df_contatos.columns and col in df_registros.columns:
            new_columns.append(f"{col}_contatos" if col in df_contatos.columns else f"{col}_registros")
        else:
            new_columns.append(col)
    merged_df.columns = new_columns
    return merged_df

###################################################################

merged_df_customizada = merge_com_colunas_customizadas(df_contatos, df_registros)

###################################################################

# Sidebar para recarregar dados
if st.sidebar.button('🔄 Atualizar consultas'):
    with st.spinner('Atualizando os dados...'):
        df_registros = baixar_csv_para_df(url_registros)
        df_contatos = baixar_csv_para_df(url_contatos)
    st.success('Dados atualizados com sucesso!')

# Título e seção principal
st.header("Lista de Leads por Processo 📋")
st.markdown("---")

# Realizar o merge e renomear coluna 'id_x' para 'id'
df_merge = merge_com_colunas_customizadas(df_contatos, df_registros)

# Criar a lista de processos disponíveis
opcoes_de_processos = df_merge['processoNome'].unique().tolist()

# Sidebar para selecionar o processo
processo_procurado = st.sidebar.selectbox("Selecione o processo:", opcoes_de_processos)

# Filtrar e contar pessoas no processo selecionado
df_processado = df_merge[df_merge['processoNome'] == processo_procurado]

# Remover duplicatas pelo campo 'nome'
df_processado_unico = df_processado.drop_duplicates(subset='nome')

# Contar o número de pessoas únicas associadas ao processo selecionado
num_pessoas_associadas = df_processado_unico['nome'].nunique()

# Exibir o número de leads associados
st.info(f"Total de pessoas associadas ao processo **{processo_procurado}**: {num_pessoas_associadas}")
st.dataframe(df_processado_unico[['nome']], use_container_width=True)


###################################################################
# Criar a lista de processos seletivos disponíveis
opcoes_de_processos_seletivos = df_merge['processoSeletivoNome'].unique().tolist()


# Side bar para selecionar o processo Seletivo
ps_procurado = st.sidebar.selectbox('Selecione o Processo Seletivo:', opcoes_de_processos_seletivos)


###################################################################

# Exibir as etapas do Processo Seletivo "Vestibular 2025"
st.header(f"Leads por Etapa no Processo Seletivo: {ps_procurado}")
st.markdown("---")

# Filtrar o DataFrame pelo Processo Seletivo "Vestibular 2025"
df_ps_procurado = df_merge[df_merge['processoSeletivoNome'] == ps_procurado]

# Lista de etapas consideradas
lista_etapas = ['Sem etapa definida', 'Inscrito parcial', 'Inscrito', 'Documentação enviada', 
                'Ausente na prova', 'Presente na prova', 'Desclassificado', 'Aprovado',
                'Convocado', 'Apto. para Matrícula', 'Matrícula provisória', 'Matriculado',
                'Matrícula Cancelada']

# Criar um DataFrame para armazenar os resultados com contagem
resultados = pd.DataFrame(columns=['Etapa', 'Quantidade de Leads'])

# Número de colunas para layout
num_colunas = 2

# Iterar sobre as etapas e coletar os leads em cada uma
for i, etapa in enumerate(lista_etapas):
    # Filtrar leads para a etapa atual
    df_etapa = df_ps_procurado[df_ps_procurado['etapaNome'] == etapa]
    quantidade_leads = df_etapa.shape[0]
    
    # Adicionar resultados ao DataFrame de contagem
    resultados = pd.concat([resultados, pd.DataFrame([{'Etapa': etapa, 'Quantidade de Leads': quantidade_leads}])], ignore_index=True)

    # Exibir colunas de layout
    if i % num_colunas == 0:
        colunas = st.columns(num_colunas)

    with colunas[i % num_colunas]:
        st.subheader(f"Etapa: {etapa}")
        if not df_etapa.empty:
            st.dataframe(df_etapa[['nome']], use_container_width=True)
            st.info(f"Total de leads na etapa '{etapa}': {quantidade_leads}")
        else:
            st.warning(f"Nenhum lead encontrado na etapa '{etapa}'.")

# Exibir o DataFrame de contagem geral
st.dataframe(resultados, use_container_width=True)

st.markdown("---")

###################################################################

# Função para listar todos os processos associados a uma pessoa específica e contar os processos distintos
# Função para listar processos por aluno
def listar_processos_por_aluno(df, nome_aluno):
    # Filtra o DataFrame para encontrar processos associados à pessoa
    processos_aluno = df[df['nome'] == nome_aluno]
    
    # Conta o total de processos distintos
    total_distintos = processos_aluno['processoNome'].nunique()  # Conta processos distintos (nunique para garantir a contagem única)
    
    return processos_aluno[['processoNome']], total_distintos

# Função para listar processos seletivos por aluno
def listar_ps_por_aluno(df, nome_aluno):
    # Filtra o DataFrame para encontrar processos seletivos associados à pessoa
    ps_aluno = df[df['nome'] == nome_aluno]

    # Conta o total de processos seletivos distintos
    total_ps = ps_aluno['processoSeletivoNome'].nunique()  # Contagem única para evitar duplicações

    return ps_aluno[['processoSeletivoNome']], total_ps


# Pesquisar por nome
st.header("🔍 Pesquisa por nome da pessoa")

# Input para receber o nome da pessoa
nome_aluno = st.text_input("Informe o nome da pessoa para pesquisa:", "Laene de Melo Freitas Gouveia")

# Realiza a pesquisa e retorna os processos associados e o total de processos distintos
if nome_aluno:
    # Listar processos
    processos_associados, total_processos_distintos = listar_processos_por_aluno(df_merge, nome_aluno)
    
    # Verifica se a pessoa tem processos associados
    if not processos_associados.empty:
        # Agrupar e contar processos
        processos_count = processos_associados.groupby('processoNome').size().reset_index(name='Total') # type: ignore
        
        st.success(f"Processos associados a {nome_aluno}:")
        st.dataframe(processos_count, use_container_width=True)
        st.info(f'Total de processos associados: {total_processos_distintos}')
    else:
        st.warning(f"⚠ Não foram encontrados processos associados a {nome_aluno}. ⚠")
    
    # Listar processos seletivos
    ps_associados, total_ps_distintos = listar_ps_por_aluno(df_merge, nome_aluno)
    
    # Verifica se a pessoa tem processos seletivos associados
    if not ps_associados.empty:
        # Agrupar e contar processos seletivos
        ps_count = ps_associados.groupby('processoSeletivoNome').size().reset_index(name='Total') # type: ignore
        
        st.success(f"Processos Seletivos associados a {nome_aluno}:")
        st.dataframe(ps_count, use_container_width=True)
        st.info(f'Total de Processos Seletivos associados: {total_ps_distintos}')
    else:
        st.warning(f"⚠ Não foram encontrados Processos Seletivos associados a {nome_aluno}. ⚠")
        