"""Assistente de analise em linguagem natural (recurso complementar, fora do Quadro 5).

O modelo de linguagem NAO recebe a planilha e NAO executa codigo. O fluxo tem duas etapas:

1. O modelo recebe o esquema das colunas (nomes, tipos e estatisticas resumidas) e a pergunta,
   e devolve um JSON: ou uma resposta direta, ou uma especificacao de consulta (agrupar,
   agregar, filtrar, ordenar).
2. A consulta e validada e executada aqui, em Pandas, e o resultado agregado volta ao modelo,
   que redige a resposta. A tabela usada acompanha a resposta, para o usuario conferir.

Assim os numeros exibidos saem sempre do Pandas, nunca da "memoria" do modelo. Os provedores
usam a API de chat compativel com a da OpenAI (Groq e xAI/Grok).
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

from .heuristics import apply_filters, cat_labels
from .inference import ColumnInfo

PROVIDERS = {
    "groq": {"label": "Groq (plano gratuito)", "base_url": "https://api.groq.com/openai/v1",
             "default_model": "openai/gpt-oss-120b", "key_url": "https://console.groq.com/keys"},
    "xai": {"label": "xAI Grok (pago)", "base_url": "https://api.x.ai/v1",
            "default_model": "grok-4.3", "key_url": "https://console.x.ai"},
}
OPS = {"sum": "sum", "mean": "mean", "median": "median", "min": "min", "max": "max",
       "count": "count", "nunique": "nunique"}
OP_LABEL = {"sum": "Soma", "mean": "Média", "median": "Mediana", "min": "Mínimo", "max": "Máximo",
            "count": "Contagem", "nunique": "Valores distintos"}
PERIODS = {"year": "Y", "month": "M", "day": "D"}
MAX_QUESTION = 1000
MAX_HISTORY = 6
MAX_ROWS = 50
MAX_SCHEMA_COLUMNS = 40
TIMEOUT = 40


class AssistantError(Exception):
    """Erro com mensagem pronta para o usuario; `status` e o codigo HTTP devolvido pela API."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------- configuracao
def server_settings() -> dict:
    """Configuracao do servidor por variaveis de ambiente (a chave nunca e devolvida ao cliente)."""
    provider = (os.environ.get("LLM_PROVIDER") or "groq").lower()
    if provider not in PROVIDERS:
        provider = "groq"
    key = os.environ.get("LLM_API_KEY") or os.environ.get(
        "XAI_API_KEY" if provider == "xai" else "GROQ_API_KEY") or ""
    return {"provider": provider, "api_key": key.strip(),
            "model": os.environ.get("LLM_MODEL") or PROVIDERS[provider]["default_model"]}


def public_status() -> dict:
    s = server_settings()
    return {"server_key": bool(s["api_key"]), "provider": s["provider"], "model": s["model"],
            "providers": {k: {"label": v["label"], "default_model": v["default_model"], "key_url": v["key_url"]}
                          for k, v in PROVIDERS.items()}}


# ------------------------------------------------------------------ chamada ao modelo
def call_llm(messages: list[dict], *, provider: str, api_key: str, model: str, json_mode: bool = False) -> str:
    """Chama /chat/completions do provedor. Levanta AssistantError com mensagem legivel."""
    if provider not in PROVIDERS:
        raise AssistantError(f"Provedor desconhecido: {provider!r}. Use um de {list(PROVIDERS)}.", 400)
    if not api_key:
        raise AssistantError("Nenhuma chave de API configurada. Informe a sua chave nas configurações do assistente.", 400)
    url = PROVIDERS[provider]["base_url"] + "/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0.1}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        return _post(url, api_key, payload)
    except AssistantError as exc:
        if json_mode and exc.status == 400:        # modelo sem suporte ao modo JSON: tenta sem
            payload.pop("response_format")
            return _post(url, api_key, payload)
        raise


def _post(url: str, api_key: str, payload: dict) -> str:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf8"), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "DashGen/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            body = json.loads(res.read().decode("utf8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            err = json.loads(exc.read().decode("utf8")).get("error")
            detail = (err.get("message") if isinstance(err, dict) else str(err or ""))[:300]
        except Exception:
            pass
        friendly = {401: "Chave de API inválida ou sem permissão.", 403: "Chave de API sem permissão para este modelo.",
                    404: "Modelo não encontrado neste provedor. Confira o nome do modelo.",
                    429: "Limite de uso do provedor atingido. Aguarde um pouco e tente de novo."}.get(
                        exc.code, f"O provedor de IA respondeu com erro {exc.code}.")
        status = 400 if exc.code in (400, 401, 403, 404) else (429 if exc.code == 429 else 502)
        raise AssistantError(f"{friendly}{' Detalhe: ' + detail if detail else ''}", status) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AssistantError("Não foi possível falar com o provedor de IA (rede ou tempo esgotado).", 502) from exc
    try:
        return body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AssistantError("Resposta inesperada do provedor de IA.", 502) from exc


# ------------------------------------------------------------- contexto (esquema)
def _n(x) -> float | int | None:
    if x is None or pd.isna(x):
        return None
    x = float(x)
    return int(x) if x.is_integer() else round(x, 4)


def build_schema(df: pd.DataFrame, infos: list[ColumnInfo]) -> list[dict]:
    """Resumo de cada coluna utilizavel: e tudo o que o modelo conhece da planilha antes de consultar."""
    out = []
    for info in infos:
        if info.kind == "ignored" or info.name not in df.columns:
            continue
        s = df[info.name].dropna()
        col = {"name": info.name, "kind": info.kind, "non_null": int(len(s))}
        if s.empty:
            pass
        elif info.kind == "numeric":
            col.update(min=_n(s.min()), max=_n(s.max()), mean=_n(s.mean()), sum=_n(s.sum()))
        elif info.kind == "categorical":
            counts = cat_labels(s).value_counts()
            col.update(distinct=int(len(counts)), top_values=[str(v) for v in counts.index[:8]])
        else:
            col.update(min=s.min().date().isoformat(), max=s.max().date().isoformat())
        out.append(col)
        if len(out) >= MAX_SCHEMA_COLUMNS:
            break
    return out


# --------------------------------------------------------- consulta estruturada
def run_query(df: pd.DataFrame, infos: list[ColumnInfo], spec: dict) -> dict:
    """Valida e executa uma consulta de agregacao. Levanta ValueError com mensagem explicativa."""
    if not isinstance(spec, dict):
        raise ValueError("A consulta deve ser um objeto JSON.")
    kinds = {i.name: i.kind for i in infos if i.kind != "ignored"}

    def col(name):
        if name not in kinds or name not in df.columns:
            raise ValueError(f"Coluna inexistente ou ignorada: {name!r}. Colunas disponíveis: {list(kinds)}.")
        return name

    op = str(spec.get("op") or "count").lower()
    if op not in OPS:
        raise ValueError(f"Operação inválida: {op!r}. Use uma de {list(OPS)}.")
    metric = spec.get("metric") or None
    if op != "count":
        if not metric:
            raise ValueError(f"A operação {op!r} exige uma coluna em 'metric'.")
        col(metric)
        if op != "nunique" and kinds[metric] != "numeric":
            raise ValueError(f"A operação {op!r} exige coluna numérica; '{metric}' é {kinds[metric]}.")
    elif metric:
        col(metric)

    group_by = spec.get("group_by") or []
    if isinstance(group_by, str):
        group_by = [group_by]
    if not isinstance(group_by, list) or len(group_by) > 2:
        raise ValueError("'group_by' aceita no máximo 2 colunas.")
    period = str(spec.get("period") or "month").lower()
    if period not in PERIODS:
        raise ValueError(f"Período inválido: {period!r}. Use um de {list(PERIODS)}.")

    filters = spec.get("filters") or []
    if not isinstance(filters, list):
        raise ValueError("'filters' deve ser uma lista.")
    data = apply_filters(df, filters, kinds)

    keys, names = [], []
    for g in group_by:
        col(g)
        if kinds[g] == "temporal":
            keys.append(data[g].dt.to_period(PERIODS[period]).astype(str).where(data[g].notna()))
            names.append(f"{g} ({ {'year': 'ano', 'month': 'mês', 'day': 'dia'}[period] })")
        elif kinds[g] == "numeric":
            keys.append(data[g])
            names.append(g)
        else:
            keys.append(cat_labels(data[g]))
            names.append(g)

    value_name = "Registros" if op == "count" and not metric else f"{OP_LABEL[op]} de {metric}"
    target = data[metric] if metric else pd.Series(1, index=data.index)
    if not keys:
        value = int(len(data)) if op == "count" and not metric else getattr(target, OPS[op])()
        return {"columns": [value_name], "rows": [[_n(value)]], "rows_considered": int(len(data)), "truncated": False}

    grouped = target.groupby([k.rename(f"k{i}") for i, k in enumerate(keys)], dropna=True).agg(OPS[op]).dropna()
    sort = str(spec.get("sort") or ("label" if any(kinds[g] == "temporal" for g in group_by) else "desc")).lower()
    if sort == "label":
        grouped = grouped.sort_index()
    else:
        grouped = grouped.sort_values(ascending=(sort == "asc"))
    try:
        limit = max(1, min(int(spec.get("limit") or 20), MAX_ROWS))
    except (TypeError, ValueError):
        limit = 20
    total = int(len(grouped))
    grouped = grouped.head(limit)
    rows = []
    for idx, v in grouped.items():
        idx = idx if isinstance(idx, tuple) else (idx,)
        rows.append([_cell(x) for x in idx] + [_n(v)])
    return {"columns": names + [value_name], "rows": rows, "rows_considered": int(len(data)),
            "truncated": total > limit, "groups_total": total}


def _cell(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return _n(x)
    return str(x)


def _table_text(table: dict) -> str:
    lines = [" | ".join(table["columns"])]
    lines += [" | ".join("" if v is None else str(v) for v in r) for r in table["rows"]]
    if table.get("truncated"):
        lines.append(f"(mostrando {len(table['rows'])} de {table['groups_total']} grupos)")
    return "\n".join(lines)


# ------------------------------------------------------------------- orquestracao
SYSTEM = """Você é o assistente de análise do DashGen. O usuário enviou uma planilha e faz perguntas sobre ela em português.
Você NÃO vê as linhas da planilha: conhece apenas o esquema abaixo. Para obter números, peça uma consulta; o sistema executa e devolve o resultado.

Responda SEMPRE com um único objeto JSON, sem texto fora dele, em um destes formatos:
1) {"action": "query", "query": {"group_by": [até 2 colunas], "period": "year|month|day", "metric": "coluna ou null", "op": "sum|mean|median|min|max|count|nunique", "filters": [...], "sort": "desc|asc|label", "limit": 1 a 50}}
2) {"action": "answer", "answer": "texto em português"}

Regras:
- Use exatamente os nomes de coluna do esquema. "period" só vale para colunas temporais em group_by.
- "op": "count" sem "metric" conta registros. Para total geral, deixe group_by vazio.
- Filtros: categórica {"column": c, "values": [..]}; numérica {"column": c, "min": n, "max": n}; temporal {"column": c, "start": "AAAA-MM-DD", "end": "AAAA-MM-DD"}.
- Use "answer" direto só quando o esquema já responde (ex.: quais colunas existem) ou quando a pergunta não puder ser respondida com esses dados; nesse caso, explique o motivo e sugira uma pergunta possível.
- Nunca invente números.

Esquema da planilha "{filename}" ({rows} registros considerados{filter_note}):
{schema}"""

FINAL = """Resultado da consulta (calculado pelo sistema sobre {n} registros):
{table}

Agora responda à pergunta do usuário em português, em até 5 frases, citando os números do resultado. Não invente valores que não estejam no resultado. Se houver uma limitação relevante (dados truncados, poucos registros), diga. Responda em texto simples, sem JSON e sem tabelas."""


def _extract_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1] if "{" in text else ""):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except (ValueError, TypeError):
            continue
    return None


def ask(df: pd.DataFrame, infos: list[ColumnInfo], filename: str, question: str, *, llm, history: list | None = None,
        filters: list | None = None) -> dict:
    """Responde a uma pergunta. `llm(messages, json_mode=bool) -> str` e injetavel (testes)."""
    question = (question or "").strip()
    if not question:
        raise AssistantError("Escreva uma pergunta.", 400)
    if len(question) > MAX_QUESTION:
        raise AssistantError(f"Pergunta muito longa (máximo de {MAX_QUESTION} caracteres).", 400)
    kinds = {i.name: i.kind for i in infos}
    try:
        data = apply_filters(df, filters or [], kinds)
    except (ValueError, TypeError) as exc:
        raise AssistantError(str(exc), 400) from exc

    schema = build_schema(data, infos)
    if not schema:
        raise AssistantError("Não há colunas utilizáveis para analisar. Revise os tipos das colunas.", 400)
    note = f", após {len(filters)} filtro(s) do dashboard; total sem filtros: {len(df)}" if filters else ""
    system = (SYSTEM.replace("{filename}", filename).replace("{rows}", str(len(data)))
              .replace("{filter_note}", note).replace("{schema}", json.dumps(schema, ensure_ascii=False)))
    messages = [{"role": "system", "content": system}]
    for h in (history or [])[-MAX_HISTORY:]:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str):
            messages.append({"role": h["role"], "content": h["content"][:2000]})
    messages.append({"role": "user", "content": question})

    base = {"rows_considered": int(len(data)), "rows_total": int(len(df)), "query": None, "table": None}
    first = llm(messages, json_mode=True)
    plan = _extract_json(first)
    if plan is None:                                   # modelo ignorou o protocolo: devolve o texto como resposta
        return {**base, "answer": first.strip() or "O modelo não devolveu uma resposta."}
    if plan.get("action") != "query":
        return {**base, "answer": str(plan.get("answer") or "").strip() or "O modelo não devolveu uma resposta."}

    query = plan.get("query") or {}
    try:
        table = run_query(data, infos, query)
    except (ValueError, TypeError, KeyError) as exc:
        return {**base, "query": query,
                "answer": f"Não consegui executar a consulta sugerida pelo modelo ({exc}) Tente reformular a pergunta, "
                          "citando os nomes das colunas."}
    messages.append({"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)})
    messages.append({"role": "user", "content": FINAL.replace("{n}", str(table["rows_considered"]))
                     .replace("{table}", _table_text(table))})
    answer = llm(messages, json_mode=False).strip()
    return {**base, "query": query, "table": table, "answer": answer or "Consulta executada; veja a tabela abaixo."}
