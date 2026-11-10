import numpy as np
import pandas as pd
import pytest

from app import synthetic
from app.inference import apply_overrides, infer_types
from app.ingestion import clean_dataframe


def kinds(df, **kw):
    return {i.name: i.kind for i in infer_types(df, **kw)}


def test_tipos_do_dataset_de_vendas():
    k = kinds(synthetic.sales())
    assert k == {"Data": "temporal", "Região": "categorical", "Produto": "categorical", "Vendedor": "categorical",
                 "Quantidade": "numeric", "Receita": "numeric", "Preço": "numeric"}


def test_identificador_e_texto_livre_sao_ignorados():
    infos = {i.name: i for i in infer_types(synthetic.identifiers())}
    assert infos["ID"].kind == "ignored" and "identificador" in infos["ID"].ignored_reason
    assert infos["Descrição"].kind == "ignored"
    assert infos["Valor"].kind == "numeric" and infos["Categoria"].kind == "categorical"


def test_coluna_vazia_e_ignorada():
    infos = {i.name: i for i in infer_types(pd.DataFrame({"a": [None] * 5, "b": [1, 2, 3, 4, 5]}))}
    assert infos["a"].kind == "ignored" and infos["a"].missing_ratio == 1.0


def test_ano_inteiro_vira_temporal_e_notas_viram_categoricas():
    df = pd.DataFrame({"Ano": np.repeat([2019, 2020, 2021, 2022], 25),
                       "Nota": np.tile([1, 2, 3, 4, 5], 20), "Valor": np.random.default_rng(0).normal(size=100)})
    k = kinds(df)
    assert k["Ano"] == "temporal" and k["Nota"] == "categorical" and k["Valor"] == "numeric"


def test_booleano_e_categorico():
    assert kinds(pd.DataFrame({"ativo": [True, False] * 10}))["ativo"] == "categorical"


def test_ajuste_do_usuario_prevalece_e_e_marcado():
    df = synthetic.sales(60)
    infos = {i.name: i for i in infer_types(df, overrides={"Quantidade": "categorical"})}
    assert infos["Quantidade"].kind == "categorical" and infos["Quantidade"].overridden
    assert infos["Quantidade"].inferred_kind == "numeric"


def test_apply_overrides_converte_e_avisa_perdas():
    df = pd.DataFrame({"x": ["1", "2", "abc", "4"], "y": ["2024-01-01", "2024-02-01", "ruim", "2024-03-01"]})
    out, warns = apply_overrides(df, {"x": "numeric", "y": "temporal"})
    assert out["x"].isna().sum() == 1 and pd.api.types.is_datetime64_any_dtype(out["y"])
    assert len(warns) == 2 and "não puderam ser convertidos" in warns[0]


def test_override_invalido():
    with pytest.raises(ValueError):
        apply_overrides(pd.DataFrame({"a": [1]}), {"a": "banana"})


def test_override_numerico_para_categorico_preserva_rotulos():
    out, _ = apply_overrides(pd.DataFrame({"cod": [1.0, 2.0, 1.0]}), {"cod": "categorical"})
    assert set(out["cod"]) == {"1", "2"}


def test_pipeline_completo_planilha_brasileira():
    from app.ingestion import read_table
    df = read_table(synthetic.brazilian_csv(), "v.csv").df
    k = kinds(df)
    assert k["Data"] == "temporal" and k["Valor"] == "numeric" and k["Cidade"] == "categorical"


# ---- regressao encontrada na demonstracao com dados reais (Gapminder e Passageiros aereos)
def test_coluna_de_ano_inteiro_vira_data_e_nao_quebra_o_dashboard():
    import numpy as np
    from app.heuristics import build_dashboard
    from app.inference import apply_overrides
    df = pd.DataFrame({"year": np.repeat(np.arange(2000, 2010), 5), "valor": np.arange(50) * 1.5,
                       "grupo": ["a", "b", "c", "d", "e"] * 10})
    out, _ = apply_overrides(df, {})
    infos = infer_types(out)
    assert {i.name: i.kind for i in infos}["year"] == "temporal"
    assert pd.api.types.is_datetime64_any_dtype(out["year"]) and out["year"].iloc[0] == pd.Timestamp("2000-01-01")
    result = build_dashboard(out, infos)
    assert any(c["rule_id"] == "R5" for c in result["charts"])


def test_ano_forcado_como_temporal_pelo_usuario():
    from app.inference import apply_overrides
    df = pd.DataFrame({"safra": [2019, 2020, 2021, None], "v": [1, 2, 3, 4]})
    out, warns = apply_overrides(df, {"safra": "temporal"})
    assert out["safra"].iloc[1] == pd.Timestamp("2020-01-01") and pd.isna(out["safra"].iloc[3]) and not warns


@pytest.mark.parametrize("nome", ["Postal Code", "CEP", "iso_num", "codigo_produto", "Código"])
def test_coluna_numerica_que_e_codigo_e_ignorada(nome):
    rng = np.random.default_rng(0)
    df = pd.DataFrame({nome: rng.integers(10000, 99999, 200), "valor": rng.normal(10, 2, 200)})
    kinds = {i.name: i for i in infer_types(df)}
    assert kinds[nome].kind == "ignored" and "código" in kinds[nome].ignored_reason
    assert kinds["valor"].kind == "numeric"


def test_nome_parecido_com_codigo_mas_decimal_nao_e_ignorado():
    df = pd.DataFrame({"code_score": np.random.default_rng(0).normal(5, 1, 100).round(2)})
    assert infer_types(df)[0].kind == "numeric"
