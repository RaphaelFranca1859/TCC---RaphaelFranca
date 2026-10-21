"""Geradores de conjuntos de dados sinteticos.

Usados pelos testes automatizados e pelo protocolo de demonstracao (secao 4.2.4 da
monografia), que exige casos-limite: colunas vazias, numeros armazenados como texto,
datas em formatos mistos, alta cardinalidade e planilhas com uma unica coluna.
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd


def sales(n: int = 500, seed: int = 7) -> pd.DataFrame:
    """Vendas diarias: exercita todas as regras (R1 a R7)."""
    rng = np.random.default_rng(seed)
    dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    region = rng.choice(["Norte", "Sul", "Leste", "Oeste", "Centro"], n)
    product = rng.choice([f"Produto {i}" for i in range(1, 9)], n)
    seller = rng.choice([f"Vendedor {i:02d}" for i in range(1, 26)], n)
    quantity = rng.integers(1, 20, n)
    price = rng.normal(50, 10, n).clip(5)
    revenue = quantity * price + rng.normal(0, 5, n)
    return pd.DataFrame({"Data": dates, "Região": region, "Produto": product, "Vendedor": seller,
                         "Quantidade": quantity, "Receita": revenue.round(2), "Preço": price.round(2)})


def brazilian_csv() -> bytes:
    """CSV tipico exportado por Excel brasileiro: ';', virgula decimal, dd/mm/aaaa e Latin-1."""
    text = (
        "Data;Cidade;Valor;Variação\n"
        "01/02/2024;São Paulo;R$ 1.234,56;3,5%\n"
        "15/02/2024;Salvador;R$ 980,00;-1,2%\n"
        "03/03/2024;Curitiba;R$ 2.450,10;0,8%\n"
        "20/03/2024;São Paulo;R$ 1.100,00;2,1%\n"
        "05/04/2024;Salvador;R$ 1.560,75;1,9%\n"
    )
    return text.encode("latin-1")


def messy() -> pd.DataFrame:
    """Planilha suja: linhas e colunas vazias, cabecalho duplicado, tokens de ausente."""
    return pd.DataFrame({
        "Nome": ["Ana", "Bruno", None, "Carla", "Diego", "N/A"],
        "Nome ": ["x", "y", None, "z", "w", "v"],
        "Idade": ["31", "42", None, "28", "-", "55"],
        "Vazia": [None] * 6,
        "Cadastro": ["2024-01-05", "2024-02-10", None, "2024-03-15", "2024-04-20", "2024-05-25"],
    })


def one_column(n: int = 100) -> pd.DataFrame:
    return pd.DataFrame({"Valor": np.random.default_rng(1).normal(100, 15, n).round(2)})


def constant_column(n: int = 50) -> pd.DataFrame:
    return pd.DataFrame({"Fixo": [7.5] * n, "Grupo": ["A", "B"] * (n // 2)})


def high_cardinality(n: int = 400, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"Cliente": [f"Cliente {i}" for i in rng.integers(0, 120, n)],
                         "Valor": rng.gamma(2.0, 100.0, n).round(2)})


def identifiers(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(5)
    return pd.DataFrame({"ID": np.arange(1, n + 1), "Descrição": [f"item numero {i} detalhado" for i in range(n)],
                         "Valor": rng.normal(10, 2, n).round(2), "Categoria": rng.choice(["A", "B", "C"], n)})


def to_csv_bytes(df: pd.DataFrame, **kwargs) -> bytes:
    return df.to_csv(index=False, **kwargs).encode("utf-8")


def to_xlsx_bytes(df: pd.DataFrame, sheet_name: str = "Dados") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name=sheet_name)
    return buf.getvalue()
