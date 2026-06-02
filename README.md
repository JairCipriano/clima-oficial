# clima-oficial - API de Dados Climáticos e Geográficos

Aplicação desenvolvida para a disciplina de **Técnicas de Integração de Sistemas (N703)** do Curso ADS/IA - EAD Unifor. A API agrega dados de serviços públicos externos para fornecer informações geográficas e climáticas de cidades brasileiras a partir apenas do nome da cidade.

---

## Links do Projeto

| Recurso | URL |
|---|---|
| Repositório GitHub | https://github.com/JairCipriano/clima-oficial |
| Documentação Swagger | http://localhost:3000/docs |
| Documentação ReDoc | http://localhost:3000/redoc |

---

## Endpoints Disponíveis

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/health` | Verifica se a API está em funcionamento |
| GET | `/api/v1/clima/{nome_cidade}` | Retorna dados climáticos de uma cidade |
| GET | `/api/v1/cidades/{sigla_uf}` | Lista cidades de um estado brasileiro |

---

## Arquitetura de Integração

A API não armazena dados — ela busca e agrega informações em tempo real a partir de APIs públicas externas:

```
[ Cliente ]
     |
     v
[ API clima-oficial - FastAPI / Porta 3000 ]
     |
     |── IBGE Localidades      →  Valida cidade e obtém estado
     |── Open-Meteo Geocoding  →  Obtém coordenadas (latitude/longitude)
     └── Open-Meteo Forecast   →  Obtém dados climáticos pelas coordenadas
```

**Fluxo do endpoint de clima:**
1. Usuário informa apenas o nome da cidade
2. API busca a cidade na base do IBGE (prioriza correspondência exata)
3. API obtém as coordenadas geográficas via Open-Meteo Geocoding
4. API consulta o clima atual via Open-Meteo Forecast
5. Dados combinados são retornados em um único JSON padronizado

---

## Tecnologias Utilizadas

| Camada | Tecnologia | Finalidade |
|---|---|---|
| Linguagem | Python 3.11 | Desenvolvimento da API |
| Framework | FastAPI | Rotas REST e documentação automática |
| Servidor | Uvicorn | Servidor ASGI |
| HTTP Client | HTTPX | Consumo das APIs externas |
| Container | Docker | Padronização do ambiente |
| Testes | Pytest + unittest.mock | Testes automatizados sem internet |

**APIs externas consumidas:**

| API | Uso |
|---|---|
| IBGE Localidades | Validação e busca de municípios brasileiros |
| Open-Meteo Geocoding | Conversão de nome de cidade em coordenadas |
| Open-Meteo Forecast | Dados climáticos por latitude e longitude |

---

## Como Rodar Localmente

### Pré-requisitos

- Python 3.11 ou superior
- Git instalado

### 1. Clone o repositório

```bash
git clone https://github.com/JairCipriano/clima-oficial.git
cd clima-oficial
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o servidor

```bash
uvicorn src.main:app --reload --port 3000
```

A API estará disponível em `http://localhost:3000` e a documentação interativa em `http://localhost:3000/docs`.

---

## Como Rodar com Docker

```bash
docker build -t clima-oficial .
docker run -p 3000:3000 clima-oficial
```

---

## Como Rodar os Testes

Os testes usam mocks e não precisam de conexão com internet:

```bash
pytest tests/ -v
```

Resultado esperado: **14 testes passando**.

---

## Estrutura do Repositório

```
clima-oficial/
├── README.md                        # Documentação principal
├── INTEGRANTES.md                   # Dados da equipe
├── Dockerfile                       # Container Docker (porta 3000)
├── requirements.txt                 # Dependências Python
├── src/
│   ├── main.py                      # Ponto de entrada da API
│   └── routers/
│       ├── health.py                # GET /api/v1/health
│       ├── clima.py                 # GET /api/v1/clima/{nome_cidade}
│       └── cidades.py               # GET /api/v1/cidades/{sigla_uf}
├── tests/
│   └── test_api.py                  # 14 testes automatizados com mock
└── docs/
    └── postman_collection.json      # Coleção Postman exportada
```

---

## Exemplos de Uso

### Health Check

```
GET /api/v1/health
```

```json
{
  "status": "healthy",
  "versao": "1.0.0",
  "timestamp": "2026-06-01T23:00:00Z"
}
```

### Clima de uma cidade

```
GET /api/v1/clima/Fortaleza
```

```json
{
  "nome": "Fortaleza",
  "estado": "CE",
  "coordenadas": {
    "latitude": -3.71722,
    "longitude": -38.5434
  },
  "clima": {
    "temperatura_min": 24.6,
    "temperatura_max": 30.2,
    "condicao": "Pancadas de Chuva Leves",
    "unidades": {
      "temperatura": "°C"
    }
  },
  "consultado_em": "2026-06-01T23:40:54Z"
}
```

### Cidades de um estado

```
GET /api/v1/cidades/CE?limite=3
```

```json
{
  "uf": "CE",
  "quantidade_retornada": 3,
  "cidades": [
    { "nome": "Abaiara" },
    { "nome": "Acarape" },
    { "nome": "Acaraú" }
  ],
  "consultado_em": "2026-06-01T23:40:54Z"
}
```

### Tratamento de Erros

| Situação | HTTP | Código |
|---|---|---|
| Nome de cidade com menos de 2 caracteres | 400 | `NOME_INVALIDO` |
| Cidade não encontrada | 404 | `CIDADE_NAO_ENCONTRADA` |
| Sigla de estado inválida | 400 | `SIGLA_UF_INVALIDA` |
| Estado não encontrado | 404 | `UF_NAO_ENCONTRADA` |
| API externa indisponível | 503 | `SERVICO_EXTERNO_INDISPONIVEL` |

---

## Equipe

Veja o arquivo [INTEGRANTES.md](./INTEGRANTES.md) para a lista completa da equipe.
