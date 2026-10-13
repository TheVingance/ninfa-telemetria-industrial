"""
api_telemetry.py — Endpoints para consulta de séries temporais e downsampling.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from src.config import BUCKET_SIZES_MS, POC_INICIO_MS, POC_FIM_MS
from src.core.predictive import analyze_predictive_health
from src.dependencies import get_telemetry_repository, get_equipment_repository
from src.repositories.base import TelemetryRepository, EquipmentRepository

router = APIRouter(prefix="/api/telemetry", tags=["Telemetria"])


def resolve_bucket_ms(start_ms: int, end_ms: int, bucket_param: Optional[str]) -> int:
    """Calcula ou resolve o tamanho do bucket em ms para downsampling inteligente."""
    if bucket_param and bucket_param in BUCKET_SIZES_MS:
        return BUCKET_SIZES_MS[bucket_param]

    delta = end_ms - start_ms
    day_ms = 86_400_000

    if delta <= day_ms:
        return BUCKET_SIZES_MS["5min"]
    elif delta <= 7 * day_ms:
        return BUCKET_SIZES_MS["1h"]
    elif delta <= 30 * day_ms:
        return BUCKET_SIZES_MS["6h"]
    else:
        return BUCKET_SIZES_MS["1d"]


@router.get("/series", summary="Série temporal agregada (Downsampling)")
def get_series(
    no_id: int = Query(..., description="ID do nó OPC UA"),
    start_ms: Optional[int] = Query(None, description="Início do período em ms (Unix)"),
    end_ms: Optional[int] = Query(None, description="Fim do período em ms (Unix)"),
    bucket: Optional[str] = Query("auto", description="Bucket de agregação: auto, 5min, 15min, 1h, 6h, 1d"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Retorna série temporal de um nó específico com agregação temporal
    (médias, mínimos, máximos, contagens de qualidade de dados e latência).
    """
    tag = eq_repo.get_tag(no_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag nó {no_id} não encontrada")

    # Defaults de período (último mês disponível do PoC ou todo o ano)
    f_end = end_ms if end_ms is not None else POC_FIM_MS
    f_start = start_ms if start_ms is not None else (f_end - (30 * 86_400_000))

    bucket_ms = resolve_bucket_ms(f_start, f_end, bucket)
    series = tel_repo.get_time_series(no_id, f_start, f_end, bucket_ms)

    return {
        "tag": tag,
        "parametros": {
            "start_ms": f_start,
            "end_ms": f_end,
            "bucket_ms": bucket_ms,
            "total_pontos": len(series),
        },
        "pontos": series,
    }


@router.get("/predictive", summary="Análise Preditiva e Projeção de Tendência")
def get_predictive_analysis(
    no_id: int = Query(..., description="ID do nó OPC UA"),
    window_hours: int = Query(72, description="Janela de histórico para projeção (em horas)"),
    end_ms: Optional[int] = Query(None, description="Timestamp de referência final"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Executa cálculo de tendência linear, estima tempo até limite de atenção/crítico
    e detecta anomalias estatísticas recentes.
    """
    tag = eq_repo.get_tag(no_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag nó {no_id} não encontrada")

    f_end = end_ms if end_ms is not None else POC_FIM_MS
    f_start = f_end - (window_hours * 3_600_000)

    # Buscar dados em resolução horária ou 15min para a janela preditiva
    bucket_ms = BUCKET_SIZES_MS["1h"] if window_hours >= 48 else BUCKET_SIZES_MS["15min"]
    series = tel_repo.get_time_series(no_id, f_start, f_end, bucket_ms)

    insights = analyze_predictive_health(
        readings=series,
        limit_attention=tag["limite_atencao"],
        limit_critical=tag["limite_critico"],
        grandeza=tag["grandeza"],
        unidade=tag["unidade"],
    )

    return {
        "tag": tag,
        "janela_horas": window_hours,
        "analise_preditiva": insights,
        "pontos_analisados": len(series),
    }


@router.get("/quality", summary="Resumo de Qualidade de Dados (OPC UA)")
def get_quality_summary(
    no_id: int = Query(..., description="ID do nó OPC UA"),
    start_ms: Optional[int] = Query(None, description="Início em ms"),
    end_ms: Optional[int] = Query(None, description="Fim em ms"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna métricas de confiabilidade: percentuais de leituras Good, Uncertain, Bad
    e latência de ingestão da rede industrial.
    """
    f_end = end_ms if end_ms is not None else POC_FIM_MS
    f_start = start_ms if start_ms is not None else (f_end - (30 * 86_400_000))

    summary = tel_repo.get_data_quality_summary(no_id, f_start, f_end)
    return summary
