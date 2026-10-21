"""Gera os conjuntos sinteticos de casos-limite da etapa de demonstracao (secao 4.2.4).
Uso:  python scripts/make_synthetic.py [pasta_de_saida]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import synthetic  # noqa: E402


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data" / "synthetic")
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "01_vendas_completo.xlsx": synthetic.to_xlsx_bytes(synthetic.sales()),
        "02_csv_brasileiro_latin1.csv": synthetic.brazilian_csv(),
        "03_planilha_suja.csv": synthetic.to_csv_bytes(synthetic.messy()),
        "04_uma_coluna.csv": synthetic.to_csv_bytes(synthetic.one_column()),
        "05_coluna_constante.csv": synthetic.to_csv_bytes(synthetic.constant_column()),
        "06_alta_cardinalidade.csv": synthetic.to_csv_bytes(synthetic.high_cardinality()),
        "07_identificadores_e_texto.csv": synthetic.to_csv_bytes(synthetic.identifiers()),
    }
    for name, content in files.items():
        (out / name).write_bytes(content)
        print(f"gerado: {out / name}")


if __name__ == "__main__":
    main()
