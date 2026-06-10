import io
import os
import re
from datetime import datetime

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

from constants import (
    COL_ANO,
    COL_BRAND_CODE,
    COL_BRAND_NAME,
    COL_DATA_COLETA,
    COL_MARCA,
    COL_MODEL_CODE,
    COL_MODEL_NAME,
    COL_MODELO,
    COL_PRECO,
    COL_YEAR_CODE,
    COL_YEAR_NAME,
    TABLE_HISTORICO,
    TABLE_TRACKED,
)

load_dotenv()

# Thresholds de tendência de preço (% ao mês)
TREND_STRONG_DROP = -2.0  # queda acentuada: mais de 2% ao mês
TREND_MILD_DROP   = -0.5  # queda leve: entre 0.5% e 2% ao mês
TREND_MILD_RISE   =  0.5  # alta: mais de 0.5% ao mês


def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY não configurados.")
    return create_client(url, key)


def parse_price(value_str: str) -> float:
    """Converte 'R$ 85.000,00' → 85000.0"""
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)


def save_price(brand: str, model: str, year: str, value_str: str) -> None:
    """Salva ou atualiza o preço do mês atual no Supabase."""
    supabase = get_supabase()
    row = {
        COL_DATA_COLETA: datetime.today().strftime("%Y-%m"),
        COL_MARCA:       brand,
        COL_MODELO:      model,
        COL_ANO:         year,
        COL_PRECO:       parse_price(value_str),
    }
    supabase.table(TABLE_HISTORICO).upsert(
        row,
        on_conflict=f"{COL_DATA_COLETA},{COL_MARCA},{COL_MODELO},{COL_ANO}"
    ).execute()


def track_vehicle(
    brand_code: str, brand_name: str,
    model_code: str, model_name: str,
    year_code:  str, year_name:  str,
) -> bool:
    """Adiciona veículo ao rastreamento. Retorna True se adicionou, False se já existia."""
    supabase = get_supabase()
    existing = (
        supabase.table(TABLE_TRACKED)
        .select("id")
        .eq(COL_BRAND_CODE, brand_code)
        .eq(COL_MODEL_CODE, str(model_code))
        .eq(COL_YEAR_CODE,  year_code)
        .execute()
    )
    if existing.data:
        return False

    supabase.table(TABLE_TRACKED).insert({
        COL_BRAND_CODE: brand_code,
        COL_BRAND_NAME: brand_name,
        COL_MODEL_CODE: str(model_code),
        COL_MODEL_NAME: model_name,
        COL_YEAR_CODE:  year_code,
        COL_YEAR_NAME:  year_name,
    }).execute()
    return True


def get_tracked_vehicles() -> list[dict]:
    """Retorna lista de veículos rastreados do Supabase."""
    supabase = get_supabase()
    result = supabase.table(TABLE_TRACKED).select("*").execute()
    return result.data


def load_history(brand: str, model: str, year: str) -> pd.DataFrame:
    """Carrega histórico de preços filtrado por veículo."""
    supabase = get_supabase()
    result = (
        supabase.table(TABLE_HISTORICO)
        .select("*")
        .eq(COL_MARCA,  brand)
        .eq(COL_MODELO, model)
        .eq(COL_ANO,    year)
        .order(COL_DATA_COLETA)
        .execute()
    )
    if not result.data:
        return pd.DataFrame()

    df = pd.DataFrame(result.data)
    preco_inicial = df[COL_PRECO].iloc[0]
    df["depreciacao_pct"] = ((df[COL_PRECO] - preco_inicial) / preco_inicial * 100).round(2)
    df["variacao_mensal"] = df[COL_PRECO].diff().round(2)
    return df


def to_excel(df: pd.DataFrame) -> bytes:
    """Gera um arquivo Excel em memória e retorna os bytes para download."""
    colunas = {
        COL_DATA_COLETA:   "Mês",
        COL_MARCA:         "Marca",
        COL_MODELO:        "Modelo",
        COL_ANO:           "Ano/Combustível",
        COL_PRECO:         "Preço (R$)",
        "variacao_mensal": "Variação Mensal (R$)",
        "depreciacao_pct": "Depreciação Acumulada (%)",
    }
    df_export = df[[c for c in colunas if c in df.columns]].rename(columns=colunas)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Histórico")
        ws = writer.sheets["Histórico"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max_len + 4
    return buffer.getvalue()


def calculate_trend(df: pd.DataFrame) -> dict | None:
    """
    Regressão linear sobre o histórico de preços.
    Retorna projeção para 3 meses e recomendação de compra.
    Requer ao menos 2 pontos de histórico.
    """
    if len(df) < 2:
        return None

    x = np.arange(len(df))
    y = df[COL_PRECO].values
    slope, intercept = np.polyfit(x, y, 1)

    last = df[COL_DATA_COLETA].iloc[-1]
    year, month = map(int, last.split("-"))
    future_months = []
    for i in range(1, 4):
        m = month + i
        y_adj = year + (m - 1) // 12
        m_adj = ((m - 1) % 12) + 1
        future_months.append(f"{y_adj}-{m_adj:02d}")

    future_x      = np.arange(len(df), len(df) + 3)
    future_prices = (slope * future_x + intercept).tolist()
    slope_pct     = (slope / df[COL_PRECO].iloc[-1]) * 100

    if slope_pct < TREND_STRONG_DROP:
        signal = "queda_forte"
        recommendation = "Preço em queda acentuada — considere esperar para comprar"
    elif slope_pct < TREND_MILD_DROP:
        signal = "queda_leve"
        recommendation = "Preço em leve queda — bom momento para negociar"
    elif slope_pct < TREND_MILD_RISE:
        signal = "estavel"
        recommendation = "Preço estável — momento neutro para compra"
    else:
        signal = "alta"
        recommendation = "Preço em alta — compre agora se quiser garantir o valor"

    return {
        "slope_pct":     round(slope_pct, 2),
        "future_months": future_months,
        "future_prices": [round(p, 2) for p in future_prices],
        "signal":        signal,
        "recommendation": recommendation,
    }