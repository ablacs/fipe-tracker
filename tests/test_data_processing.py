import pytest
import pandas as pd
import json
import data_processing as dp


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


# ── save_price ────────────────────────────────────────────────────────────────

class TestSavePrice:
    def test_cria_csv_se_nao_existe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")
        assert (tmp_path / "historico.csv").exists()

    def test_salva_valores_corretos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")
        df = pd.read_csv(tmp_path / "historico.csv")
        assert df.iloc[0]["marca"]  == "BMW"
        assert df.iloc[0]["modelo"] == "330i"
        assert df.iloc[0]["preco"]  == 85000.0

    def test_deduplica_mesmo_mes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")
        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 86.000,00")
        df = pd.read_csv(tmp_path / "historico.csv")
        assert len(df) == 1
        assert df.iloc[0]["preco"] == 86000.0  # mantém o último

    def test_acumula_meses_diferentes(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        # Escreve um registro de mês anterior diretamente
        df_old = pd.DataFrame([{
            "data_coleta": "2026-05", "marca": "BMW",
            "modelo": "330i", "ano": "2020 Gasolina", "preco": 87000.0
        }])
        df_old.to_csv(tmp_path / "historico.csv", index=False)
        # Salva o mês atual via função
        dp.save_price("BMW", "330i", "2020 Gasolina", "R$ 85.000,00")
        df = pd.read_csv(tmp_path / "historico.csv")
        assert len(df) == 2


# ── track_vehicle ─────────────────────────────────────────────────────────────

class TestTrackVehicle:
    def test_adiciona_novo_veiculo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "TRACKED_FILE", tmp_path / "tracked.json")
        resultado = dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        assert resultado is True
        with open(tmp_path / "tracked.json") as f:
            veiculos = json.load(f)
        assert len(veiculos) == 1
        assert veiculos[0]["brand_name"] == "BMW"

    def test_nao_duplica(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "TRACKED_FILE", tmp_path / "tracked.json")
        dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        resultado = dp.track_vehicle("7", "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        assert resultado is False
        with open(tmp_path / "tracked.json") as f:
            veiculos = json.load(f)
        assert len(veiculos) == 1

    def test_adiciona_multiplos_veiculos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "TRACKED_FILE", tmp_path / "tracked.json")
        dp.track_vehicle("7",  "BMW", "3956", "330i", "2006-1", "2006 Gasolina")
        dp.track_vehicle("59", "VW",  "5585", "Gol",  "2019-1", "2019 Gasolina")
        with open(tmp_path / "tracked.json") as f:
            veiculos = json.load(f)
        assert len(veiculos) == 2


# ── load_history ──────────────────────────────────────────────────────────────

class TestLoadHistory:
    def test_retorna_df_vazio_sem_arquivo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert df.empty

    def test_filtra_por_veiculo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dp.save_price("BMW", "330i",  "2020 Gasolina", "R$ 85.000,00")
        dp.save_price("VW",  "Gol",   "2019 Gasolina", "R$ 30.000,00")
        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert len(df) == 1
        assert df.iloc[0]["marca"] == "BMW"

    def test_calcula_depreciacao(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dados = pd.DataFrame([
            {"data_coleta": "2026-04", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 90000.0},
            {"data_coleta": "2026-05", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 85000.0},
        ])
        dados.to_csv(tmp_path / "historico.csv", index=False)
        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert "depreciacao_pct" in df.columns
        assert df.iloc[0]["depreciacao_pct"] == 0.0    # primeiro mês é a base
        assert df.iloc[1]["depreciacao_pct"] < 0       # preço caiu

    def test_calcula_variacao_mensal(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dp, "HISTORY_FILE", tmp_path / "historico.csv")
        dados = pd.DataFrame([
            {"data_coleta": "2026-04", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 90000.0},
            {"data_coleta": "2026-05", "marca": "BMW", "modelo": "330i",
             "ano": "2020 Gasolina", "preco": 85000.0},
        ])
        dados.to_csv(tmp_path / "historico.csv", index=False)
        df = dp.load_history("BMW", "330i", "2020 Gasolina")
        assert df.iloc[1]["variacao_mensal"] == -5000.0