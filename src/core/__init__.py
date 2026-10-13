"""
src/core/__init__.py — Regras de negócio, status OPC UA e análise preditiva.
"""

from src.core.status_codes import (
    OpcUaStatusCode,
    STATUS_LABELS,
    STATUS_COLORS,
    is_valid_reading,
    is_usable_reading,
    classify_reading,
)
from src.core.predictive import (
    calculate_linear_trend,
    project_time_to_limits,
    detect_statistical_anomalies,
    analyze_predictive_health,
)

__all__ = [
    "OpcUaStatusCode",
    "STATUS_LABELS",
    "STATUS_COLORS",
    "is_valid_reading",
    "is_usable_reading",
    "classify_reading",
    "calculate_linear_trend",
    "project_time_to_limits",
    "detect_statistical_anomalies",
    "analyze_predictive_health",
]
