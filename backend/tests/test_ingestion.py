import io

import pandas as pd
import pytest

from app import synthetic
from app.ingestion import IngestionError, MAX_BYTES, read_table


def test_csv_virgula_e_ponto_e_virgula():
    a = read_table(b"x,y\n1,a\n2,b\n3,c\n", "a.csv")
    b = read_table(b"x;y\n1;a\n2;b\n3;c\n", "b.csv")
    assert a.delimiter == "," and b.delimiter == ";"
    assert list(a.df.columns) == list(b.df.columns) == ["x", "y"]
    assert a.df["x"].tolist() == [1, 2, 3]


def test_csv_brasileiro_latin1_numeros_datas():
    r = read_table(synthetic.brazilian_csv(), "vendas.csv")
    df = r.df
    assert r.encoding is not None and r.encoding.lower() not in ("utf-8", "utf-8-sig")
    assert "São Paulo" in df["Cidade"].tolist()
    assert pd.api.types.is_numeric_dtype(df["Valor"])
    assert df["Valor"].iloc[0] == pytest.approx(1234.56)
    assert df["Variação"].iloc[1] == pytest.approx(-1.2)
    assert pd.api.types.is_datetime64_any_dtype(df["Data"])
    assert df["Data"].iloc[0] == pd.Timestamp(2024, 2, 1)   # dia primeiro, convencao brasileira


@pytest.mark.parametrize("raw,expected", [
    (["1.234,56", "2.000,00", "10,5"], [1234.56, 2000.0, 10.5]),       # brasileiro
    (["1,234.56", "2,000.00", "10.5"], [1234.56, 2000.0, 10.5]),       # americano
    (["3,14", "2,71", "1,41"], [3.14, 2.71, 1.41]),                    # virgula decimal
    (["3.14", "2.71", "1.41"], [3.14, 2.71, 1.41]),                    # ponto decimal
    (["R$ 10,00", "R$ 25,50", "R$ 7,25"], [10.0, 25.5, 7.25]),
])
def test_formatos_numericos(raw, expected):
    content = ("v;k\n" + "\n".join(f"{v};x" for v in raw)).encode()
    df = read_table(content, "n.csv").df
    assert df["v"].tolist() == pytest.approx(expected)


def test_limpeza_de_planilha_suja():
    content = synthetic.to_csv_bytes(synthetic.messy())
    r = read_table(content, "suja.csv")
    df = r.df
    assert "Vazia" not in df.columns                       # coluna vazia removida
    assert len(df) == 5                                    # linha totalmente vazia removida
    assert df["Nome"].isna().sum() == 1                    # 'N/A' tratado como ausente
    assert pd.api.types.is_numeric_dtype(df["Idade"])      # '-' tratado como ausente
    assert df["Idade"].isna().sum() == 1
    assert pd.api.types.is_datetime64_any_dtype(df["Cadastro"])
    assert any("removida" in n for n in r.notes)


def test_cabecalho_duplicado_renomeado():
    r = read_table(b"a,a,b\n1,2,3\n4,5,6\n", "d.csv")
    assert list(r.df.columns) == ["a", "a (2)", "b"]


def test_excel_tipos_nativos():
    r = read_table(synthetic.to_xlsx_bytes(synthetic.sales(50)), "vendas.xlsx")
    assert r.source_format == "excel" and r.sheet_used == "Dados"
    assert pd.api.types.is_datetime64_any_dtype(r.df["Data"])
    assert pd.api.types.is_numeric_dtype(r.df["Receita"])


def test_excel_escolhe_aba_pedida():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"a": [1, 2, 3]}).to_excel(xw, index=False, sheet_name="Um")
        pd.DataFrame({"b": [4, 5, 6]}).to_excel(xw, index=False, sheet_name="Dois")
    r = read_table(buf.getvalue(), "x.xlsx", sheet="Dois")
    assert r.sheets == ["Um", "Dois"] and list(r.df.columns) == ["b"]


def test_excel_com_numeros_como_texto():
    df = pd.DataFrame({"Valor": ["1.234,56", "2.000,00", "99,90", "10,00"], "G": list("abcd")})
    r = read_table(synthetic.to_xlsx_bytes(df), "t.xlsx")
    assert r.df["Valor"].tolist() == pytest.approx([1234.56, 2000.0, 99.9, 10.0])


@pytest.mark.parametrize("content,name,msg", [
    (b"", "a.csv", "vazio"),
    (b"a,b\n1,2\n", "a.pdf", "não suportado"),
    (b"not an excel file", "a.xlsx", "Excel"),
    (b",,\n,,\n", "a.csv", "dados"),
])
def test_erros_de_ingestao(content, name, msg):
    with pytest.raises(IngestionError, match=msg):
        read_table(content, name)


def test_limite_de_tamanho():
    with pytest.raises(IngestionError, match="limite"):
        read_table(b"a\n" + b"1\n" * MAX_BYTES, "grande.csv")


def test_coluna_de_anos_continua_numerica_na_ingestao():
    df = read_table(b"Ano,V\n2020,1\n2021,2\n2022,3\n", "a.csv").df
    assert pd.api.types.is_numeric_dtype(df["Ano"])
