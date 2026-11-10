"""Testes do assistente de IA. O modelo de linguagem e substituido por um dublê: nenhum teste acessa a rede."""
import io
import json

import pandas as pd
import pytest

from app import assistant, create_app, synthetic
from app.inference import infer_types
from app.store import FileConfigStore


@pytest.fixture()
def sales():
    df = synthetic.sales()
    return df, infer_types(df)


def test_esquema_nao_contem_linhas_da_planilha(sales):
    df, infos = sales
    schema = assistant.build_schema(df, infos)
    by = {c["name"]: c for c in schema}
    assert by["Receita"]["kind"] == "numeric" and by["Receita"]["sum"] == pytest.approx(df["Receita"].sum(), rel=1e-6)
    assert by["Região"]["distinct"] == df["Região"].nunique() and len(by["Região"]["top_values"]) <= 8
    assert by["Data"]["min"] == df["Data"].min().date().isoformat()


def test_consulta_agrupada_confere_com_pandas(sales):
    df, infos = sales
    t = assistant.run_query(df, infos, {"group_by": ["Região"], "metric": "Receita", "op": "sum"})
    esperado = df.groupby("Região")["Receita"].sum().sort_values(ascending=False)
    assert t["columns"] == ["Região", "Soma de Receita"]
    assert [r[0] for r in t["rows"]] == list(esperado.index)
    assert t["rows"][0][1] == pytest.approx(esperado.iloc[0], rel=1e-6)


def test_consulta_total_contagem_periodo_e_filtro(sales):
    df, infos = sales
    assert assistant.run_query(df, infos, {"op": "count"})["rows"] == [[len(df)]]
    t = assistant.run_query(df, infos, {"group_by": ["Data"], "period": "year", "metric": "Receita", "op": "mean"})
    assert t["columns"][0] == "Data (ano)" and len(t["rows"]) == df["Data"].dt.year.nunique()
    regiao = df["Região"].iloc[0]
    t = assistant.run_query(df, infos, {"op": "count", "filters": [{"column": "Região", "values": [regiao]}]})
    assert t["rows"] == [[int((df["Região"] == regiao).sum())]]
    t = assistant.run_query(df, infos, {"group_by": ["Vendedor"], "op": "count", "limit": 3})
    assert len(t["rows"]) == 3 and t["truncated"] is True


@pytest.mark.parametrize("spec, trecho", [
    ({"op": "apagar"}, "Operação inválida"),
    ({"op": "sum"}, "exige uma coluna"),
    ({"op": "sum", "metric": "Região"}, "exige coluna numérica"),
    ({"op": "sum", "metric": "Inexistente"}, "inexistente"),
    ({"op": "count", "group_by": ["a", "b", "c"]}, "no máximo 2"),
    ({"op": "count", "group_by": ["Data"], "period": "semana"}, "Período inválido"),
])
def test_consulta_invalida_e_rejeitada(sales, spec, trecho):
    df, infos = sales
    with pytest.raises(ValueError, match=trecho):
        assistant.run_query(df, infos, spec)


def _fake(*answers):
    calls, queue = [], list(answers)

    def llm(messages, json_mode=False):
        calls.append({"messages": messages, "json_mode": json_mode})
        return queue.pop(0)
    return llm, calls


def test_fluxo_em_duas_etapas_usa_numeros_do_pandas(sales):
    df, infos = sales
    plano = json.dumps({"action": "query", "query": {"group_by": ["Região"], "metric": "Receita", "op": "sum", "limit": 1}})
    llm, calls = _fake(plano, "A região líder é X.")
    r = assistant.ask(df, infos, "vendas.csv", "Qual região vendeu mais?", llm=llm)
    lider = df.groupby("Região")["Receita"].sum().idxmax()
    assert r["answer"] == "A região líder é X." and r["table"]["rows"][0][0] == lider
    assert calls[0]["json_mode"] is True and calls[1]["json_mode"] is False
    assert lider in calls[1]["messages"][-1]["content"]            # o resultado calculado vai ao modelo
    enviado = json.dumps([c["messages"] for c in calls], ensure_ascii=False)
    assert str(df["Receita"].iloc[0]) not in enviado               # so esquema e agregados, nunca linhas brutas


def test_resposta_direta_texto_livre_e_consulta_invalida(sales):
    df, infos = sales
    llm, _ = _fake(json.dumps({"action": "answer", "answer": "As colunas são..."}))
    assert assistant.ask(df, infos, "v.csv", "Quais colunas?", llm=llm)["answer"] == "As colunas são..."
    llm, _ = _fake("texto fora do protocolo")
    assert assistant.ask(df, infos, "v.csv", "oi", llm=llm)["answer"] == "texto fora do protocolo"
    llm, calls = _fake(json.dumps({"action": "query", "query": {"op": "sum", "metric": "Nada"}}))
    r = assistant.ask(df, infos, "v.csv", "soma de nada", llm=llm)
    assert "Não consegui executar" in r["answer"] and r["table"] is None and len(calls) == 1


def test_filtros_do_dashboard_e_validacao_da_pergunta(sales):
    df, infos = sales
    regiao = df["Região"].iloc[0]
    llm, calls = _fake(json.dumps({"action": "query", "query": {"op": "count"}}), "ok")
    r = assistant.ask(df, infos, "v.csv", "quantos?", llm=llm, filters=[{"column": "Região", "values": [regiao]}])
    assert r["rows_considered"] == int((df["Região"] == regiao).sum()) == r["table"]["rows"][0][0]
    assert r["rows_total"] == len(df)
    with pytest.raises(assistant.AssistantError):
        assistant.ask(df, infos, "v.csv", "   ", llm=llm)
    with pytest.raises(assistant.AssistantError):
        assistant.ask(df, infos, "v.csv", "x" * 1001, llm=llm)


def test_extracao_de_json_tolerante():
    assert assistant._extract_json('```json\n{"action": "answer"}\n```') == {"action": "answer"}
    assert assistant._extract_json('Claro! {"action": "query", "query": {}} pronto') == {"action": "query", "query": {}}
    assert assistant._extract_json("sem json") is None


def test_sem_chave_devolve_erro_claro(monkeypatch):
    for v in ("LLM_API_KEY", "GROQ_API_KEY", "XAI_API_KEY", "LLM_PROVIDER", "LLM_MODEL"):
        monkeypatch.delenv(v, raising=False)
    assert assistant.public_status()["server_key"] is False
    with pytest.raises(assistant.AssistantError, match="chave"):
        assistant.call_llm([], provider="groq", api_key="", model="m")
    with pytest.raises(assistant.AssistantError, match="Provedor"):
        assistant.call_llm([], provider="outro", api_key="k", model="m")


def test_rotas_do_assistente(tmp_path, monkeypatch):
    for v in ("LLM_API_KEY", "GROQ_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    llm, calls = _fake(json.dumps({"action": "query", "query": {"group_by": ["Produto"], "op": "count"}}), "Resposta final.")
    app = create_app({"TESTING": True, "CONFIG_STORE": FileConfigStore(str(tmp_path)), "LLM_CALL": llm})
    c = app.test_client()
    st = c.get("/api/assistant/status").get_json()
    assert st["server_key"] is False and set(st["providers"]) == {"groq", "xai"} and "api_key" not in json.dumps(st)
    sid = c.post("/api/upload", data={"file": (io.BytesIO(synthetic.to_csv_bytes(synthetic.sales())), "v.csv")},
                 content_type="multipart/form-data").get_json()["session_id"]
    r = c.post(f"/api/sessions/{sid}/assistant", json={"question": "Quantas vendas por produto?"})
    body = r.get_json()
    assert r.status_code == 200 and body["answer"] == "Resposta final." and body["table"]["columns"] == ["Produto", "Registros"]
    assert c.post(f"/api/sessions/{sid}/assistant", json={"question": ""}).status_code == 400
    assert c.post("/api/sessions/naoexiste/assistant", json={"question": "oi"}).status_code == 404
    assert c.post(f"/api/sessions/{sid}/assistant", json={"question": "oi", "provider": "x"},
                  headers={"X-LLM-Key": "k"}).status_code == 400


def test_rota_sem_chave_configurada(client, monkeypatch):
    for v in ("LLM_API_KEY", "GROQ_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    sid = client.post("/api/upload", data={"file": (io.BytesIO(synthetic.to_csv_bytes(synthetic.sales())), "v.csv")},
                      content_type="multipart/form-data").get_json()["session_id"]
    r = client.post(f"/api/sessions/{sid}/assistant", json={"question": "oi"})
    assert r.status_code == 400 and "chave" in r.get_json()["error"].lower()
