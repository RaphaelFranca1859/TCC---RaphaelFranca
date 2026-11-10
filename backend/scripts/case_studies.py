"""Estudos de caso (secao 4.2.4): roda o pipeline completo em cada arquivo de uma pasta e registra
entrada, tipos inferidos, graficos escolhidos, regra aplicada e registro de decisoes.
Uso:  python scripts/case_studies.py data/real data/synthetic --out ../docs/estudos_de_caso"""
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.heuristics import build_dashboard  # noqa: E402
from app.inference import apply_overrides, infer_types  # noqa: E402
from app.ingestion import IngestionError, read_table  # noqa: E402


def run(path: Path) -> dict:
    t0 = time.perf_counter()
    try:
        res = read_table(path.read_bytes(), path.name)
    except IngestionError as exc:
        return {"arquivo": path.name, "erro": str(exc)}
    df, _ = apply_overrides(res.df, {})          # mesmo caminho da sessao: converte as colunas aos tipos inferidos
    infos = infer_types(df)
    dash = build_dashboard(df, infos)
    return {
        "arquivo": path.name, "linhas": int(len(df)), "abas": res.sheets, "notas": res.notes,
        "colunas": [{"nome": i.name, "tipo": i.kind, "distintos": i.n_unique, "ausentes_pct": round(i.missing_ratio * 100, 1),
                     "motivo_ignorada": i.ignored_reason} for i in infos],
        "graficos": [{"regra": c["rule_id"], "tipo": c["chart_type"], "titulo": c["title"], "avisos": c["warnings"]}
                     for c in dash["charts"]],
        "registro": dash["decision_log"], "tempo_s": round(time.perf_counter() - t0, 2)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pastas", nargs="+"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    files = sorted(f for d in a.pastas for f in Path(d).iterdir() if f.suffix.lower() in (".csv", ".xlsx"))
    results = [run(f) for f in files]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf8")
    md = ["# Estudos de caso (saída automática do sistema)\n"]
    for r in results:
        md.append(f"\n## {r['arquivo']}\n")
        if "erro" in r:
            md.append(f"Erro de leitura: {r['erro']}\n"); continue
        md.append(f"- Linhas: {r['linhas']:,}".replace(",", ".") + f" | tempo total: {r['tempo_s']} s")
        if r["abas"]: md.append(f"- Abas: {', '.join(r['abas'])}")
        for n in r["notas"]: md.append(f"- Nota de leitura: {n}")
        md.append("\n| Coluna | Tipo inferido | Distintos | Ausentes (%) |\n|---|---|---:|---:|")
        for c in r["colunas"]:
            extra = f" ({c['motivo_ignorada']})" if c["motivo_ignorada"] else ""
            md.append(f"| {c['nome']} | {c['tipo']}{extra} | {c['distintos']} | {c['ausentes_pct']} |")
        md.append("\n| Regra | Gráfico | Título | Avisos |\n|---|---|---|---|")
        for g in r["graficos"]:
            md.append(f"| {g['regra']} | {g['tipo']} | {g['titulo']} | {' '.join(g['avisos'])} |")
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf8")
    print(f"{len(results)} arquivos -> {out.with_suffix('.md')}")


main()
