"""
seed_anexo_a.py — Popula a tabela mapeamento_tag com os 38 nós OPC UA
do Anexo A (Tabela 04) do Memorial Descritivo da Ninfa Alimentos.

Limites de referência padrão baseados em:
  - Vibração RMS: ISO 10816 Classe II (máquinas médias)
  - Temperatura: Referências típicas de mancais/motores industriais

Uso:
    python scripts/seed_anexo_a.py
    python scripts/seed_anexo_a.py --db-path caminho/para/banco.sqlite
"""

import sqlite3
import argparse
import os
import sys

# ============================================================
# Dados do Anexo A — Tabela 04: Correlação mapeamento_tag
# ============================================================

# Mapeamento: equipamento_codigo -> equipamento_id (conforme tabela 'equipamento')
EQUIPAMENTO_MAP = {
    "MBF1.1FRN01": 1,   # FORNO
    "MBE2.1EHR03": 2,   # EMBALADORA HORIZONTAL 03
    "MBH2.2RCH02": 3,   # RECHEADORA
    "MME5.2GVE01": 4,   # GRUPO VENTILAÇÃO 01 ENCARTAMENTO
    "MMP5.3AMS01": 5,   # AMASSADEIRA 01
    "MMS5.4RDS01": 6,   # ROSCA TRANSPORTADORA
    "MMF5.1FTD01": 7,   # FRITADEIRA
    "MWU3.0CRA01": 8,   # CHILLER
    "MWR3.1TRV01": 9,   # TÚNEL DE RESFRIAMENTO VERTICAL
    "MWE3.3EHR01": 10,  # EMPACOTADORA FLOW PACK 01
}

# Limites padrão por grandeza (podem ser ajustados na tela de Configuração)
# Vibração RMS (mm/s) — ISO 10816 Classe II
LIMITES_VIBRACAO = {"limite_atencao": 4.5, "limite_critico": 7.1}

# Temperatura (°C) — Referência para mancais/motores industriais
LIMITES_TEMPERATURA = {"limite_atencao": 70.0, "limite_critico": 85.0}

# Chiller opera com componentes em faixa térmica mais baixa
LIMITES_TEMPERATURA_CHILLER = {"limite_atencao": 50.0, "limite_critico": 65.0}

# ============================================================
# Tabela 04 completa: 38 nós OPC UA
# ============================================================

ANEXO_A = [
    # no_id, tag_equipamento,   ponto, grandeza,        unidade
    (1,  "MBF1.1FRN01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (2,  "MBF1.1FRN01", "P01", "TEMPERATURA",   "°C"),
    (3,  "MBF1.1FRN01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (4,  "MBF1.1FRN01", "P02", "TEMPERATURA",   "°C"),
    (5,  "MBE2.1EHR03", "P01", "VIBRACAO_RMS",  "mm/s"),
    (6,  "MBE2.1EHR03", "P01", "TEMPERATURA",   "°C"),
    (7,  "MBE2.1EHR03", "P02", "VIBRACAO_RMS",  "mm/s"),
    (8,  "MBE2.1EHR03", "P02", "TEMPERATURA",   "°C"),
    (9,  "MBH2.2RCH02", "P01", "VIBRACAO_RMS",  "mm/s"),
    (10, "MBH2.2RCH02", "P01", "TEMPERATURA",   "°C"),
    (11, "MBH2.2RCH02", "P02", "VIBRACAO_RMS",  "mm/s"),
    (12, "MBH2.2RCH02", "P02", "TEMPERATURA",   "°C"),
    (13, "MME5.2GVE01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (14, "MME5.2GVE01", "P01", "TEMPERATURA",   "°C"),
    (15, "MME5.2GVE01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (16, "MME5.2GVE01", "P02", "TEMPERATURA",   "°C"),
    (17, "MMP5.3AMS01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (18, "MMP5.3AMS01", "P01", "TEMPERATURA",   "°C"),
    (19, "MMP5.3AMS01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (20, "MMP5.3AMS01", "P02", "TEMPERATURA",   "°C"),
    (21, "MMS5.4RDS01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (22, "MMS5.4RDS01", "P01", "TEMPERATURA",   "°C"),
    (23, "MMS5.4RDS01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (24, "MMS5.4RDS01", "P02", "TEMPERATURA",   "°C"),
    (25, "MMF5.1FTD01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (26, "MMF5.1FTD01", "P01", "TEMPERATURA",   "°C"),
    (27, "MMF5.1FTD01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (28, "MMF5.1FTD01", "P02", "TEMPERATURA",   "°C"),
    # DEV08 / Chiller — apenas 2 nós de Temperatura (sem vibração)
    (29, "MWU3.0CRA01", "P01", "TEMPERATURA",   "°C"),
    (30, "MWU3.0CRA01", "P02", "TEMPERATURA",   "°C"),
    (31, "MWR3.1TRV01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (32, "MWR3.1TRV01", "P01", "TEMPERATURA",   "°C"),
    (33, "MWR3.1TRV01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (34, "MWR3.1TRV01", "P02", "TEMPERATURA",   "°C"),
    (35, "MWE3.3EHR01", "P01", "VIBRACAO_RMS",  "mm/s"),
    (36, "MWE3.3EHR01", "P01", "TEMPERATURA",   "°C"),
    (37, "MWE3.3EHR01", "P02", "VIBRACAO_RMS",  "mm/s"),
    (38, "MWE3.3EHR01", "P02", "TEMPERATURA",   "°C"),
]


def get_limites(tag: str, grandeza: str) -> dict:
    """Retorna os limites de atenção e crítico para a combinação tag/grandeza."""
    if grandeza == "VIBRACAO_RMS":
        return LIMITES_VIBRACAO
    # Chiller tem faixa térmica diferenciada
    if tag == "MWU3.0CRA01":
        return LIMITES_TEMPERATURA_CHILLER
    return LIMITES_TEMPERATURA


def seed(db_path: str) -> None:
    """Insere os 38 registros do Anexo A na tabela mapeamento_tag."""
    if not os.path.exists(db_path):
        print(f"[ERRO] Banco não encontrado: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar se a tabela já possui dados
    cursor.execute("SELECT COUNT(*) FROM mapeamento_tag;")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"[AVISO] A tabela mapeamento_tag já possui {count} registros.")
        resp = input("Deseja limpar e reinserir? (s/N): ").strip().lower()
        if resp != "s":
            print("[INFO] Operação cancelada.")
            conn.close()
            return
        cursor.execute("DELETE FROM mapeamento_tag;")
        print(f"[INFO] {count} registros removidos.")

    # Inserir os 38 nós do Anexo A
    inseridos = 0
    for no_id, tag, ponto, grandeza, unidade in ANEXO_A:
        equip_id = EQUIPAMENTO_MAP[tag]
        limites = get_limites(tag, grandeza)

        cursor.execute(
            """
            INSERT INTO mapeamento_tag
                (no_id, equipamento_id, ponto_medicao, grandeza, unidade,
                 limite_atencao, limite_critico)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                no_id,
                equip_id,
                ponto,
                grandeza,
                unidade,
                limites["limite_atencao"],
                limites["limite_critico"],
            ),
        )
        inseridos += 1

    conn.commit()

    # Validação
    cursor.execute("SELECT COUNT(*) FROM mapeamento_tag;")
    total = cursor.fetchone()[0]
    conn.close()

    print(f"[OK] {inseridos} registros inseridos na tabela mapeamento_tag.")
    print(f"[OK] Total de registros na tabela: {total}")
    print()
    print("Limites padrão aplicados:")
    print(f"  Vibração RMS:        atenção={LIMITES_VIBRACAO['limite_atencao']} mm/s | crítico={LIMITES_VIBRACAO['limite_critico']} mm/s")
    print(f"  Temperatura (geral): atenção={LIMITES_TEMPERATURA['limite_atencao']} °C  | crítico={LIMITES_TEMPERATURA['limite_critico']} °C")
    print(f"  Temperatura (Chiller): atenção={LIMITES_TEMPERATURA_CHILLER['limite_atencao']} °C  | crítico={LIMITES_TEMPERATURA_CHILLER['limite_critico']} °C")


if __name__ == "__main__":
    # Importar DATABASE_PATH da configuração se disponível
    try:
        from src.config import DATABASE_PATH
        default_db = DATABASE_PATH
    except ImportError:
        default_db = os.path.join(
            os.path.dirname(__file__), "..", "data", "On_Time_POC_OPCUA_1_ano.sqlite"
        )
        if not os.path.exists(default_db):
            root_db = os.path.join(
                os.path.dirname(__file__), "..", "On_Time_POC_OPCUA_1_ano.sqlite"
            )
            if os.path.exists(root_db):
                default_db = root_db

    parser = argparse.ArgumentParser(
        description="Popula mapeamento_tag com os 38 nós do Anexo A."
    )
    parser.add_argument(
        "--db-path",
        default=default_db,
        help="Caminho para o arquivo SQLite",
    )
    args = parser.parse_args()
    seed(os.path.abspath(args.db_path))
