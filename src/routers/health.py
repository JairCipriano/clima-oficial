from fastapi import APIRouter
from datetime import datetime, timezone
import httpx

router = APIRouter(
    prefix="/api/v1",
    tags=["Health Check"]
)

@router.get("/health")
def health_check():
    """
    Verifica se a API está funcionando corretamente.
    Retorna status 'healthy' ou 'degraded' se algum serviço externo estiver fora.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Testa se a BrasilAPI está acessível
    try:
        resp = httpx.get("https://brasilapi.com.br/api/ibge/municipios/v1/CE?providers=dados-abertos-br,gov,wikipedia", timeout=5)
        brasil_api_ok = resp.status_code == 200
    except Exception:
        brasil_api_ok = False

    if brasil_api_ok:
        return {
            "status": "healthy",
            "versao": "1.0.0",
            "timestamp": timestamp
        }
    else:
        return {
            "status": "degraded",
            "versao": "1.0.0",
            "timestamp": timestamp,
            "motivo": "Serviço externo indisponível"
        }
