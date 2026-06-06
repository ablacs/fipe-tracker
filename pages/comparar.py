import streamlit as st
import plotly.graph_objects as go
import fipe_api as api
import data_processing as dp
import charts

st.set_page_config(page_title="Comparar — FIPE Tracker", page_icon="⚖️", layout="wide")
st.title("⚖️ Comparar Veículos")

brands = api.get_brands()
brand_names = [b["nome"] for b in brands]

# ── Sidebar: dois seletores ───────────────────────────────────────────────────
with st.sidebar:
    st.header("🚗 Veículo 1")
    brand1_name = st.selectbox("Marca", brand_names, key="brand1")
    brand1 = next(b for b in brands if b["nome"] == brand1_name)

    models1 = api.get_models(brand1["codigo"])
    model1_name = st.selectbox("Modelo", [m["nome"] for m in models1], key="model1")
    model1 = next(m for m in models1 if m["nome"] == model1_name)

    years1 = api.get_years(brand1["codigo"], model1["codigo"])
    year1_name = st.selectbox("Ano/Combustível", [y["nome"] for y in years1], key="year1")
    year1 = next(y for y in years1 if y["nome"] == year1_name)

    st.divider()

    st.header("🚙 Veículo 2")
    brand2_name = st.selectbox("Marca", brand_names, key="brand2")
    brand2 = next(b for b in brands if b["nome"] == brand2_name)

    models2 = api.get_models(brand2["codigo"])
    model2_name = st.selectbox("Modelo", [m["nome"] for m in models2], key="model2")
    model2 = next(m for m in models2 if m["nome"] == model2_name)

    years2 = api.get_years(brand2["codigo"], model2["codigo"])
    year2_name = st.selectbox("Ano/Combustível", [y["nome"] for y in years2], key="year2")
    year2 = next(y for y in years2 if y["nome"] == year2_name)

# ── Preços atuais ─────────────────────────────────────────────────────────────
label1 = f"{brand1_name} {model1_name} ({year1_name})"
label2 = f"{brand2_name} {model2_name} ({year2_name})"

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown(f"**🚗 {label1}**")
        try:
            price1 = api.get_price(brand1["codigo"], model1["codigo"], year1["codigo"])
            st.metric("Preço FIPE atual", price1["Valor"])
            st.caption(f"Referência: {price1.get('MesReferencia', '—')}")
        except Exception:
            st.error("Preço indisponível")

with col2:
    with st.container(border=True):
        st.markdown(f"**🚙 {label2}**")
        try:
            price2 = api.get_price(brand2["codigo"], model2["codigo"], year2["codigo"])
            st.metric("Preço FIPE atual", price2["Valor"])
            st.caption(f"Referência: {price2.get('MesReferencia', '—')}")
        except Exception:
            st.error("Preço indisponível")

st.divider()

# ── Gráficos comparativos ─────────────────────────────────────────────────────
df1 = dp.load_history(brand1_name, model1_name, year1_name)
df2 = dp.load_history(brand2_name, model2_name, year2_name)

sem_historico1 = df1.empty
sem_historico2 = df2.empty

if sem_historico1 and sem_historico2:
    st.info("Nenhum dos veículos tem histórico. Registre preços em **Detalhes** primeiro.")
    st.stop()

if sem_historico1:
    st.warning(f"**{label1}** ainda não tem histórico. Registre em Detalhes para incluir na comparação.")
if sem_historico2:
    st.warning(f"**{label2}** ainda não tem histórico. Registre em Detalhes para incluir na comparação.")

if not sem_historico1 and not sem_historico2:
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
        st.plotly_chart(fig, width='stretch')