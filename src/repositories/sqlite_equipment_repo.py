"""
sqlite_equipment_repo.py — Implementação SQLite do repositório de equipamentos.

Lê dados das tabelas: equipamento, no_opcua, mapeamento_tag, servidor_opcua.
"""

import sqlite3
from typing import Optional

from src.repositories.base import EquipmentRepository


class SQLiteEquipmentRepository(EquipmentRepository):
    """Acesso a equipamentos e mapeamento de tags via SQLite."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_equipments(self) -> list[dict]:
        """Retorna todos os equipamentos com contagem de nós mapeados."""
        conn = self._connect()
        cursor = conn.execute(
            """
            SELECT
                e.equipamento_id,
                e.codigo,
                e.descricao,
                COUNT(mt.no_id) AS total_nos
            FROM equipamento e
            LEFT JOIN mapeamento_tag mt ON mt.equipamento_id = e.equipamento_id
            GROUP BY e.equipamento_id
            ORDER BY e.equipamento_id
            """
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_equipment(self, equipamento_id: int) -> Optional[dict]:
        """Retorna um equipamento pelo ID com suas tags mapeadas."""
        conn = self._connect()

        cursor = conn.execute(
            "SELECT * FROM equipamento WHERE equipamento_id = ?",
            (equipamento_id,),
        )
        equip_row = cursor.fetchone()
        if equip_row is None:
            conn.close()
            return None

        equip = dict(equip_row)

        # Buscar tags associadas
        cursor = conn.execute(
            """
            SELECT
                mt.no_id,
                n.node_id,
                n.dispositivo_simulado,
                mt.ponto_medicao,
                mt.grandeza,
                mt.unidade,
                mt.limite_atencao,
                mt.limite_critico
            FROM mapeamento_tag mt
            JOIN no_opcua n ON n.no_id = mt.no_id
            WHERE mt.equipamento_id = ?
            ORDER BY mt.ponto_medicao, mt.grandeza
            """,
            (equipamento_id,),
        )
        equip["tags"] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return equip

    def list_tags(self, equipamento_id: Optional[int] = None) -> list[dict]:
        """Retorna os mapeamentos de tag, opcionalmente filtrados por equipamento."""
        conn = self._connect()
        query = """
            SELECT
                mt.no_id,
                n.node_id,
                n.dispositivo_simulado,
                e.equipamento_id,
                e.codigo AS equipamento_codigo,
                e.descricao AS equipamento_descricao,
                mt.ponto_medicao,
                mt.grandeza,
                mt.unidade,
                mt.limite_atencao,
                mt.limite_critico
            FROM mapeamento_tag mt
            JOIN no_opcua n ON n.no_id = mt.no_id
            JOIN equipamento e ON e.equipamento_id = mt.equipamento_id
        """
        params = ()
        if equipamento_id is not None:
            query += " WHERE mt.equipamento_id = ?"
            params = (equipamento_id,)
        query += " ORDER BY mt.no_id"

        cursor = conn.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_tag(self, no_id: int) -> Optional[dict]:
        """Retorna o mapeamento de uma tag específica."""
        conn = self._connect()
        cursor = conn.execute(
            """
            SELECT
                mt.no_id,
                n.node_id,
                n.dispositivo_simulado,
                e.equipamento_id,
                e.codigo AS equipamento_codigo,
                e.descricao AS equipamento_descricao,
                mt.ponto_medicao,
                mt.grandeza,
                mt.unidade,
                mt.limite_atencao,
                mt.limite_critico
            FROM mapeamento_tag mt
            JOIN no_opcua n ON n.no_id = mt.no_id
            JOIN equipamento e ON e.equipamento_id = mt.equipamento_id
            WHERE mt.no_id = ?
            """,
            (no_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_tag_limits(
        self, no_id: int, limite_atencao: float, limite_critico: float
    ) -> bool:
        """Atualiza os limites de atenção e crítico de uma tag."""
        conn = self._connect()
        cursor = conn.execute(
            """
            UPDATE mapeamento_tag
            SET limite_atencao = ?, limite_critico = ?
            WHERE no_id = ?
            """,
            (limite_atencao, limite_critico, no_id),
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
