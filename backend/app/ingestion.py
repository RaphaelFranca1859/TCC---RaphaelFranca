"""Modulo de ingestao e tratamento de dados.

Le planilhas Excel (.xlsx, .xlsm) e CSV, detecta codificacao e delimitador,
limpa inconsistencias comuns (colunas vazias, nomes duplicados, numeros salvos
como texto em formato brasileiro ou americano, datas em formatos mistos) e
devolve um DataFrame consistente, junto com um registro das transformacoes
aplicadas (usado na interface e nos estudos de caso da etapa de demonstracao).
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

import chardet
import numpy as np
import pandas as pd

MAX_BYTES = 20 * 1024 * 1024
CSV_EXTENSIONS = {".csv", ".tsv", ".txt"}
EXCEL_EXTENSIONS = {".xlsx", ".xlsm"}
NA_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "#n/d", "#n/a", "s/d", "nd"}

NUMERIC_GATE = 0.95   # fracao minima de valores com cara de numero para converter a coluna
DATE_GATE = 0.90      # fracao minima de valores com cara de data para converter a coluna

_DATE_PATTERNS = [
    r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)?$",
    r"^\d{1,2}/\d{4}$",
    r"^\d{4}-\d{2}$",
]
_DATE_RE = "|".join(f"(?:{p})" for p in _DATE_PATTERNS)
_DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S",
                 "%d/%m/%Y %H:%M", "%d-%m-%Y", "%d.%m.%Y", "%m/%Y", "%Y-%m")
_NUMBER_CHARS = re.compile(r"^[+-]?[\d.,]+$")


class IngestionError(ValueError):
    """Erro de leitura ou formato de arquivo, com mensagem apresentavel ao usuario."""


@dataclass
class IngestionResult:
    df: pd.DataFrame
    sheets: list[str] = field(default_factory=list)
    sheet_used: str | None = None
    source_format: str = "csv"
    delimiter: str | None = None
    encoding: str | None = None
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- leitura
def read_table(content: bytes, filename: str, sheet: str | None = None) -> IngestionResult:
    if not content:
        raise IngestionError("O arquivo enviado está vazio.")
    if len(content) > MAX_BYTES:
        raise IngestionError(f"O arquivo excede o limite de {MAX_BYTES // (1024 * 1024)} MB.")
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in CSV_EXTENSIONS:
        result = _read_csv(content, tab_default=(ext == ".tsv"))
    elif ext in EXCEL_EXTENSIONS:
        result = _read_excel(content, sheet)
    else:
        raise IngestionError("Formato não suportado. Envie um arquivo .xlsx, .xlsm ou .csv.")
    result.df = clean_dataframe(result.df, result.notes)
    if result.df.empty or result.df.shape[1] == 0:
        raise IngestionError("Não foram encontrados dados na planilha após a limpeza.")
    return result


def _decode(content: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return content.decode(enc), enc
        except UnicodeDecodeError:
            pass
    guess = chardet.detect(content[:100_000]).get("encoding") or "latin-1"
    try:
        return content.decode(guess), guess
    except (UnicodeDecodeError, LookupError):
        return content.decode("latin-1"), "latin-1"


def _sniff_delimiter(text: str, tab_default: bool) -> str:
    head = "\n".join(text.splitlines()[:30])
    try:
        return csv.Sniffer().sniff(head, delimiters=",;\t|").delimiter
    except csv.Error:
        counts = {d: head.count(d) for d in (";", ",", "\t", "|")}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ("\t" if tab_default else ",")


def _read_csv(content: bytes, tab_default: bool) -> IngestionResult:
    text, enc = _decode(content)
    delim = _sniff_delimiter(text, tab_default)
    kwargs = dict(sep=delim, dtype=str, skipinitialspace=True, header=None, on_bad_lines="skip")
    try:
        try:
            raw = pd.read_csv(io.StringIO(text), engine="c", **kwargs)
        except (ValueError, pd.errors.ParserError):
            raw = pd.read_csv(io.StringIO(text), engine="python", **kwargs)
    except Exception as exc:  # pandas lanca varios tipos de erro de parsing
        raise IngestionError(f"Não foi possível ler o CSV: {exc}") from exc
    if raw.empty:
        raise IngestionError("Não foram encontrados dados na planilha após a limpeza.")
    # O cabecalho e lido manualmente para que nomes duplicados cheguem intactos a limpeza.
    df = raw.iloc[1:].reset_index(drop=True)
    df.columns = raw.iloc[0].tolist()
    notes = []
    if enc not in ("utf-8", "utf-8-sig"):
        notes.append(f"Codificação detectada: {enc}.")
    return IngestionResult(df=df, source_format="csv", delimiter=delim, encoding=enc, notes=notes)


def _read_excel(content: bytes, sheet: str | None) -> IngestionResult:
    try:
        book = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise IngestionError(f"Não foi possível abrir a planilha Excel: {exc}") from exc
    sheets = list(book.sheet_names)
    used = sheet if sheet in sheets else _first_nonempty_sheet(book, sheets)
    df = book.parse(used, dtype=object)
    notes = []
    if len(sheets) > 1:
        notes.append(f"A planilha possui {len(sheets)} abas; foi lida a aba '{used}'.")
    return IngestionResult(df=df, sheets=sheets, sheet_used=used, source_format="excel", notes=notes)


def _first_nonempty_sheet(book: pd.ExcelFile, sheets: list[str]) -> str:
    for name in sheets:
        if not book.parse(name, nrows=5, header=None).dropna(how="all").empty:
            return name
    return sheets[0]


# --------------------------------------------------------------------------- limpeza
def clean_dataframe(df: pd.DataFrame, notes: list[str] | None = None) -> pd.DataFrame:
    notes = notes if notes is not None else []
    df = df.copy()
    df.columns = _normalize_headers(list(df.columns), notes)

    for col in df.columns:
        if not (pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col])
                or pd.api.types.is_bool_dtype(df[col])):
            df[col] = _clean_text_series(df[col])

    before_rows, before_cols = df.shape
    df = df.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    if df.shape[0] < before_rows:
        notes.append(f"{before_rows - df.shape[0]} linha(s) totalmente vazia(s) removida(s).")
    if df.shape[1] < before_cols:
        notes.append(f"{before_cols - df.shape[1]} coluna(s) totalmente vazia(s) removida(s).")

    for col in list(df.columns):
        df[col] = _coerce_column(df[col], col, notes)
    return df


def _normalize_headers(cols: list, notes: list[str]) -> list[str]:
    out, seen = [], {}
    for i, c in enumerate(cols, start=1):
        name = "" if c is None or (isinstance(c, float) and np.isnan(c)) else str(c).strip()
        if not name or name.lower().startswith("unnamed:"):
            name = f"Coluna {i}"
        if name in seen:
            seen[name] += 1
            new = f"{name} ({seen[name]})"
            notes.append(f"Nome de coluna duplicado '{name}' renomeado para '{new}'.")
            name = new
        else:
            seen[name] = 1
        out.append(name)
    return out


def _clean_text_series(s: pd.Series) -> pd.Series:
    """Remove espacos (inclusive o espaco insecavel) e troca tokens de ausente por NaN, de forma vetorizada."""
    def clean(txt: pd.Series) -> pd.Series:
        txt = txt.str.replace("\u00a0", " ", regex=False).str.strip()
        return txt.mask(txt.str.lower().isin(NA_TOKENS))

    if s.dtype != object:
        return clean(s) if pd.api.types.is_string_dtype(s) else s
    is_str = s.map(lambda v: isinstance(v, str))      # colunas do Excel podem misturar tipos
    if not is_str.any():
        return s
    out = s.copy()
    out[is_str] = clean(s[is_str].astype(str))
    return out


def _coerce_column(s: pd.Series, name: str, notes: list[str]) -> pd.Series:
    if pd.api.types.is_bool_dtype(s) or pd.api.types.is_datetime64_any_dtype(s) or pd.api.types.is_numeric_dtype(s):
        return s
    nonnull = s.dropna()
    if nonnull.empty:
        return s

    if s.dtype == object:  # Excel pode entregar colunas mistas: trata datas e numeros nativos
        head = nonnull.head(50)
        if any(isinstance(v, (pd.Timestamp, np.datetime64)) or (hasattr(v, "year") and hasattr(v, "month"))
               for v in head):
            parsed = pd.to_datetime(s, errors="coerce")
            if parsed.notna().sum() / len(nonnull) >= DATE_GATE:
                return parsed
        if all(isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) for v in nonnull):
            return pd.to_numeric(s, errors="coerce")

    text = s.astype(str).where(s.notna())
    sample = _sample(nonnull.astype(str))
    # Triagem em amostra: so processa a coluna inteira quando ela parece numerica ou data.
    if parse_number_column(sample)[0] is not None:
        num, style = parse_number_column(text.dropna())
        if num is not None:
            notes.append(f"Coluna '{name}' convertida de texto para número ({style}).")
            return to_numeric_series(text, style)

    if parse_date_column(sample) is not None and parse_date_column(text.dropna()) is not None:
        notes.append(f"Coluna '{name}' convertida de texto para data.")
        return _parse_dates(text)
    return text


def _sample(s: pd.Series, k: int = 1000) -> pd.Series:
    return s if len(s) <= k else s.sample(k, random_state=0)


# ------------------------------------------------------------------------ numeros
_DECOR_PREFIX = r"(?i)^(?:r\$|us\$|\$|eur|€)\s*"


def _strip_decorations(s: pd.Series) -> pd.Series:
    """Remove simbolo de moeda, '%' e espacos de uma serie de textos."""
    return (s.str.strip().str.replace(_DECOR_PREFIX, "", regex=True)
            .str.replace(r"\s*%$", "", regex=True).str.replace(" ", "", regex=False))


def parse_number_column(strings: pd.Series) -> tuple[pd.Series | None, str]:
    """Decide se uma coluna de texto representa numeros e em qual formato.

    Retorna (serie_convertida_ou_None, descricao_do_formato).
    """
    cleaned = _strip_decorations(strings.astype(str))
    ok = cleaned.str.fullmatch(r"[+-]?[\d.,]+").fillna(False).astype(bool)
    if ok.mean() < NUMERIC_GATE:
        return None, ""
    valid = cleaned[ok]
    style = _detect_style(valid)
    conv = to_numeric_series(valid, style)
    if conv.notna().mean() < NUMERIC_GATE:
        return None, ""
    return conv, style


def _detect_style(values: pd.Series) -> str:
    has_comma = values.str.contains(",", regex=False)
    has_dot = values.str.contains(".", regex=False)
    if has_comma.any() and has_dot.any():
        both = values[has_comma & has_dot]
        br = (both.str.rfind(",") > both.str.rfind(".")).mean()
        return "formato brasileiro" if br >= 0.5 else "formato americano"
    if has_comma.any():
        multi_group = values[has_comma].str.fullmatch(r"[+-]?\d{1,3}(?:,\d{3}){2,}")
        return "formato americano" if multi_group.all() else "vírgula decimal"
    if has_dot.any():
        multi_group = values[has_dot].str.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3}){2,}")
        return "formato brasileiro" if multi_group.any() else "ponto decimal"
    return "inteiros"


def to_numeric_series(strings: pd.Series, style: str) -> pd.Series:
    """Converte textos numericos para float conforme o formato detectado (vetorizado)."""
    v = _strip_decorations(strings)
    if style == "formato brasileiro":
        v = v.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    elif style == "vírgula decimal":
        v = v.str.replace(",", ".", regex=False)
    elif style == "formato americano":
        v = v.str.replace(",", "", regex=False)
    return pd.to_numeric(v, errors="coerce")


# --------------------------------------------------------------------------- datas
def parse_date_column(strings: pd.Series) -> pd.Series | None:
    if strings.empty or strings.astype(str).str.contains(_DATE_RE, regex=True).mean() < DATE_GATE:
        return None
    parsed = _parse_dates(strings.astype(str))
    return parsed if parsed.notna().mean() >= DATE_GATE else None


def _parse_dates(strings: pd.Series) -> pd.Series:
    """Interpreta datas assumindo dia primeiro (convencao brasileira) quando ha ambiguidade.

    Tenta primeiro formatos conhecidos (rapido) e so recorre ao parser flexivel quando nenhum serve.
    """
    sample = strings.dropna().head(200)
    for fmt in _DATE_FORMATS:
        if len(sample) and pd.to_datetime(sample, format=fmt, errors="coerce").notna().mean() >= 0.95:
            return pd.to_datetime(strings, format=fmt, errors="coerce")
    iso = sample.str.match(r"^\d{4}-\d{1,2}-\d{1,2}").mean() if len(sample) else 0
    try:
        if iso > 0.5:
            return pd.to_datetime(strings, errors="coerce", format="mixed")
        return pd.to_datetime(strings, errors="coerce", dayfirst=True, format="mixed")
    except (ValueError, TypeError):
        return pd.to_datetime(strings, errors="coerce")
