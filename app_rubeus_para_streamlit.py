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

# Verificar se as variáveis foram carregadas corretamente
if not login or not senha or not url_registros or not url_contatos:
    st.error("Erro ao carregar variáveis de ambiente. Verifique o arquivo .env.")
    st.stop()  # Para o script aqui se as variáveis não forem carregadas

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
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

# Carregar DataFrames
df_registros = baixar_csv_para_df(url_registros)
df_contatos = baixar_csv_para_df(url_contatos)

# Verificar se os DataFrames foram carregados e se as colunas existem
if df_registros.empty or df_contatos.empty:
    st.error("Erro ao carregar DataFrames. Verifique as URLs e suas autenticações.")
    st.stop()

# Verificando se as colunas 'id' e 'pessoa' existem nos DataFrames
if 'id' not in df_contatos.columns: # ESSA PARTE JÁ FOI DANDO ERRO DE NAO TER LOCALZIADO AS COLUNAS ID E PESSOA, QUE SAO AS CHAVES PRA O MERGE 
    st.error("A coluna 'id' não está presente no DataFrame de contatos.")
    st.stop()

if 'pessoa' not in df_registros.columns:
    st.error("A coluna 'pessoa' não está presente no DataFrame de registros.")
    st.stop()

# Função para realizar o merge e renomear colunas duplicadas
def merge_com_colunas_customizadas(df_contatos, df_registros):
    merged_df = pd.merge(df_contatos, df_registros, how='left', left_on='id', right_on='pessoa')
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

# Criar a lista de processos disponíveis
opcoes_de_processos = df_merge['processoNome'].unique().tolist()

# Seção interativa para selecionar o processo com caixa destacada
st.subheader("🔍 Selecione um processo para visualizar os leads associados")
processo_procurado = st.selectbox("Selecione o processo:", opcoes_de_processos)

# Filtrar os dados pelo processo selecionado
df_processado = df_merge[df_merge['processoNome'] == processo_procurado]

# Limpar espaços em branco em torno dos nomes e IDs (se houver)
df_processado['nome'] = df_processado['nome'].str.strip()
df_processado['id_x'] = df_processado['id_x'].astype(str).str.strip()

# Remover duplicatas considerando 'id_x' e 'nome' dentro do processo selecionado
df_processado_unico = df_processado.drop_duplicates(subset=['id_x', 'nome'])

# Contar o número de pessoas únicas associadas ao processo selecionado
num_pessoas_associadas = df_processado_unico['nome'].nunique()

# Exibir os resultados em um formato mais destacado
st.info(f"Total de pessoas associadas ao processo **{processo_procurado}**: {num_pessoas_associadas}")
st.dataframe(df_processado_unico[['id_x', 'nome']], use_container_width=True)


# Seção para visualização de leads por processo seletivo
st.header("Lista de Leads por Processo Seletivo 📋")
st.markdown("---")

# Criar a lista de Processos Seletivos disponíveis
opcoes_de_ps = df_merge['processoSeletivoNome'].unique().tolist()

# Seção interativa para selecionar o processo com caixa destacada
st.subheader('🔍 Selecione um Processo Seletivo para visualizar os leads associados')
ps_procurado = st.selectbox('Selecione o Processo Seletivo:', opcoes_de_ps)

# Filtrar os dados pelo processo seletivo selecionado
df_processado_ps = df_merge[df_merge['processoSeletivoNome'] == ps_procurado]

# Limpar espaços em branco em torno dos nomes e IDs (se houver)
df_processado_ps['nome'] = df_processado_ps['nome'].str.strip()
df_processado_ps['id_x'] = df_processado_ps['id_x'].astype(str).str.strip()

# Remover duplicatas considerando 'id_x' e 'nome' dentro do processo seletivo
df_processado_ps_unico = df_processado_ps.drop_duplicates(subset=['id_x', 'nome'])

# Contar o número de pessoas únicas associadas ao processo seletivo selecionado
num_pessoas_associadas_ao_ps = df_processado_ps_unico['id_x'].nunique()

# Exibir os resultados em um formato mais destacado
st.info(f'Total de pessoas associadas ao PS **{ps_procurado}**: {num_pessoas_associadas_ao_ps}')
st.dataframe(df_processado_ps_unico[['id_x', 'nome']], use_container_width=True)


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
    st.write(f"Total de pessoas em 'Inscrito Parcial': {df_inscrito_parcial['id_x'].nunique()}")
    st.dataframe(df_inscrito_parcial[['id_x', 'nome']], use_container_width=True)

# Coluna 2: Exibir os dados para 'Inscrito'
with col2:
    st.subheader("Inscrito")
    st.write(f"Total de pessoas em 'Inscrito': {df_inscrito['id_x'].nunique()}")
    st.dataframe(df_inscrito[['id_x', 'nome']], use_container_width=True)

# Verificação de similaridade de nomes entre as etapas
st.header("Verificação de Nomes Semelhantes entre Etapas")
st.markdown("---")

# Criar uma lista para armazenar os resultados
resultados_nomes_semelhantes = [
    (nome_parcial, nome, fuzz.ratio(nome_parcial, nome)) # type: ignore
    for nome_parcial in df_inscrito_parcial['nome'].tolist()
    for nome in df_inscrito['nome'].tolist()
    if fuzz.ratio(nome_parcial, nome) > 98 # type: ignore
]

# Exibir resultados
if resultados_nomes_semelhantes:
    st.success("Nomes semelhantes encontrados com mais de 98% de similaridade:")
    df_resultados = pd.DataFrame(resultados_nomes_semelhantes, columns=['Nome Inscrito Parcial', 'Nome Inscrito', 'Similaridade'])
    st.dataframe(df_resultados, use_container_width=True)
else:
    st.warning("Nenhum nome semelhante encontrado entre as etapas 'Inscrito Parcial' e 'Inscrito'.")

# Seção para leads com 0 ou 1 processo
# Contar o número de processos distintos por pessoa (baseado na coluna 'processoNome')
df_merge['qtd_processos'] = df_merge.groupby('id_x')['processoNome'].transform('nunique')

# Função para filtrar pessoas com base na quantidade de processos distintos
def filtrar_por_processos(df, num_processos):
    return df[df['qtd_processos'] == num_processos]

# Filtrar pessoas com 0 processos distintos
pessoas_sem_processos = filtrar_por_processos(df_merge, 0)

# Filtrar pessoas com exatamente 1 processo distinto
pessoas_com_um_processo = filtrar_por_processos(df_merge, 1)

# Exibir os resultados em uma seção para cada filtro
st.header("Leads com 0 processos distintos")
st.markdown("---")

if not pessoas_sem_processos.empty:
    st.success(f"Total de leads com 0 processos: {len(pessoas_sem_processos)}")
    st.dataframe(pessoas_sem_processos[['id_x', 'nome']], use_container_width=True)
else:
    st.warning("Nenhum lead com 0 processos encontrados.")

st.header("Leads com 1 processo distinto")
st.markdown("---")

if not pessoas_com_um_processo.empty:
    st.success(f"Total de leads com 1 processo: {len(pessoas_com_um_processo)}")
    st.dataframe(pessoas_com_um_processo[['id_x', 'nome']], use_container_width=True)
else:
    st.warning("Nenhum lead com 1 processo encontrado.")


# Pesquisa por nome da pessoa e retorna quantos e quais processos ela está associada

# Função para listar todos os processos associados a uma pessoa específica e contar os processos distintos
def listar_processos_por_aluno(df, nome_aluno):
    # Filtra o DataFrame para encontrar processos associados à pessoa
    processos_aluno = df[df['nome'] == nome_aluno]
    
    # Conta o total de processos distintos
    total_distintos = processos_aluno['processoNome'].nunique()  # Conta processos distintos
    
    return processos_aluno[['processoNome']], total_distintos

# Exemplo de uso no Streamlit
st.header("Pesquisa por nome da pessoa")

# Input para receber o nome da pessoa
nome_aluno = st.text_input("Informe o nome da pessoa para pesquisa:", "Laene de Melo Freitas Gouveia")

# Realiza a pesquisa e retorna os processos associados e o total de processos distintos
if nome_aluno:
    processos_associados, total_processos_distintos = listar_processos_por_aluno(df_merge, nome_aluno)
    
    # Verifica se a pessoa tem processos associados
    if not processos_associados.empty:
        st.success(f"Processos associados a {nome_aluno}:")
        st.dataframe(processos_associados, use_container_width=True)
        st.info(f'Total de processos distintos associados: {total_processos_distintos}')
    else:
        st.warning(f"Não foram encontrados processos associados a {nome_aluno}.")

