---

## 🚀 Como rodar localmente

### Pré-requisitos
- Python 3.11+
- Conta no [Supabase](https://supabase.com) (gratuita)

### 1. Clone o repositório

```bash
git clone https://github.com/ablacs/fipe-tracker.git
cd fipe-tracker
```

### 2. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
# Para desenvolvimento (testes):
pip install -r requirements-dev.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_anon_key
```

> As credenciais estão em **Supabase → Project Settings → API Keys**.

### 5. Crie as tabelas no Supabase

No **SQL Editor** do Supabase, execute:

```sql
CREATE TABLE tracked_vehicles (
    id SERIAL PRIMARY KEY,
    brand_code TEXT NOT NULL,
    brand_name TEXT NOT NULL,
    model_code TEXT NOT NULL,
    model_name TEXT NOT NULL,
    year_code  TEXT NOT NULL,
    year_name  TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (brand_code, model_code, year_code)
);

CREATE TABLE historico (
    id SERIAL PRIMARY KEY,
    data_coleta TEXT NOT NULL,
    marca       TEXT NOT NULL,
    modelo      TEXT NOT NULL,
    ano         TEXT NOT NULL,
    preco       NUMERIC NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (data_coleta, marca, modelo, ano)
);
```

### 6. Rode o app

```bash
streamlit run app.py
```

Acesse em: http://localhost:8501

---

## 🐳 Como rodar com Docker

```bash
# Sobe o container (lê as variáveis do .env automaticamente)
docker compose up --build

# Em background
docker compose up -d

# Para o container
docker compose down
```

---

## ⚙️ Variáveis de ambiente

| Variável       | Descrição                      | Onde configurar                                   |
| -------------- | ------------------------------ | ------------------------------------------------- |
| `SUPABASE_URL` | URL do projeto Supabase        | `.env` local / Streamlit Secrets / GitHub Secrets |
| `SUPABASE_KEY` | Chave anon pública do Supabase | `.env` local / Streamlit Secrets / GitHub Secrets |

---

## 🔌 API utilizada

**Base URL:** `https://parallelum.com.br/fipe/api/v1`

| Endpoint                                            | Descrição             |
| --------------------------------------------------- | --------------------- |
| `GET /carros/marcas`                                | Lista todas as marcas |
| `GET /carros/marcas/{cod}/modelos`                  | Modelos de uma marca  |
| `GET /carros/marcas/{cod}/modelos/{cod}/anos`       | Anos disponíveis      |
| `GET /carros/marcas/{cod}/modelos/{cod}/anos/{ano}` | Preço atual           |

> A API retorna apenas o preço do mês corrente. O histórico é construído através
> de coletas mensais automáticas armazenadas no Supabase.

---

## ⚡ GitHub Actions — Coleta automática

Todo dia 1 de cada mês às 9h UTC, uma GitHub Action executa `scripts/collect_prices.py`,
que busca o preço atualizado de cada veículo rastreado no Supabase e salva o novo registro.

Para configurar, adicione `SUPABASE_URL` e `SUPABASE_KEY` em:
**GitHub → Settings → Secrets and variables → Actions**

Para rodar manualmente:
**GitHub → Actions → Coleta Mensal de Preços FIPE → Run workflow**

---

## 🧪 Testes

```bash
# Roda todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=data_processing
```

Os testes cobrem as funções de processamento de dados com mocks do Supabase,
sem necessidade de conexão com o banco em ambiente de testes.

---

## 📦 Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte sua conta GitHub
2. Selecione o repositório `fipe-tracker` e o branch `main`
3. Aponte para `app.py` como arquivo principal
4. Em **Advanced settings**, adicione as variáveis de ambiente:

```toml
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_KEY = "sua_anon_key"
```

5. Clique em **Deploy**

---

## ⚠️ Limitações conhecidas e próximos passos

O app atual usa um **banco de dados compartilhado** — todos os usuários veem e
contribuem com os mesmos dados. Para uma versão multi-usuário completa, os próximos
passos seriam:

- [ ] Autenticação com **Supabase Auth**
- [ ] **Row Level Security (RLS)** para isolamento de dados por usuário
- [ ] Suporte a **motos e caminhões** (a API FIPE já disponibiliza esses endpoints)
- [ ] **Alertas de preço** por e-mail quando um veículo atingir um valor alvo
- [ ] Melhoria da análise de tendência com modelos mais sofisticados

---

## 📄 Licença

MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.
