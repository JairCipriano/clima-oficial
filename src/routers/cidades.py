from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
import httpx

router = APIRouter(
    prefix="/api/v1",
    tags=["Cidades"]
)

UFS_VALIDAS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO",
    "MA","MT","MS","MG","PA","PB","PR","PE","PI",
    "RJ","RN","RS","RO","RR","SC","SP","SE","TO"
]


@router.get("/cidades/{sigla_uf}")
def listar_cidades_por_estado(
    sigla_uf: str,
    limite: int = Query(default=10, ge=1, le=100, description="Quantidade máxima de cidades (1-100)")
):
    """
    Lista cidades de um estado brasileiro pela sigla da UF.
    Usa a API do IBGE para buscar os municípios dinamicamente.
    """
    uf = sigla_uf.strip().upper()

    if len(uf) != 2 or not uf.isalpha():
        raise HTTPException(status_code=400, detail={
            "erro": True, "codigo": "SIGLA_UF_INVALIDA",
            "mensagem": "A sigla do estado deve conter exatamente 2 letras",
            "sigla_uf_informada": sigla_uf
        })

    if uf not in UFS_VALIDAS:
        raise HTTPException(status_code=404, detail={
            "erro": True, "codigo": "UF_NAO_ENCONTRADA",
            "mensagem": "Estado com a sigla informada não foi encontrado",
            "sigla_uf_informada": sigla_uf
        })

    # API do IBGE - busca municípios por UF (endpoint correto e gratuito)
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"

    try:
        resp = httpx.get(url, timeout=15)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail={
            "erro": True, "codigo": "SERVICO_EXTERNO_INDISPONIVEL",
            "mensagem": "Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            "servico": "IBGE"
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=404, detail={
            "erro": True, "codigo": "UF_NAO_ENCONTRADA",
            "mensagem": "Estado com a sigla informada não foi encontrado",
            "sigla_uf_informada": sigla_uf
        })

    municipios = resp.json()
    municipios_limitados = municipios[:limite]
    cidades_formatadas = [{"nome": m["nome"]} for m in municipios_limitados]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "uf": uf,
        "quantidade_retornada": len(cidades_formatadas),
        "cidades": cidades_formatadas,
        "consultado_em": timestamp
    }
