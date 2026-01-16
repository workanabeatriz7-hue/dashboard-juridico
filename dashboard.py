import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Dashboard Jurídico", layout="wide")

# Link do seu Google Sheets (CSV)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhZkSAHlqT2Zd8WF1fB_qXsmXGLweLLfxbRknHuZam5O41fipcb1Gfn7PAh00OGaGOhTwFpc62n26t/pub?output=csv"

@st.cache_data
def load_data():
    # Carrega os dados
    df = pd.read_csv(URL)
    
    # COLUNAS QUE DEVEM SER NÚMEROS
    cols_financeiras = ["Valor Total", "Valor Escritório", "Valor Honorários", "Valor Principal"]
    
    for col in cols_financeiras:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace('R$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Converter datas (Colunas J, U, W)
    df['Data do Protocolo'] = pd.to_datetime(df['Data do Protocolo'], dayfirst=True, errors='coerce')
    df['Data MLE/Manifestação'] = pd.to_datetime(df['Data MLE/Manifestação'], dayfirst=True, errors='coerce')
    df['Data do recebimento'] = pd.to_datetime(df['Data do recebimento'], dayfirst=True, errors='coerce')
    
    # Garantir que colunas de filtro não tenham valores vazios
    df['Estado'] = df['Estado'].fillna('N/A')
    df['Protocolado'] = df['Protocolado'].fillna('Não')
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")

# 1. Filtros de Data (J, U, W)
st.sidebar.subheader("📅 Períodos")
def sidebar_date(label, col):
    min_d, max_d = df[col].min(), df[col].max()
    if pd.isnull(min_d): min_d = datetime.today()
    if pd.isnull(max_d): max_d = datetime.today()
    return st.sidebar.date_input(label, [min_d, max_d])

f_prot = sidebar_date("Data do Protocolo (J)", "Data do Protocolo")
f_mle = sidebar_date("Data MLE/Manifestação (U)", "Data MLE/Manifestação")
f_rec = sidebar_date("Data do recebimento (W)", "Data do recebimento")

# 2. Filtros de Status Sim/Não (K, S, T, V, X)
st.sidebar.subheader("📌 Status Processuais")
status_map = {
    "Inserido no Astrea (K)": "Inserido no Astrea",
    "Pagto nos autos (S)": "Pagto nos autos",
    "MLE / Manifestação (T)": "MLE / Manifestação",
    "Pagto Recebido (V)": "Pagto Recebido",
    "cliente atualizado (X)": "cliente atualizado"
}

selecoes_status = {}
for label, col in status_map.items():
    if col in df.columns:
        opcoes = ["Todos"] + sorted(list(df[col].dropna().unique()))
        selecoes_status[col] = st.sidebar.selectbox(label, opcoes)

# 3. Filtros Originais
estados = st.sidebar.multiselect("Selecione o Estado:", options=sorted(df["Estado"].unique()), default=df["Estado"].unique())
protocolado_filtro = st.sidebar.multiselect("Protocolado:", options=df["Protocolado"].unique(), default=df["Protocolado"].unique())

# --- APLICAR TODOS OS FILTROS ---
df_filtrado = df.copy()

# Filtro de Estado e Protocolado
df_filtrado = df_filtrado[df_filtrado["Estado"].isin(estados) & df_filtrado["Protocolado"].isin(protocolado_filtro)]

# Filtro das colunas K, S, T, V, X
for col, val in selecoes_status.items():
    if val != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col] == val]

# Filtro de Datas
for col, sel in [("Data do Protocolo", f_prot), ("Data MLE/Manifestação", f_mle), ("Data do recebimento", f_rec)]:
    if len(sel) == 2:
        df_filtrado = df_filtrado[(df_filtrado[col] >= pd.Timestamp(sel[0])) & (df_filtrado[col] <= pd.Timestamp(sel[1]))]

# --- CABEÇALHO ---
st.title("📊 Dashboard Estratégico - Juros Abusivos")
st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)

total_geral = df_filtrado["Valor Total"].sum()
total_escritorio = df_filtrado["Valor Escritório"].sum()
qtd_processos = len(df_filtrado)
qtd_protocolados = len(df_filtrado[df_filtrado["Protocolado"] == "Sim"])

with col1:
    st.metric("Valor Total Geral", f"R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
with col2:
    st.metric("Total Escritório", f"R$ {total_escritorio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
with col3:
    st.metric("Total Processos", qtd_processos)
with col4:
    st.metric("Protocolados", qtd_protocolados)

# --- GRÁFICOS ---
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Evolução Financeira")
    df_evolucao = df_filtrado.dropna(subset=['Data do Protocolo']).sort_values("Data do Protocolo")
    if not df_evolucao.empty:
        fig_evolucao = px.line(df_evolucao, x="Data do Protocolo", y="Valor Total", title="Soma de Valor por Data")
        st.plotly_chart(fig_evolucao, use_container_width=True)
    else:
        st.write("Sem dados de data para exibir o gráfico.")

with c2:
    st.subheader("Volume por Estado")
    fig_estado = px.bar(df_filtrado, x="Estado", y="Valor Total", color="Estado", title="Total por UF")
    st.plotly_chart(fig_estado, use_container_width=True)

# --- TABELA DE RANKING (TOP 10) ---
st.subheader("Ranking de Processos (Top 10 Maiores Valores)")
df_ranking = df_filtrado[["Número do processo", "Estado", "Valor Total"]].sort_values(by="Valor Total", ascending=False).head(10)
# Formatar valor para R$ na tabela
df_ranking["Valor Total"] = df_ranking["Valor Total"].apply(lambda x: f"R$ {x:,.2f}")
st.dataframe(df_ranking, use_container_width=True)
