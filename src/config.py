"""
config.py — Configurações centrais da aplicação Ninfa Telemetria Industrial.

Centraliza caminhos, constantes e parâmetros de ambiente.
"""

import os
from pathlib import Path

# ============================================================
# Caminhos
# ============================================================

# Raiz do projeto (pasta que contém src/, data/, scripts/, etc.)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def _find_database_path() -> str:
    if "NINFA_DB_PATH" in os.environ:
        return os.environ["NINFA_DB_PATH"]
    data_path = PROJECT_ROOT / "data" / "On_Time_POC_OPCUA_1_ano.sqlite"
    if data_path.exists():
        return str(data_path)
    root_path = PROJECT_ROOT / "On_Time_POC_OPCUA_1_ano.sqlite"
    if root_path.exists():
        return str(root_path)
    return str(data_path)

DATABASE_PATH = _find_database_path()

# Diretório de arquivos estáticos servidos pelo FastAPI
STATIC_DIR = Path(__file__).resolve().parent / "static"

# ============================================================
# Parâmetros de Downsampling / Agregação
# ============================================================

# Número máximo de pontos retornados por série temporal em um request
MAX_POINTS_PER_SERIES = 500

# Buckets de agregação disponíveis (em milissegundos)
BUCKET_SIZES_MS = {
    "5min":  5 * 60 * 1000,         #    300.000 ms
    "15min": 15 * 60 * 1000,        #    900.000 ms
    "1h":    60 * 60 * 1000,        #  3.600.000 ms
    "6h":    6 * 60 * 60 * 1000,    # 21.600.000 ms
    "1d":    24 * 60 * 60 * 1000,   # 86.400.000 ms
}

# ============================================================
# Limites do Período de Dados do PoC
# ============================================================

# Timestamps Unix (ms) — Conforme metadado_poc do banco
POC_INICIO_MS = 1758585600000   # 23/09/2025 00:00:00 UTC
POC_FIM_MS    = 1758585600000 + (365 * 24 * 60 * 60 * 1000) - (5 * 60 * 1000)
# ~22/09/2026 23:55:00 UTC

# ============================================================
# API
# ============================================================

API_TITLE = "Ninfa Telemetria Industrial"
API_DESCRIPTION = "API REST para monitoramento de vibração e temperatura em equipamentos industriais."
API_VERSION = "0.1.0"
