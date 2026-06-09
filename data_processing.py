import pandas as pd
from datetime import datetime
import json
import re
import io
import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY não configurados.")
    return create_client(url, key)


def parse_price(value_str: str) -> float:
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)


def save_price(brand: str, model: str, year: str, value_str: str) -> None:
    """Salva ou atualiza o preço do mês atual no Supabase."""
    supabase = get_supabase()
    preco = parse_price(value_str)
    row = {
        "data_coleta": datetime.today().strftime("%Y-%m"),
        "marca":  brand,
        "modelo": model,
        "ano":    year,
        "preco":  preco,
    }
    supabase.table("historico").upsert(
        row,
        on_conflict="data_coleta,marca,modelo,ano"
    ).execute()


def track_vehicle(
    brand_code: str, brand_name: str,
    model_code: str, model_name: str,
    year_code:  str, year_name:  str
) -> bool:
    """Adiciona veículo ao rastreamento. Retorna True se adicionou, False se já existia."""
    supabase = get_supabase()
    existing = (
        supabase.table("tracked_vehicles")
        .select("id")
        .eq("brand_code", brand_code)
        .eq("model_code", str(model_code))
        .eq("year_code",  year_code)
        .execute()
    )
    if existing.data:
        return False

    supabase.table("tracked_vehicles").insert({
        "brand_code": brand_code,
        "brand_name": brand_name,
        "model_code": str(model_code),
        "model_name": model_name,
        "year_code":  year_code,
        "year_name":  year_name,
    }).execute()
    return True


def get_tracked_vehicles() -> list[dict]:
    """Retorna lista de veículos rastreados do Supabase."""
    supabase = get_supabase()
    result = supabase.table("tracked_vehicles").select("*").execute()
    return result.data


def load_history(brand: str, model: str, year: str) -> pd.DataFrame:
    """Carrega histórico de preços filtrado por veículo."""
    supabase = get_supabase()
    result = (
        supabase.table("historico")
        .select("*")
        .eq("marca",  brand)
        .eq("modelo", model)
        .eq("ano",    year)
        .order("data_coleta")
        .execute()
    )
    if not result.data:
        return pd.DataFrame()

    df = pd.DataFrame(result.data)
    preco_inicial = df["preco"].iloc[0]
    df["depreciacao_pct"] = ((df["preco"] - preco_inicial) / preco_inicial * 100).round(2)
    df["variacao_mensal"] = df["preco"].diff().round(2)
    return df


def to_excel(df: pd.DataFrame) -> bytes:
    colunas = {
        "data_coleta":    "Mês",
        "marca":          "Marca",
        "modelo":         "Modelo",
        "ano":            "Ano/Combustível",
        "preco":          "Preço (R$)",
        "variacao_mensal":"Variação Mensal (R$)",
        "depreciacao_pct":"Depreciação Acumulada (%)",
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
    if len(df) < 2:
        return None

    x = np.arange(len(df))
    y = df["preco"].values
    slope, intercept = np.polyfit(x, y, 1)

    last = df["data_coleta"].iloc[-1]
    year, month = map(int, last.split("-"))
    future_months = []
    for i in range(1, 4):
        m = month + i
        y_adj = year + (m - 1) // 12
        m_adj = ((m - 1) % 12) + 1
        future_months.append(f"{y_adj}-{m_adj:02d}")

    future_x     = np.arange(len(df), len(df) + 3)
    future_prices = (slope * future_x + intercept).tolist()
    slope_pct     = (slope / df["preco"].iloc[-1]) * 100

    if slope_pct < -2:
        signal = "queda_forte"; icon = "⬇️"
        recommendation = "Preço em queda acentuada — considere esperar para comprar"
    elif slope_pct < -0.5:
        signal = "queda_leve"; icon = "📉"
        recommendation = "Preço em leve queda — bom momento para negociar"
    elif slope_pct < 0.5:
        signal = "estavel"; icon = "➡️"
        recommendation = "Preço estável — momento neutro para compra"
    else:
        signal = "alta"; icon = "📈"
        recommendation = "Preço em alta — compre agora se quiser garantir o valor"

    return {
        "slope_pct":     round(slope_pct, 2),
        "future_months": future_months,
        "future_prices": [round(p, 2) for p in future_prices],
        "signal":        signal,
        "icon":          icon,
        "recommendation": recommendation,
    }