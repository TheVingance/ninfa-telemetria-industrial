"""
src/repositories/__init__.py

Exporta as interfaces abstratas e as implementações concretas (SQLite).
Permite futura injeção de dependência transparente para Oracle / On Time.
"""

from src.repositories.base import EquipmentRepository, TelemetryRepository
from src.repositories.sqlite_equipment_repo import SQLiteEquipmentRepository
from src.repositories.sqlite_telemetry_repo import SQLiteTelemetryRepository

__all__ = [
    "EquipmentRepository",
    "TelemetryRepository",
    "SQLiteEquipmentRepository",
    "SQLiteTelemetryRepository",
]
