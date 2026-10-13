"""
predictive.py — Módulo de Análise Preditiva e Detecção de Tendências Industriais.

Implementa:
1. Regressão linear de tendência (taxa de variação horária e projeção de LSE).
2. Estimativa de tempo restante até atingir Limite de Atenção e Limite Crítico.
3. Detecção de anomalias estatísticas via Z-score (afastamento em desvios-padrão).
"""

from typing import Optional
import numpy as np


def calculate_linear_trend(
    timestamps_ms: list[int],
    values: list[float],
) -> dict:
    """
    Calcula regressão linear sobre série temporal.
    Retorna inclinação por hora (slope_per_hour), intercepto, coeficiente R²
    e direção da tendência.
    """
    if len(timestamps_ms) < 3 or len(values) < 3:
        return {
            "slope_per_hour": 0.0,
            "r2": 0.0,
            "direction": "insuficiente",
        }

    # Converter timestamps de ms para horas relativas ao início da janela
    t0 = timestamps_ms[0]
    t_hours = np.array([(ts - t0) / 3_600_000.0 for ts in timestamps_ms], dtype=np.float64)
    y = np.array(values, dtype=np.float64)

    # Regressão linear de 1º grau
    slope, intercept = np.polyfit(t_hours, y, deg=1)

    # Coeficiente de determinação R²
    y_pred = slope * t_hours + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    r2 = max(0.0, min(1.0, float(r2)))

    # Direção da tendência
    if abs(slope) < 0.01:
        direction = "estavel"
    elif slope > 0:
        direction = "subindo"
    else:
        direction = "descendo"

    return {
        "slope_per_hour": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
        "r2": round(r2, 3),
        "direction": direction,
    }


def project_time_to_limits(
    current_value: float,
    slope_per_hour: float,
    limit_attention: Optional[float],
    limit_critical: Optional[float],
) -> dict:
    """
    Estima quantas horas faltam para atingir os limites se a taxa atual se mantiver.
    """
    hours_to_attention: Optional[float] = None
    hours_to_critical: Optional[float] = None

    if slope_per_hour > 0.001:
        if limit_attention is not None and current_value < limit_attention:
            hours_to_attention = round((limit_attention - current_value) / slope_per_hour, 1)

        if limit_critical is not None and current_value < limit_critical:
            hours_to_critical = round((limit_critical - current_value) / slope_per_hour, 1)

    return {
        "hours_to_attention": hours_to_attention,
        "hours_to_critical": hours_to_critical,
    }


def detect_statistical_anomalies(
    values: list[float],
    z_threshold: float = 3.0,
) -> list[int]:
    """
    Retorna os índices da lista onde o valor se afasta em mais de z_threshold
    desvios padrão da média (|z| > 3.0).
    """
    if len(values) < 5:
        return []

    arr = np.array(values, dtype=np.float64)
    mean = np.mean(arr)
    std = np.std(arr)

    if std < 1e-6:
        return []

    z_scores = np.abs((arr - mean) / std)
    anomalous_indices = np.where(z_scores > z_threshold)[0].tolist()
    return anomalous_indices


def analyze_predictive_health(
    readings: list[dict],
    limit_attention: Optional[float],
    limit_critical: Optional[float],
    grandeza: str = "VALOR",
    unidade: str = "",
) -> dict:
    """
    Análise preditiva consolidada para exibição em dashboard.
    Recebe leituras já ordenadas por timestamp.
    """
    if not readings:
        return {
            "status": "dados_insuficientes",
            "mensagem": "Sem dados suficientes para análise preditiva.",
            "slope_per_hour": 0.0,
            "r2": 0.0,
            "hours_to_attention": None,
            "hours_to_critical": None,
            "anomalias_detectadas": 0,
        }

    # Filtrar apenas leituras válidas para o modelo
    valid_pts = [
        r for r in readings
        if r.get("media") is not None or r.get("valor") is not None
    ]

    if len(valid_pts) < 3:
        return {
            "status": "dados_insuficientes",
            "mensagem": "Pontos válidos insuficientes.",
            "slope_per_hour": 0.0,
            "r2": 0.0,
            "hours_to_attention": None,
            "hours_to_critical": None,
            "anomalias_detectadas": 0,
        }

    timestamps = [r.get("timestamp") or r.get("source_timestamp_ms") for r in valid_pts]
    values = [r.get("media") if r.get("media") is not None else r.get("valor") for r in valid_pts]

    trend = calculate_linear_trend(timestamps, values)
    current_val = values[-1]
    slope = trend["slope_per_hour"]

    projections = project_time_to_limits(current_val, slope, limit_attention, limit_critical)
    anomalies = detect_statistical_anomalies(values)

    # Mensagem contextual para o operador industrial
    if trend["direction"] == "subindo" and slope > 0.05:
        if projections["hours_to_critical"] is not None and projections["hours_to_critical"] <= 48:
            status = "critico_iminente"
            msg = (
                f"Alerta Preditivo: Tendência de elevação a {slope:+.2f} {unidade}/h. "
                f"Projeção de ultrapassar Limite Crítico em ~{projections['hours_to_critical']}h."
            )
        elif projections["hours_to_attention"] is not None and projections["hours_to_attention"] <= 72:
            status = "atencao_iminente"
            msg = (
                f"Atenção Preditiva: Taxa de subida de {slope:+.2f} {unidade}/h. "
                f"Projeção de atingir Limite de Atenção em ~{projections['hours_to_attention']}h."
            )
        else:
            status = "tendencia_alta"
            msg = f"Tendência de aumento de {slope:+.2f} {unidade}/h (estabilidade sob monitoramento)."
    elif trend["direction"] == "descendo":
        status = "estabilizando"
        msg = f"Tendência decrescente ({slope:+.2f} {unidade}/h) — grandezas em alívio operacional."
    else:
        status = "estavel"
        msg = "Comportamento térmico e vibratório estável na janela analisada."

    return {
        "status": status,
        "mensagem": msg,
        "slope_per_hour": slope,
        "direction": trend["direction"],
        "r2": trend["r2"],
        "valor_atual": current_val,
        "hours_to_attention": projections["hours_to_attention"],
        "hours_to_critical": projections["hours_to_critical"],
        "anomalias_detectadas": len(anomalies),
    }
