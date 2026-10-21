"""Armazenamento de sessoes (dados em memoria) e de configuracoes (persistencia opcional).

Decisao de projeto registrada na monografia (secao 4.2.2): o conteudo das planilhas
nunca e persistido. As sessoes vivem apenas em memoria, com tempo de expiracao, e o
banco guarda somente configuracoes de dashboards e metadados.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .inference import ColumnInfo, apply_overrides, infer_types


# ------------------------------------------------------------------------- sessoes
@dataclass
class Session:
    id: str
    filename: str
    raw_df: pd.DataFrame
    notes: list[str]
    sheets: list[str] = field(default_factory=list)
    sheet_used: str | None = None
    overrides: dict[str, str] = field(default_factory=dict)
    df: pd.DataFrame | None = None
    infos: list[ColumnInfo] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    touched: float = field(default_factory=time.time)

    def refresh(self) -> list[str]:
        """Reaplica os ajustes de tipo sobre os dados originais e reinfere as colunas."""
        self.df, warnings = apply_overrides(self.raw_df, self.overrides)
        auto = {i.name: i.kind for i in infer_types(self.raw_df)}
        infos = infer_types(self.df, self.overrides)
        for info in infos:
            info.inferred_kind = auto.get(info.name, info.kind)
            info.overridden = info.name in self.overrides and self.overrides[info.name] != info.inferred_kind
        self.infos = infos
        return warnings


class SessionStore:
    def __init__(self, ttl_seconds: int = 7200, max_sessions: int = 50):
        self._items: dict[str, Session] = {}
        self._lock = threading.Lock()
        self.ttl = ttl_seconds
        self.max_sessions = max_sessions

    def create(self, filename: str, df: pd.DataFrame, notes: list[str], sheets=None, sheet_used=None) -> Session:
        sess = Session(id=uuid.uuid4().hex, filename=filename, raw_df=df, notes=notes,
                       sheets=sheets or [], sheet_used=sheet_used)
        sess.refresh()
        with self._lock:
            self._evict()
            self._items[sess.id] = sess
        return sess

    def get(self, session_id: str) -> Session:
        with self._lock:
            self._evict()
            sess = self._items.get(session_id)
            if sess is None:
                raise KeyError(session_id)
            sess.touched = time.time()
            return sess

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._items.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._items)

    def _evict(self) -> None:
        now = time.time()
        for sid in [k for k, v in self._items.items() if now - v.touched > self.ttl]:
            del self._items[sid]
        while len(self._items) >= self.max_sessions:
            oldest = min(self._items.values(), key=lambda s: s.touched)
            del self._items[oldest.id]


# ----------------------------------------------------------------- configuracoes
def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class FileConfigStore:
    """Persistencia de configuracoes em arquivos JSON (alternativa quando nao ha MongoDB)."""
    backend = "arquivo JSON"

    def __init__(self, directory: str):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, config: dict) -> str:
        cid = uuid.uuid4().hex[:12]
        doc = {**config, "id": cid, "created_at": _now()}
        (self.dir / f"{cid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf8")
        return cid

    def get(self, cid: str) -> dict:
        path = self.dir / f"{cid}.json"
        if not path.exists() or not cid.isalnum():
            raise KeyError(cid)
        return json.loads(path.read_text(encoding="utf8"))

    def list(self) -> list[dict]:
        docs = [json.loads(p.read_text(encoding="utf8")) for p in self.dir.glob("*.json")]
        return sorted(docs, key=lambda d: d["created_at"], reverse=True)


class MongoConfigStore:
    """Persistencia de configuracoes no MongoDB (documentos JSON de estrutura variavel)."""
    backend = "MongoDB"

    def __init__(self, uri: str, db_name: str = "dashgen", client=None):
        if client is None:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
        self.col = client[db_name]["configs"]

    def save(self, config: dict) -> str:
        cid = uuid.uuid4().hex[:12]
        self.col.insert_one({**config, "_id": cid, "id": cid, "created_at": _now()})
        return cid

    def get(self, cid: str) -> dict:
        doc = self.col.find_one({"_id": cid}, {"_id": 0})
        if doc is None:
            raise KeyError(cid)
        return doc

    def list(self) -> list[dict]:
        return list(self.col.find({}, {"_id": 0}).sort("created_at", -1))


def create_config_store(mongo_uri: str | None, data_dir: str):
    """Usa MongoDB quando MONGO_URI esta definido e acessivel; caso contrario, arquivos JSON."""
    if mongo_uri:
        try:
            return MongoConfigStore(mongo_uri)
        except Exception:
            pass
    return FileConfigStore(os.path.join(data_dir, "configs"))
