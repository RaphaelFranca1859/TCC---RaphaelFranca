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
