"""
src/routes/__init__.py — Registro e exportação das rotas da API REST.
"""

from src.routes.api_equipments import router as equipments_router
from src.routes.api_telemetry import router as telemetry_router
from src.routes.api_tags import router as tags_router
from src.routes.api_alarms import router as alarms_router
from src.routes.api_grafana import router as grafana_router

__all__ = [
    "equipments_router",
    "telemetry_router",
    "tags_router",
    "alarms_router",
    "grafana_router",
]

