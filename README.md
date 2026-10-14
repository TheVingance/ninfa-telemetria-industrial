# Ninfa Telemetria Industrial

**Prova de Conceito (PoC)** — Monitoramento de Vibração e Temperatura em equipamentos industriais do parque fabril da **Ninfa Alimentos**.

> Projeto de extensão universitária desenvolvido em parceria entre o MEIU e a equipe de Automação da Ninfa.

---

## Sobre o Projeto

Aplicação Web completa (Backend + Frontend) para:

- **Monitoramento** de vibração mecânica (RMS, mm/s) e temperatura (°C) de 10 equipamentos industriais
- **Análise de tendências** históricas com 1 ano de dados (~4 milhões de leituras)
- **Gerenciamento de limites operacionais** (LIE/LSE) com classificação de estados: Normal, Atenção e Crítico
- **Apoio à análise preditiva** com projeção de tendências e detecção de anomalias
- **Gestão de alarmes** diferenciando falhas de processo vs falhas de comunicação (OPC UA StatusCodes)

---

## Stack Tecnológica

| Camada | Tecnologia |
| :--- | :--- |
| **Backend / API** | Python 3.12+ · FastAPI |
| **Banco de Dados (PoC)** | SQLite (base sintética de ~370 MB) |
| **Banco de Dados (Futuro)** | Oracle · Projeto On Time |
| **Frontend** | HTML5 · CSS3 · JavaScript (Vanilla) |
| **Gráficos** | ApexCharts / Chart.js (via CDN) |
| **Protocolo Industrial** | OPC UA (dados simulados para o PoC) |

---

## Estrutura do Repositório

```
ninfa-telemetria-industrial/
├── .gitignore
├── README.md
├── requirements.txt
├── dashboards/                  # Painéis exportáveis para Grafana
│   └── grafana_ninfa_telemetria.json
├── data/                        # Base SQLite (não versionada — ver .gitignore)
├── docs/                        # Documentação técnica do projeto
│   ├── SPEC.md
│   ├── Auditoria do SQLite Ninfa.md
│   ├── Plano de implementação e estrutura.md
│   ├── GUIA_TRANSICAO_ORACLE.md
│   └── GUIA_INTEGRACAO_GRAFANA.md
├── scripts/                     # Scripts de seed e manutenção do banco
│   ├── seed_anexo_a.py
│   └── optimize_indexes.sql
└── src/                         # Código-fonte da aplicação
    ├── main.py                  # Ponto de entrada (FastAPI)
    ├── config.py
    ├── core/                    # Regras de negócio e análise
    ├── repositories/            # Padrão Repository (SQLite → Oracle)
    ├── routes/                  # Endpoints da API REST
    └── static/                  # Frontend (HTML/CSS/JS)
        ├── css/
        ├── js/
        ├── index.html           # Dashboard Visão Geral
        ├── equipment.html       # Análise por Equipamento
        ├── comparison.html      # Comparativo de Máquinas
        ├── alarms.html          # Central de Alarmes
        └── limites.html         # Configuração de Limites
```

---

## Como Executar

### Pré-requisitos
- Python 3.12+
- Arquivo `On_Time_POC_OPCUA_1_ano.sqlite` na pasta raiz ou `data/`

### Instalação
```bash
# Clonar o repositório
git clone https://github.com/TheVingance/ninfa-telemetria-industrial.git
cd ninfa-telemetria-industrial

# Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Popular a tabela mapeamento_tag (Anexo A)
python scripts/seed_anexo_a.py

# Iniciar o servidor de desenvolvimento
python -m uvicorn src.main:app --reload --port 8000
```

### Acesso
- **Aplicação Web:** http://localhost:8000
- **Documentação da API (Swagger):** http://localhost:8000/docs
- **Endpoints Grafana:** http://localhost:8000/api/grafana/health

---

## Integração com Grafana

A aplicação disponibiliza integração completa com o ecossistema **Grafana**:
- **Dashboard Pronto para Importação:** [`dashboards/grafana_ninfa_telemetria.json`](dashboards/grafana_ninfa_telemetria.json) contendo séries temporais, thresholds de LIE/LSE, KPIs de última medição e central de alarmes.
- **API REST (Plugin Infinity):** Rota `/api/grafana/series` com downsampling automático e compatibilidade com as variáveis `${__from}` e `${__to}`.
- **Guia Passo a Passo:** Consulte o [`docs/GUIA_INTEGRACAO_GRAFANA.md`](docs/GUIA_INTEGRACAO_GRAFANA.md) para instruções detalhadas de instalação do plugin, criação do data source e consultas SQL nativas para Oracle/SQLite.

---

## Escopo dos Dados (PoC)

| Métrica | Valor |
| :--- | :--- |
| **Registros** | 3.994.557 leituras |
| **Período** | 23/09/2025 → 22/09/2026 (1 ano) |
| **Intervalo** | 5 minutos entre leituras |
| **Equipamentos** | 10 máquinas industriais |
| **Nós OPC UA** | 38 sinais (Vibração RMS + Temperatura) |

---

## Equipe

| Papel | Responsável |
| :--- | :--- |
| **Responsáveis Ninfa** | Danilo Lang Junior · Adriele Rosso |
| **Desenvolvimento (MEIU)** | Equipe de Extensão Universitária |

---

## Licença

Projeto acadêmico de extensão. Código restrito ao escopo da parceria MEIU–Ninfa Alimentos.

