# FIPE Tracker

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)
fipe-tracker/
├── app.py # ponto de entrada do Streamlit
├── fipe_api.py # funções de consulta à API da FIPE
├── data_processing.py # limpeza e transformação com Pandas
├── charts.py # funções de geração de gráficos com Plotly
├── requirements.txt
└── README.md

Dashboard interativo de análise de depreciação de veículos usando dados históricos
da Tabela FIPE. Permite comparar a desvalorização de diferentes modelos ao longo
do tempo e tomar decisões mais informadas na hora de comprar ou vender um carro.

## Problema que resolve

A Tabela FIPE é atualizada mensalmente, mas a maioria das pessoas só consulta o
valor atual do veículo. Este projeto coleta e armazena o histórico de preços,
permitindo visualizar como um modelo específico deprecia com o tempo — informação
valiosa para compradores, vendedores e entusiastas do mercado automotivo.

## Funcionalidades

- Busca por marca, modelo, ano e tipo de combustível
- Gráfico de evolução do preço ao longo dos meses
- Curva de depreciação percentual acumulada
- Comparação lado a lado entre dois veículos
- Indicador de "melhor momento para comprar" baseado na tendência histórica
- Tabela com variação mensal em R$ e percentual

## Stack

| Camada      | Tecnologia                            |
| ----------- | ------------------------------------- |
| Linguagem   | Python 3.11+                          |
| Dashboard   | Streamlit                             |
| Gráficos    | Plotly Express                        |
| Dados       | Pandas                                |
| HTTP        | Requests                              |
| API externa | FIPE API (gratuita, sem autenticação) |

## Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/fipe-tracker.git
cd fipe-tracker

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install streamlit pandas plotly requests

# 4. Rode o app
streamlit run app.py
```

Acesse em: http://localhost:8501

## Estrutura do projeto

## API utilizada

Base URL: `https://parallelum.com.br/fipe/api/v1`

Endpoints relevantes:

- `GET /carros/marcas` — lista todas as marcas
- `GET /carros/marcas/{codMarca}/modelos` — modelos de uma marca
- `GET /carros/marcas/{codMarca}/modelos/{codModelo}/anos` — anos disponíveis
- `GET /carros/marcas/{codMarca}/modelos/{codModelo}/anos/{ano}` — preço atual

> A API não retorna histórico diretamente. A estratégia é agendar coletas mensais
> e armazenar os resultados em um CSV local ou no Supabase para construir o
> histórico ao longo do tempo.

## Deploy (gratuito)

1. Suba o projeto no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta GitHub e selecione o repositório
4. Aponte para `app.py` como arquivo principal
5. Clique em Deploy — o link público é gerado automaticamente

Nenhuma variável de ambiente necessária.

## Variáveis de ambiente

Nenhuma. A API da FIPE é pública e não requer autenticação.

## Notas de implementação

- A API FIPE retorna preços apenas do mês atual. Para ter histórico, você precisa
  rodar uma coleta periódica. Use um GitHub Actions com schedule mensal para
  coletar e commitar um CSV atualizado no próprio repositório.
- O código do veículo muda entre anos (ex: "Golf 2020" e "Golf 2021" têm códigos
  diferentes). Armazene a combinação marca+modelo+ano para evitar bugs no histórico.
- Comece com apenas carros (`/carros`). A API também tem motos (`/motos`) e
  caminhões (`/caminhoes`) — adicione como feature extra depois.
