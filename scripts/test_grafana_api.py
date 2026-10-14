import sys
import json
from pathlib import Path

# Garantir que a raiz do projeto esteja no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from src.main import app

def run_tests():
    client = TestClient(app)
    print("Iniciando testes da integração com Grafana...")

    # 1. Teste /api/grafana/health
    r = client.get("/api/grafana/health")
    assert r.status_code == 200, f"Falha no health check: {r.status_code}"
    health_data = r.json()
    assert health_data["status"] == "ok"
    assert "poc_period" in health_data
    print("  [OK] /api/grafana/health")

    # 2. Teste /api/grafana/variables/equipments
    r = client.get("/api/grafana/variables/equipments")
    assert r.status_code == 200
    equips = r.json()
    assert len(equips) == 10, f"Esperado 10 equipamentos, obtido {len(equips)}"
    assert "text" in equips[0] and "value" in equips[0]
    print(f"  [OK] /api/grafana/variables/equipments ({len(equips)} itens)")

    # 3. Teste /api/grafana/variables/tags
    r = client.get("/api/grafana/variables/tags?equipamento_id=1")
    assert r.status_code == 200
    tags = r.json()
    assert len(tags) == 4, f"Esperado 4 tags para o equipamento 1, obtido {len(tags)}"
    assert tags[0]["value"] == 1 or tags[0]["value"] == 2
    print(f"  [OK] /api/grafana/variables/tags ({len(tags)} tags)")

    # 4. Teste /api/grafana/overview
    r = client.get("/api/grafana/overview")
    assert r.status_code == 200
    overview = r.json()
    assert len(overview) == 10
    assert "status_operacional" in overview[0]
    assert "ultima_leitura_time" in overview[0]
    print("  [OK] /api/grafana/overview")

    # 5. Teste /api/grafana/series com no_id
    r = client.get("/api/grafana/series?no_id=1&bucket=1d")
    assert r.status_code == 200
    series = r.json()
    assert len(series) > 0, "Série retornou vazia"
    sample = series[0]
    assert "time" in sample and "timestamp" in sample
    assert "valor" in sample and "unidade" in sample
    assert "qualidade" in sample
    print(f"  [OK] /api/grafana/series (no_id=1, {len(series)} pontos retornados)")

    # 6. Teste /api/grafana/series com equipamento_id (Chiller DEV08 sem vibração)
    r = client.get("/api/grafana/series?equipamento_id=8&grandeza=TEMPERATURA&ponto=P01&bucket=1d")
    assert r.status_code == 200
    chiller_series = r.json()
    assert len(chiller_series) > 0
    assert chiller_series[0]["equipamento_codigo"] == "MWU3.0CRA01"
    assert chiller_series[0]["grandeza"] == "TEMPERATURA"
    print("  [OK] /api/grafana/series (equipamento_id=8 Chiller)")

    # 7. Teste /api/grafana/alarms
    r = client.get("/api/grafana/alarms?limit=10")
    assert r.status_code == 200
    alarms = r.json()
    assert isinstance(alarms, list)
    if alarms:
        assert "severidade" in alarms[0]
        assert "mensagem" in alarms[0]
    print(f"  [OK] /api/grafana/alarms ({len(alarms)} alarmes retornados)")

    # 8. Validação do arquivo JSON do Dashboard
    dash_path = Path("dashboards/grafana_ninfa_telemetria.json")
    assert dash_path.exists(), "Arquivo dashboards/grafana_ninfa_telemetria.json não encontrado"
    with open(dash_path, encoding="utf-8") as f:
        dash_json = json.load(f)
    assert dash_json["title"] == "Ninfa Alimentos — Telemetria Industrial OPC UA"
    assert len(dash_json["panels"]) >= 8
    print("  [OK] dashboards/grafana_ninfa_telemetria.json validado com sucesso")

    print("\nTodos os 8 testes passaram com sucesso!")

if __name__ == "__main__":
    run_tests()
