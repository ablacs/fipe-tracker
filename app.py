import streamlit as st
import fipe_api as api
import data_processing as dp
import charts

st.set_page_config(page_title="FIPE Tracker", page_icon="📉", layout="wide")
st.title("📉 FIPE Tracker — Histórico de Depreciação")

# ── Sidebar: seleção do veículo ──────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Selecionar Veículo")

    brands = api.get_brands()
    brand_names = [b["nome"] for b in brands]
    selected_brand_name = st.selectbox("Marca", brand_names)
    selected_brand = next(b for b in brands if b["nome"] == selected_brand_name)

    models = api.get_models(selected_brand["codigo"])
    model_names = [m["nome"] for m in models]
    selected_model_name = st.selectbox("Modelo", model_names)
    selected_model = next(m for m in models if m["nome"] == selected_model_name)

    years = api.get_years(selected_brand["codigo"], selected_model["codigo"])
    year_names = [y["nome"] for y in years]
    selected_year_name = st.selectbox("Ano/Combustível", year_names)
    selected_year = next(y for y in years if y["nome"] == selected_year_name)

    if st.button("💾 Registrar preço atual"):
        price_data = api.get_price(
            selected_brand["codigo"],
            selected_model["codigo"],
            selected_year["codigo"]
        )
        dp.save_price(
            selected_brand_name,
            selected_model_name,
            selected_year_name,
            price_data["Valor"]
        )
        st.success(f"Salvo: {price_data['Valor']}")

# ── Painel principal ─────────────────────────────────────────────────────────
price_data = api.get_price(
    selected_brand["codigo"],
    selected_model["codigo"],
    selected_year["codigo"]
)

col1, col2 = st.columns(2)
col1.metric("💰 Preço atual (FIPE)", price_data["Valor"])
col2.metric("📅 Referência", price_data.get("MesReferencia", "—"))

st.divider()

df = dp.load_history(selected_brand_name, selected_model_name, selected_year_name)
vehicle_label = f"{selected_brand_name} {selected_model_name} ({selected_year_name})"

if df.empty:
    st.info("Nenhum histórico ainda. Clique em **Registrar preço atual** para começar a construir o histórico.")
else:
    tab1, tab2, tab3 = st.tabs(["Evolução de Preço", "Depreciação", "Tabela"])

    with tab1:
        st.plotly_chart(charts.price_evolution_chart(df, vehicle_label), width="stretch")

    with tab2:
        st.plotly_chart(charts.depreciation_chart(df, vehicle_label), width="stretch")

    with tab3:
        st.dataframe(
            df[["data_coleta", "preco", "variacao_mensal", "depreciacao_pct"]],
            width="stretch"
        )