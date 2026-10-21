import numpy as np
import pandas as pd
import pytest

from app import synthetic
from app.heuristics import HeuristicConfig, RULES, apply_filters, build_dashboard, filter_options
from app.inference import infer_types


def rv(n, loc=100.0, scale=10.0, seed=1):
    return np.random.default_rng(seed).normal(loc, scale, n).round(2)


def dash(df, **kw):
    return build_dashboard(df, infer_types(df), **kw)


def rules_of(result):
    return [c["rule_id"] for c in result["charts"]]


def chart(result, rule_id):
    return next(c for c in result["charts"] if c["rule_id"] == rule_id)


# ------------------------------------------------------------- uma regra por vez
def test_R1_histograma_para_uma_numerica():
    r = dash(synthetic.one_column())
    assert rules_of(r) == ["R1"]
    c = r["charts"][0]
    assert c["chart_type"] == "histogram" and sum(c["data"]["values"]) == 100
    assert 5 <= len(c["data"]["labels"]) <= 30


def test_R2_barras_para_categorica_com_ate_10_categorias():
    df = pd.DataFrame({"g": list("ABCDE") * 20})
    r = dash(df)
    c = chart(r, "R2")
    assert c["chart_type"] == "bar" and c["alternatives"] == ["pie"]
    assert sum(c["data"]["values"]) == 100 and set(c["data"]["labels"]) == set("ABCDE")


def test_R2_R3_limiar_de_10_categorias():
    ten = pd.DataFrame({"g": [f"c{i}" for i in range(10)] * 5})
    eleven = pd.DataFrame({"g": [f"c{i}" for i in range(11)] * 5})
    assert rules_of(dash(ten)) == ["R2"]
    r = dash(eleven)
    assert rules_of(r) == ["R3"] and r["charts"][0]["chart_type"] == "hbar" and r["charts"][0]["alternatives"] == []


def test_R3_ordenadas_e_limitadas_ao_top_n():
    r = dash(synthetic.high_cardinality())
    c = chart(r, "R3")
    vals = c["data"]["values"]
    assert len(vals) == 15 and vals == sorted(vals, reverse=True)
    assert any("categorias mais frequentes" in w for w in c["warnings"])


def test_R4_dispersao_para_duas_numericas():
    rng = np.random.default_rng(0)
    x = rng.normal(size=300)
    df = pd.DataFrame({"x": x, "y": 2 * x + rng.normal(scale=0.1, size=300)})
    r = dash(df)
    assert "R4" in rules_of(r)
    c = chart(r, "R4")
    assert c["data"]["correlation"] > 0.9 and len(c["data"]["points"]) == 300


def test_R4_amostra_quando_ha_muitos_pontos():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x": rng.normal(size=5000), "y": rng.normal(size=5000)})
    c = chart(dash(df), "R4")
    assert len(c["data"]["points"]) == 2000 and any("Amostra" in w for w in c["warnings"])


def test_R5_linha_para_uma_numerica_e_uma_temporal():
    df = pd.DataFrame({"d": pd.date_range("2024-01-01", periods=120, freq="D"), "v": rv(120)})
    r = dash(df)
    c = chart(r, "R5")
    assert c["chart_type"] == "line" and len(c["data"]["series"]) == 1
    assert "R7" not in rules_of(r)


def test_R6_barras_agrupadas_numerica_por_categorica():
    df = pd.DataFrame({"g": ["A", "B", "C"] * 20, "v": rv(60)})
    c = chart(dash(df), "R6")
    assert c["chart_type"] == "bar" and set(c["data"]["labels"]) == {"A", "B", "C"}
    assert c["data"]["values"][0] == max(c["data"]["values"])    # ordenado por valor (padrao)


def test_R6_vira_horizontal_acima_de_10_categorias():
    df = pd.DataFrame({"g": [f"c{i}" for i in range(12)] * 5, "v": rv(60)})
    assert chart(dash(df), "R6")["chart_type"] == "hbar"


def test_R7_linhas_multiplas_para_temporal_e_duas_ou_mais_numericas():
    r = dash(synthetic.sales())
    c = chart(r, "R7")
    assert c["chart_type"] == "multiline" and len(c["data"]["series"]) == 3
    assert "R5" not in rules_of(r)


def test_R7_avisa_escalas_muito_diferentes():
    df = pd.DataFrame({"d": pd.date_range("2024-01-01", periods=90), "a": rv(90, 100, 10),
                       "b": rv(90, 1e7, 1e6, seed=2)})
    c = chart(dash(df), "R7")
    assert any("escalas" in w for w in c["warnings"])


def test_dataset_de_vendas_dispara_todas_as_regras_menos_R5():
    assert set(rules_of(dash(synthetic.sales()))) == {"R1", "R2", "R3", "R4", "R6", "R7"}


# ------------------------------------------------------------- agregacao, ordenacao
def test_agregacao_e_ordenacao():
    df = pd.DataFrame({"g": ["A", "A", "B", "B", "C"], "v": [10.0, 30.0, 5.0, 5.0, 100.0]})
    soma = chart(dash(df, agg="sum"), "R6")["data"]
    media = chart(dash(df, agg="mean"), "R6")["data"]
    assert dict(zip(soma["labels"], soma["values"])) == {"A": 40.0, "B": 10.0, "C": 100.0}
    assert dict(zip(media["labels"], media["values"])) == {"A": 20.0, "B": 5.0, "C": 100.0}
    asc = chart(dash(df, sort="value_asc"), "R6")["data"]["values"]
    assert asc == sorted(asc)
    assert chart(dash(df, sort="label"), "R6")["data"]["labels"] == ["A", "B", "C"]


def test_parametros_invalidos():
    df = synthetic.one_column()
    with pytest.raises(ValueError, match="Agregação"):
        dash(df, agg="max")
    with pytest.raises(ValueError, match="Ordenação"):
        dash(df, sort="x")


# ------------------------------------------------------------- casos-limite
def test_coluna_constante_nao_gera_histograma_e_registra_motivo():
    r = dash(synthetic.constant_column())
    assert "R1" not in rules_of(r)
    assert any("constante" in line for line in r["decision_log"])


def test_categoria_unica_e_ignorada():
    df = pd.DataFrame({"g": ["A"] * 30, "v": rv(30)})
    r = dash(df)
    assert not {"R2", "R3", "R6"} & set(rules_of(r))
    assert any("só há uma categoria" in line for line in r["decision_log"])


def test_data_unica_nao_gera_linha():
    df = pd.DataFrame({"d": pd.to_datetime(["2024-01-01"] * 20), "v": rv(20)})
    r = dash(df)
    assert not {"R5", "R7"} & set(rules_of(r))
    assert any("menos de dois períodos" in line for line in r["decision_log"])


def test_granularidade_automatica():
    def g(days):
        df = pd.DataFrame({"d": pd.date_range("2020-01-01", periods=days, freq="D"), "v": rv(days)})
        return chart(dash(df), "R5")["data"]["labels"][0]
    assert len(g(30)) == 10          # AAAA-MM-DD
    assert len(g(400)) == 7          # AAAA-MM
    assert len(g(2000)) == 4         # AAAA


def test_linha_preserva_lacunas_como_ausentes():
    d = pd.to_datetime(["2024-01-15", "2024-02-10", "2024-05-20", "2024-06-01"])
    df = pd.DataFrame({"d": d, "v": [1.0, 2.0, 3.0, 4.0]})
    vals = chart(dash(df), "R5")["data"]["series"][0]["values"]
    assert vals[2:4] == [None, None] and vals[0] == 1.0


def test_limite_maximo_de_graficos():
    df = synthetic.sales()
    r = build_dashboard(df, infer_types(df), config=HeuristicConfig(max_charts=3))
    assert len(r["charts"]) == 3


def test_toda_regra_tem_fundamentacao_e_cada_grafico_explica_a_regra():
    assert set(RULES) == {f"R{i}" for i in range(1, 8)} and all(r.sources and r.rationale for r in RULES.values())
    for c in dash(synthetic.sales())["charts"]:
        assert c["rule_id"] in c["explanation"] and c["sources"]


def test_kpis():
    r = dash(synthetic.sales())
    labels = [k["label"] for k in r["kpis"]]
    assert labels[0] == "Registros" and r["kpis"][0]["value"] == 500 and "Soma de Quantidade" in labels


# ------------------------------------------------------------- filtros
def test_filtros_categorico_numerico_temporal():
    df = synthetic.sales()
    kinds = {i.name: i.kind for i in infer_types(df)}
    a = apply_filters(df, [{"column": "Região", "values": ["Norte"]}], kinds)
    assert set(a["Região"]) == {"Norte"}
    b = apply_filters(df, [{"column": "Receita", "min": 500, "max": 600}], kinds)
    assert b["Receita"].between(500, 600).all() and len(b) > 0
    c = apply_filters(df, [{"column": "Data", "start": "2024-03-01", "end": "2024-03-31"}], kinds)
    assert c["Data"].min() >= pd.Timestamp("2024-03-01") and c["Data"].max() < pd.Timestamp("2024-04-01")
    d = apply_filters(df, [{"column": "Região", "values": ["Norte"]}, {"column": "Receita", "min": 500}], kinds)
    assert len(d) < len(a)


def test_filtro_atualiza_graficos_e_kpis():
    df = synthetic.sales()
    r = dash(df, filters=[{"column": "Região", "values": ["Sul"]}])
    assert r["meta"]["rows_filtered"] < r["meta"]["rows_total"] == 500
    assert r["kpis"][0]["detail"] == "de 500"


def test_filtro_sem_resultados():
    r = dash(synthetic.sales(), filters=[{"column": "Receita", "min": 10 ** 9}])
    assert r["charts"] == [] and "Nenhum registro" in r["decision_log"][0]


def test_filtro_em_coluna_inexistente():
    with pytest.raises(ValueError, match="inexistente"):
        dash(synthetic.sales(), filters=[{"column": "Nada", "values": ["x"]}])


def test_filter_options():
    df = synthetic.sales()
    opts = filter_options(df, infer_types(df))
    assert opts["Região"]["kind"] == "categorical" and len(opts["Região"]["values"]) == 5
    assert opts["Receita"]["min"] < opts["Receita"]["max"]
    assert opts["Data"]["min"].startswith("2024")


def test_valores_ausentes_nao_quebram():
    df = synthetic.sales(200)
    df.loc[::3, "Receita"] = np.nan
    df.loc[::5, "Região"] = np.nan
    r = dash(df)
    assert len(r["charts"]) > 0


# ------------------------------------------------------------- agregacao automatica
def test_agregacao_automatica_usa_media_para_precos_e_soma_para_o_resto():
    from app.heuristics import resolve_agg
    assert resolve_agg("Preço", "auto") == "mean" and resolve_agg("Taxa de juros", "auto") == "mean"
    assert resolve_agg("Receita", "auto") == "sum" and resolve_agg("Quantidade", "auto") == "sum"
    assert resolve_agg("preco_unitario", "auto") == "mean" and resolve_agg("Idade", "auto") == "mean"
    assert resolve_agg("Faturamento", "auto") == "sum" and resolve_agg("Variação %", "auto") == "mean"
    assert resolve_agg("Preço", "sum") == "sum"            # escolha explicita do usuario prevalece


def test_agregacao_automatica_no_dashboard():
    r = dash(synthetic.sales())
    c = chart(r, "R7")
    assert c["agg"] == "mixed" and any("(média)" in s["name"] for s in c["data"]["series"])
    assert "média de Preço" in c["title"]
    assert any("Agregação automática" in line for line in r["decision_log"])
    explicit = chart(dash(synthetic.sales(), agg="sum"), "R7")
    assert explicit["agg"] == "sum" and explicit["title"].startswith("Soma de")
