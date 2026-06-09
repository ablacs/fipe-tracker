import streamlit as st
import plotly.graph_objects as go
import json
from pathlib import Path
import fipe_api as api
import data_processing as dp
import charts

st.set_page_config(page_title="Comparar — FIPE Tracker", page_icon="⚖️", layout="wide")
st.title("⚖️ Comparar Veículos")

TRACKED_FILE = Path("tracked_vehicles.json")

if not TRACKED_FILE.exists():
    st.info("Nenhum veículo rastreado ainda. Registre veículos em **Detalhes** primeiro.")
    st.stop()

with open(TRACKED_FILE) as f:
    vehicles = json.load(f)

if len(vehicles) < 2:
    st.info("Você precisa de ao menos 2 veículos rastreados para comparar. Adicione mais em **Detalhes**.")
    st.stop()

def make_label(v):
    return f"{v['brand_name']} {v['model_name']} ({v['year_name']})"

labels = [make_label(v) for v in vehicles]

with st.sidebar:
    st.header("Selecionar veículos")
    label1 = st.selectbox("Veículo 1", labels, index=0, key="v1")
    label2 = st.selectbox("Veículo 2", labels, index=min(1, len(labels)-1), key="v2")

v1 = vehicles[labels.index(label1)]
v2 = vehicles[labels.index(label2)]

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown(f"**🚗 {label1}**")
        try:
            price1 = api.get_price(str(v1['brand_code']), str(v1['model_code']), str(v1['year_code']))
            st.metric("Preço FIPE atual", price1["Valor"])
            st.caption(f"Referência: {price1.get('MesReferencia', '—')}")
        except Exception:
            st.error("Preço indisponível")

with col2:
    with st.container(border=True):
        st.markdown(f"**🚙 {label2}**")
        try:
            price2 = api.get_price(str(v2['brand_code']), str(v2['model_code']), str(v2['year_code']))
            st.metric("Preço FIPE atual", price2["Valor"])
            st.caption(f"Referência: {price2.get('MesReferencia', '—')}")
        except Exception:
            st.error("Preço indisponível")

st.divider()

df1 = dp.load_history(v1['brand_name'], v1['model_name'], v1['year_name'])
df2 = dp.load_history(v2['brand_name'], v2['model_name'], v2['year_name'])

if df1.empty and df2.empty:
    st.info("Nenhum dos veículos tem histórico. Registre preços em **Detalhes** primeiro.")
    st.stop()

if df1.empty:
    st.warning(f"**{label1}** ainda não tem histórico registrado.")
if df2.empty:
    st.warning(f"**{label2}** ainda não tem histórico registrado.")

if not df1.empty and not df2.empty:
    tab1, tab2 = st.tabs(["Depreciação comparada", "Evolução de preço"])

    with tab1:
        st.plotly_chart(
            charts.comparison_chart(df1, label1, df2, label2),
            width='stretch'
        )

    with tab2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df1["data_coleta"], y=df1["preco"],
            name=label1, mode="lines+markers"
        ))
        fig.add_trace(go.Scatter(
            x=df2["data_coleta"], y=df2["preco"],
            name=label2, mode="lines+markers"
        ))
        fig.update_layout(
            title="Evolução de Preço",
            xaxis_title="Mês",
            yaxis_title="Preço (R$)"
        )
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, width='stretch')