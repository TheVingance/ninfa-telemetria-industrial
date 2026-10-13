# 🏛️ Guia de Transição para Oracle (Projeto On Time Ninfa)

Este documento descreve como a equipe de Automação e TI da **Ninfa Alimentos** pode conectar a aplicação ao banco de dados corporativo **Oracle / Projeto On Time** quando a infraestrutura de produção estiver liberada, substituindo a base de dados de Prova de Conceito (SQLite).

---

## 1. Arquitetura Desacoplada (Repository Pattern)

A aplicação foi desenvolvida seguindo o padrão **Repository Pattern**. Isso significa que as regras de negócio, as análises preditivas, os endpoints da API REST e as telas web **não possuem acoplamento com o SQLite**.

```
┌────────────────────────────────────────────────────────┐
│             Frontend Web (HTML / CSS / JS)             │
└───────────────────────────▲────────────────────────────┘
                            │ REST JSON
┌───────────────────────────┴────────────────────────────┐
│         FastAPI Routes (api_telemetry, api_equipments) │
└───────────────────────────▲────────────────────────────┘
                            │ Contrato Abstrato (ABC)
┌───────────────────────────┴────────────────────────────┐
│      src/repositories/base.py (Interfaces Abstratas)   │
└─────────────▲────────────────────────────▲─────────────┘
              │ Implementação              │ Implementação
              │ Atual                      │ Futura
┌─────────────┴─────────────┐ ┌────────────┴─────────────┐
│  SQLite Repositories      │ │  Oracle Repositories     │
│  - sqlite_equipment_repo  │ │  - oracle_equipment_repo │
│  - sqlite_telemetry_repo  │ │  - oracle_telemetry_repo │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 2. Passo a Passo da Migração

### Passo 1: Instalar o driver Oracle
Adicione o driver oficial ao ambiente:
```bash
pip install oracledb
```

### Passo 2: Configurar variáveis de ambiente no `.env`
Defina as credenciais do banco Oracle corporativo:
```env
ORACLE_USER=usr_ninfa_telemetria
ORACLE_PASSWORD=sua_senha_aqui
ORACLE_DSN=oracle-scan.ninfa.com.br:1521/ONTIME_PRD
```

### Passo 3: Implementar os repositórios Oracle
Crie os arquivos em `src/repositories/`:
1. `src/repositories/oracle_equipment_repo.py`:
   - Herda de `EquipmentRepository` (`src.repositories.base`).
   - Implementa os métodos `list_equipments()`, `get_equipment()`, `list_tags()`, `get_tag()`, `update_tag_limits()`.
2. `src/repositories/oracle_telemetry_repo.py`:
   - Herda de `TelemetryRepository` (`src.repositories.base`).
   - Implementa `get_time_series()`, `get_latest_readings()`, `get_alarm_events()`, `get_data_quality_summary()`.

#### Exemplo de Query Downsampling para Oracle:
No Oracle, o agrupamento por bucket temporal pode ser feito diretamente via agregação por intervalo ou funções analíticas:
```sql
SELECT
    TRUNC(source_timestamp, 'HH24') AS bucket_ts,
    ROUND(AVG(valor), 2) AS media,
    ROUND(MIN(valor), 2) AS minimo,
    ROUND(MAX(valor), 2) AS maximo,
    COUNT(*) AS total_leituras,
    SUM(CASE WHEN status_code = 0 THEN 1 ELSE 0 END) AS good_count,
    ROUND(AVG(recebido_em_ms - source_timestamp_ms), 0) AS latencia_media_ms
FROM leitura_opcua
WHERE no_id = :no_id
  AND source_timestamp BETWEEN :inicio AND :fim
GROUP BY TRUNC(source_timestamp, 'HH24')
ORDER BY bucket_ts ASC;
```

### Passo 4: Alternar a Injeção de Dependências
Em [src/dependencies.py](file:///c:/Users/triches/Documents/Projeto%20Extensao%20-%20NINFA/ProjetoNinfa/src/dependencies.py), alterne a inicialização com base em uma variável de ambiente:

```python
import os
from src.repositories.sqlite_equipment_repo import SQLiteEquipmentRepository
from src.repositories.sqlite_telemetry_repo import SQLiteTelemetryRepository
# from src.repositories.oracle_equipment_repo import OracleEquipmentRepository
# from src.repositories.oracle_telemetry_repo import OracleTelemetryRepository

USE_ORACLE = os.environ.get("USE_ORACLE", "false").lower() == "true"

def get_equipment_repository():
    if USE_ORACLE:
        return OracleEquipmentRepository(...)
    return SQLiteEquipmentRepository(DATABASE_PATH)

def get_telemetry_repository():
    if USE_ORACLE:
        return OracleTelemetryRepository(...)
    return SQLiteTelemetryRepository(DATABASE_PATH)
```

Nenhuma linha de código das rotas da API, regras preditivas ou interfaces web precisará ser alterada!
