"""
api_tags.py — Endpoints de consulta e gerenciamento de limites de tags.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.dependencies import get_equipment_repository
from src.repositories.base import EquipmentRepository

router = APIRouter(prefix="/api/tags", tags=["Tags"])


class TagLimitsUpdate(BaseModel):
    limite_atencao: float = Field(..., description="Valor limite para disparo de alerta de Atenção")
    limite_critico: float = Field(..., description="Valor limite para disparo de alerta Crítico")


@router.get("", summary="Listar tags mapeadas")
def list_tags(
    equipamento_id: Optional[int] = Query(None, description="Filtrar por ID do equipamento"),
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """Retorna todas as 38 tags cadastradas ou as tags de um determinado equipamento."""
    return eq_repo.list_tags(equipamento_id)


@router.get("/{no_id}", summary="Detalhes de uma tag")
def get_tag(
    no_id: int,
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """Retorna dados de cadastro e limites operacionais de um nó OPC UA."""
    tag = eq_repo.get_tag(no_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    return tag


@router.put("/{no_id}/limits", summary="Atualizar limites operacionais da tag")
def update_tag_limits(
    no_id: int,
    payload: TagLimitsUpdate,
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Atualiza os limites de atenção e crítico de uma tag.
    Permite ajuste fino diretamente pelos supervisores de automação da Ninfa.
    """
    if payload.limite_critico <= payload.limite_atencao:
        raise HTTPException(
            status_code=400,
            detail="O limite crítico deve ser estritamente maior que o limite de atenção.",
        )

    tag = eq_repo.get_tag(no_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")

    success = eq_repo.update_tag_limits(
        no_id=no_id,
        limite_atencao=payload.limite_atencao,
        limite_critico=payload.limite_critico,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao persistir novos limites.")

    updated_tag = eq_repo.get_tag(no_id)
    return {
        "mensagem": "Limites operacionais atualizados com sucesso.",
        "tag": updated_tag,
    }
