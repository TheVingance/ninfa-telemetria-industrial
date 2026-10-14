"""
api_grafana.py — Endpoints dedicados para integração com Grafana (Plugin Infinity / REST).

Permite que o Grafana consuma dados de séries temporais, alarmes, visão fabril
e variáveis de template diretamente da API REST da Ninfa, preservando 100% das
regras de negócio, downsampling inteligente e tratamento de status codes OPC UA.
"""

from datetime import datetime, timezone
from typing import Optional, Union
from fastapi import APIRouter, Depends, Query, HTTPException

from src.config import BUCKET_SIZES_MS, POC_INICIO_MS, POC_FIM_MS
from src.dependencies import get_telemetry_repository, get_equipment_repository
from src.repositories.base import TelemetryRepository, EquipmentRepository

router = APIRouter(prefix="/api/grafana", tags=["Grafana Integration"])


def parse_timestamp_ms(val: Optional[Union[str, int, float]], default_val: int) -> int:
    """
    Converte múltiplos formatos de timestamp aceitos pelo Grafana para Epoch ms (UTC).
    Aceita:
    - Inteiro ou float Epoch ms (ex: 1758585600000)
    - Inteiro Epoch segundos (ex: 1758585600)
    - String ISO-8601 (ex: '2025-09-23T00:00:00.000Z' ou '2025-09-23T00:00:00Z')
    """
    if val is None or val == "" or str(val).strip().lower() in ("null", "none"):
        return default_val

    # Se for numérico ou string numérica
    try:
        num = float(val)
        # Se for menor que 10^11, é provável que seja em segundos
        if num < 100_000_000_000:
            return int(num * 1000)
        return int(num)
    except (ValueError, TypeError):
        pass

    # Se for string ISO-8601
    val_str = str(val).strip()
    try:
        clean_iso = val_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        return int(dt.timestamp() * 1000)
    except Exception:
        return default_val


def resolve_bucket_ms(start_ms: int, end_ms: int, bucket_param: Optional[str]) -> int:
    """Calcula ou resolve o bucket para downsampling inteligente."""
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


@router.get("/health", summary="Health check da integração com Grafana")
def grafana_health():
    """Valida conexão do Grafana Data Source."""
    return {
        "status": "ok",
        "message": "Ninfa Telemetria — API de Integração Grafana ativa",
        "poc_period": {
            "start_ms": POC_INICIO_MS,
            "end_ms": POC_FIM_MS,
            "start_iso": datetime.fromtimestamp(POC_INICIO_MS / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_iso": datetime.fromtimestamp(POC_FIM_MS / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }


@router.get("/series", summary="Série temporal otimizada para painéis do Grafana")
def get_grafana_series(
    no_id: Optional[int] = Query(None, description="ID do nó OPC UA"),
    equipamento_id: Optional[int] = Query(None, description="ID do equipamento (opcional se no_id for passado)"),
    grandeza: Optional[str] = Query(None, description="Grandeza: TEMPERATURA ou VIBRACAO_RMS"),
    ponto: Optional[str] = Query("P01", description="Ponto de medição: P01 ou P02"),
    from_param: Optional[str] = Query(None, alias="from", description="Timestamp inicial (ISO ou Epoch ms)"),
    to_param: Optional[str] = Query(None, alias="to", description="Timestamp final (ISO ou Epoch ms)"),
    start_ms: Optional[Union[str, int]] = Query(None, description="Timestamp inicial alternativo"),
    end_ms: Optional[Union[str, int]] = Query(None, description="Timestamp final alternativo"),
    bucket: Optional[str] = Query("auto", description="Bucket de agregação: auto, 5min, 15min, 1h, 6h, 1d"),
    raw: bool = Query(False, description="Se True, retorna pontos brutos sem bucket (máx 1000)"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Retorna dados de série temporal em formato de array plano (tabular) compatível nativamente
    com o plugin Infinity do Grafana para renderização em painéis Time Series e Stat.
    """
    resolved_no_id = no_id

    # Se no_id não foi passado mas equipamento_id foi
    if resolved_no_id is None and equipamento_id is not None:
        equip = eq_repo.get_equipment(equipamento_id)
        if not equip:
            raise HTTPException(status_code=404, detail=f"Equipamento {equipamento_id} não encontrado")

        g_upper = (grandeza or "TEMPERATURA").upper().strip()
        if "VIB" in g_upper:
            g_target = "VIBRACAO_RMS"
        else:
            g_target = "TEMPERATURA"

        p_target = (ponto or "P01").upper().strip()

        matched = [
            t for t in equip.get("tags", [])
            if t["grandeza"] == g_target and t["ponto_medicao"] == p_target
        ]
        if matched:
            resolved_no_id = matched[0]["no_id"]
        elif equip.get("tags"):
            resolved_no_id = equip["tags"][0]["no_id"]
        else:
            raise HTTPException(status_code=404, detail=f"Nenhuma tag encontrada para o equipamento {equipamento_id}")

    if resolved_no_id is None:
        resolved_no_id = 1

    tag = eq_repo.get_tag(resolved_no_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag nó {resolved_no_id} não encontrada")

    # Resolução de intervalo temporal
    default_end = POC_FIM_MS
    default_start = POC_FIM_MS - (30 * 86_400_000)

    f_end = parse_timestamp_ms(to_param or end_ms, default_end)
    f_start = parse_timestamp_ms(from_param or start_ms, default_start)

    if f_start > f_end:
        f_start, f_end = f_end, f_start

    bucket_ms = 0 if raw else resolve_bucket_ms(f_start, f_end, bucket)
    raw_series = tel_repo.get_time_series(resolved_no_id, f_start, f_end, bucket_ms)

    # Formatação plana para o Grafana Infinity
    formatted_points = []
    for pt in raw_series:
        ts = pt["timestamp"]
        iso_time = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        bad_cnt = pt.get("bad_count", 0)
        uncert_cnt = pt.get("uncertain_count", 0)
        if bad_cnt > 0:
            qualidade_label = "Bad"
        elif uncert_cnt > 0:
            qualidade_label = "Uncertain"
        else:
            qualidade_label = "Good"

        formatted_points.append({
            "time": iso_time,
            "timestamp": ts,
            "equipamento_codigo": tag["equipamento_codigo"],
            "equipamento_descricao": tag["equipamento_descricao"],
            "ponto": tag["ponto_medicao"],
            "grandeza": tag["grandeza"],
            "unidade": tag["unidade"],
            "valor": pt.get("media"),
            "minimo": pt.get("minimo"),
            "maximo": pt.get("maximo"),
            "limite_atencao": tag["limite_atencao"],
            "limite_critico": tag["limite_critico"],
            "latencia_ms": pt.get("latencia_media_ms", 0),
            "total_leituras": pt.get("total_leituras", 1),
            "status_code": pt.get("status_code", 0),
            "qualidade": qualidade_label,
        })

    return formatted_points


@router.get("/overview", summary="Visão geral de todos os equipamentos para painéis Stat/Tabela do Grafana")
def get_grafana_overview(
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna o status consolidado dos 10 equipamentos fabris, formatado para
    painéis Stat, Status History ou Polystat do Grafana.
    """
    overview_data = tel_repo.get_factory_overview()
    rows = []

    for item in overview_data:
        max_ts = item.get("ultimo_timestamp_ms") or POC_FIM_MS
        iso_str = (
            datetime.fromtimestamp(max_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if max_ts > 0
            else ""
        )

        rows.append({
            "equipamento_id": item["equipamento_id"],
            "codigo": item["codigo"],
            "descricao": item["descricao"],
            "status_operacional": item["status_geral"],
            "motivo": item.get("motivo", ""),
            "total_tags": len(item.get("leituras_recentes", [])),
            "ultima_leitura_time": iso_str,
            "ultima_leitura_timestamp": max_ts,
        })

    return rows


@router.get("/alarms", summary="Central de alarmes formatada para tabela do Grafana")
def get_grafana_alarms(
    equipamento_id: Optional[int] = Query(None, description="Filtrar por equipamento"),
    from_param: Optional[str] = Query(None, alias="from", description="Timestamp inicial"),
    to_param: Optional[str] = Query(None, alias="to", description="Timestamp final"),
    limit: int = Query(100, description="Limite de registros"),
    tel_repo: TelemetryRepository = Depends(get_telemetry_repository),
):
    """
    Retorna lista de alarmes e anomalias registradas no formato de tabela para o Grafana.
    """
    f_end = parse_timestamp_ms(to_param, POC_FIM_MS)
    f_start = parse_timestamp_ms(from_param, POC_FIM_MS - (30 * 86_400_000))

    events = tel_repo.get_alarm_events(
        equipamento_id=equipamento_id,
        start_ms=f_start,
        end_ms=f_end,
        limit=limit,
    )

    rows = []
    for ev in events:
        ts = ev["source_timestamp_ms"]
        iso_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        rows.append({
            "time": iso_str,
            "timestamp": ts,
            "equipamento": ev["equipamento_descricao"],
            "codigo": ev["equipamento_codigo"],
            "ponto": ev["ponto_medicao"],
            "grandeza": ev["grandeza"],
            "valor": ev["valor"],
            "unidade": ev["unidade"],
            "severidade": ev["severidade"],
            "tipo_alarme": ev["tipo_alarme"],
            "mensagem": ev["mensagem"],
            "status_code": ev["status_code"],
            "latencia_ms": ev["latencia_ms"],
        })

    return rows


@router.get("/variables/equipments", summary="Opções de equipamentos para Template Variables do Grafana")
def get_variable_equipments(
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Retorna array no formato padrão de variáveis de template do Grafana:
    [{"text": "...", "value": "..."}].
    """
    equips = eq_repo.list_equipments()
    return [
        {
            "text": f"{eq['codigo']} — {eq['descricao']}",
            "value": eq["equipamento_id"],
            "codigo": eq["codigo"],
            "descricao": eq["descricao"],
        }
        for eq in equips
    ]


@router.get("/variables/tags", summary="Opções de tags para Template Variables do Grafana")
def get_variable_tags(
    equipamento_id: Optional[int] = Query(None, description="Filtrar por ID do equipamento"),
    eq_repo: EquipmentRepository = Depends(get_equipment_repository),
):
    """
    Retorna tags mapeadas formatadas para dropdowns do Grafana.
    """
    tags = eq_repo.list_tags(equipamento_id=equipamento_id)
    return [
        {
            "text": f"{t['ponto_medicao']} — {t['grandeza']} ({t['unidade']}) [{t['equipamento_codigo']}]",
            "value": t["no_id"],
            "equipamento_id": t["equipamento_id"],
            "equipamento_codigo": t["equipamento_codigo"],
            "ponto": t["ponto_medicao"],
            "grandeza": t["grandeza"],
            "unidade": t["unidade"],
            "limite_atencao": t["limite_atencao"],
            "limite_critico": t["limite_critico"],
        }
        for t in tags
    ]
