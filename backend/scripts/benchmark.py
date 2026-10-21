"""Analise de desempenho (secao 4.2.5 da monografia).

Mede o tempo de cada etapa do pipeline (ingestao, inferencia de tipos e geracao do
dashboard) para bases de mil, dez mil e cem mil linhas, em CSV e Excel, e imprime
uma tabela em Markdown. Uso:  python scripts/benchmark.py [--runs 5] [--out resultado.json]
"""
import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import synthetic  # noqa: E402
from app.heuristics import build_dashboard  # noqa: E402
from app.inference import infer_types  # noqa: E402
from app.ingestion import read_table  # noqa: E402

SIZES = (1_000, 10_000, 100_000)


def timed(fn, runs):
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        out = fn()
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--out")
    ap.add_argument("--excel", action="store_true", help="inclui medicoes com arquivos .xlsx (mais lento)")
    args = ap.parse_args()

    results = []
    for n in SIZES:
        df = synthetic.sales(n)
        formats = [("csv", synthetic.to_csv_bytes(df), "v.csv")]
        if args.excel:
            formats.append(("xlsx", synthetic.to_xlsx_bytes(df), "v.xlsx"))
        for fmt, content, name in formats:
            runs = args.runs if n < 100_000 else max(3, args.runs // 2)
            t_ing, res = timed(lambda: read_table(content, name), runs)
            t_inf, infos = timed(lambda: infer_types(res.df), runs)
            t_dash, dash = timed(lambda: build_dashboard(res.df, infos), runs)
            t_filt, _ = timed(lambda: build_dashboard(res.df, infos, filters=[
                {"column": "Região", "values": ["Norte", "Sul"]}]), runs)
            results.append({"linhas": n, "formato": fmt, "tamanho_kb": round(len(content) / 1024),
                            "ingestao_s": round(t_ing, 4), "inferencia_s": round(t_inf, 4),
                            "dashboard_s": round(t_dash, 4), "dashboard_filtrado_s": round(t_filt, 4),
                            "total_s": round(t_ing + t_inf + t_dash, 4), "graficos": len(dash["charts"])})

    env = {"python": platform.python_version(), "plataforma": platform.platform(), "processador": platform.processor()}
    print(f"Ambiente: Python {env['python']} em {env['plataforma']}\n")
    print("| Linhas | Formato | Tamanho (KB) | Ingestão (s) | Inferência (s) | Dashboard (s) | Com filtro (s) | Total (s) |")
    print("|---:|:---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        print(f"| {r['linhas']:,} | {r['formato']} | {r['tamanho_kb']:,} | {r['ingestao_s']} | {r['inferencia_s']} | "
              f"{r['dashboard_s']} | {r['dashboard_filtrado_s']} | {r['total_s']} |".replace(",", "."))
    if args.out:
        Path(args.out).write_text(json.dumps({"ambiente": env, "resultados": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
