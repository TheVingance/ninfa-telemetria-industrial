"""
sqlite_telemetry_repo.py — Implementação SQLite do repositório de telemetria.

Executa consultas otimizadas de séries temporais com downsampling/bucketing,
leituras recentes, eventos de alarme e métricas de qualidade de dados.
"""

import sqlite3
from typing import Optional

from src.core.status_codes import OpcUaStatusCode, classify_reading
from src.repositories.base import TelemetryRepository


class SQLiteTelemetryRepository(TelemetryRepository):
    """Acesso a séries temporais e telemetria industrial via SQLite."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_time_series(
        self,
        no_id: int,
        start_ms: int,
        end_ms: int,
        bucket_ms: int = 3_600_000,
    ) -> list[dict]:
        """
        Retorna série temporal agregada em buckets de tempo.
        Se bucket_ms <= 0, retorna leituras brutas limitadas a 1000 pontos.
        """
        conn = self._connect()

        if bucket_ms <= 0:
            query = """
                SELECT
                    source_timestamp_ms AS timestamp,
                    valor AS media,
                    valor AS minimo,
                    valor AS maximo,
                    1 AS total_leituras,
                    (status_code = 0) AS good_count,
                    (status_code = 1073741824) AS uncertain_count,
                    (status_code = 2147483648) AS bad_count,
                    (recebido_em_ms - source_timestamp_ms) AS latencia_media_ms,
                    status_code
                FROM leitura_opcua
                WHERE no_id = ? AND source_timestamp_ms BETWEEN ? AND ?
                ORDER BY source_timestamp_ms ASC
                LIMIT 1000
            """
            cursor = conn.execute(query, (no_id, start_ms, end_ms))
        else:
            query = """
                SELECT
                    (source_timestamp_ms / ?) * ? AS timestamp,
                    ROUND(AVG(valor), 2) AS media,
                    ROUND(MIN(valor), 2) AS minimo,
                    ROUND(MAX(valor), 2) AS maximo,
                    COUNT(*) AS total_leituras,
                    SUM(CASE WHEN status_code = 0 THEN 1 ELSE 0 END) AS good_count,
                    SUM(CASE WHEN status_code = 1073741824 THEN 1 ELSE 0 END) AS uncertain_count,
                    SUM(CASE WHEN status_code = 2147483648 THEN 1 ELSE 0 END) AS bad_count,
                    ROUND(AVG(recebido_em_ms - source_timestamp_ms), 0) AS latencia_media_ms
                FROM leitura_opcua
                WHERE no_id = ? AND source_timestamp_ms BETWEEN ? AND ?
                GROUP BY timestamp
                ORDER BY timestamp ASC
            """
            cursor = conn.execute(query, (bucket_ms, bucket_ms, no_id, start_ms, end_ms))

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_latest_readings(self, equipamento_id: int) -> list[dict]:
        """Retorna a leitura mais recente de cada nó pertencente a um equipamento."""
        conn = self._connect()
        query = """
            SELECT
                mt.no_id,
                mt.equipamento_id,
                e.codigo AS equipamento_codigo,
                e.descricao AS equipamento_descricao,
                mt.ponto_medicao,
                mt.grandeza,
                mt.unidade,
                mt.limite_atencao,
                mt.limite_critico,
                l.source_timestamp_ms,
                l.server_timestamp_ms,
                l.recebido_em_ms,
                ROUND(l.valor, 2) AS valor,
                l.status_code,
                (l.recebido_em_ms - l.source_timestamp_ms) AS latencia_ms
            FROM mapeamento_tag mt
            JOIN equipamento e ON e.equipamento_id = mt.equipamento_id
            JOIN leitura_opcua l ON l.no_id = mt.no_id
            WHERE mt.equipamento_id = ?
              AND l.source_timestamp_ms = (
                  SELECT MAX(l2.source_timestamp_ms)
                  FROM leitura_opcua l2
                  WHERE l2.no_id = mt.no_id
              )
            ORDER BY mt.ponto_medicao, mt.grandeza
        """
        cursor = conn.execute(query, (equipamento_id,))
        rows = []
        for row in cursor.fetchall():
            d = dict(row)
            d["qualidade"] = classify_reading(d["status_code"])

            # Avaliação de status operacional
            valor = d["valor"]
            lim_crit = d["limite_critico"]
            lim_aten = d["limite_atencao"]

            if d["status_code"] == OpcUaStatusCode.BAD:
                d["status_operacional"] = "critico"
                d["motivo_status"] = "Falha de comunicação (Bad StatusCode)"
            elif valor is not None and lim_crit is not None and valor >= lim_crit:
                d["status_operacional"] = "critico"
                d["motivo_status"] = f"Valor ({valor} {d['unidade']}) excedeu Limite Crítico ({lim_crit})"
            elif valor is not None and lim_aten is not None and valor >= lim_aten:
                d["status_operacional"] = "atencao"
                d["motivo_status"] = f"Valor ({valor} {d['unidade']}) excedeu Limite de Atenção ({lim_aten})"
            elif d["status_code"] == OpcUaStatusCode.UNCERTAIN:
                d["status_operacional"] = "atencao"
                d["motivo_status"] = "Sinal Incerto (Uncertain StatusCode)"
            else:
                d["status_operacional"] = "normal"
                d["motivo_status"] = "Operação normal"

            rows.append(d)

        conn.close()
        return rows

    def get_factory_overview(self) -> list[dict]:
        """
        Retorna o resumo de status operacional de todos os 10 equipamentos da fábrica.
        Inclui status consolidado (normal, atencao, critico), contagem de tags e leitura mais recente.
        """
        conn = self._connect()
        # Busca todos os equipamentos
        cur_eq = conn.execute("SELECT equipamento_id, codigo, descricao FROM equipamento ORDER BY equipamento_id")
        equipamentos = [dict(r) for r in cur_eq.fetchall()]
        conn.close()

        overview = []
        for eq in equipamentos:
            readings = self.get_latest_readings(eq["equipamento_id"])
            status_geral = "normal"
            motivo_geral = "Operação estável"
            max_ts = 0

            # Determina o pior status entre as tags do equipamento
            has_critico = any(r["status_operacional"] == "critico" for r in readings)
            has_atencao = any(r["status_operacional"] == "atencao" for r in readings)

            if has_critico:
                status_geral = "critico"
                piores = [r for r in readings if r["status_operacional"] == "critico"]
                motivo_geral = piores[0]["motivo_status"]
            elif has_atencao:
                status_geral = "atencao"
                piores = [r for r in readings if r["status_operacional"] == "atencao"]
                motivo_geral = piores[0]["motivo_status"]
            elif not readings:
                status_geral = "sem_sinal"
                motivo_geral = "Sem tags configuradas ou sem dados"

            for r in readings:
                if r["source_timestamp_ms"] and r["source_timestamp_ms"] > max_ts:
                    max_ts = r["source_timestamp_ms"]

            overview.append({
                "equipamento_id": eq["equipamento_id"],
                "codigo": eq["codigo"],
                "descricao": eq["descricao"],
                "status_geral": status_geral,
                "motivo": motivo_geral,
                "ultimo_timestamp_ms": max_ts,
                "leituras_recentes": readings,
            })

        return overview

    def get_alarm_events(
        self,
        equipamento_id: Optional[int] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Retorna eventos anômalos e alarmes registrados:
        - Leituras que ultrapassaram limite de atenção ou crítico
        - Leituras com StatusCode Bad ou Uncertain
        """
        conn = self._connect()

        where_clauses = [
            "(l.status_code != 0 OR (mt.limite_atencao IS NOT NULL AND l.valor >= mt.limite_atencao))"
        ]
        params = []

        if equipamento_id is not None:
            where_clauses.append("mt.equipamento_id = ?")
            params.append(equipamento_id)

        if start_ms is not None:
            where_clauses.append("l.source_timestamp_ms >= ?")
            params.append(start_ms)

        if end_ms is not None:
            where_clauses.append("l.source_timestamp_ms <= ?")
            params.append(end_ms)

        where_sql = " AND ".join(where_clauses)
        params.append(limit)

        query = f"""
            SELECT
                l.leitura_id,
                l.no_id,
                l.source_timestamp_ms,
                ROUND(l.valor, 2) AS valor,
                l.status_code,
                mt.equipamento_id,
                e.codigo AS equipamento_codigo,
                e.descricao AS equipamento_descricao,
                mt.ponto_medicao,
                mt.grandeza,
                mt.unidade,
                mt.limite_atencao,
                mt.limite_critico,
                (l.recebido_em_ms - l.source_timestamp_ms) AS latencia_ms
            FROM leitura_opcua l
            JOIN mapeamento_tag mt ON mt.no_id = l.no_id
            JOIN equipamento e ON e.equipamento_id = mt.equipamento_id
            WHERE {where_sql}
            ORDER BY l.source_timestamp_ms DESC
            LIMIT ?
        """

        cursor = conn.execute(query, tuple(params))
        events = []

        for row in cursor.fetchall():
            ev = dict(row)
            val = ev["valor"]
            lim_crit = ev["limite_critico"]
            lim_aten = ev["limite_atencao"]
            code = ev["status_code"]

            # Classificação da severidade e categoria do alarme
            if code == OpcUaStatusCode.BAD:
                ev["severidade"] = "critico"
                ev["tipo_alarme"] = "qualidade_dado"
                ev["mensagem"] = f"Falha de comunicação OPC UA (StatusCode Bad)"
            elif code == OpcUaStatusCode.UNCERTAIN:
                ev["severidade"] = "atencao"
                ev["tipo_alarme"] = "qualidade_dado"
                ev["mensagem"] = f"Qualidade do dado incerta (StatusCode Uncertain)"
            elif val is not None and lim_crit is not None and val >= lim_crit:
                ev["severidade"] = "critico"
                ev["tipo_alarme"] = "limite_processo"
                ev["mensagem"] = f"{ev['grandeza']} ({val} {ev['unidade']}) excedeu Limite Crítico ({lim_crit})"
            elif val is not None and lim_aten is not None and val >= lim_aten:
                ev["severidade"] = "atencao"
                ev["tipo_alarme"] = "limite_processo"
                ev["mensagem"] = f"{ev['grandeza']} ({val} {ev['unidade']}) excedeu Limite de Atenção ({lim_aten})"
            else:
                ev["severidade"] = "informativo"
                ev["tipo_alarme"] = "processo"
                ev["mensagem"] = f"Evento em {ev['grandeza']}"

            events.append(ev)

        conn.close()
        return events

    def get_data_quality_summary(
        self,
        no_id: int,
        start_ms: int,
        end_ms: int,
    ) -> dict:
        """
        Retorna resumo de integridade e latência para um nó no período.
        """
        conn = self._connect()
        query = """
            SELECT
                COUNT(*) AS total_leituras,
                SUM(CASE WHEN status_code = 0 THEN 1 ELSE 0 END) AS good_count,
                SUM(CASE WHEN status_code = 1073741824 THEN 1 ELSE 0 END) AS uncertain_count,
                SUM(CASE WHEN status_code = 2147483648 THEN 1 ELSE 0 END) AS bad_count,
                ROUND(AVG(recebido_em_ms - source_timestamp_ms), 1) AS latencia_media_ms,
                MAX(recebido_em_ms - source_timestamp_ms) AS latencia_max_ms,
                MIN(source_timestamp_ms) AS primeiro_ts,
                MAX(source_timestamp_ms) AS ultimo_ts
            FROM leitura_opcua
            WHERE no_id = ? AND source_timestamp_ms BETWEEN ? AND ?
        """
        cursor = conn.execute(query, (no_id, start_ms, end_ms))
        row = cursor.fetchone()
        conn.close()

        if not row or row["total_leituras"] == 0:
            return {
                "total_leituras": 0,
                "good_count": 0,
                "uncertain_count": 0,
                "bad_count": 0,
                "good_pct": 0.0,
                "uncertain_pct": 0.0,
                "bad_pct": 0.0,
                "latencia_media_ms": 0.0,
                "latencia_max_ms": 0,
            }

        total = row["total_leituras"]
        good = row["good_count"] or 0
        uncertain = row["uncertain_count"] or 0
        bad = row["bad_count"] or 0

        return {
            "total_leituras": total,
            "good_count": good,
            "uncertain_count": uncertain,
            "bad_count": bad,
            "good_pct": round((good / total) * 100, 2),
            "uncertain_pct": round((uncertain / total) * 100, 2),
            "bad_pct": round((bad / total) * 100, 2),
            "latencia_media_ms": row["latencia_media_ms"] or 0.0,
            "latencia_max_ms": row["latencia_max_ms"] or 0,
        }
