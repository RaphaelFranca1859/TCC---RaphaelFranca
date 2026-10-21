"""Modulo de inferencia automatica de tipos de variaveis.

Classifica cada coluna como numerica, categorica ou temporal (os tres tipos que
alimentam o motor de visualizacao) e identifica colunas que nao devem gerar
graficos (identificadores, texto livre, colunas vazias). A classificacao combina
o tipo do Pandas com uma heuristica de cardinalidade. Todos os limiares ficam em
InferenceConfig para serem calibrados na etapa de demonstracao.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

from .ingestion import _parse_dates, parse_number_column, to_numeric_series

CHARTABLE = ("numeric", "categorical", "temporal")
ALL_KINDS = CHARTABLE + ("ignored",)
_ID_HINT = re.compile(r"(^|[^a-z])(id|cod|codigo|código|matricula|matrícula|cpf|cnpj|uuid|chave)([^a-z]|$)", re.I)
_YEAR_HINT = re.compile(r"^(ano|year)$", re.I)


@dataclass(frozen=True)
class InferenceConfig:
    low_unique_ratio: float = 0.5          # abaixo disso, texto e tratado como categorico
    max_categories_always: int = 30        # ate esse numero de valores distintos, texto e sempre categorico
    text_unique_ratio: float = 0.9         # acima disso (e com muitos valores), texto vira "ignorado"
    text_min_unique: int = 50
    int_as_category_max_unique: int = 6    # inteiros com poucos valores distintos viram categoricos
    int_as_category_max_ratio: float = 0.05
    id_unique_ratio: float = 0.98
    min_rows_for_id: int = 10


DEFAULT_CONFIG = InferenceConfig()


@dataclass
class ColumnInfo:
    name: str
    kind: str                  # kind efetivo (apos eventual ajuste do usuario)
    inferred_kind: str         # kind inferido automaticamente
    ignored_reason: str | None
    dtype: str
    n_unique: int
    unique_ratio: float
    missing_ratio: float
    sample: list = field(default_factory=list)
    overridden: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def infer_types(df: pd.DataFrame, overrides: dict[str, str] | None = None,
                config: InferenceConfig = DEFAULT_CONFIG) -> list[ColumnInfo]:
    overrides = overrides or {}
    infos = []
    for col in df.columns:
        info = _infer_column(df[col], str(col), config)
        forced = overrides.get(str(col))
        if forced and forced in ALL_KINDS and forced != info.kind:
            info.kind, info.overridden = forced, True
            info.ignored_reason = "Ignorada por escolha do usuário." if forced == "ignored" else None
        infos.append(info)
    return infos


def _infer_column(s: pd.Series, name: str, cfg: InferenceConfig) -> ColumnInfo:
    n = len(s)
    nonnull = s.dropna()
    n_nonnull = len(nonnull)
    n_unique = int(nonnull.nunique()) if n_nonnull else 0
    ratio = (n_unique / n_nonnull) if n_nonnull else 0.0
    missing = float(s.isna().mean()) if n else 1.0
    kind, reason = "ignored", None

    if n_nonnull == 0:
        reason = "Coluna sem valores."
    elif pd.api.types.is_bool_dtype(s):
        kind = "categorical"
    elif pd.api.types.is_datetime64_any_dtype(s):
        kind = "temporal"
    elif pd.api.types.is_numeric_dtype(s):
        kind, reason = _classify_numeric(nonnull, name, n_unique, ratio, n_nonnull, cfg)
    else:
        kind, reason = _classify_text(nonnull, n_unique, ratio, cfg)

    return ColumnInfo(name=name, kind=kind, inferred_kind=kind, ignored_reason=reason, dtype=str(s.dtype),
                      n_unique=n_unique, unique_ratio=round(ratio, 4), missing_ratio=round(missing, 4),
                      sample=_sample(nonnull))


def _classify_numeric(nonnull, name, n_unique, ratio, n, cfg):
    is_int = bool(np.all(np.mod(nonnull.to_numpy(dtype=float), 1) == 0))
    if is_int and _YEAR_HINT.match(name) and nonnull.between(1900, 2100).all():
        return "temporal", None
    if is_int and n >= cfg.min_rows_for_id and ratio >= cfg.id_unique_ratio:
        if _ID_HINT.search(name) or _is_sequence(nonnull):
            return "ignored", "Parece um identificador (valores únicos)."
    if is_int and n_unique <= cfg.int_as_category_max_unique and ratio <= cfg.int_as_category_max_ratio:
        return "categorical", None
    return "numeric", None


def _is_sequence(nonnull: pd.Series) -> bool:
    v = nonnull.to_numpy(dtype=float)
    return len(v) > 1 and bool(np.all(np.diff(v) == 1))


def _classify_text(nonnull, n_unique, ratio, cfg):
    if ratio >= cfg.text_unique_ratio and n_unique >= cfg.text_min_unique:
        return "ignored", "Texto livre ou identificador (quase todos os valores são únicos)."
    if ratio <= cfg.low_unique_ratio or n_unique <= cfg.max_categories_always:
        return "categorical", None
    return "categorical", None


def _sample(nonnull: pd.Series, k: int = 3) -> list:
    out = []
    for v in nonnull.head(k).tolist():
        if isinstance(v, pd.Timestamp):
            out.append(v.strftime("%Y-%m-%d") if v == v.normalize() else v.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            out.append(v if isinstance(v, (int, float, str)) else str(v))
    return out


# --------------------------------------------------------------------- ajustes do usuario
def apply_overrides(df: pd.DataFrame, overrides: dict[str, str]) -> tuple[pd.DataFrame, list[str]]:
    """Converte colunas conforme os tipos escolhidos pelo usuario.

    Retorna o novo DataFrame e uma lista de avisos (por exemplo, valores que não puderam ser convertidos).
    """
    df, warnings = df.copy(), []
    for col, kind in overrides.items():
        if col not in df.columns:
            continue
        if kind not in ALL_KINDS:
            raise ValueError(f"Tipo inválido '{kind}' para a coluna '{col}'.")
        s, before = df[col], df[col].notna().sum()
        if kind == "numeric" and not pd.api.types.is_numeric_dtype(s):
            text = s.astype(str).where(s.notna())
            _, style = parse_number_column(text.dropna())
            df[col] = to_numeric_series(text, style or "ponto decimal")
        elif kind == "temporal" and not pd.api.types.is_datetime64_any_dtype(s):
            df[col] = _parse_dates(s.astype(str).where(s.notna()))
        elif kind == "categorical" and (pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s)):
            df[col] = s.map(lambda v: v if pd.isna(v) else (f"{v:g}" if isinstance(v, float) else str(v)))
        lost = int(before - df[col].notna().sum())
        if lost > 0:
            pct = 100 * lost / max(before, 1)
            warnings.append(f"{lost} valor(es) ({pct:.0f}%) da coluna '{col}' não puderam ser convertidos "
                            f"para '{kind}' e foram tratados como ausentes.")
    return df, warnings
