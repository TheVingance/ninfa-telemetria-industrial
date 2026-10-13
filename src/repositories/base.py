"""
base.py — Interfaces abstratas para a camada de repositórios.

Define os contratos (Protocol classes) que qualquer implementação de
banco de dados deve satisfazer. Atualmente implementado com SQLite;
futuramente será substituído por Oracle / Projeto On Time.

Uso do Repository Pattern:
  - SQLite (atual):  sqlite_equipment_repo.py, sqlite_telemetry_repo.py
  - Oracle (futuro): oracle_equipment_repo.py, oracle_telemetry_repo.py
"""

from abc import ABC, abstractmethod
from typing import Optional


class EquipmentRepository(ABC):
    """Contrato para acesso a dados de equipamentos e mapeamento de tags."""

    @abstractmethod
    def list_equipments(self) -> list[dict]:
        """Retorna todos os equipamentos cadastrados."""
        ...

    @abstractmethod
    def get_equipment(self, equipamento_id: int) -> Optional[dict]:
        """Retorna um equipamento pelo ID."""
        ...

    @abstractmethod
    def list_tags(self, equipamento_id: Optional[int] = None) -> list[dict]:
        """Retorna os mapeamentos de tag, opcionalmente filtrados por equipamento."""
        ...

    @abstractmethod
    def get_tag(self, no_id: int) -> Optional[dict]:
        """Retorna o mapeamento de uma tag específica."""
        ...

    @abstractmethod
    def update_tag_limits(
        self, no_id: int, limite_atencao: float, limite_critico: float
    ) -> bool:
        """Atualiza os limites de atenção e crítico de uma tag."""
        ...


class TelemetryRepository(ABC):
    """Contrato para acesso a dados de leituras e séries temporais."""

    @abstractmethod
    def get_time_series(
        self,
        no_id: int,
        start_ms: int,
        end_ms: int,
        bucket_ms: int,
    ) -> list[dict]:
        """
        Retorna série temporal agregada em buckets.
        Cada bucket contém: timestamp, média, min, max, contagens de status
        e latência média de ingestão.
        """
        ...

    @abstractmethod
    def get_latest_readings(self, equipamento_id: int) -> list[dict]:
        """Retorna a leitura mais recente de cada nó de um equipamento."""
        ...

    @abstractmethod
    def get_alarm_events(
        self,
        equipamento_id: Optional[int] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Retorna eventos de alarme: leituras que ultrapassaram limites
        operacionais ou apresentaram StatusCode Bad/Uncertain.
        """
        ...

    @abstractmethod
    def get_data_quality_summary(
        self,
        no_id: int,
        start_ms: int,
        end_ms: int,
    ) -> dict:
        """
        Retorna resumo de qualidade dos dados: contagem de Good, Uncertain,
        Bad e gaps detectados no período.
        """
        ...
