import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import re

import requests
from dotenv import load_dotenv

import data_processing as dp

load_dotenv()

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

def parse_price(value_str: str) -> float:
    cleaned = re.sub(r"[R$\s.]", "", value_str).replace(",", ".")
    return float(cleaned)

def collect():
    vehicles = dp.get_tracked_vehicles()
    if not vehicles:
        print("Nenhum veículo rastreado.")
        return

    for v in vehicles:
        try:
            url = f"{BASE_URL}/marcas/{v['brand_code']}/modelos/{v['model_code']}/anos/{v['year_code']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            dp.save_price(v["brand_name"], v["model_name"], v["year_name"], data["Valor"])
            print(f"✓ {v['brand_name']} {v['model_name']}: {data['Valor']}")
        except Exception as e:
            print(f"✗ Erro em {v['brand_name']} {v['model_name']}: {e}")

if __name__ == "__main__":
    collect()