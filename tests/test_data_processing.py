import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import data_processing as dp
from constants import (
    COL_ANO, TABLE_HISTORICO, TABLE_TRACKED,
    COL_MARCA, COL_MODELO, COL_PRECO, COL_DATA_COLETA,
)


# ── parse_price ───────────────────────────────────────────────────────────────

class TestParsePrice:
    def test_formato_padrao(self):
        assert dp.parse_price("R$ 85.000,00") == 85000.0

    def test_valor_sem_milhar(self):
        assert dp.parse_price("R$ 999,00") == 999.0

    def test_valor_grande(self):
        assert dp.parse_price("R$ 250.000,00") == 250000.0

    def test_valor_real(self):
        assert dp.parse_price("R$ 53.257,00") == 53257.0

    def test_valor_com_centavos(self):
        assert dp.parse_price("R$ 35.500,50") == 35500.50


# ── calculate_trend ───────────────────────────────────────────────────────────

class TestCalculateTrend:
    def test_retorna_none_com_um_registro(self):
        df = pd.DataFrame([{COL_DATA_COLETA: "2026-06", COL_PRECO: 50000.0}])
        assert dp.calculate_trend(df) is None

    def test_detecta_queda_forte(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-04", COL_PRECO: 90000.0},
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 80000.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 70000.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "queda_forte"
        assert result["slope_pct"] < dp.TREND_STRONG_DROP

    def test_detecta_queda_leve(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-04", COL_PRECO: 50000.0},
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 49700.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 49400.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "queda_leve"
        assert dp.TREND_STRONG_DROP <= result["slope_pct"] < dp.TREND_MILD_DROP

    def test_detecta_estavel(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-04", COL_PRECO: 50000.0},
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 50010.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 49990.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "estavel"

    def test_detecta_alta(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-04", COL_PRECO: 70000.0},
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 80000.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 90000.0},
        ])
        result = dp.calculate_trend(df)
        assert result["signal"] == "alta"
        assert result["slope_pct"] > dp.TREND_MILD_RISE

    def test_gera_tres_meses_futuros(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 50000.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 49000.0},
        ])
        result = dp.calculate_trend(df)
        assert len(result["future_months"]) == 3
        assert len(result["future_prices"]) == 3

    def test_virada_de_ano(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-11", COL_PRECO: 50000.0},
            {COL_DATA_COLETA: "2026-12", COL_PRECO: 49000.0},
        ])
        result = dp.calculate_trend(df)
        assert "2027-01" in result["future_months"]
        assert "2027-02" in result["future_months"]
        assert "2027-03" in result["future_months"]

    def test_retorna_todos_os_campos(self):
        df = pd.DataFrame([
            {COL_DATA_COLETA: "2026-05", COL_PRECO: 50000.0},
            {COL_DATA_COLETA: "2026-06", COL_PRECO: 49000.0},
        ])
        result = dp.calculate_trend(df)
        assert all(k in result for k in [
            "slope_pct", "future_months", "future_prices",
            "signal", "icon", "recommendation"
        ])


# ── save_price ────────────────────────────────────────────────────────────────

class TestSavePrice:
    @patch("data_processing.get_supabase")
    def test_chama_upsert_com_dados_corretos(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")

        mock_client.table.assert_called_with(TABLE_HISTORICO)
        upsert_call = mock_client.table().upsert.call_args[0][0]
        assert upsert_call[COL_MARCA]  == "BMW"
        assert upsert_call[COL_MODELO] == "330i"
        assert upsert_call[COL_PRECO]  == 85000.0

    @patch("data_processing.get_supabase")
    def test_data_coleta_formato_ano_mes(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        dp.save_price("VW", "Gol", "2019 Gasolina", "R$ 30.000,00")

        upsert_call = mock_client.table().upsert.call_args[0][0]
        data = upsert_call[COL_DATA_COLETA]
        assert len(data) == 7           # "YYYY-MM"
        assert data[4] == "-"
        assert data[:4].isdigit()
        assert data[5:].isdigit()

    @patch("data_processing.get_supabase")
    def test_converte_preco_corretamente(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        dp.save_price("VW", "Gol", "2019 Gasolina", "R$ 35.500,00")

        upsert_call = mock_client.table().upsert.call_args[0][0]
        assert upsert_call[COL_PRECO] == 35500.0


# ── track_vehicle ─────────────────────────────────────────────────────────────

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

    @patch("data_processing.get_supabase")
    def test_chama_tabela_correta(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().execute.return_value = MagicMock(data=[])

        dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        mock_client.table.assert_called_with(TABLE_TRACKED)


# ── load_history ──────────────────────────────────────────────────────────────

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
            {COL_DATA_COLETA: "2026-04", COL_MARCA: "BMW", COL_MODELO: "330i",
             COL_ANO: "2020 Gasolina", COL_PRECO: 90000.0},
            {COL_DATA_COLETA: "2026-05", COL_MARCA: "BMW", COL_MODELO: "330i",
             COL_ANO: "2020 Gasolina", COL_PRECO: 85000.0},
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
            {COL_DATA_COLETA: "2026-04", COL_MARCA: "BMW", COL_MODELO: "330i",
             COL_ANO: "2020 Gasolina", COL_PRECO: 90000.0},
            {COL_DATA_COLETA: "2026-05", COL_MARCA: "BMW", COL_MODELO: "330i",
             COL_ANO: "2020 Gasolina", COL_PRECO: 85000.0},
        ])
        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert df.iloc[1]["variacao_mensal"] == -5000.0

    @patch("data_processing.get_supabase")
    def test_chama_tabela_correta(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table().select().eq().eq().eq().order().execute.return_value = MagicMock(data=[])

        dp.load_history("BMW", "330i", "2020 Gasolina")
        mock_client.table.assert_called_with(TABLE_HISTORICO)


# ── to_excel ──────────────────────────────────────────────────────────────────

class TestToExcel:
    def test_retorna_bytes(self):
        df = pd.DataFrame([{
            COL_DATA_COLETA: "2026-06", COL_MARCA: "BMW", COL_MODELO: "330i",
            COL_ANO: "2020 Gasolina", COL_PRECO: 85000.0,
            "variacao_mensal": None, "depreciacao_pct": 0.0
        }])
        result = dp.to_excel(df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_gera_xlsx_valido(self):
        df = pd.DataFrame([{
            COL_DATA_COLETA: "2026-06", COL_MARCA: "BMW", COL_MODELO: "330i",
            COL_ANO: "2020 Gasolina", COL_PRECO: 85000.0,
            "variacao_mensal": None, "depreciacao_pct": 0.0
        }])
        result = dp.to_excel(df)
        # Arquivos XLSX começam com a assinatura PK (ZIP)
        assert result[:2] == b"PK"