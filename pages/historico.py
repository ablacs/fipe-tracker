import streamlit as st

import charts
import data_processing as dp
import fipe_api as api

vehicles = dp.get_tracked_vehicles()

if not vehicles:
    st.info("Nenhum veículo cadastrado ainda. Acesse **Adicionar** para começar.")
    st.stop()

def make_label(v: dict) -> str:
    return f"{v['brand_name']} {v['model_name']} ({v['year_name']})"

labels = [make_label(v) for v in vehicles]

with st.sidebar:
    st.header("Selecionar Veículo")
    selected_label = st.selectbox("Veículo", labels)
    v = vehicles[labels.index(selected_label)]

    if st.button("💾 Registrar preço atual"):
        price_data = api.get_price(
            str(v["brand_code"]),
            str(v["model_code"]),
            str(v["year_code"])
        )
        dp.save_price(v["brand_name"], v["model_name"], v["year_name"], price_data["Valor"])
        st.success(f"Salvo: {price_data['Valor']}")

st.title("📋 Histórico")

try:
    price_data = api.get_price(
        str(v["brand_code"]),
        str(v["model_code"]),
        str(v["year_code"])
    )
    col1, col2 = st.columns(2)
    col1.metric("💰 Preço atual (FIPE)", price_data["Valor"])
    col2.metric("📅 Referência", price_data.get("MesReferencia", "—"))
except Exception:
    st.error("Não foi possível buscar o preço atual.")

st.divider()

df = dp.load_history(v["brand_name"], v["model_name"], v["year_name"])
vehicle_label = make_label(v)

if df.empty:
    st.info("Nenhum histórico ainda. Clique em **Registrar preço atual** para começar.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["Evolução de Preço", "Depreciação", "Tabela", "📊 Análise"])

    with tab1:
        st.plotly_chart(charts.price_evolution_chart(df, vehicle_label), width='stretch')

    with tab2:
        st.plotly_chart(charts.depreciation_chart(df, vehicle_label), width='stretch')

    with tab3:
        st.dataframe(
            df[["data_coleta", "preco", "variacao_mensal", "depreciacao_pct"]],
            width='stretch'
        )
        nome_arquivo = (
            f"fipe_{v['brand_name']}_{v['model_name']}_{v['year_name']}"
            .replace(" ", "_").replace("/", "-") + ".xlsx"
        )
        st.download_button(
            label="📥 Exportar para Excel",
            data=dp.to_excel(df),
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab4:
        trend = dp.calculate_trend(df)
        if trend is None:
            st.info("Registre ao menos 2 meses de histórico para gerar a análise de tendência.")
        else:
            cor = {
                "queda_forte": "inverse",
                "queda_leve":  "inverse",
                "estavel":     "off",
                "alta":        "normal",
            }[trend["signal"]]

            col_a, col_b = st.columns(2)
            col_a.metric(
                "Tendência mensal",
                f"{trend['slope_pct']:+.2f}% / mês",
                delta=trend["icon"] + " " + trend["recommendation"],
                delta_color=cor
            )
            col_b.metric(
                "Preço projetado (3 meses)",
                f"R$ {trend['future_prices'][-1]:,.2f}"
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
            st.plotly_chart(
                charts.price_with_projection_chart(
                    df, trend["future_months"], trend["future_prices"], vehicle_label
                ),
                width='stretch'
            )
            st.caption(
                "⚠️ Projeção baseada em regressão linear sobre o histórico disponível. "
                "Quanto mais meses de dados, mais precisa a projeção."
            )