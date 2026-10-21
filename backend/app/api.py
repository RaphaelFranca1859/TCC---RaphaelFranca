"""Rotas REST (JSON). Casos de uso da Figura 2: enviar planilha, visualizar inferencia,
ajustar tipos, gerar dashboard, aplicar filtros, salvar configuracao e exportar."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
from flask import Blueprint, current_app, jsonify, request, send_file

from .heuristics import AGGREGATIONS, DEFAULT_CONFIG, RULES, SORTS, build_dashboard, filter_options
from .ingestion import IngestionError, read_table
from .inference import ALL_KINDS, DEFAULT_CONFIG as INFERENCE_DEFAULTS

bp = Blueprint("api", __name__)


def _sessions():
    return current_app.extensions["sessions"]


def _configs():
    return current_app.extensions["configs"]


def _session_or_404(session_id: str):
    try:
        return _sessions().get(session_id)
    except KeyError:
        return None


def _not_found():
    return jsonify(error="Sessão não encontrada ou expirada. Envie a planilha novamente."), 404


def _json_value(v):
    if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NaT:
        return None
    if isinstance(v, (pd.Timestamp,)):
        return v.strftime("%Y-%m-%d") if v == v.normalize() else v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _preview(df: pd.DataFrame, n: int = 10) -> dict:
    head = df.head(n)
    rows = [[_json_value(v) for v in row] for row in head.itertuples(index=False, name=None)]
    return {"columns": [str(c) for c in head.columns], "rows": rows}


def _session_payload(sess, warnings=None) -> dict:
    return {
        "session_id": sess.id, "filename": sess.filename, "rows": int(len(sess.df)),
        "columns": [i.to_dict() for i in sess.infos], "preview": _preview(sess.df),
        "sheets": sess.sheets, "sheet_used": sess.sheet_used, "notes": sess.notes,
        "warnings": warnings or [], "filter_options": filter_options(sess.df, sess.infos),
    }


# ------------------------------------------------------------------------ geral
@bp.get("/health")
def health():
    return jsonify(status="ok", sessions=len(_sessions()), config_backend=_configs().backend)


@bp.get("/rules")
def rules():
    """Regras heuristicas e limiares vigentes (transparencia e auditabilidade)."""
    return jsonify(
        rules=[r.to_dict() for r in RULES.values()],
        heuristic_thresholds={k: getattr(DEFAULT_CONFIG, k) for k in DEFAULT_CONFIG.__dataclass_fields__},
        inference_thresholds={k: getattr(INFERENCE_DEFAULTS, k) for k in INFERENCE_DEFAULTS.__dataclass_fields__},
        aggregations=AGGREGATIONS, sorts=list(SORTS), kinds=list(ALL_KINDS))


# ---------------------------------------------------------------------- sessoes
@bp.post("/upload")
def upload():
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify(error="Nenhum arquivo enviado. Selecione uma planilha .xlsx ou .csv."), 400
    try:
        result = read_table(file.read(), file.filename, sheet=request.form.get("sheet") or None)
    except IngestionError as exc:
        return jsonify(error=str(exc)), 422
    sess = _sessions().create(file.filename, result.df, result.notes, result.sheets, result.sheet_used)
    return jsonify(_session_payload(sess)), 201


@bp.get("/sessions/<session_id>")
def get_session(session_id):
    sess = _session_or_404(session_id)
    return jsonify(_session_payload(sess)) if sess else _not_found()


@bp.delete("/sessions/<session_id>")
def delete_session(session_id):
    _sessions().delete(session_id)
    return "", 204


@bp.put("/sessions/<session_id>/types")
def set_types(session_id):
    sess = _session_or_404(session_id)
    if not sess:
        return _not_found()
    types = (request.get_json(silent=True) or {}).get("types")
    if not isinstance(types, dict):
        return jsonify(error="Envie um objeto 'types' no formato {coluna: tipo}."), 400
    invalid = {c: k for c, k in types.items() if k not in ALL_KINDS}
    if invalid:
        return jsonify(error=f"Tipos inválidos: {invalid}. Use um de {list(ALL_KINDS)}."), 400
    unknown = [c for c in types if c not in sess.raw_df.columns]
    if unknown:
        return jsonify(error=f"Colunas inexistentes: {unknown}."), 400
    sess.overrides.update(types)
    return jsonify(_session_payload(sess, sess.refresh()))


@bp.post("/sessions/<session_id>/dashboard")
def dashboard(session_id):
    sess = _session_or_404(session_id)
    if not sess:
        return _not_found()
    body = request.get_json(silent=True) or {}
    try:
        result = build_dashboard(sess.df, sess.infos, filters=body.get("filters") or [],
                                 agg=body.get("agg", "auto"), sort=body.get("sort", "value_desc"))
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result)


@bp.post("/sessions/<session_id>/export")
def export_csv(session_id):
    sess = _session_or_404(session_id)
    if not sess:
        return _not_found()
    from .heuristics import apply_filters
    body = request.get_json(silent=True) or {}
    try:
        kinds = {i.name: i.kind for i in sess.infos}
        out = apply_filters(sess.df, body.get("filters") or [], kinds)
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400
    buf = io.BytesIO(out.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"))
    name = sess.filename.rsplit(".", 1)[0] + "_filtrado.csv"
    return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=name)


# ------------------------------------------------------------------ configuracoes
@bp.post("/sessions/<session_id>/config")
def save_config(session_id):
    sess = _session_or_404(session_id)
    if not sess:
        return _not_found()
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip() or f"Configuração de {sess.filename}"
    config = {  # somente configuracao e metadados; nunca o conteudo da planilha
        "name": name, "filename": sess.filename,
        "columns": {i.name: i.kind for i in sess.infos},
        "filters": body.get("filters") or [], "agg": body.get("agg", "auto"), "sort": body.get("sort", "value_desc"),
    }
    return jsonify(id=_configs().save(config), name=name), 201


@bp.get("/configs")
def list_configs():
    return jsonify(configs=_configs().list())


@bp.get("/configs/<config_id>")
def get_config(config_id):
    try:
        return jsonify(_configs().get(config_id))
    except KeyError:
        return jsonify(error="Configuração não encontrada."), 404


@bp.post("/sessions/<session_id>/apply-config")
def apply_config(session_id):
    sess = _session_or_404(session_id)
    if not sess:
        return _not_found()
    cid = (request.get_json(silent=True) or {}).get("config_id")
    try:
        cfg = _configs().get(cid)
    except KeyError:
        return jsonify(error="Configuração não encontrada."), 404
    present = {c: k for c, k in cfg["columns"].items() if c in sess.raw_df.columns}
    missing = [c for c in cfg["columns"] if c not in sess.raw_df.columns]
    extra = [c for c in sess.raw_df.columns if c not in cfg["columns"]]
    sess.overrides.update(present)
    warnings = sess.refresh()
    if missing:
        warnings.append(f"Colunas da configuração ausentes na planilha atual: {missing}.")
    payload = _session_payload(sess, warnings)
    payload["applied"] = {"filters": [f for f in cfg.get("filters", []) if f.get("column") in present],
                          "agg": cfg.get("agg", "auto"), "sort": cfg.get("sort", "value_desc"),
                          "missing_columns": missing, "new_columns": extra}
    return jsonify(payload)
