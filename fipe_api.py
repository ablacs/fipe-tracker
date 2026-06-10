import requests
import streamlit as st

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

@st.cache_data(ttl=86400)
def get_brands() -> list[dict]:
    """Retorna lista de marcas: [{ 'codigo': '59', 'nome': 'Volkswagen' }, ...]"""
    response = requests.get(f"{BASE_URL}/marcas")
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=86400)
def get_models(brand_code: str) -> list[dict]:
    """Retorna modelos de uma marca."""
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos")
    response.raise_for_status()
    return response.json()["modelos"]

@st.cache_data(ttl=86400)
def get_years(brand_code: str, model_code: str) -> list[dict]:
    """Retorna anos/combustíveis disponíveis para um modelo."""
    response = requests.get(
        f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos"
    )
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=3600)
def get_price(brand_code: str, model_code: str, year_code: str) -> dict:
    """
    Retorna o preço atual do veículo.
    Exemplo de retorno:
      { 'Valor': 'R$ 85.000,00', 'Marca': 'Volkswagen', 'Modelo': 'Golf', ... }
    """
    response = requests.get(
        f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}"
    )
    response.raise_for_status()
    return response.json()