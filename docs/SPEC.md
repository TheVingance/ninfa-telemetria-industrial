Aqui está a especificação completa, técnica e estruturada do projeto com base no Memorial Descritivo fornecido pela Ninfa Alimentos. Você pode copiar este texto diretamente para o **Antigravity IDE** como prompt mestre ou arquivo de especificação (`SPEC.md` / `README.md`) para orientar o desenvolvimento.

---

# ESPECIFICAÇÃO TÉCNICA E PLANO DE DESENVOLVIMENTO

**Projeto:** Prova de Conceito (PoC) – Monitoramento de Vibração e Temperatura Industrial

**Cliente/Empresa:** Ninfa Alimentos

**Responsáveis Ninfa:** Danilo Lang Junior e Adriele Rosso

**Origem dos Dados do PoC:** Base histórica estática em SQLite (`3.994.557` leituras sintetizadas)

---

## 1. OBJETIVO PRINCIPAL DO PROJETO

Desenvolver uma aplicação Web completa (Backend + Frontend) para monitoramento, análise de tendências históricas, gerenciamento de limites operacionais e apoio à análise preditiva de **vibração mecânica** e **temperatura** em equipamentos do parque fabril da Ninfa.

A aplicação deve desacoplar a camada de dados por meio de abstração/repositórios para que, no futuro, a fonte de dados possa ser migrada do banco **SQLite sintético** para o ambiente corporativo **Oracle / Projeto On Time** sem necessidade de refatorar regras de negócio ou telas da interface.

---

## 2. ESCOPO DA BASE DE DADOS (SQLite Fornecido)

* **Volume de dados:** 3.994.557 registros de leitura gerados em intervalos simulados de 5 minutos.


* **Período coberto:** 23/09/2025 00:00 UTC até 22/09/2026 23:55 UTC.


* **Equipamentos:** 10 máquinas industriais mapeadas (códigos `DEV01` a `DEV10`).


* **Sinais/Nós:** 38 nós OPC UA no total.


* 9 equipamentos possuem 4 nós cada (P01 Vibração, P01 Temperatura, P02 Vibração, P02 Temperatura).


* 1 equipamento (`DEV08` / Chiller `MWU3.0CRA01`) possui apenas 2 nós (P01 e P02 de Temperatura).




* **Estrutura das Tabelas do SQLite:**
1. `equipamento`: Contém os códigos das máquinas (ex.: `MBF1.1FRN01`), descrições e setores.


2. `servidor_opcua`: Cadastro do endpoint fictício (`opc.tcp://192.0.2.10:4840`).


3. `no_opcua`: Cadastro dos 38 `NodeId` simulados (`ns=2;s=DEV01/S01` até `DEV10/S04`).


4. `leitura_opcua`: Guarda as medições brutas com `leitura_id`, `no_id`, `source_timestamp_ms`, `server_timestamp_ms`, `recebido_em_ms`, `valor` e `status_code`.


5. `mapeamento_tag`: **Tabela inicialmente vazia**. Deve ser alimentada pelo módulo de cadastro da aplicação ou via script de seed com o **Anexo A** do memorial.


6. `metadado_poc`: Metadados e parâmetros da simulação.





---

## 3. REGRAS DE NEGÓCIO E TRATAMENTO DE DADOS

### 3.1. Eixo Temporal e Atraso de Ingestão

* **Eixo X dos gráficos históricos:** Deve utilizar obrigatoriamente `source_timestamp_ms` (timestamp Unix em milissegundos UTC gerado na origem).


* **Métrica de Latência:** O atraso de ingestão deve ser calculado como:

$$\Delta t = \text{recebido\_em\_ms} - \text{source\_timestamp\_ms}$$




### 3.2. Tratamento de Qualidade (`StatusCode` OPC UA)

O sistema deve diferenciar claramente falha física/operacional de falha de comunicação/coleta:

* **`0` (Good):** Dado válido. Plota no gráfico, computa estatísticas e compara contra limites operacionais.


* **`1073741824` (Uncertain):** Dado duvidoso. Deve ser destacado visualmente como alerta de qualidade, sem disparar ações automáticas críticas.


* **`2147483648` (Bad):** Dado inválido/corrompido (valor nulo). **Não plotar como medição contínua**; indicar no gráfico ou dashboard como falha de coleta de sensor.


* **Lacunas de coleta (gaps):** O banco contém pelo menos uma lacuna de 3 ciclos sem dados; a interface deve evidenciar o intervalo sem leitura.



### 3.3. Classificação de Estados Operacionais

A aplicação deve avaliar o valor lido contra limites de referência cadastrados:

* **Normal:** Dentro da faixa esperada.
* **Atenção:** Valor aproximando-se do limite operacional pré-configurado.


* **Crítico:** Ultrapassou o Limite Superior Especificado (LSE) ou ficou abaixo do Limite Inferior Especificado (LIE).


* **Separação de Alarmes:** Manter alarmes de processo (temperatura/vibração crítica) separados dos alarmes de comunicação (StatusCode Bad, atraso elevado de ingestão e perda de pacotes).



---

## 4. O QUE PRECISA SER FEITO (REQUISITOS DO SISTEMA)

### Módulo 1: Backend & Camada de Dados

1. **Configuração de Conexão com SQLite:** Leitura otimizada do arquivo `.sqlite` (considerando índices em `source_timestamp_ms` e `no_id` devido às quase 4 milhões de linhas).


2. **Camada de Abstração (Repository Pattern):** Criar interfaces/classes abstratas para acesso a dados, facilitando a troca futura por queries em Oracle Database / PL-SQL.


3. **Módulo de Mapeamento/Cadastro de Tags (`mapeamento_tag`):**
* Interface e endpoints para associar cada `no_id` (OPC UA) a: `equipamento_id`, ponto de medição (`P01`, `P02`), tipo de grandeza (Temperatura ou Vibração RMS), unidade (`°C` ou `mm/s`) e limites de referência (LIE, LSE, faixa de atenção).


* Script inicial de carga baseado na **Tabela 04 (Anexo A)** do memorial descritivo para pré-popular a base.




4. **Agregação e Downsampling de Leituras:**
* Devido ao volume de quase 4 milhões de registros, endpoints de séries temporais para telas e gráficos precisam suportar agregação (médias horárias/diárias, min/max/RMS) para períodos longos.





### Módulo 2: Frontend & Telas da Aplicação Web

1. **Dashboard Geral (Visão Fabril):**
* Cartões com os 10 equipamentos monitorados exibindo o status consolidado de cada um (Normal, Atenção, Crítico ou Sem Comunicação).


* Indicadores gerais/KPIs da planta (total de pontos ativos, ocorrências de alarmes ativas, integridade de dados).


* Filtros por setor da fábrica, linha e criticidade.




2. **Dashboard Detalhado por Equipamento:**
* Gráfico de linha interativo de **Temperatura (°C)** com faixas visuais de limites (LIE/LSE e atenção).


* Gráfico de linha interativo de **Vibração RMS (mm/s)** com limites de tolerância.


* Seletor de período (últimas 24 horas, 7 dias, mês específico ou período customizado entre 2025 e 2026).


* Indicadores de anomalia (pontos fora do padrão, status incerto/bad destacados).




3. **Tela de Comparativos e Análise de Tendências:**
* Comparação entre dois equipamentos diferentes ou dois pontos da mesma máquina (ex.: P01 vs. P02).


* Comparação temporal (ex.: comportamento térmico do turno atual vs. turno da semana anterior).




4. **Tela de Gestão de Alarmes e Eventos:**
* Registro histórico dos momentos em que valores cruzaram limites críticos.


* Lista de falhas de qualidade (`StatusCode Bad` e `Uncertain`) e lacunas de dados.




5. **Tela de Configuração de Tags e Limites:**
* Visualização e edição dos limites LSE/LIE por ponto de medição.





---

## 5. ENTREGÁVEIS OBRIGATÓRIOS DO PROJETO

1. **Aplicação Web funcional** (Interface + API).


2. **Código-fonte completo** e versionado.


3. **Scripts SQL** de criação de índices, consultas analíticas e carga de sementes (seed do Anexo A).


4. **Documentação técnica** detalhando a arquitetura, regras de negócio de alarme e guia de transição para banco Oracle / Projeto On Time.