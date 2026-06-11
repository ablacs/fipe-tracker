# tests/test_fipe_api.py
from unittest.mock import MagicMock, patch

import pytest

import fipe_api as api


class TestGetBrands:
    @patch("fipe_api.requests.get")
    def test_retorna_lista_de_marcas(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: [{"codigo": "59", "nome": "Volkswagen"}]
        )
        result = api.get_brands()
        assert isinstance(result, list)
        assert result[0]["nome"] == "Volkswagen"

    @patch("fipe_api.requests.get")
    def test_chama_endpoint_correto(self, mock_get):
        api.get_brands.clear()
        mock_get.return_value = MagicMock(json=lambda: [])
        api.get_brands()
        url_chamada = mock_get.call_args[0][0]
        assert "/carros/marcas" in url_chamada
    @patch("fipe_api.requests.get")
    def test_levanta_excecao_em_erro_http(self, mock_get):
        api.get_brands.clear()
        mock_get.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=Exception("500"))
        )
        with pytest.raises(Exception):
            api.get_brands()


class TestGetPrice:
    @patch("fipe_api.requests.get")
    def test_retorna_dicionario_com_valor(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: {"Valor": "R$ 53.257,00", "Marca": "BMW",
                          "Modelo": "330i", "MesReferencia": "junho de 2026"}
        )
        result = api.get_price("7", "3956", "2006-1")
        assert "Valor" in result
        assert result["Valor"] == "R$ 53.257,00"

    @patch("fipe_api.requests.get")
    def test_levanta_excecao_em_erro_http(self, mock_get):
        mock_get.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=Exception("404"))
        )
        with pytest.raises(Exception):
            api.get_price("999", "999", "999-1")