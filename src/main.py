from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import clima, cidades, health

app = FastAPI(
    title="API de Dados Climáticos e Geográficos",
    description="API de agregação de dados climáticos e geográficos para cidades brasileiras. Disciplina N703 - Unifor.",
    version="1.0.0"
)

# CORS habilitado conforme requisito da proposta
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROTEADORES
app.include_router(health.router)
app.include_router(clima.router)
app.include_router(cidades.router)

@app.get("/")
def raiz():
    return {
        "status": "online",
        "mensagem": "API de Dados Climáticos e Geográficos - N703 Unifor",
        "docs": "/docs"
    }
