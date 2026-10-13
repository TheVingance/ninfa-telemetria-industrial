"""
api_alarms.py — Endpoints para consulta e monitoramento de alarmes industriais.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from src.dependencies import get_telemetry_repository
from src.repositories.base import TelemetryRepository

router = APIRouter(prefix="/api/alarms", tags=["Alarmes"])


@router.get("", summary="Listar ocorrências e eventos de alarme")
def list_alarms(
    equipamento_id: Optional[int] = Query(None, description="Filtrar por equipamento"),
    start_ms: Optional[int] = Query(None, description="Timestamp inicial em ms"),
    end_ms: Optional[int] = Query(None, description="Timestamp final em ms"),
    severidade: Optional[str] = Query(None, description="Filtrar por severidade: critico, atencao"),
    tipo_alarme: Optional[str] = Query(None, description="Filtrar por tipo: limite_processo, qualidade_dado"),
    limit: int = Query(100, ge=1, le=1000, description="Quantidade máxima de eventos"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna o histórico de eventos anômalos registrados na base,
    com distinção clara entre Desvios de Processo vs Falhas de Coleta (Bad/Uncertain).
    """
    events = tel_repo.get_alarm_events(
        equipamento_id=equipamento_id,
        start_ms=start_ms,
        end_ms=end_ms,
        limit=limit,
    )

    # Filtros em memória se especificados
    if severidade:
        events = [e for e in events if e.get("severidade") == severidade]
    if tipo_alarme:
        events = [e for e in events if e.get("tipo_alarme") == tipo_alarme]

    return {
        "total_retornados": len(events),
        "eventos": events,
    }


@router.get("/summary", summary="Resumo e estatísticas de alarmes")
def get_alarms_summary(
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna consolidação estatística das últimas ocorrências de alarme
    para alimentar os cartões de alerta no topo do dashboard.
    """
    events = tel_repo.get_alarm_events(limit=500)

    total_critico = sum(1 for e in events if e.get("severidade") == "critico")
    total_atencao = sum(1 for e in events if e.get("severidade") == "atencao")
    falhas_processo = sum(1 for e in events if e.get("tipo_alarme") == "limite_processo")
    falhas_comunicacao = sum(1 for e in events if e.get("tipo_alarme") == "qualidade_dado")

    return {
        "amostra_tamanho": len(events),
        "total_critico": total_critico,
        "total_atencao": total_atencao,
        "falhas_processo": falhas_processo,
        "falhas_comunicacao": falhas_comunicacao,
    }
