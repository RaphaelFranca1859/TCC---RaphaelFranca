import io
import json
import os

import mongomock
import pytest

from app import create_app, synthetic
from app.store import FileConfigStore, MongoConfigStore, SessionStore


def upload(client, content=None, name="vendas.csv"):
    content = content if content is not None else synthetic.to_csv_bytes(synthetic.sales())
    return client.post("/api/upload", data={"file": (io.BytesIO(content), name)}, content_type="multipart/form-data")


def test_health_e_regras(client):
    h = client.get("/api/health").get_json()
    assert h["status"] == "ok" and h["config_backend"]
    r = client.get("/api/rules").get_json()
    assert [x["id"] for x in r["rules"]] == [f"R{i}" for i in range(1, 8)]
    assert r["heuristic_thresholds"]["category_limit"] == 10 and "sum" in r["aggregations"]


def test_fluxo_completo_das_tres_telas(client):
    # Tela 1: enviar
    res = upload(client)
    assert res.status_code == 201
    body = res.get_json()
    sid = body["session_id"]
    assert body["rows"] == 500 and {c["name"]: c["kind"] for c in body["columns"]}["Data"] == "temporal"
    assert len(body["preview"]["rows"]) == 10 and body["filter_options"]["Região"]["kind"] == "categorical"
    # Tela 2: ajustar tipos
    res = client.put(f"/api/sessions/{sid}/types", json={"types": {"Quantidade": "categorical"}})
    cols = {c["name"]: c for c in res.get_json()["columns"]}
    assert cols["Quantidade"]["kind"] == "categorical" and cols["Quantidade"]["overridden"] is True
    # voltar ao tipo original
    res = client.put(f"/api/sessions/{sid}/types", json={"types": {"Quantidade": "numeric"}})
    assert {c["name"]: c for c in res.get_json()["columns"]}["Quantidade"]["kind"] == "numeric"
    # Tela 3: dashboard + filtros
    dash = client.post(f"/api/sessions/{sid}/dashboard", json={}).get_json()
    assert dash["meta"]["rows_total"] == 500 and len(dash["charts"]) >= 6
    filtered = client.post(f"/api/sessions/{sid}/dashboard",
                           json={"filters": [{"column": "Região", "values": ["Norte"]}], "agg": "mean",
                                 "sort": "value_asc"}).get_json()
    assert filtered["meta"]["rows_filtered"] < 500 and filtered["meta"]["agg"] == "mean"
    # exportar
    exp = client.post(f"/api/sessions/{sid}/export", json={"filters": [{"column": "Região", "values": ["Norte"]}]})
    assert exp.status_code == 200 and exp.mimetype == "text/csv"
    lines = exp.data.decode("utf-8-sig").strip().splitlines()
    assert len(lines) - 1 == filtered["meta"]["rows_filtered"] and lines[0].startswith("Data;")
    assert "attachment" in exp.headers["Content-Disposition"]


def test_dashboard_json_serializavel_com_ausentes(client):
    import numpy as np
    df = synthetic.sales(200)
    df.loc[::4, "Receita"] = np.nan
    sid = upload(client, synthetic.to_xlsx_bytes(df), "v.xlsx").get_json()["session_id"]
    res = client.post(f"/api/sessions/{sid}/dashboard", json={})
    assert res.status_code == 200
    json.dumps(res.get_json(), allow_nan=False)    # nenhum NaN no JSON


def test_erros_de_upload_mensagens(client):
    r = client.post("/api/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400 and "Nenhum arquivo" in r.get_json()["error"]
    r = upload(client, b"x", "a.pdf")
    assert r.status_code == 422 and "não suportado" in r.get_json()["error"]
    r = upload(client, b"", "a.csv")
    assert r.status_code == 422 and "vazio" in r.get_json()["error"]


def test_sessao_inexistente_e_validacoes(client):
    assert client.post("/api/sessions/nada/dashboard", json={}).status_code == 404
    assert client.get("/api/sessions/nada").status_code == 404
    sid = upload(client).get_json()["session_id"]
    assert client.put(f"/api/sessions/{sid}/types", json={"types": {"Receita": "banana"}}).status_code == 400
    assert client.put(f"/api/sessions/{sid}/types", json={"types": {"Nada": "numeric"}}).status_code == 400
    assert client.put(f"/api/sessions/{sid}/types", json={}).status_code == 400
    r = client.post(f"/api/sessions/{sid}/dashboard", json={"agg": "max"})
    assert r.status_code == 400 and "Agregação" in r.get_json()["error"]
    r = client.post(f"/api/sessions/{sid}/dashboard", json={"filters": [{"column": "X", "values": ["a"]}]})
    assert r.status_code == 400


def test_excluir_sessao(client):
    sid = upload(client).get_json()["session_id"]
    assert client.delete(f"/api/sessions/{sid}").status_code == 204
    assert client.get(f"/api/sessions/{sid}").status_code == 404


def test_expiracao_de_sessao():
    store = SessionStore(ttl_seconds=0)
    import pandas as pd
    s = store.create("a.csv", pd.DataFrame({"a": [1, 2, 3]}), [])
    import time
    time.sleep(0.01)
    with pytest.raises(KeyError):
        store.get(s.id)


def test_limite_de_sessoes_simultaneas():
    import pandas as pd
    store = SessionStore(max_sessions=3)
    ids = [store.create("a.csv", pd.DataFrame({"a": [1, 2, 3]}), []).id for _ in range(5)]
    assert len(store) <= 3
    with pytest.raises(KeyError):
        store.get(ids[0])


# ------------------------------------------------------------- configuracoes
def test_salvar_e_reaplicar_configuracao(client):
    sid = upload(client).get_json()["session_id"]
    client.put(f"/api/sessions/{sid}/types", json={"types": {"Quantidade": "categorical"}})
    saved = client.post(f"/api/sessions/{sid}/config", json={
        "name": "Vendas por região", "filters": [{"column": "Região", "values": ["Sul"]}],
        "agg": "mean", "sort": "label"})
    assert saved.status_code == 201
    cid = saved.get_json()["id"]
    cfg = client.get(f"/api/configs/{cid}").get_json()
    assert cfg["columns"]["Quantidade"] == "categorical" and cfg["name"] == "Vendas por região"
    assert "rows" not in cfg and "data" not in cfg           # nunca persiste conteudo da planilha
    assert any(c["id"] == cid for c in client.get("/api/configs").get_json()["configs"])

    # nova versao da planilha, com uma coluna a menos e uma nova
    df2 = synthetic.sales(300, seed=99).drop(columns=["Preço"])
    df2["Desconto"] = 0.1
    sid2 = upload(client, synthetic.to_csv_bytes(df2), "vendas_v2.csv").get_json()["session_id"]
    applied = client.post(f"/api/sessions/{sid2}/apply-config", json={"config_id": cid}).get_json()
    cols = {c["name"]: c["kind"] for c in applied["columns"]}
    assert cols["Quantidade"] == "categorical"
    assert applied["applied"]["missing_columns"] == ["Preço"] and applied["applied"]["new_columns"] == ["Desconto"]
    assert applied["applied"]["agg"] == "mean" and applied["applied"]["filters"][0]["column"] == "Região"
    assert any("ausentes" in w for w in applied["warnings"])


def test_configuracao_inexistente(client):
    assert client.get("/api/configs/naoexiste").status_code == 404
    sid = upload(client).get_json()["session_id"]
    assert client.post(f"/api/sessions/{sid}/apply-config", json={"config_id": "naoexiste"}).status_code == 404


def test_config_store_mongodb_simulado():
    store = MongoConfigStore("mongodb://x", client=mongomock.MongoClient())
    cid = store.save({"name": "n", "columns": {"a": "numeric"}})
    assert store.get(cid)["name"] == "n" and store.list()[0]["id"] == cid
    with pytest.raises(KeyError):
        store.get("nada")


def test_app_usa_mongodb_quando_configurado(tmp_path):
    store = MongoConfigStore("mongodb://x", client=mongomock.MongoClient())
    app = create_app({"TESTING": True, "CONFIG_STORE": store})
    c = app.test_client()
    assert c.get("/api/health").get_json()["config_backend"] == "MongoDB"
    sid = upload(c).get_json()["session_id"]
    assert c.post(f"/api/sessions/{sid}/config", json={"name": "x"}).status_code == 201
    assert len(store.list()) == 1


def test_fallback_para_arquivo_sem_mongodb(tmp_path):
    from app.store import create_config_store
    store = create_config_store("mongodb://host-inexistente:1", str(tmp_path))
    assert isinstance(store, FileConfigStore)
    cid = store.save({"name": "n"})
    assert store.get(cid)["name"] == "n"
    with pytest.raises(KeyError):
        store.get("../etc/passwd")


# ------------------------------------------------------- aba do Excel e escala R7
def _xlsx_duas_abas() -> bytes:
    import pandas as pd
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        synthetic.sales(120).to_excel(xw, index=False, sheet_name="Vendas")
        pd.DataFrame({"Produto": ["A", "B", "C", "A", "B", "C"], "Estoque": [10, 20, 30, 15, 25, 35]}) \
            .to_excel(xw, index=False, sheet_name="Estoque")
    return buf.getvalue()


def test_trocar_de_aba_do_excel_sem_reenviar_o_arquivo(client):
    body = upload(client, _xlsx_duas_abas(), "multi.xlsx").get_json()
    sid = body["session_id"]
    assert body["sheets"] == ["Vendas", "Estoque"] and body["sheet_used"] == "Vendas"
    client.put(f"/api/sessions/{sid}/types", json={"types": {"Quantidade": "categorical"}})
    res = client.post(f"/api/sessions/{sid}/sheet", json={"sheet": "Estoque"})
    assert res.status_code == 200
    out = res.get_json()
    assert out["sheet_used"] == "Estoque" and out["rows"] == 6
    assert [c["name"] for c in out["columns"]] == ["Produto", "Estoque"]
    assert client.post(f"/api/sessions/{sid}/dashboard", json={}).get_json()["meta"]["rows_total"] == 6
    back = client.post(f"/api/sessions/{sid}/sheet", json={"sheet": "Vendas"}).get_json()
    assert back["rows"] == 120
    # os ajustes de tipo da aba anterior nao vazam para a nova leitura
    assert {c["name"]: c["kind"] for c in back["columns"]}["Quantidade"] == "numeric"


def test_trocar_de_aba_validacoes(client):
    sid = upload(client, _xlsx_duas_abas(), "multi.xlsx").get_json()["session_id"]
    r = client.post(f"/api/sessions/{sid}/sheet", json={"sheet": "Nada"})
    assert r.status_code == 400 and "Abas disponíveis" in r.get_json()["error"]
    csv_sid = upload(client).get_json()["session_id"]
    assert client.post(f"/api/sessions/{csv_sid}/sheet", json={"sheet": "x"}).status_code == 400
    assert client.post("/api/sessions/nada/sheet", json={"sheet": "x"}).status_code == 404


def test_planilha_de_uma_aba_nao_guarda_o_arquivo_original(client, app):
    sid = upload(client, synthetic.to_xlsx_bytes(synthetic.sales(50)), "uma.xlsx").get_json()["session_id"]
    assert app.extensions["sessions"].get(sid).source is None


def test_escala_r7_pela_api_e_na_configuracao_salva(client):
    sid = upload(client).get_json()["session_id"]
    dash = client.post(f"/api/sessions/{sid}/dashboard", json={"scale": "index100"}).get_json()
    r7 = next(c for c in dash["charts"] if c["rule_id"] == "R7")
    assert dash["meta"]["scale"] == "index100" and r7["scale"] == "index100"
    bad = client.post(f"/api/sessions/{sid}/dashboard", json={"scale": "log"})
    assert bad.status_code == 400 and "Escala" in bad.get_json()["error"]
    cid = client.post(f"/api/sessions/{sid}/config", json={"scale": "secondary"}).get_json()["id"]
    assert client.get(f"/api/configs/{cid}").get_json()["scale"] == "secondary"
    sid2 = upload(client).get_json()["session_id"]
    applied = client.post(f"/api/sessions/{sid2}/apply-config", json={"config_id": cid}).get_json()
    assert applied["applied"]["scale"] == "secondary"
    assert "scales" in client.get("/api/rules").get_json()


# ------------------------------------------- MongoDB real (so roda com MONGO_TEST_URI)
@pytest.mark.skipif(not os.environ.get("MONGO_TEST_URI"), reason="defina MONGO_TEST_URI para testar contra um MongoDB real")
def test_config_store_mongodb_real():
    store = MongoConfigStore(os.environ["MONGO_TEST_URI"], db_name="dashgen_test")
    store.col.delete_many({})
    cid = store.save({"name": "real", "columns": {"a": "numeric"}, "scale": "index100"})
    got = store.get(cid)
    assert got["name"] == "real" and got["scale"] == "index100" and "_id" not in got
    assert [d["id"] for d in store.list()] == [cid]
    with pytest.raises(KeyError):
        store.get("nada")
    app = create_app({"TESTING": True, "CONFIG_STORE": store})
    assert app.test_client().get("/api/health").get_json()["config_backend"] == "MongoDB"
    store.col.delete_many({})
