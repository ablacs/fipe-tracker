import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import data_processing as dp


# ── parse_price (função pura — sem mock) ─────────────────────────────────────

class TestParsePrice:
    def test_formato_padrao(self):
        assert dp.parse_price("R$ 85.000,00") == 85000.0

    def test_valor_sem_milhar(self):
        assert dp.parse_price("R$ 999,00") == 999.0

    def test_valor_grande(self):
        assert dp.parse_price("R$ 250.000,00") == 250000.0

    def test_valor_real(self):
        assert dp.parse_price("R$ 53.257,00") == 53257.0


# ── calculate_trend (função pura — sem mock) ──────────────────────────────────

class TestCalculateTrend:
    def test_retorna_none_com_um_registro(self):
        df = pd.DataFrame([{"data_coleta": "2026-06", "preco": 50000.0}])
        assert dp.calculate_trend(df) is None

    def test_detecta_queda_forte(self):
        df = pd.DataFrame([
            {"data_coleta": "2026-04", "preco": 90000.0},
            {"data_coleta": "2026-05", "preco": 80000.0},
            {"data_coleta": "2026-06", "preco": 70000.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "queda_forte"
        assert result["slope_pct"] < -2

    def test_detecta_alta(self):
        df = pd.DataFrame([
            {"data_coleta": "2026-04", "preco": 70000.0},
            {"data_coleta": "2026-05", "preco": 80000.0},
            {"data_coleta": "2026-06", "preco": 90000.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "alta"
        assert result["slope_pct"] > 0.5

    def test_gera_tres_meses_futuros(self):
        df = pd.DataFrame([
            {"data_coleta": "2026-05", "preco": 50000.0},
            {"data_coleta": "2026-06", "preco": 49000.0},
        ])
        result = dp.calculate_trend(df)
        assert len(result["future_months"]) == 3
        assert len(result["future_prices"]) == 3

    def test_virada_de_ano(self):
        df = pd.DataFrame([
            {"data_coleta": "2026-11", "preco": 50000.0},
            {"data_coleta": "2026-12", "preco": 49000.0},
        ])
        result = dp.calculate_trend(df)
        assert "2027-01" in result["future_months"]


# ── save_price (Supabase mockado) ─────────────────────────────────────────────

class TestSavePrice:
    @patch("data_processing.get_supabase")
    def test_chama_upsert_com_dados_corretos(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")

        mock_client.table.assert_called_with("historico")
        upsert_call = mock_client.table().upsert.call_args[0][0]
        assert upsert_call["marca"]  == "BMW"
        assert upsert_call["modelo"] == "330i"
        assert upsert_call["preco"]  == 85000.0

    @patch("data_processing.get_supabase")
    def test_converte_preco_corretamente(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        dp.save_price("VW", "Gol", "2019 Gasolina", "R$ 35.500,00")

        upsert_call = mock_client.table().upsert.call_args[0][0]
        assert upsert_call["preco"] == 35500.0


# ── track_vehicle (Supabase mockado) ─────────────────────────────────────────

class TestTrackVehicle:
    @patch("data_processing.get_supabase")
    def test_adiciona_veiculo_novo(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().execute.return_value = MagicMock(data=[])

        result = dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        assert result is True

    @patch("data_processing.get_supabase")
    def test_nao_duplica_veiculo_existente(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().execute.return_value = MagicMock(data=[{"id": 1}])

        result = dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        assert result is False


# ── load_history (Supabase mockado) ──────────────────────────────────────────

class TestLoadHistory:
    @patch("data_processing.get_supabase")
    def test_retorna_df_vazio_sem_dados(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().order().execute.return_value = MagicMock(data=[])

        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert df.empty

    @patch("data_processing.get_supabase")
    def test_calcula_depreciacao(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().order().execute.return_value = MagicMock(data=[
            {"data_coleta": "2026-04", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 90000.0},
            {"data_coleta": "2026-05", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 85000.0},
        ])

        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert "depreciacao_pct" in df.columns
        assert df.iloc[0]["depreciacao_pct"] == 0.0
        assert df.iloc[1]["depreciacao_pct"] < 0

    @patch("data_processing.get_supabase")
    def test_calcula_variacao_mensal(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().order().execute.return_value = MagicMock(data=[
            {"data_coleta": "2026-04", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 90000.0},
            {"data_coleta": "2026-05", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 85000.0},
        ])

        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert df.iloc[1]["variacao_mensal"] == -5000.0