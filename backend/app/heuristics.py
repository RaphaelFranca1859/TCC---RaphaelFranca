"""Motor de visualizacao: heuristica de selecao automatica de graficos.

Implementa as sete regras do Quadro 5 da monografia. Cada regra e explicita,
auditavel e carrega a fundamentacao bibliografica que a justifica. O motor
registra, para cada dashboard, um log de decisoes (quais regras dispararam,
quais foram ignoradas e por que), que serve de evidencia nos estudos de caso da
etapa de demonstracao e de insumo para a avaliacao com especialistas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .inference import ColumnInfo

AGGREGATIONS = {"auto": "automática", "sum": "soma", "mean": "média", "median": "mediana"}
# Nomes de coluna que indicam valor unitario, taxa ou medida que nao faz sentido somar.
_MEAN_HINT = re.compile(
    r"(?:\b(?:pre[cç]o|price|unit[aá]ri[oa]|taxa|rate|m[eé]dia|average|nota|score|idade|age|temperatura|"
    r"percentual|percent|desconto|discount|margem|margin|ratio|[ií]ndice|index|peso|weight|altura|height)s?\b)|%",
    re.I)


def resolve_agg(column: str, agg: str) -> str:
    """No modo automatico, usa media para colunas que parecem valores unitarios ou taxas e soma nas demais."""
    if agg != "auto":
        return agg
    words = re.sub(r"[_\-./]+", " ", column)      # "preco_unitario" e "Preço unitário" se comportam igual
    return "mean" if _MEAN_HINT.search(words) else "sum"
SORTS = ("value_desc", "value_asc", "label")


@dataclass(frozen=True)
class HeuristicConfig:
    category_limit: int = 10        # limiar entre R2 e R3 (Quadro 5)
    top_n: int = 15                 # maximo de categorias exibidas em barras
    max_charts: int = 12
    max_series: int = 5             # series maximas em linhas multiplas (R7)
    max_histograms: int = 3
    max_frequency_charts: int = 3
    max_group_charts: int = 4
    scatter_max_points: int = 2000
    scatter_max_pairs: int = 2
    corr_min_abs: float = 0.2
    scale_warning_ratio: float = 10.0


DEFAULT_CONFIG = HeuristicConfig()


@dataclass(frozen=True)
class Rule:
    id: str
    combination: str
    chart: str
    rationale: str
    sources: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"id": self.id, "combination": self.combination, "chart": self.chart,
                "rationale": self.rationale, "sources": list(self.sources)}


RULES: dict[str, Rule] = {r.id: r for r in [
    Rule("R1", "1 numérica contínua", "Histograma",
         "Mostra a distribuição de uma única variável quantitativa, aplicando o critério de expressividade.",
         ("Mackinlay (1986)",)),
    Rule("R2", "1 categórica (≤ 10 categorias)", "Barras (padrão) ou setores",
         "Barras permitem comparar comprimentos em escala comum, tarefa de maior precisão perceptiva. Setores são "
         "oferecidos apenas como alternativa para partes de um todo, pois ângulos e áreas são decodificados com "
         "menor precisão.",
         ("Cleveland; McGill (1984)", "Knaflic (2015)")),
    Rule("R3", "1 categórica (> 10 categorias)", "Barras horizontais ordenadas",
         "Muitas categorias e rótulos longos favorecem barras horizontais, e a ordenação facilita a leitura de ranking.",
         ("Few (2013)", "Knaflic (2015)")),
    Rule("R4", "2 numéricas", "Dispersão (scatter plot)",
         "Posição em duas escalas comuns, que favorece a percepção da relação entre variáveis.",
         ("Cleveland; McGill (1984)", "Few (2013)")),
    Rule("R5", "1 numérica × 1 temporal", "Linha",
         "A linha evidencia tendência e variação ao longo do tempo.",
         ("Few (2013)", "Knaflic (2015)")),
    Rule("R6", "1 numérica × 1 categórica", "Barras agrupadas",
         "Comparação de valores entre categorias por comprimento em escala comum.",
         ("Cleveland; McGill (1984)", "Few (2013)")),
    Rule("R7", "1 temporal + 2 ou mais numéricas", "Linhas múltiplas",
         "Permite comparar a trajetória de várias medidas no mesmo eixo temporal.",
         ("Few (2013)", "Knaflic (2015)")),
]}


# ---------------------------------------------------------------------- utilitarios
def _label(v) -> str:
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return str(v)


def cat_labels(s: pd.Series) -> pd.Series:
    """Rotulos textuais de uma coluna categorica, preservando NaN."""
    return s.map(lambda v: v if pd.isna(v) else _label(v))


def _num(x) -> float | None:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), 4)


def _fmt(x: float) -> str:
    if abs(x) >= 1000 or float(x).is_integer():
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:.2f}".replace(".", ",")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


# ---------------------------------------------------------------------- filtros
def apply_filters(df: pd.DataFrame, filters: list[dict], kinds: dict[str, str]) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for f in filters or []:
        col = f.get("column")
        if col not in df.columns:
            raise ValueError(f"Filtro aplicado a coluna inexistente: '{col}'.")
        kind = kinds.get(col)
        s = df[col]
        if kind == "categorical":
            values = [str(v) for v in f.get("values", [])]
            if values:
                mask &= cat_labels(s).isin(values)
        elif kind == "numeric":
            if f.get("min") is not None:
                mask &= s >= float(f["min"])
            if f.get("max") is not None:
                mask &= s <= float(f["max"])
        elif kind == "temporal":
            if f.get("start"):
                mask &= s >= pd.to_datetime(f["start"])
            if f.get("end"):
                mask &= s <= pd.to_datetime(f["end"]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return df[mask]


def filter_options(df: pd.DataFrame, infos: list[ColumnInfo], max_values: int = 60) -> dict:
    """Opcoes de filtro por coluna, calculadas sobre os dados completos."""
    out = {}
    for info in infos:
        if info.kind not in ("numeric", "categorical", "temporal"):
            continue
        s = df[info.name].dropna()
        if s.empty:
            continue
        if info.kind == "categorical":
            counts = cat_labels(s).value_counts()
            out[info.name] = {"kind": "categorical", "values": list(counts.index[:max_values]),
                              "truncated": bool(len(counts) > max_values)}
        elif info.kind == "numeric":
            out[info.name] = {"kind": "numeric", "min": _num(s.min()), "max": _num(s.max())}
        else:
            out[info.name] = {"kind": "temporal", "min": s.min().date().isoformat(),
                              "max": s.max().date().isoformat()}
    return out


# ---------------------------------------------------------------------- motor principal
def build_dashboard(df: pd.DataFrame, infos: list[ColumnInfo], filters: list[dict] | None = None,
                    agg: str = "auto", sort: str = "value_desc",
                    config: HeuristicConfig = DEFAULT_CONFIG) -> dict:
    if agg not in AGGREGATIONS:
        raise ValueError(f"Agregação inválida: '{agg}'. Use uma de {sorted(AGGREGATIONS)}.")
    if sort not in SORTS:
        raise ValueError(f"Ordenação inválida: '{sort}'. Use uma de {list(SORTS)}.")

    kinds = {i.name: i.kind for i in infos}
    fdf = apply_filters(df, filters or [], kinds)
    log: list[str] = []
    charts: list[dict] = []

    def add(chart: dict) -> bool:
        if len(charts) >= config.max_charts:
            return False
        charts.append(chart)
        return True

    if fdf.empty:
        return _response(df, fdf, infos, charts, log + ["Nenhum registro atende aos filtros aplicados."], agg, sort,
                         filters, [])

    def coverage(c: str) -> int:
        return int(fdf[c].notna().sum())

    numerics = sorted([i.name for i in infos if i.kind == "numeric" and coverage(i.name) > 0], key=lambda c: -coverage(c))
    temporals = sorted([i.name for i in infos if i.kind == "temporal" and coverage(i.name) > 0], key=lambda c: -coverage(c))
    categoricals = [i.name for i in infos if i.kind == "categorical" and coverage(i.name) > 0]
    nuniq = {c: int(cat_labels(fdf[c]).nunique()) for c in categoricals}
    categoricals.sort(key=lambda c: (nuniq[c] > config.category_limit, -coverage(c)))

    for i in infos:
        if i.kind == "ignored":
            log.append(f"Coluna '{i.name}' ignorada: {i.ignored_reason or 'sem uso em gráficos.'}")
    log.append(f"Variáveis: {len(numerics)} numérica(s), {len(categoricals)} categórica(s), {len(temporals)} temporal(is).")

    if agg == "auto":
        means = [c for c in numerics if resolve_agg(c, agg) == "mean"]
        if means:
            log.append("Agregação automática: média para " + ", ".join(f"'{c}'" for c in means) +
                       " (o nome sugere valor unitário ou taxa); soma para as demais colunas numéricas.")

    tcol = temporals[0] if temporals else None
    for extra in temporals[1:]:
        log.append(f"Coluna temporal '{extra}' não usada: a coluna '{tcol}' tem maior cobertura.")

    # ---- R5 e R7: tempo
    if tcol and numerics:
        grain = _grain(fdf[tcol])
        if grain is None:
            log.append(f"R5/R7 não aplicadas: a coluna '{tcol}' tem menos de dois períodos distintos.")
        elif len(numerics) == 1:
            add(_line_chart("R5", fdf, tcol, [numerics[0]], grain, agg, config, log))
        else:
            add(_line_chart("R7", fdf, tcol, numerics[:config.max_series], grain, agg, config, log))
    elif tcol:
        log.append("Coluna temporal encontrada, mas sem variável numérica: nenhuma regra de série temporal aplicada.")

    # ---- R6: numerica x categorica
    group_count = 0
    for cat in categoricals[:2]:
        for num in numerics[:2]:
            if group_count >= config.max_group_charts:
                break
            if nuniq[cat] < 2:
                log.append(f"R6 não aplicada a '{cat}': só há uma categoria.")
                continue
            if add(_group_chart(fdf, cat, num, agg, sort, config)):
                group_count += 1

    # ---- R2 e R3: frequencia de categoricas
    for cat in categoricals[:config.max_frequency_charts]:
        if nuniq[cat] < 2:
            log.append(f"R2/R3 não aplicadas a '{cat}': só há uma categoria.")
            continue
        add(_frequency_chart(fdf, cat, nuniq[cat], sort, config))

    # ---- R1: histogramas
    hist_count = 0
    for num in numerics:
        if hist_count >= config.max_histograms:
            break
        if fdf[num].nunique() < 2:
            log.append(f"R1 não aplicada a '{num}': valor constante.")
            continue
        if add(_histogram(fdf, num)):
            hist_count += 1

    # ---- R4: dispersao
    if len(numerics) >= 2:
        for pair in _scatter_pairs(fdf, numerics, config, log):
            add(_scatter(fdf, pair[0], pair[1], config, pair[2]))

    log.append(f"{len(charts)} gráfico(s) gerado(s).")
    kpis = _kpis(df, fdf, numerics)
    return _response(df, fdf, infos, charts, log, agg, sort, filters, kpis)


def _response(df, fdf, infos, charts, log, agg, sort, filters, kpis) -> dict:
    return {
        "meta": {"rows_total": int(len(df)), "rows_filtered": int(len(fdf)), "charts": len(charts),
                 "agg": agg, "sort": sort, "filters": filters or []},
        "kpis": kpis, "charts": charts, "decision_log": log,
    }


def _kpis(df, fdf, numerics) -> list[dict]:
    out = [{"label": "Registros", "value": int(len(fdf)),
            "detail": f"de {len(df)}" if len(fdf) != len(df) else None}]
    for c in numerics[:2]:
        out.append({"label": f"Soma de {c}", "value": _num(fdf[c].sum()), "detail": None})
        out.append({"label": f"Média de {c}", "value": _num(fdf[c].mean()), "detail": None})
    return out


def _explain(rule_id: str, cols: str, extra: str = "") -> dict:
    r = RULES[rule_id]
    text = f"Regra {r.id}, {r.combination}, aplicada a {cols}. Gráfico: {r.chart.lower()}. {r.rationale}"
    return {"rule_id": r.id, "rule_name": r.combination, "explanation": (text + " " + extra).strip(),
            "sources": list(r.sources)}


# ---------------------------------------------------------------------- graficos
def _grain(s: pd.Series) -> str | None:
    s = s.dropna()
    if s.empty:
        return None
    span = (s.max() - s.min()).days
    grain = "D" if span <= 62 else ("M" if span <= 365 * 3 else "Y")
    return grain if s.dt.to_period(grain).nunique() >= 2 else None


def _line_chart(rule_id, df, tcol, ycols, grain, agg, config, log) -> dict:
    period = df[tcol].dt.to_period(grain)
    full = pd.period_range(period.min(), period.max(), freq=grain)
    series, warns, used = [], [], []
    for y in ycols:
        a = resolve_agg(y, agg)
        used.append(a)
        grouped = df.groupby(period)[y].agg(a).reindex(full)
        name = f"{y} ({AGGREGATIONS[a]})" if agg == "auto" and len(ycols) > 1 else y
        series.append({"name": name, "values": [_num(v) for v in grouped.to_numpy()]})
    labels = [str(p) for p in full]
    if rule_id == "R7":
        mags = [abs(np.nanmean([v for v in s["values"] if v is not None])) for s in series if any(v is not None for v in s["values"])]
        mags = [m for m in mags if m > 0]
        if mags and max(mags) / min(mags) > config.scale_warning_ratio:
            warns.append("As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis.")
    grain_txt = {"D": "dia", "M": "mês", "Y": "ano"}[grain]
    if len(set(used)) == 1:
        title = f"{AGGREGATIONS[used[0]].capitalize()} de {', '.join(ycols)} por {grain_txt}"
        agg_out = used[0]
    else:
        parts = [f"{AGGREGATIONS[a]} de {y}" for a, y in zip(used, ycols)]
        title = f"{', '.join(parts)} por {grain_txt}"
        title = title[0].upper() + title[1:]
        agg_out = "mixed"
    cols = ", ".join(f"'{c}'" for c in ycols) + f" ao longo de '{tcol}'"
    chart = {"id": f"{rule_id}-{_slug(tcol)}-{_slug('-'.join(ycols))}", "chart_type": "line" if rule_id == "R5" else "multiline",
             "alternatives": [], "title": title,
             "x": {"column": tcol, "kind": "temporal"}, "y": [{"column": c, "kind": "numeric"} for c in ycols],
             "agg": agg_out, "data": {"labels": labels, "series": series}, "warnings": warns}
    chart.update(_explain(rule_id, cols, f"Granularidade automática: {grain_txt}."))
    log.append(f"{rule_id} disparada: {cols} (granularidade {grain_txt}).")
    return chart


def _sorted_series(values: pd.Series, sort: str) -> pd.Series:
    if sort == "value_asc":
        return values.sort_values(ascending=True)
    if sort == "label":
        return values.sort_index()
    return values.sort_values(ascending=False)


def _group_chart(df, cat, num, agg, sort, config) -> dict:
    labels = cat_labels(df[cat])
    agg = resolve_agg(num, agg)
    grouped = df.groupby(labels)[num].agg(agg).dropna()
    total_cats = len(grouped)
    top = grouped.sort_values(ascending=False).head(config.top_n)
    top = _sorted_series(top, sort)
    horizontal = total_cats > config.category_limit
    warns = [f"Exibidas as {config.top_n} maiores categorias de {total_cats}."] if total_cats > config.top_n else []
    chart = {"id": f"R6-{_slug(cat)}-{_slug(num)}", "chart_type": "hbar" if horizontal else "bar", "alternatives": [],
             "title": f"{AGGREGATIONS[agg].capitalize()} de {num} por {cat}",
             "x": {"column": cat, "kind": "categorical"}, "y": [{"column": num, "kind": "numeric"}], "agg": agg,
             "data": {"labels": list(top.index), "values": [_num(v) for v in top.to_numpy()]}, "warnings": warns}
    chart.update(_explain("R6", f"'{num}' por '{cat}'"))
    return chart


def _frequency_chart(df, cat, n_unique, sort, config) -> dict:
    counts = cat_labels(df[cat]).value_counts()
    shown = _sorted_series(counts.head(config.top_n), sort)
    few = n_unique <= config.category_limit
    rule_id = "R2" if few else "R3"
    warns = [f"Exibidas as {config.top_n} categorias mais frequentes de {n_unique}."] if n_unique > config.top_n else []
    chart = {"id": f"{rule_id}-{_slug(cat)}", "chart_type": "bar" if few else "hbar",
             "alternatives": ["pie"] if few else [], "title": f"Frequência de {cat}",
             "x": {"column": cat, "kind": "categorical"}, "y": [], "agg": "count",
             "data": {"labels": list(shown.index), "values": [int(v) for v in shown.to_numpy()]}, "warnings": warns}
    chart.update(_explain(rule_id, f"'{cat}' ({n_unique} categorias)"))
    return chart


def _histogram(df, num) -> dict:
    vals = df[num].dropna().to_numpy(dtype=float)
    edges = np.histogram_bin_edges(vals, bins="auto")
    bins = int(min(max(len(edges) - 1, 5), 30))
    counts, edges = np.histogram(vals, bins=bins)
    labels = [f"{_fmt(edges[i])} a {_fmt(edges[i + 1])}" for i in range(len(counts))]
    chart = {"id": f"R1-{_slug(num)}", "chart_type": "histogram", "alternatives": [], "title": f"Distribuição de {num}",
             "x": {"column": num, "kind": "numeric"}, "y": [], "agg": "count",
             "data": {"labels": labels, "values": [int(c) for c in counts]}, "warnings": []}
    chart.update(_explain("R1", f"'{num}'"))
    return chart


def _scatter_pairs(df, numerics, config, log) -> list[tuple[str, str, float]]:
    cols = numerics[:8]
    corr = df[cols].corr(numeric_only=True)
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            if pd.notna(r):
                pairs.append((a, b, float(r)))
    if not pairs:
        log.append("R4 não aplicada: não foi possível calcular correlação entre as variáveis numéricas.")
        return []
    pairs.sort(key=lambda p: -abs(p[2]))
    strong = [p for p in pairs if abs(p[2]) >= config.corr_min_abs][:config.scatter_max_pairs]
    if strong:
        return strong
    log.append(f"R4: correlações fracas (|r| < {config.corr_min_abs}); exibido apenas o par mais correlacionado.")
    return pairs[:1]


def _scatter(df, a, b, config, r) -> dict:
    sub = df[[a, b]].dropna()
    sampled = len(sub) > config.scatter_max_points
    if sampled:
        sub = sub.sample(config.scatter_max_points, random_state=42)
    chart = {"id": f"R4-{_slug(a)}-{_slug(b)}", "chart_type": "scatter", "alternatives": [],
             "title": f"{b} versus {a}", "x": {"column": a, "kind": "numeric"}, "y": [{"column": b, "kind": "numeric"}],
             "agg": "none", "data": {"points": [{"x": _num(x), "y": _num(y)} for x, y in zip(sub[a], sub[b])],
                                       "correlation": round(r, 3)},
             "warnings": ([f"Amostra de {config.scatter_max_points} pontos para manter a legibilidade."] if sampled else [])}
    chart.update(_explain("R4", f"'{a}' e '{b}'", f"Correlação de Pearson: {r:.2f}."))
    return chart
