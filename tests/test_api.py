"""
Testes automatizados para a API N703 - Dados Climáticos e Geográficos
Usa unittest.mock para simular chamadas às APIs externas,
garantindo que os testes rodem em qualquer ambiente (CI/CD incluído).
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)


# ─────────────────────────────────────────────
# TESTES DO HEALTH CHECK
# ─────────────────────────────────────────────

def test_health_check_retorna_200():
    """Testa se o endpoint de health check responde com HTTP 200."""
    with patch("src.routers.health.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_tem_campo_status_healthy():
    """Testa se health retorna 'healthy' quando serviço externo está OK."""
    with patch("src.routers.health.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        response = client.get("/api/v1/health")
    dados = response.json()
    assert "status" in dados
    assert dados["status"] == "healthy"
    assert "versao" in dados
    assert dados["versao"] == "1.0.0"
    assert "timestamp" in dados


def test_health_check_retorna_degraded_quando_servico_cai():
    """Testa se health retorna 'degraded' quando o serviço externo está fora."""
    with patch("src.routers.health.httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=503)
        response = client.get("/api/v1/health")
    dados = response.json()
    assert dados["status"] == "degraded"
    assert "motivo" in dados


# ─────────────────────────────────────────────
# TESTES DO ENDPOINT DE CLIMA
# ─────────────────────────────────────────────

def _mock_brasil_api(nome="Fortaleza", estado="CE"):
    """Helper que simula a resposta da API do IBGE para uma cidade válida."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = [{
        "nome": nome,
        "microrregiao": {
            "mesorregiao": {
                "UF": {"sigla": estado}
            }
        }
    }]
    return mock


def _mock_geocoding():
    """Helper que simula a resposta do Open-Meteo Geocoding."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "results": [{"latitude": -3.71722, "longitude": -38.5434, "country_code": "BR"}]
    }
    return mock


def _mock_previsao():
    """Helper que simula a resposta do Open-Meteo Forecast."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "daily": {
            "temperature_2m_max": [32.0],
            "temperature_2m_min": [24.0],
            "weathercode": [2]
        },
        "current_weather": {}
    }
    return mock


def test_clima_cidade_valida_retorna_200():
    """Testa se a rota de clima retorna HTTP 200 para cidade válida (Fortaleza)."""
    with patch("src.routers.clima.httpx.get") as mock_get:
        mock_get.side_effect = [
            _mock_brasil_api(),
            _mock_geocoding(),
            _mock_previsao()
        ]
        response = client.get("/api/v1/clima/Fortaleza")
    assert response.status_code == 200


def test_clima_cidade_valida_tem_campos_obrigatorios():
    """Testa se a resposta tem os campos: nome, estado, clima, consultado_em."""
    with patch("src.routers.clima.httpx.get") as mock_get:
        mock_get.side_effect = [
            _mock_brasil_api(),
            _mock_geocoding(),
            _mock_previsao()
        ]
        response = client.get("/api/v1/clima/Fortaleza")
    dados = response.json()
    assert "nome" in dados
    assert "estado" in dados
    assert "clima" in dados
    assert "consultado_em" in dados
    assert dados["nome"] == "Fortaleza"
    assert dados["estado"] == "CE"


def test_clima_objeto_clima_tem_campos_corretos():
    """Testa se o objeto 'clima' contém temperatura_min, temperatura_max e condicao."""
    with patch("src.routers.clima.httpx.get") as mock_get:
        mock_get.side_effect = [
            _mock_brasil_api(),
            _mock_geocoding(),
            _mock_previsao()
        ]
        response = client.get("/api/v1/clima/Fortaleza")
    clima = response.json()["clima"]
    assert "temperatura_min" in clima
    assert "temperatura_max" in clima
    assert "condicao" in clima
    assert "unidades" in clima
    assert clima["temperatura_min"] == 24.0
    assert clima["temperatura_max"] == 32.0


def test_clima_cidade_invalida_retorna_400():
    """Testa se retorna HTTP 400 para nome com menos de 2 caracteres."""
    response = client.get("/api/v1/clima/X")
    assert response.status_code == 400
    dados = response.json()
    assert dados["detail"]["codigo"] == "NOME_INVALIDO"
    assert dados["detail"]["erro"] is True


def test_clima_cidade_nao_encontrada_retorna_404():
    """Testa se retorna HTTP 404 quando a cidade não existe."""
    with patch("src.routers.clima.httpx.get") as mock_get:
        # Retorna status 200 com lista vazia — cidade não encontrada no IBGE
        mock_nao_encontrada = MagicMock()
        mock_nao_encontrada.status_code = 200
        mock_nao_encontrada.json.return_value = []
        mock_get.return_value = mock_nao_encontrada
        response = client.get("/api/v1/clima/CidadeQueNaoExiste999")
    assert response.status_code == 404
    dados = response.json()
    assert dados["detail"]["codigo"] == "CIDADE_NAO_ENCONTRADA"


def test_clima_servico_externo_indisponivel_retorna_503():
    """Testa se retorna HTTP 503 quando API externa está fora."""
    import httpx
    with patch("src.routers.clima.httpx.get") as mock_get:
        mock_get.side_effect = httpx.RequestError("timeout")
        response = client.get("/api/v1/clima/Fortaleza")
    assert response.status_code == 503
    dados = response.json()
    assert dados["detail"]["codigo"] == "SERVICO_EXTERNO_INDISPONIVEL"


# ─────────────────────────────────────────────
# TESTES DO ENDPOINT DE CIDADES POR ESTADO
# ─────────────────────────────────────────────

def _mock_cidades_ce():
    """Helper que simula a resposta da API do IBGE com municípios do CE."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = [
        {"nome": "Abaiara"},
        {"nome": "Acarape"},
        {"nome": "Acaraú"},
        {"nome": "Acopiara"},
        {"nome": "Aiuaba"},
        {"nome": "Alcântaras"},
        {"nome": "Altaneira"},
        {"nome": "Alto Santo"},
    ]
    return mock


def test_cidades_estado_valido_retorna_200():
    """Testa se a rota de cidades retorna HTTP 200 para estado válido (CE)."""
    with patch("src.routers.cidades.httpx.get") as mock_get:
        mock_get.return_value = _mock_cidades_ce()
        response = client.get("/api/v1/cidades/CE")
    assert response.status_code == 200


def test_cidades_estado_valido_tem_campos_obrigatorios():
    """Testa se a resposta contém uf, quantidade_retornada e cidades."""
    with patch("src.routers.cidades.httpx.get") as mock_get:
        mock_get.return_value = _mock_cidades_ce()
        response = client.get("/api/v1/cidades/CE")
    dados = response.json()
    assert "uf" in dados
    assert "quantidade_retornada" in dados
    assert "cidades" in dados
    assert isinstance(dados["cidades"], list)
    assert dados["uf"] == "CE"


def test_cidades_limite_funciona():
    """Testa se o parâmetro 'limite' restringe a quantidade de cidades retornadas."""
    with patch("src.routers.cidades.httpx.get") as mock_get:
        mock_get.return_value = _mock_cidades_ce()
        response = client.get("/api/v1/cidades/CE?limite=3")
    assert response.status_code == 200
    dados = response.json()
    assert dados["quantidade_retornada"] == 3
    assert len(dados["cidades"]) == 3


def test_cidades_sigla_invalida_retorna_400():
    """Testa se retorna HTTP 400 para sigla com mais de 2 caracteres."""
    response = client.get("/api/v1/cidades/ceara")
    assert response.status_code == 400
    dados = response.json()
    assert dados["detail"]["codigo"] == "SIGLA_UF_INVALIDA"


def test_cidades_uf_nao_existente_retorna_404():
    """Testa se retorna HTTP 404 para sigla de estado que não existe."""
    response = client.get("/api/v1/cidades/XX")
    assert response.status_code == 404
    dados = response.json()
    assert dados["detail"]["codigo"] == "UF_NAO_ENCONTRADA"