# AI Agent Guidelines — Ninfa Telemetria Industrial

> **LEITURA OBRIGATÓRIA ANTES DE QUALQUER IMPLEMENTAÇÃO**  
> Este documento define as regras arquiteturais, restrições de banco de dados, padrões de código e regras de negócio para o repositório `ninfa-telemetria-industrial`. Todo agente de IA deve seguir rigorosamente estas diretrizes antes de propor, criar ou alterar qualquer código.

---

## 1. Contexto Rápido do Projeto
- **Projeto:** Prova de Conceito (PoC) para Monitoramento de Vibração e Temperatura Industrial (Ninfa Alimentos / MEIU).
- **Fonte de Dados Atual:** Arquivo local **SQLite** contendo **3.994.557 registros** históricos simulados (intervalos de 5 minutos, de 23/09/2025 a 22/09/2026 UTC).
- **Evolução Futura Obrigatória:** Migração transparente da camada de persistência para **Oracle Database** e integração com o sistema **On Time**, sem refatoração das regras de negócio ou do Frontend.

---

## 2. Protocolo Pré-Implementação (Checklist do Agente)
Antes de gerar código para qualquer funcionalidade, você (Agente) **DEVE**:
1. **Inspecionar o Banco SQLite:** Nunca assuma nomes de colunas ou tipos sem antes verificar o schema real do arquivo SQLite (`sqlite_master`) e o conteúdo da tabela `metadado_poc`.
2. **Garantir Desacoplamento (Oracle-Ready):** Perguntar a si mesmo: *"Se trocarmos o SQLite pelo Oracle amanhã, este código fora da camada de repositório continuará funcionando?"* Se a resposta for não, refatore.
3. **Avaliar Impacto de Performance:** Lembrar que a tabela `leitura_opcua` possui quase **4 milhões de linhas**. Nunca faça `SELECT *` sem paginação, agregação temporal (downsampling) ou filtros indexados.
4. **Criação Obrigatória de Artefato de Plano de Implementação:** Para toda nova funcionalidade, alteração estrutural ou módulo a ser implementado, o Agente **DEVE** obrigatoriamente criar um artefato de plano de implementação detalhado antes de propor, gerar ou modificar qualquer código no repositório.

---

## 3. Diretrizes de Arquitetura e Banco de Dados

### 3.1. Padrão Repository / Data Access Layer (DAL)
- **Proibido:** Escrever queries SQL diretamente em Controllers, Rotas da API ou Serviços de Regra de Negócio.
- **Obrigatório:** Utilizar o padrão **Repository** (ou Adapter). A camada de domínio/serviço deve chamar interfaces abstratas (ex.: `ITelemetryRepository`, `IEquipmentRepository`).
- **Portabilidade SQL (SQLite -> Oracle):**
  - Evite funções exclusivas do SQLite que sejam difíceis de traduzir sem camada intermediária, ou isole-as estritamente dentro de `SqliteTelemetryRepository`.
  - Use parâmetros nomeados ou preparados (Prepared Statements) para evitar SQL Injection e facilitar a portabilidade de driver.

### 3.2. Performance em Séries Temporais (`leitura_opcua`)
- **Indexação:** Antes de rodar queries pesadas, verifique se existem índices em `leitura_opcua(no_id, source_timestamp_ms)`. Caso não existam, crie um script de migração/otimização.
- **Downsampling / Agregação:** O Frontend **nunca** deve receber centenas de milhares de pontos para renderizar um único gráfico.
  - Períodos curtos (ex.: 24h a 7 dias): Retornar dados brutos (intervalos de 5 min).
  - Períodos médios (ex.: 7 a 30 dias): Retornar agregação horária (Média, Mínimo, Máximo).
  - Períodos longos (ex.: > 30 dias / 1 ano): Retornar agregação diária.

---

## 4. Regras de Negócio Inegociáveis (Domínio OPC UA)

### 4.1. Tratamento de Timestamps
Todas as tabelas de leitura possuem 3 colunas de tempo em **Unix Epoch Milissegundos (UTC)**:
1. `source_timestamp_ms`: Horário na origem (sensor/PLC). **DEVE SER USADO como eixo X oficial em todos os gráficos e análises de série temporal.**
2. `server_timestamp_ms`: Horário no servidor OPC UA.
3. `recebido_em_ms`: Horário de gravação no banco.
- **Cálculo de Latência de Ingestão:**
  $$\text{Latência (ms)} = \text{recebido\_em\_ms} - \text{source\_timestamp\_ms}$$

### 4.2. Qualidade do Sinal (`status_code`) vs. Alertas Operacionais
O sistema **jamais** deve confundir falha de leitura/comunicação com anomalia física da máquina:

| `status_code` | Estado OPC UA | Regra de Tratamento no Código e UI |
| :--- | :--- | :--- |
| **`0`** | `Good` | Dado válido. Plota normalmente nos gráficos, calcula KPIs/médias e valida contra limites (LIE/LSE). |
| **`1073741824`** | `Uncertain` | Qualidade incerta. Exibir com marcador visual de aviso na UI; **não** disparar alarme crítico automático sem regra explícita. |
| **`2147483648`** | `Bad` | Dado inválido (`valor` é `NULL`). **PROIBIDO converter `NULL` para `0`**. Não traçar linha contínua no gráfico (abrir gap ou marcar ponto de falha) e gerar alerta de *Falha de Coleta/Sensor*. |
| *Ausência de linha* | `Gap de Coleta` | Se o delta entre duas leituras consecutivas for $> 5\text{ min}$ (ex.: lacuna de 3 coletas no banco), sinalizar como *Perda de Comunicação / Gap de Dados*. |

### 4.3. Mapeamento de Tags (`mapeamento_tag`)
- Os identificadores `DEV01`..`DEV10` e `S01`..`S04` são apenas endereços lógicos do servidor OPC UA.
- Toda consulta de negócio deve cruzar `leitura_opcua` $\rightarrow$ `no_opcua` $\rightarrow$ `mapeamento_tag` $\rightarrow$ `equipamento`.
- Respeitar a particularidade do **Chiller (`MWU3.0CRA01` / `DEV08`)**, que possui apenas **2 sensores de Temperatura** (`P01` e `P02`) e **nenhum sensor de vibração**. A UI deve se adaptar dinamicamente a equipamentos sem vibração.

---

## 5. Diretrizes de Interface (Frontend / UX Industrial)
1. **Clareza Operacional (Padrão ISA-101 / High-Performance HMI):**
   - Cores vibrantes (Vermelho/Amarelo) devem ser reservadas exclusivamente para estados de **Crítico**, **Atenção** ou **Falha de Comunicação**. Condições normais devem usar tons neutros/verdes suaves.
2. **Gráficos de Tendência:**
   - Sempre exibir linhas horizontais tracejadas indicando os limites cadastrados: **LSE** (Limite Superior Especificado), **LIE** (Limite Inferior Especificado) e faixas de **Atenção**.
   - Exibir claramente a unidade de engenharia: Temperatura em **$^\circ\text{C}$** e Vibração RMS em **$\text{mm/s}$**.
3. **Separação de Visões:**
   - **Visão Geral (Planta):** Cards resumidos dos 10 equipamentos com status atual, último valor lido e filtros rápidos por setor/criticidade.
   - **Visão Detalhada (Equipamento):** Gráficos sincronizados de Temperatura e Vibração (`P01` e `P02`), seletor de datas, KPIs estatísticos e histórico de eventos.
   - **Gestão de Tags e Limites:** Tela CRUD para configurar `mapeamento_tag` e ajustar os valores de LIE/LSE dinamicamente.
4. **Proibição Estrita de Emojis na Interface (UI):**
   - **NÃO DEVE** utilizar emojis em novas telas, componentes, botões, cabeçalhos, tabelas ou funcionalidades da interface.
   - A interface deve adotar exclusivamente **ícones vetoriais SVG** técnicos, limpos e profissionais (estilo Feather/Lucide/Heroicons), garantindo legibilidade, consistência visual e conformidade com o padrão ISA-101.


---

## 6. Padrões de Código, Commits e Documentação
- **Clean Code & Tipagem Forte:** Utilize tipagem estrita (TypeScript no Frontend/Node ou Type Hints/Pydantic em Python) para garantir contratos claros entre Backend e Frontend.
- **Variáveis de Ambiente (`.env`):** Caminhos do arquivo SQLite, portas e strings de conexão futuras do Oracle devem vir de variáveis de ambiente (nunca hardcoded).
- **Scripts SQL Versionados:** Qualquer alteração de schema, criação de índice ou seed inicial (como o seed do Anexo A em `mapeamento_tag`) deve ser salva em arquivos `.sql` numerados na pasta `/database/migrations` ou `/database/seeds`.
- **Commits Semânticos (Conventional Commits):**
  - `feat:` nova funcionalidade
  - `fix:` correção de bug
  - `perf:` melhoria de performance em queries/gráficos
  - `docs:` atualização de documentação
  - `refactor:` mudança de código sem alterar funcionalidade
- **Fluxo de Branches (Feature Branches Obrigatórias):**
  - **PROIBIDO** comitar código diretamente na branch principal (`main`).
  - Para toda nova funcionalidade, melhoria ou correção de bug, deve-se obrigatoriamente criar uma nova branch temática a partir da `main` (ex.: `feat/nome-da-funcionalidade`, `fix/descricao-do-bug`, `refactor/camada-ou-modulo`).
  - Todas as alterações devem ser desenvolvidas, testadas e validadas nessa branch antes de serem integradas à branch principal via Pull Request / Merge.

---

## 7. Primeiro Passo Recomendado para o Agente
Ao iniciar os trabalhos neste repositório, execute na ordem:
1. Analise o arquivo `.sqlite` presente no projeto e extraia o DDL completo e os dados de `equipamento`, `no_opcua` e `metadado_poc`.
2. Gere um relatório de diagnóstico confirmando se há limites pré-cadastrados em `metadado_poc` e quais índices já existem no banco.
3. Crie o script de Seed para popular a tabela `mapeamento_tag` conforme o Anexo A do Memorial Descritivo.
4. Proponha a estrutura de pastas (Backend + Frontend + Database) antes de iniciar a codificação das telas.