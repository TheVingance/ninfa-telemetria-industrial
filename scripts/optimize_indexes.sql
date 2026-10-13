-- ============================================================
-- optimize_indexes.sql
-- Índices adicionais para otimizar consultas analíticas
-- no banco On_Time_POC_OPCUA_1_ano.sqlite
-- ============================================================

-- Índice composto principal (já existe na base fornecida)
-- CREATE INDEX IF NOT EXISTS idx_leitura_no_tempo
--     ON leitura_opcua(no_id, source_timestamp_ms);

-- Índice para filtrar apenas por janela temporal (já existe)
-- CREATE INDEX IF NOT EXISTS idx_leitura_tempo
--     ON leitura_opcua(source_timestamp_ms);

-- Índice para consultas de alarme por status_code
CREATE INDEX IF NOT EXISTS idx_leitura_status
    ON leitura_opcua(no_id, status_code, source_timestamp_ms);

-- Índice para consultas de latência de ingestão
CREATE INDEX IF NOT EXISTS idx_leitura_latencia
    ON leitura_opcua(no_id, source_timestamp_ms, recebido_em_ms);

-- Atualizar estatísticas do otimizador SQLite
ANALYZE;
