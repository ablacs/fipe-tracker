import pandas as pd
from pathlib import Path
from datetime import datetime
import re

HISTORY_FILE = Path("historico.csv")

def parse_price(value_str: str) -> float:
    """Converte 'R$ 85.000,00' → 85000.0"""
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)

def save_price(brand: str, model: str, year: str, value_str: str) -> None:
    """Adiciona uma linha ao CSV histórico."""
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
        # Evita duplicatas da mesma coleta mensal
        df = df.drop_duplicates(subset=["data_coleta", "marca", "modelo", "ano"], keep="last")
    else:
        df = df_new

    df.to_csv(HISTORY_FILE, index=False)

def load_history(brand: str, model: str, year: str) -> pd.DataFrame:
    """Carrega histórico filtrado por veículo."""
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