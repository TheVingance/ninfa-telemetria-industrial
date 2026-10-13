"""
api_equipments.py — Endpoints de consulta e status de equipamentos fabris.
"""

from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_equipment_repository, get_telemetry_repository
from src.repositories.base import EquipmentRepository, TelemetryRepository

router = APIRouter(prefix="/api/equipments", tags=["Equipamentos"])


@router.get("", summary="Listar equipamentos cadastrados")
def list_equipments(
    repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """Retorna os 10 equipamentos cadastrados no parque fabril e total de nós."""
    return repo.list_equipments()


@router.get("/overview", summary="Visão Geral Operacional da Fábrica")
def get_factory_overview(
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna o status consolidado de cada equipamento (Normal, Atenção, Crítico)
    baseado na leitura mais recente de suas tags, junto com métricas gerais.
    """
    if hasattr(tel_repo, "get_factory_overview"):
        equipments = tel_repo.get_factory_overview()
    else:
        equipments = []

    # KPIs globais da fábrica
    total = len(equipments)
    normais = sum(1 for e in equipments if e["status_geral"] == "normal")
    atencao = sum(1 for e in equipments if e["status_geral"] == "atencao")
    criticos = sum(1 for e in equipments if e["status_geral"] == "critico")
    sem_sinal = sum(1 for e in equipments if e["status_geral"] == "sem_sinal")

    return {
        "kpis": {
            "total_equipamentos": total,
            "operacao_normal": normais,
            "em_atencao": atencao,
            "em_alerta_critico": criticos,
            "sem_sinal": sem_sinal,
            "indice_saude_fabril": round((normais / total) * 100, 1) if total > 0 else 0,
        },
        "equipamentos": equipments,
    }


@router.get("/{equipamento_id}", summary="Detalhes do equipamento")
def get_equipment_details(
    equipamento_id: int,
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """Retorna os detalhes de um equipamento, suas tags e leituras recentes."""
    equip = eq_repo.get_equipment(equipamento_id)
    if not equip:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")

    latest_readings = tel_repo.get_latest_readings(equipamento_id)
    equip["leituras_recentes"] = latest_readings

    return equip
