"""
dependencies.py — Injeção de dependências para os repositórios da aplicação.

Centraliza a instanciação dos repositórios para que futuras trocas de banco
(ex: SQLite para Oracle / On Time) ocorram em um único ponto.
"""

from functools import lru_cache
from src.config import DATABASE_PATH
from src.repositories import (
    EquipmentRepository,
    TelemetryRepository,
    SQLiteEquipmentRepository,
    SQLiteTelemetryRepository,
)


@lru_cache()
def get_equipment_repository() -> EquipmentRepository:
    """Retorna a instância singleton do repositório de equipamentos."""
    return SQLiteEquipmentRepository(DATABASE_PATH)


@lru_cache()
def get_telemetry_repository() -> TelemetryRepository:
    """Retorna a instância singleton do repositório de telemetria."""
    return SQLiteTelemetryRepository(DATABASE_PATH)
