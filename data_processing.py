import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import re
import io

import numpy as np

HISTORY_FILE = Path("historico.csv")
TRACKED_FILE = Path("tracked_vehicles.json")

def parse_price(value_str: str) -> float:
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)

def save_price(brand: str, model: str, year: str, value_str: str) -> None:
    price = parse_price(value_str)
    row = {
        "data_coleta": datetime.today().strftime("%Y-%m"),
        "marca": brand,
        "modelo": model,
        "ano": year,
        "preco": price,
    }
    df_new = pd.DataFrame([row])

    if HISTORY_FILE.exists():
        df_existing = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df_existing, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["data_coleta", "marca", "modelo", "ano"], keep="last")
    else:
        df = df_new

    df.to_csv(HISTORY_FILE, index=False)

def track_vehicle(
    brand_code: str, brand_name: str,
    model_code: str, model_name: str,
    year_code: str, year_name: str
) -> bool:
    """Adiciona veículo ao JSON de rastreamento. Retorna True se adicionou, False se já existia."""
    vehicle = {
        "brand_code": brand_code, "brand_name": brand_name,
        "model_code": model_code, "model_name": model_name,
        "year_code": year_code,   "year_name": year_name,
    }

    vehicles = []
    if TRACKED_FILE.exists():
        with open(TRACKED_FILE) as f:
            vehicles = json.load(f)

    already_tracked = any(
        v["brand_code"] == brand_code and
        v["model_code"] == model_code and
        v["year_code"] == year_code
        for v in vehicles
    )

    if not already_tracked:
        vehicles.append(vehicle)
        with open(TRACKED_FILE, "w") as f:
            json.dump(vehicles, f, ensure_ascii=False, indent=2)
        return True

    return False

def load_history(brand: str, model: str, year: str) -> pd.DataFrame:
    if not HISTORY_FILE.exists():
        return pd.DataFrame()

    df = pd.read_csv(HISTORY_FILE)
    mask = (df["marca"] == brand) & (df["modelo"] == model) & (df["ano"] == year)
    df = df[mask].copy().sort_values("data_coleta")

    if not df.empty:
        preco_inicial = df["preco"].iloc[0]
        df["depreciacao_pct"] = ((df["preco"] - preco_inicial) / preco_inicial * 100).round(2)
        df["variacao_mensal"] = df["preco"].diff().round(2)

    return df

import io

def to_excel(df: pd.DataFrame) -> bytes:
    """Gera um arquivo Excel em memória e retorna os bytes para download."""
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

        # Ajusta largura das colunas automaticamente
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
    y = df["preco"].values
    slope, intercept = np.polyfit(x, y, 1)

    # Gera os próximos 3 meses como strings "YYYY-MM"
    last = df["data_coleta"].iloc[-1]
    year, month = map(int, last.split("-"))
    future_months = []
    for i in range(1, 4):
        m = month + i
        y_adj = year + (m - 1) // 12
        m_adj = ((m - 1) % 12) + 1
        future_months.append(f"{y_adj}-{m_adj:02d}")

    future_x = np.arange(len(df), len(df) + 3)
    future_prices = (slope * future_x + intercept).tolist()

    # Slope como % do preço atual por mês
    slope_pct = (slope / df["preco"].iloc[-1]) * 100

    if slope_pct < -2:
        signal      = "queda_forte"
        icon        = "⬇️"
        recommendation = "Preço em queda acentuada — considere esperar para comprar"
    elif slope_pct < -0.5:
        signal      = "queda_leve"
        icon        = "📉"
        recommendation = "Preço em leve queda — bom momento para negociar"
    elif slope_pct < 0.5:
        signal      = "estavel"
        icon        = "➡️"
        recommendation = "Preço estável — momento neutro para compra"
    else:
        signal      = "alta"
        icon        = "📈"
        recommendation = "Preço em alta — compre agora se quiser garantir o valor"

    return {
        "slope_pct":     round(slope_pct, 2),
        "future_months": future_months,
        "future_prices": [round(p, 2) for p in future_prices],
        "signal":        signal,
        "icon":          icon,
        "recommendation": recommendation,
    }