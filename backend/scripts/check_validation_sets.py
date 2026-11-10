"""Roda cada base de uma pasta de data/ pelo sistema (leitura, inferencia de tipos e motor de graficos)
e grava em docs/ uma tabela com o que aconteceu. Apenas registra fatos; a analise e do autor.
Uso, a partir de backend/:
    python scripts/check_validation_sets.py                     # data/validacao -> docs/validacao_novas_bases.md
    python scripts/check_validation_sets.py brasil              # data/brasil    -> docs/validacao_bases_brasileiras.md"""
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.heuristics import build_dashboard      # noqa: E402
from app.inference import apply_overrides, infer_types  # noqa: E402
from app.ingestion import read_table            # noqa: E402

folder = sys.argv[1] if len(sys.argv) > 1 else "validacao"
base = Path(__file__).resolve().parents[1] / "data" / folder
out_name = {"validacao": "validacao_novas_bases.md", "brasil": "validacao_bases_brasileiras.md"}.get(folder, f"validacao_{folder}.md")
rows, fails = [], 0
for f in sorted(base.glob("*.xlsx")):
    t0 = time.perf_counter()
    try:
        res = read_table(f.read_bytes(), f.name)
        df, _ = apply_overrides(res.df, {})
        infos = infer_types(df)
        dash = build_dashboard(df, infos)
        secs = time.perf_counter() - t0
        kinds = Counter(i.kind for i in infos)
        rules = Counter(c["rule_id"] for c in dash["charts"])
        rows.append(f"| `{f.name}` | {len(df)} | {len(infos)} | {kinds['numeric']} | {kinds['categorical']} | {kinds['temporal']} | "
                    f"{kinds['ignored']} | {len(dash['charts'])} | {', '.join(f'{k}×{v}' for k, v in sorted(rules.items())) or '-'} | {secs:.2f} | ok |")
    except Exception as exc:  # registra a falha em vez de interromper
        fails += 1
        rows.append(f"| `{f.name}` | - | - | - | - | - | - | - | - | - | ERRO: {type(exc).__name__}: {str(exc)[:120]} |")
    print(rows[-1])
out = Path(__file__).resolve().parents[2] / "docs" / out_name
out.write_text("\n".join([
    f"# Execução do sistema nas bases de data/{folder}", "",
    "Gerado por `backend/scripts/check_validation_sets.py`. Cada base passou por leitura, inferência de tipos e motor de gráficos, "
    "com as opções padrão e sem ajuste manual de tipos. A tabela registra apenas o que o sistema fez; "
    "se os tipos e os gráficos escolhidos são adequados a cada base é uma avaliação que ainda precisa ser feita, base a base. "
    "Os tempos são de uma única execução no ambiente de desenvolvimento e não substituem o benchmark da seção 4.2.5.", "",
    f"Bases executadas: {len(rows)}. Falhas: {fails}.", "",
    "| Arquivo | Linhas | Colunas | Numéricas | Categóricas | Temporais | Ignoradas | Gráficos | Regras disparadas | Tempo (s) | Situação |",
    "|---|---|---|---|---|---|---|---|---|---|---|", *rows]) + "\n", encoding="utf8")
print("falhas:", fails)
