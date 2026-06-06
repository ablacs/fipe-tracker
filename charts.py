import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def price_evolution_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Gráfico de linha: evolução do preço ao longo dos meses."""
    fig = px.line(
        df,
        x="data_coleta",
        y="preco",
        title=title,
        markers=True,
        labels={"data_coleta": "Mês", "preco": "Preço (R$)"},
    )
    fig.update_traces(line_color="#2563EB")
    return fig

def depreciation_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Gráfico de área: depreciação percentual acumulada."""
    fig = px.area(
        df,
        x="data_coleta",
        y="depreciacao_pct",
        title=title,
        labels={"data_coleta": "Mês", "depreciacao_pct": "Variação acumulada (%)"},
    )
    fig.update_traces(line_color="#DC2626", fillcolor="rgba(220,38,38,0.15)")
    return fig

def comparison_chart(df1: pd.DataFrame, label1: str, df2: pd.DataFrame, label2: str) -> go.Figure:
    """Sobrepõe a depreciação de dois veículos num mesmo gráfico."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df1["data_coleta"], y=df1["depreciacao_pct"],
        name=label1, mode="lines+markers"
    ))
    fig.add_trace(go.Scatter(
        x=df2["data_coleta"], y=df2["depreciacao_pct"],
        name=label2, mode="lines+markers"
    ))
    fig.update_layout(
        title="Comparação de Depreciação",
        xaxis_title="Mês",
        yaxis_title="Variação acumulada (%)"
    )
    return fig