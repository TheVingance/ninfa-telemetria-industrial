Viewed Auditoria%20do%20SQLite%20Ninfa.md:44-104

Com base na análise do [Auditoria do SQLite Ninfa.md](file:///c:/Users/triches/Documents/Projeto%20Extensao%20-%20NINFA/ProjetoNinfa/Auditoria%20do%20SQLite%20Ninfa.md) e nos requisitos consolidados do [SPEC.md](file:///c:/Users/triches/Documents/Projeto%20Extensao%20-%20NINFA/ProjetoNinfa/SPEC.md), preparei o **Plano de Implementação** e a **Estrutura Sugerida para o Repositório GitHub**.

A escolha de **Python + HTML/CSS/JS (Vanilla)** é a mais acertada para esse projeto: dispensa dependências pesadas de NodeJS/npm no ambiente fabril, roda de forma nativa e simples em qualquer servidor, e facilita a transição futura da Ninfa para integração com Oracle/On Time.

---

### 1. Diretrizes Técnicas para os Pontos Pendentes da Auditoria

Para o projeto não travar nos pontos que a Ninfa não especificou, adotamos decisões práticas:

1. **Limites de Referência (LSE e LIE):**
   * No script de inicialização (*seed*), calculamos ou definimos valores padrão razoáveis com base na distribuição dos dados da própria base (ex.: Temperatura normal ~40-60°C, Atenção > 70°C, Crítico > 85°C; Vibração normal < 2.8 mm/s, Atenção > 4.5 mm/s, Crítico > 7.1 mm/s - norma ISO 10816).
   * A aplicação terá a tela de configuração permitindo à equipe da Ninfa ajustar esses limites a qualquer momento.
2. **Análise Preditiva:**
   * Implementar modelos transparentes e determinísticos: **Regressão Linear de Tendência** (projeção de quantas horas faltam para cruzar o LSE se a taxa de subida continuar) e **Detecção de Anomalias Estatísticas** (Z-score / afastamento de $\pm 3\sigma$ da média móvel).
3. **Gestão de Alarmes:**
   * Central de alarmes em tela com histórico, indicação de severidade (Atenção/Crítico) e distinção visual imediata entre *Falha de Processo* vs *Falha de Coleta* (`Bad` / `Uncertain` / `Gaps`).
4. **Interface (UX/UI):**
   * Layout responsivo com tema industrial escuro (Dark Theme), excelente tanto para telas de desktop quanto para painéis/telas de monitoramento contínuo em operação fabril.

---

### 2. Estrutura Recomendada do Repositório (Esqueleto Inicial)

```text
ProjetoNinfa/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   └── On_Time_POC_OPCUA_1_ano.sqlite       # Base de dados original (ou via link/volume)
├── docs/
│   ├── SPEC.md                              # Especificação técnica do projeto
│   ├── Auditoria do SQLite Ninfa.md
│   └── GUIA_TRANSICAO_ORACLE.md             # Documentação de migração futura
├── scripts/
│   ├── seed_anexo_a.py                      # Popula mapeamento_tag e limites iniciais
│   └── optimize_indexes.sql                 # Validação/criação de índices analíticos
├── src/
│   ├── __init__.py
│   ├── main.py                              # Entrada da aplicação (FastAPI)
│   ├── config.py                            # Configurações de caminhos e ambiente
│   ├── core/
│   │   ├── __init__.py
│   │   ├── status_codes.py                  # Tratamento dos status OPC UA (Good, Uncertain, Bad)
│   │   └── predictive.py                    # Cálculos de tendência e predição de LSE
│   ├── repositories/                        # PADRÃO REPOSITORY (Isola o SQLite para futuro Oracle)
│   │   ├── __init__.py
│   │   ├── base.py                          # Interfaces abstratas (Protocol/ABC)
│   │   ├── sqlite_equipment_repo.py         # Leitura de máquinas e tags
│   │   └── sqlite_telemetry_repo.py         # Leitura e downsampling de séries temporais
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api_equipments.py                # Endpoints de equipamentos e status fabril
│   │   ├── api_telemetry.py                 # Endpoints de leituras com downsampling
│   │   ├── api_tags.py                      # Endpoints de cadastro e ajuste de limites
│   │   └── api_alarms.py                    # Endpoints de ocorrências e anomalias
│   └── static/                              # FRONTEND (HTML / CSS / JS Vanilla)
│       ├── css/
│       │   ├── variables.css                # Paleta industrial, cores de status (Verde, Amarelo, Vermelho)
│       │   └── style.css                    # Estilos gerais, cards, tabelas e gráficos
│       ├── js/
│       │   ├── api.js                       # Wrapper de chamadas fetch à API
│       │   ├── charts.js                    # Configuração de gráficos (ApexCharts ou Chart.js via CDN)
│       │   └── app.js                       # Lógica de navegação e filtros
│       ├── index.html                       # Dashboard 1: Visão Geral da Fábrica (Plant Overview)
│       ├── equipment.html                   # Dashboard 2: Análise Detalhada da Máquina (Curvas + Latência)
│       ├── comparison.html                  # Dashboard 3: Comparativo de Máquinas/Pontos
│       ├── alarms.html                      # Tela 4: Central de Eventos e Alarmes
│       └── settings.html                    # Tela 5: Configuração de Tags e Limites (LIE/LSE)
```

---

### 3. Plano de Implementação Passo a Passo

#### **Fase 1: Preparação da Base e Seed de Metadados**
1. **Script de Seed (`scripts/seed_anexo_a.py`):**
   * Ler a Tabela 04 do Anexo A (já levantada: 38 nós para os 10 equipamentos).
   * Popular a tabela `mapeamento_tag` (que atualmente está vazia) associando os pontos `P01` e `P02`, grandezas (`TEMPERATURA` e `VIBRACAO_RMS`), unidades (`°C` e `mm/s`) e limites padrão (LIE/LSE e atenção).

#### **Fase 2: Backend e Camada de Abstração (Repository Pattern)**
1. **Setup do Servidor:**
   * Utilizar **FastAPI** (leve, veloz, documentação Swagger interativa em `/docs`, sem necessidade de compilação).
2. **Isolamento de Banco:**
   * Criar classes base abstratas de repositório. O SQLite será apenas a implementação atual (`SQLiteTelemetryRepository`).
   * Quando a Ninfa migrar para Oracle / On Time, bastará plugar `OracleTelemetryRepository` implementando a mesma interface.
3. **Mecanismo de Agregação e Downsampling (Crítico para 4 milhões de linhas):**
   * Criar query SQL otimizada no SQLite que agrupa por intervalos de tempo:
     ```sql
     -- Exemplo de agregação por balde de tempo (ex: 1 hora / 3600000 ms)
     SELECT 
         (source_timestamp_ms / :bucket_ms) * :bucket_ms AS bucket_ts,
         AVG(valor) AS media,
         MIN(valor) AS minimo,
         MAX(valor) AS maximo,
         COUNT(CASE WHEN status_code = 0 THEN 1 END) AS good_count,
         COUNT(CASE WHEN status_code = 1073741824 THEN 1 END) AS uncertain_count,
         COUNT(CASE WHEN status_code = 2147483648 THEN 1 END) AS bad_count,
         AVG(recebido_em_ms - source_timestamp_ms) AS latencia_media_ms
     FROM leitura_opcua
     WHERE no_id = :no_id AND source_timestamp_ms BETWEEN :inicio AND :fim
     GROUP BY bucket_ts
     ORDER BY bucket_ts ASC;
     ```
   * Isso reduz 100.000 pontos para apenas 200 a 500 pontos na tela, garantindo renderização instantânea do gráfico.

#### **Fase 3: Desenvolvimento do Frontend Web (Python + HTML)**
1. **Design Industrial & Dashboard:**
   * Visual moderno escuro (*dark theme*), responsivo, com cards de alto contraste.
   * Uso de biblioteca de gráficos leve e interativa (ApexCharts ou Chart.js via CDN local/estático).
2. **As 5 Telas Exigidas:**
   * **Visão Geral:** Cards dos 10 equipamentos com badge de status (Normal, Atenção, Crítico, Sem Sinal) e KPIs da fábrica.
   * **Detalhes do Equipamento:** Gráficos de Temperatura e Vibração lado a lado, faixas coloridas dos limites operacionais, métrica de atraso de ingestão ($\Delta t$) e seletor temporal de datas.
   * **Comparativo:** Sobreposição de curvas entre P01 e P02 ou entre duas máquinas.
   * **Alarmes:** Tabela com histórico de desvios, gaps de dados e status incertos/ruins.
   * **Configurações:** Formulário para editar limites de alerta e críticos salvando direto no banco.

#### **Fase 4: Análise Preditiva Simples e Eficaz**
1. **Projeção de Tendência:**
   * Endpoint que calcula a inclinação (slope) da reta das últimas $N$ horas de medição válida.
   * Exibição na interface de um indicador preditivo: *"No ritmo atual, o Limite Superior será atingido em ~X horas"*.

---

### Próximo Passo Sugerido

Podemos iniciar criando:
1. O arquivo `requirements.txt` e o `.gitignore`.
2. O script `scripts/seed_anexo_a.py` para popular a tabela `mapeamento_tag` com os 38 nós e os limites de referência padrão.
3. O esqueleto inicial do backend em FastAPI com o repositório SQLite.

Deseja que eu crie o script de seed e a estrutura base do projeto agora?