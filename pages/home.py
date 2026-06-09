import streamlit as st
import json
from pathlib import Path
import plotly.graph_objects as go
import fipe_api as api
import data_processing as dp

st.title("📉 FIPE Tracker")
st.caption("Acompanhamento histórico de depreciação — Tabela FIPE")

TRACKED_FILE = Path("tracked_vehicles.json")

if not TRACKED_FILE.exists():
    st.info("Nenhum veículo rastreado ainda. Acesse **Registrar** na barra lateral para adicionar o primeiro.")
    st.stop()

with open(TRACKED_FILE) as f:
    vehicles = json.load(f)

if not vehicles:
    st.info("Nenhum veículo rastreado ainda. Acesse **Registrar** na barra lateral para adicionar o primeiro.")
    st.stop()

n = len(vehicles)
st.subheader(f"🚗 {n} veículo{'s' if n > 1 else ''} rastreado{'s' if n > 1 else ''}")
st.divider()

cols = st.columns(3)

for i, v in enumerate(vehicles):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"#### {v['brand_name']} {v['model_name']}")
            st.caption(v['year_name'])

            try:
                price_data = api.get_price(
                    str(v['brand_code']),
                    str(v['model_code']),
                    str(v['year_code'])
                )
                current_price = price_data['Valor']
            except Exception:
                current_price = "Indisponível"

            df = dp.load_history(v['brand_name'], v['model_name'], v['year_name'])

            if not df.empty and len(df) >= 2:
                delta_pct = df['depreciacao_pct'].iloc[-1]
                st.metric("Preço FIPE", current_price, delta=f"{delta_pct:+.1f}% acumulado", delta_color="inverse")

                fig = go.Figure(go.Scatter(
                    x=df['data_coleta'], y=df['preco'],
                    mode='lines+markers',
                    line=dict(color='#2563EB', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(37,99,235,0.1)'
                ))
                fig.update_layout(
                    height=100,
                    margin=dict(l=0, r=0, t=4, b=0),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                )
                st.plotly_chart(fig, width='stretch', key=f"spark_{i}")
            else:
                st.metric("Preço FIPE", current_price)
                st.caption("📊 Registre ao menos 2 meses para ver o gráfico")