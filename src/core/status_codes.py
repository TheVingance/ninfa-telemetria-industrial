"""
status_codes.py — Tratamento de StatusCode OPC UA.

Define os códigos de qualidade usados na base e funções utilitárias
para classificar e filtrar leituras por qualidade.
"""

from enum import IntEnum


class OpcUaStatusCode(IntEnum):
    """Códigos de qualidade OPC UA presentes na base do PoC."""

    GOOD = 0
    UNCERTAIN = 1_073_741_824   # 0x40000000
    BAD = 2_147_483_648         # 0x80000000


# Mapeamento para exibição na interface
STATUS_LABELS = {
    OpcUaStatusCode.GOOD: "Good",
    OpcUaStatusCode.UNCERTAIN: "Uncertain",
    OpcUaStatusCode.BAD: "Bad",
}

STATUS_COLORS = {
    OpcUaStatusCode.GOOD: "#10b981",       # Verde esmeralda
    OpcUaStatusCode.UNCERTAIN: "#f59e0b",  # Âmbar
    OpcUaStatusCode.BAD: "#ef4444",        # Vermelho
}


def is_valid_reading(status_code: int) -> bool:
    """Retorna True se a leitura é válida para plotagem e cálculos."""
    return status_code == OpcUaStatusCode.GOOD


def is_usable_reading(status_code: int) -> bool:
    """Retorna True se a leitura pode ser exibida (Good ou Uncertain)."""
    return status_code in (OpcUaStatusCode.GOOD, OpcUaStatusCode.UNCERTAIN)


def classify_reading(status_code: int) -> str:
    """Classifica a leitura como 'good', 'uncertain' ou 'bad'."""
    try:
        return OpcUaStatusCode(status_code).name.lower()
    except ValueError:
        return "unknown"
