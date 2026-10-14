# Guia de Integração — Grafana & Ninfa Telemetria Industrial

> **Público-Alvo:** Engenharia de Automação, Equipe MEIU, TI e Administradores Grafana da Ninfa Alimentos.  
> **Versão da API:** 0.1.0 (Oracle-Ready)  
> **Arquivo de Dashboard Pronto:** [`dashboards/grafana_ninfa_telemetria.json`](../dashboards/grafana_ninfa_telemetria.json)

---

## 1. Visão Geral e Arquitetura

Este documento orienta a equipe técnica da **Ninfa Alimentos** a integrar o sistema de monitoramento de vibração e temperatura com o **Grafana** já em operação na planta fabril.

Existem duas vias arquiteturais suportadas pelo projeto:

```
[ SENSORES / CLP ] ---> [ OPC UA SERVER ] ---> [ BANCO DE DADOS ]
                                                      |
    +-------------------------------------------------+
    | (Via B: Conexão Direta SQL - Oracle/SQLite)     | (Camada de Persistência)
    v                                                 v
[ PLUGIN ORACLE / SQL ]                     [ API FASTAPI NINFA ]
         |                                  (Downsampling, LIE/LSE, Qualidade OPC UA)
         |                                            |
         |                                            | (Via A: REST API - RECOMENDADA)
         v                                            v
    [ GRAFANA ] <--------------------------- [ PLUGIN INFINITY ]
```

### 1.1. Comparativo Técnico entre as Abordagens

| Critério | **Via A: REST API (Plugin Infinity)** ⭐ *Recomendada* | **Via B: Conexão Direta ao Banco (Oracle / SQL)** |
| :--- | :--- | :--- |
| **Desacoplamento do Banco** | **Total.** A migração de SQLite para Oracle é 100% transparente para os painéis. | **Nenhum.** Painéis precisam ser reconfigurados na troca de driver. |
| **Downsampling Temporal** | **Automático.** A API agrega 4 milhões de pontos em baldes de 5m, 1h ou 1d conforme o zoom. | **Manual.** Exige queries SQL complexas com agrupamentos matemáticos por janela. |
| **Tratamento OPC UA** | **Nativo.** Diferenciação estrita de *Good (0)*, *Uncertain* e *Bad*, sem traçar linha contínua em falhas. | Deve ser tratado caso a caso em cláusulas `CASE WHEN` no SQL. |
| **Limites Operacionais** | Retornados dinamicamente junto com as leituras (LIE, LSE, Atenção e Crítico). | Exige `JOIN` contínuo com a tabela `mapeamento_tag`. |

---

## 2. Via A (Recomendada): Integração via API REST (Plugin Infinity)

O plugin **Infinity** é o padrão recomendado no ecossistema Grafana para consumir APIs REST em formato JSON, transformando as respostas automaticamente em séries temporais e tabelas industriais.

### 2.1. Instalação do Plugin Infinity no Grafana

Caso o Grafana da Ninfa ainda não possua o plugin instalado, execute no servidor do Grafana:

```bash
grafana-cli plugins install yesoreyeram-infinity-datasource
```

Ou, se estiver utilizando Docker:
```bash
docker run -d -p 3000:3000 \
  -e "GF_INSTALL_PLUGINS=yesoreyeram-infinity-datasource" \
  grafana/grafana:latest
```

Após a instalação, reinicie o serviço do Grafana:
```bash
systemctl restart grafana-server
```

---

### 2.2. Criação da Fonte de Dados (Data Source)

1. No menu lateral do Grafana, navegue até **Connections** $\rightarrow$ **Data sources** $\rightarrow$ **Add new data source**.
2. Pesquise por **Infinity** e selecione-o.
3. Defina as configurações básicas:
   - **Name:** `Ninfa-Telemetria-API`
   - **Type:** `Infinity`
   - **Authentication:** `None` (ou configure API Key caso ative autenticação no proxy reverso).
   - **Base URL:** `http://<IP_DO_SERVIDOR_NINFA>:8000` (ex.: `http://192.168.1.100:8000` ou `http://localhost:8000`).
4. Clique em **Save & Test**. Deve retornar a mensagem de sucesso: *"Data source is working"*.

---

### 2.3. Importação do Dashboard Pré-configurado

Disponibilizamos um painel industrial pronto com layout de alta performance (ISA-101) em [`dashboards/grafana_ninfa_telemetria.json`](../dashboards/grafana_ninfa_telemetria.json).

Para importar:
1. No menu lateral do Grafana, clique em **Dashboards** $\rightarrow$ **New** $\rightarrow$ **Import**.
2. Faça o upload do arquivo `dashboards/grafana_ninfa_telemetria.json` (ou copie e cole seu conteúdo).
3. No campo **Data Source**, selecione a fonte `Ninfa-Telemetria-API` criada no passo anterior.
4. Clique em **Import**.

O dashboard será aberto imediatamente com os seguintes recursos:
- **Seletores no Topo (Dropdowns):**
  - **Equipamento:** Seleção entre os 10 equipamentos da fábrica (ex.: Forno, Amassadeira, Chiller).
  - **Ponto / Grandeza (Tag):** Seleção do nó OPC UA (`P01`, `P02`, Temperatura ou Vibração RMS).
  - **Resolução (Bucket):** `auto` (dinâmico), `5min`, `15min`, `1h`, `6h`, `1d`.
- **Cartões de Estado (KPIs):**
  - Status operacional da planta (Normal, Atenção, Crítico).
  - Último valor lido da tag selecionada.
  - Latência média de ingestão da rede industrial.
  - Indicador de qualidade do sinal OPC UA (*Good / Uncertain / Bad*).
- **Gráficos de Tendência:**
  - Curva de tendência temporal contendo linhas horizontais tracejadas dos limites cadastrados (Atenção e Crítico).
  - Histórico de latência de transmissão em milissegundos.
- **Central de Eventos:**
  - Tabela com registro das últimas anomalias e ultrapassagens de limites com coloração conforme severidade.

---

## 3. Dicionário de Endpoints da API para o Grafana

Todos os endpoints estão documentados interativamente no Swagger da aplicação em `http://<IP>:8000/docs`.

### 3.1. Série Temporal com Downsampling: `/api/grafana/series`
- **Método:** `GET`
- **Finalidade:** Alimentar painéis do tipo **Time Series**, **State Timeline** ou **Stat**.
- **Parâmetros de Consulta (Query String):**
  - `no_id` *(int, opcional)*: ID do nó OPC UA (1 a 38).
  - `equipamento_id` *(int, opcional)*: ID do equipamento (1 a 10). Usado caso `no_id` não seja informado.
  - `grandeza` *(string, opcional)*: `TEMPERATURA` ou `VIBRACAO_RMS`.
  - `ponto` *(string, opcional)*: `P01` ou `P02` (padrão: `P01`).
  - `from` *(string/int, opcional)*: Início em ISO-8601 ou Epoch ms (variável `${__from}` do Grafana).
  - `to` *(string/int, opcional)*: Fim em ISO-8601 ou Epoch ms (variável `${__to}` do Grafana).
  - `bucket` *(string, opcional)*: `auto`, `5min`, `15min`, `1h`, `6h`, `1d`.
  - `raw` *(bool, opcional)*: `true` para forçar pontos brutos (máximo 1000).

**Exemplo de Resposta JSON:**
```json
[
  {
    "time": "2026-09-22T00:00:00Z",
    "timestamp": 1790035200000,
    "equipamento_codigo": "MBF1.1FRN01",
    "equipamento_descricao": "FORNO",
    "ponto": "P01",
    "grandeza": "VIBRACAO_RMS",
    "unidade": "mm/s",
    "valor": 1.7,
    "minimo": 1.39,
    "maximo": 2.01,
    "limite_atencao": 4.5,
    "limite_critico": 7.1,
    "latencia_ms": 3000.0,
    "total_leituras": 288,
    "status_code": 0,
    "qualidade": "Good"
  }
]
```

### 3.2. Visão Geral Fabril: `/api/grafana/overview`
- **Método:** `GET`
- **Finalidade:** Alimentar painéis de resumo fabril (**Polystat**, **Bar Gauge**, **Table**).
- **Retorno:** Status de cada um dos 10 equipamentos com status consolidado (`normal`, `atencao`, `critico`), motivo da pior tag e timestamp da última leitura.

### 3.3. Central de Alarmes e Eventos: `/api/grafana/alarms`
- **Método:** `GET`
- **Parâmetros:**
  - `equipamento_id` *(int, opcional)*: Filtro por máquina.
  - `from` / `to` *(string, opcional)*: Período.
  - `limit` *(int, padrão: 100)*: Quantidade máxima de registros.
- **Retorno:** Registros com severidade (`critico`, `atencao`, `informativo`), mensagem descritiva e dados da medição.

### 3.4. Variáveis de Template: `/api/grafana/variables/equipments` e `/api/grafana/variables/tags`
- Fornecem listas estruturadas com `{ "text": "...", "value": "..." }` para preenchimento automático das caixas de seleção do Grafana sem necessidade de escrever queries manuais.

---

## 4. Via B: Conexão Direta SQL (Oracle Database & SQLite)

Caso a equipe de TI da Ninfa prefira conectar o Grafana diretamente ao banco corporativo Oracle via plugin **Oracle Database Data Source**, utilize as consultas otimizadas abaixo.

### 4.1. Configuração do Data Source Oracle no Grafana
- **Host:** `<IP_ORACLE>:<PORTA>/<SERVICE_NAME>`
- **User / Password:** Credenciais com permissão de leitura (`SELECT`) nas tabelas `leitura_opcua`, `no_opcua`, `mapeamento_tag` e `equipamento`.

### 4.2. Query 1: Série Temporal com Agregação e Macros do Grafana (Oracle)
Esta consulta utiliza a macro `$__timeFilter` do Grafana para limitar o período e realiza o downsampling agrupando em blocos de 1 hora:

```sql
SELECT
    TO_DATE('1970-01-01', 'YYYY-MM-DD') + (TRUNC(l.source_timestamp_ms / 3600000) * 3600 / 86400) AS "time",
    ROUND(AVG(l.valor), 2) AS "valor_medio",
    ROUND(MIN(l.valor), 2) AS "minimo",
    ROUND(MAX(l.valor), 2) AS "maximo",
    AVG(mt.limite_atencao) AS "limite_atencao",
    AVG(mt.limite_critico) AS "limite_critico"
FROM leitura_opcua l
JOIN mapeamento_tag mt ON mt.no_id = l.no_id
WHERE
    l.no_id = :tag
    AND l.status_code = 0 -- Apenas medições válidas (Good)
    AND l.source_timestamp_ms >= :__from
    AND l.source_timestamp_ms <= :__to
GROUP BY TRUNC(l.source_timestamp_ms / 3600000)
ORDER BY "time" ASC;
```

> [!NOTE]
> No Oracle, para plotar linhas de threshold contínuas nos gráficos de série temporal, as colunas `limite_atencao` e `limite_critico` são projetadas na mesma query com agregação `AVG()`.

### 4.3. Query 2: Cálculo de Latência de Ingestão (Oracle)
Monitora a latência entre a geração do dado no sensor e o registro no banco:

```sql
SELECT
    TO_DATE('1970-01-01', 'YYYY-MM-DD') + (TRUNC(l.source_timestamp_ms / 3600000) * 3600 / 86400) AS "time",
    ROUND(AVG(l.recebido_em_ms - l.source_timestamp_ms), 0) AS "latencia_media_ms"
FROM leitura_opcua l
WHERE
    l.no_id = :tag
    AND l.source_timestamp_ms >= :__from
    AND l.source_timestamp_ms <= :__to
GROUP BY TRUNC(l.source_timestamp_ms / 3600000)
ORDER BY "time" ASC;
```

### 4.4. Query 3: Distribuição de Qualidade do Sinal OPC UA (Oracle)
Agrupa o volume de coletas pelos 3 status codes padronizados:

```sql
SELECT
    CASE l.status_code
        WHEN 0 THEN 'Good (Válido)'
        WHEN 1073741824 THEN 'Uncertain (Incerto)'
        WHEN 2147483648 THEN 'Bad (Falha de Sensor)'
        ELSE 'Desconhecido'
    END AS metric,
    COUNT(*) AS total_ocorrencias
FROM leitura_opcua l
WHERE
    l.no_id = :tag
    AND l.source_timestamp_ms >= :__from
    AND l.source_timestamp_ms <= :__to
GROUP BY l.status_code;
```

---

## 5. Diretrizes de Ergonomia Visual (ISA-101) no Grafana

Para manter a consistência com a IHM da planta da Ninfa e as recomendações da norma ISA-101:

1. **Evitar Saturação de Cores:**
   - Telas de operação devem adotar tema escuro (*Dark Mode*).
   - Não utilizar cores chamativas para condições normais de funcionamento.
2. **Convenção de Cores para Limites e Alarmes:**
   - **Operação Normal:** Cinza neutro (`#94a3b8`) ou verde suave (`#10b981`).
   - **Atenção:** Âmbar / Amarelo industrial (`#f59e0b`).
   - **Crítico:** Vermelho vivo (`#ef4444`).
   - **Falha de Comunicação / Bad:** Vermelho escuro ou cinza com indicador de gap.
3. **Tratamento de Dados Inválidos (*Bad*):**
   - No Grafana Time Series Panel, configure o campo `Connect null values` como **Never**.
   - Valores `NULL` provenientes de *StatusCode Bad* não devem ser conectados por linhas contínuas para não induzir a equipe de manutenção ao erro.

---

## 6. Suporte e Validação Rápida

Para verificar rapidamente se a API está respondendo antes de conectar o Grafana, execute no terminal da rede interna:

```bash
# Validar saúde da integração
curl http://localhost:8000/api/grafana/health

# Consultar primeiras medições da tag 1
curl "http://localhost:8000/api/grafana/series?no_id=1&bucket=1d"

# Consultar lista de equipamentos para variáveis
curl http://localhost:8000/api/grafana/variables/equipments
```

Caso ocorra qualquer dúvida, consulte também a documentação de transição de persistência em [`docs/GUIA_TRANSICAO_ORACLE.md`](./GUIA_TRANSICAO_ORACLE.md).
