import streamlit as st

import data_processing as dp
import fipe_api as api

st.title("➕ Adicionar Veículo")
st.caption("Busque um veículo na Tabela FIPE e adicione ao rastreamento.")

with st.sidebar:
    st.header("Buscar Veículo")

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

try:
    price_data = api.get_price(
        selected_brand["codigo"],
        selected_model["codigo"],
        selected_year["codigo"]
    )
    col1, col2 = st.columns(2)
    col1.metric("💰 Preço atual (FIPE)", price_data["Valor"])
    col2.metric("📅 Referência", price_data.get("MesReferencia", "—"))

    st.divider()

    if st.button("💾 Adicionar ao rastreamento", type="primary"):
        dp.save_price(
            selected_brand_name,
            selected_model_name,
            selected_year_name,
            price_data["Valor"]
        )
        added = dp.track_vehicle(
            selected_brand["codigo"], selected_brand_name,
            selected_model["codigo"], selected_model_name,
            selected_year["codigo"], selected_year_name,
        )
        if added:
            st.success(f"✅ {selected_brand_name} {selected_model_name} adicionado! Acesse **Histórico** para acompanhar.")
        else:
            st.info("Este veículo já está no rastreamento.")

except Exception:
    st.error("Não foi possível buscar o preço. Tente outro veículo.")