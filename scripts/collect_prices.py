# scripts/collect_prices.py
import sys
from pathlib import Path

# Permite importar os módulos da raiz do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import pandas as pd
import json
import re
from datetime import datetime

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"
HISTORY_FILE = Path("historico.csv")
TRACKED_FILE = Path("tracked_vehicles.json")

def parse_price(value_str: str) -> float:
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)

def collect():
    if not TRACKED_FILE.exists():
        print("tracked_vehicles.json não encontrado — nenhum veículo rastreado ainda.")
        return

    with open(TRACKED_FILE) as f:
        vehicles = json.load(f)

    if not vehicles:
        print("Nenhum veículo na lista de rastreamento.")
        return

    rows = []
    for v in vehicles:
        try:
            url = f"{BASE_URL}/marcas/{v['brand_code']}/modelos/{v['model_code']}/anos/{v['year_code']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            rows.append({
                "data_coleta": datetime.today().strftime("%Y-%m"),
                "marca":  v["brand_name"],
                "modelo": v["model_name"],
                "ano":    v["year_name"],
                "preco":  parse_price(data["Valor"]),
            })
            print(f"✓ {v['brand_name']} {v['model_name']} {v['year_name']}: {data['Valor']}")
        except Exception as e:
            print(f"✗ Erro em {v['brand_name']} {v['model_name']}: {e}")

    if not rows:
        print("Nenhum preço coletado.")
        return

    df_new = pd.DataFrame(rows)

    if HISTORY_FILE.exists():
        df_existing = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df_existing, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["data_coleta", "marca", "modelo", "ano"], keep="last")
    else:
        df = df_new

    df.to_csv(HISTORY_FILE, index=False)
    print(f"\nHistórico atualizado: {len(df)} registros no total.")

if __name__ == "__main__":
    collect()