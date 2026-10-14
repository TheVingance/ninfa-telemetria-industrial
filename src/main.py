"""
main.py — Ponto de entrada da aplicação Ninfa Telemetria Industrial.

Inicializa o servidor FastAPI, monta os arquivos estáticos (HTML/CSS/JS)
e registra os roteadores da API REST.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import (
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    STATIC_DIR,
    DATABASE_PATH,
)
from src.routes import (
    equipments_router,
    telemetry_router,
    tags_router,
    alarms_router,
    grafana_router,
)

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Habilitar CORS para flexibilidade em ambiente local ou dashboards externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Roteadores da API REST
app.include_router(equipments_router)
app.include_router(telemetry_router)
app.include_router(tags_router)
app.include_router(alarms_router)
app.include_router(grafana_router)

# Montar arquivos estáticos (CSS, JS, assets)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# -------------------------------------------------------------
# Rotas para entrega das páginas HTML (Frontend Vanilla)
# -------------------------------------------------------------
@app.get("/", summary="Dashboard Visão Geral da Fábrica", include_in_schema=False)
def page_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/equipment", summary="Página de Detalhes do Equipamento", include_in_schema=False)
@app.get("/equipment.html", include_in_schema=False)
def page_equipment():
    return FileResponse(STATIC_DIR / "equipment.html")


@app.get("/comparison", summary="Página de Comparativo entre Máquinas", include_in_schema=False)
@app.get("/comparison.html", include_in_schema=False)
def page_comparison():
    return FileResponse(STATIC_DIR / "comparison.html")


@app.get("/alarms", summary="Página da Central de Alarmes", include_in_schema=False)
@app.get("/alarms.html", include_in_schema=False)
def page_alarms():
    return FileResponse(STATIC_DIR / "alarms.html")


@app.get("/limites", summary="Página de Configuração de Limites", include_in_schema=False)
@app.get("/limites.html", include_in_schema=False)
@app.get("/settings", include_in_schema=False)
@app.get("/settings.html", include_in_schema=False)
def page_limites():
    return FileResponse(STATIC_DIR / "limites.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


# -------------------------------------------------------------
# Health Check
# -------------------------------------------------------------
@app.get("/api/health", summary="Health check da aplicação")
def health_check():
    db_exists = Path(DATABASE_PATH).is_file()
    return {
        "status": "healthy" if db_exists else "warning",
        "database_connected": db_exists,
        "database_path": str(DATABASE_PATH),
        "version": API_VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
