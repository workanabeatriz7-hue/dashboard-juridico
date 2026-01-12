import streamlit as st
import pandas as pd
import plotly.express as px

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
            # Limpeza: Remove R$, pontos de milhar, troca vírgula por ponto e remove espaços
            df[col] = (
                df[col].astype(str)
                .str.replace('R$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            # Converte para número real (float). O que não for número vira 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Converter datas
    df['Data do Protocolo'] = pd.to_datetime(df['Data do Protocolo'], errors='coerce')
    
    # Garantir que Estado e Protocolado não tenham valores vazios para os filtros
    df['Estado'] = df['Estado'].fillna('N/A')
    df['Protocolado'] = df['Protocolado'].fillna('Não')
    
    return df

# Carregar os dados limpos
try:
    df = load_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")
estados = st.sidebar.multiselect("Selecione o Estado:", options=sorted(df["Estado"].unique()), default=df["Estado"].unique())
status = st.sidebar.multiselect("Protocolado:", options=df["Protocolado"].unique(), default=df["Protocolado"].unique())

# Aplicar filtros
df_filtrado = df[df["Estado"].isin(estados) & df["Protocolado"].isin(status)]

# --- CABEÇALHO ---
st.title("📊 Dashboard Estratégico - Juros Abusivos")
st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)

# Agora os cálculos não darão erro de "str"
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

# --- TABELA DE RANKING ---
st.subheader("Ranking de Processos (Top 10 Maiores Valores)")
st.dataframe(df_filtrado[["Número do processo", "Estado", "Valor Total"]].sort_values(by="Valor Total", ascending=False).head(10), use_container_width=True)