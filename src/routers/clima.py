from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import httpx

router = APIRouter(
    prefix="/api/v1",
    tags=["Clima"]
)

CONDICOES_TEMPO = {
    0: "Céu Limpo", 1: "Principalmente Limpo", 2: "Parcialmente Nublado",
    3: "Nublado", 45: "Nevoeiro", 48: "Nevoeiro com Geada",
    51: "Garoa Leve", 53: "Garoa Moderada", 55: "Garoa Intensa",
    61: "Chuva Leve", 63: "Chuva Moderada", 65: "Chuva Forte",
    71: "Neve Leve", 73: "Neve Moderada", 75: "Neve Forte",
    80: "Pancadas de Chuva Leves", 81: "Pancadas de Chuva Moderadas",
    82: "Pancadas de Chuva Fortes", 95: "Tempestade",
    96: "Tempestade com Granizo", 99: "Tempestade com Granizo Forte",
}


def buscar_cidade_ibge(nome_cidade: str) -> dict:
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    try:
        resp = httpx.get(url, timeout=15)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail={
            "erro": True, "codigo": "SERVICO_EXTERNO_INDISPONIVEL",
            "mensagem": "Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            "servico": "IBGE"
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=503, detail={
            "erro": True, "codigo": "SERVICO_EXTERNO_INDISPONIVEL",
            "mensagem": "Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            "servico": "IBGE"
        })

    municipios = resp.json()
    nome_busca = nome_cidade.strip().lower()

    # 1º: tenta correspondência EXATA (ex: "fortaleza" == "fortaleza")
    exatos = [
        m for m in municipios
        if m["nome"].lower() == nome_busca
    ]

    # 2º: se não achar exato, aceita parcial (ex: "fortal" encontra "Fortaleza")
    parciais = [
        m for m in municipios
        if nome_busca in m["nome"].lower()
    ] if not exatos else []

    encontrados = exatos if exatos else parciais

    if not encontrados:
        return None

    cidade = encontrados[0]
    estado = cidade.get("microrregiao", {}).get("mesorregiao", {}).get("UF", {}).get("sigla", "")
    nome_oficial = cidade.get("nome", nome_cidade)

    return {"nome": nome_oficial, "estado": estado}


def buscar_coordenadas(nome_cidade: str) -> dict:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": nome_cidade,
        "count": 10,
        "language": "pt",
        "format": "json"
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail={
            "erro": True, "codigo": "SERVICO_EXTERNO_INDISPONIVEL",
            "mensagem": "Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            "servico": "Open-Meteo Geocoding"
        })

    dados = resp.json()
    resultados = dados.get("results", [])

    if not resultados:
        return None

    # Prefere resultado do Brasil (country_code == "BR"), senão pega o primeiro
    br_results = [r for r in resultados if r.get("country_code", "").upper() == "BR"]
    escolhido = br_results[0] if br_results else resultados[0]

    return {
        "latitude": escolhido["latitude"],
        "longitude": escolhido["longitude"]
    }


def buscar_clima(latitude: float, longitude: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
        "current_weather": True,
        "timezone": "America/Sao_Paulo",
        "forecast_days": 1
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail={
            "erro": True, "codigo": "SERVICO_EXTERNO_INDISPONIVEL",
            "mensagem": "Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            "servico": "Open-Meteo"
        })

    dados = resp.json()
    daily = dados.get("daily", {})
    temp_max = daily.get("temperature_2m_max", [None])[0]
    temp_min = daily.get("temperature_2m_min", [None])[0]
    codigo_tempo = daily.get("weathercode", [0])[0]
    condicao = CONDICOES_TEMPO.get(codigo_tempo, "Condição desconhecida")

    return {
        "temperatura_min": temp_min,
        "temperatura_max": temp_max,
        "condicao": condicao,
        "unidades": {"temperatura": "°C"}
    }


@router.get("/clima/{nome_cidade}")
def obter_clima_cidade(nome_cidade: str):
    """
    Retorna informações geográficas e climáticas de uma cidade brasileira.
    O usuário informa apenas o nome — coordenadas e clima são buscados automaticamente.
    """
    if len(nome_cidade.strip()) < 2:
        raise HTTPException(status_code=400, detail={
            "erro": True, "codigo": "NOME_INVALIDO",
            "mensagem": "O nome da cidade deve conter pelo menos 2 caracteres",
            "nome_informado": nome_cidade
        })

    # Passo 1: buscar cidade no IBGE (exato primeiro, parcial depois)
    cidade = buscar_cidade_ibge(nome_cidade)
    if not cidade:
        raise HTTPException(status_code=404, detail={
            "erro": True, "codigo": "CIDADE_NAO_ENCONTRADA",
            "mensagem": "Nenhuma cidade encontrada com o nome informado",
            "nome_informado": nome_cidade
        })

    nome_oficial = cidade["nome"]
    estado = cidade["estado"]

    # Passo 2: buscar coordenadas (só pelo nome)
    coordenadas = buscar_coordenadas(nome_oficial)
    if not coordenadas:
        raise HTTPException(status_code=404, detail={
            "erro": True, "codigo": "CIDADE_NAO_ENCONTRADA",
            "mensagem": "Não foi possível localizar as coordenadas da cidade informada",
            "nome_informado": nome_cidade
        })

    # Passo 3: buscar clima pelas coordenadas
    clima = buscar_clima(coordenadas["latitude"], coordenadas["longitude"])

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "nome": nome_oficial,
        "estado": estado,
        "coordenadas": {
            "latitude": coordenadas["latitude"],
            "longitude": coordenadas["longitude"]
        },
        "clima": clima,
        "consultado_em": timestamp
    }