"""Gera as bases publicas de validacao (pasta data/validacao) e o arquivo FONTES.md.

Estas bases NAO participaram da calibracao dos limiares (docs/calibracao.md): servem para
verificar o sistema em dados novos. Todas sao conjuntos classicos, publicados e distribuidos
com pacotes Python de codigo aberto; nada e baixado de sites avulsos. As descricoes de fonte
do FONTES.md sao copiadas da documentacao que acompanha cada pacote.

Dependencias so deste script (nao entram no requirements.txt do sistema):
    pip install pydataset vega_datasets statsmodels scikit-learn openpyxl

Uso, a partir de backend/:  python scripts/make_validation_sets.py
"""
from __future__ import annotations

import contextlib
import io
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parents[1] / "data" / "validacao"

# (id no pacote, nome do arquivo, area, descricao curta em portugues)
PYDATASET = [
    ("birthwt", "Saude_baixo_peso_ao_nascer", "saúde", "Fatores de risco para baixo peso ao nascer"),
    ("Pima.te", "Saude_diabetes_mulheres_Pima", "saúde", "Diabetes em mulheres Pima"),
    ("Melanoma", "Saude_sobrevida_melanoma", "saúde", "Sobrevida de pacientes com melanoma maligno"),
    ("esoph", "Saude_cancer_esofago_fumo_alcool", "saúde", "Fumo, álcool e câncer de esôfago (caso-controle)"),
    ("infert", "Saude_infertilidade_pos_aborto", "saúde", "Infertilidade após aborto espontâneo e induzido"),
    ("biopsy", "Saude_biopsias_cancer_mama", "saúde", "Biópsias de pacientes com câncer de mama"),
    ("Aids2", "Saude_sobrevida_AIDS_Australia", "saúde", "Sobrevida de pacientes com AIDS na Austrália"),
    ("colon", "Saude_quimioterapia_cancer_colon", "saúde", "Quimioterapia para câncer de cólon estágios B/C"),
    ("pbc", "Saude_cirrose_biliar_Mayo", "saúde", "Cirrose biliar primária (Clínica Mayo)"),
    ("cancer", "Saude_cancer_pulmao_NCCTG", "saúde", "Câncer de pulmão avançado (NCCTG)"),
    ("epil", "Saude_crises_epilepsia", "saúde", "Contagem de crises em pacientes com epilepsia"),
    ("deaths", "Saude_mortes_doencas_pulmonares_UK", "saúde", "Mortes mensais por doenças pulmonares no Reino Unido"),
    ("diamonds", "Precos_diamantes", "varejo", "Preços de cerca de 54 mil diamantes"),
    ("mpg", "Consumo_combustivel_carros", "transporte", "Consumo de combustível de carros (1999 e 2008)"),
    ("economics", "Economia_series_EUA", "economia", "Séries econômicas mensais dos EUA"),
    ("Salaries", "Salarios_professores", "educação", "Salários de professores universitários"),
    ("Housing", "Precos_casas_Windsor", "imóveis", "Preços de venda de casas em Windsor"),
    ("Cars93", "Carros_a_venda_1993", "transporte", "93 carros à venda nos EUA em 1993"),
    ("msleep", "Sono_mamiferos", "biologia", "Sono de mamíferos"),
    ("midwest", "Demografia_meio_oeste_EUA", "demografia", "Demografia de condados do Meio-Oeste dos EUA"),
    ("quakes", "Terremotos_Fiji", "geociências", "Localização de terremotos próximos a Fiji"),
    ("Caschool", "Notas_escolas_California", "educação", "Notas de testes em distritos escolares da Califórnia"),
    ("SLID", "Trabalho_e_renda_Canada", "trabalho", "Pesquisa de dinâmica de trabalho e renda (Canadá)"),
    ("Chile", "Intencao_voto_Chile_1988", "política", "Intenção de voto no plebiscito chileno de 1988"),
    ("titanic", "Passageiros_Titanic", "história", "Passageiros do Titanic por classe, idade e sexo"),
    ("UScereal", "Cereais_nutricao_EUA", "alimentos", "Informação nutricional de cereais dos EUA"),
    ("airquality", "Qualidade_do_ar_Nova_York", "meio ambiente", "Medições diárias da qualidade do ar em Nova York"),
    ("drivers", "Mortes_motoristas_GB_1969-84", "transporte", "Mortes mensais de motoristas na Grã-Bretanha"),
    ("movies", "Filmes_IMDB", "entretenimento", "Filmes e avaliações de usuários do IMDB"),
]
VEGA = [
    ("stocks", "Acoes_tecnologia_2000-2010", "finanças", "Preço de fechamento de 5 ações de tecnologia"),
    ("barley", "Producao_cevada_Minnesota", "agricultura", "Produção de cevada por variedade, local e ano"),
    ("cars", "Carros_desempenho_1970-82", "transporte", "Desempenho e consumo de carros por ano do modelo"),
    ("iowa-electricity", "Geracao_eletrica_Iowa", "energia", "Geração de eletricidade em Iowa por fonte"),
    ("us-employment", "Emprego_EUA_por_setor", "economia", "Emprego mensal nos EUA por setor"),
]
TS_MONTHLY = {"deaths", "drivers"}        # series do R: coluna "time" em anos decimais


def _pydataset_doc(name: str) -> str:
    from pydataset import data
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data(name, show_doc=True)
    return buf.getvalue()


def _section(doc: str, title: str) -> str:
    m = re.search(rf"### {title}\s*\n(.*?)(?=\n### |\Z)", doc, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def _decimal_year_to_date(t: pd.Series) -> pd.Series:
    year = np.floor(t + 1e-6).astype(int)
    month = (np.round((t - year) * 12).astype(int) % 12) + 1
    return pd.to_datetime(dict(year=year, month=month, day=1))


def build() -> list[dict]:
    from pydataset import data
    from sklearn import datasets as skl
    from vega_datasets import local_data
    import statsmodels.api as sm

    items = []

    def add(df, fname, area, desc, package, dataset_id, title, source, changes="nenhuma"):
        items.append(dict(df=df.reset_index(drop=True), fname=fname, area=area, desc=desc, package=package,
                          dataset_id=dataset_id, title=title, source=source or "(não informado na documentação do pacote)",
                          changes=changes))

    titles = data().set_index("dataset_id")["title"]
    for name, fname, area, desc in PYDATASET:
        df, doc, changes = data(name), _pydataset_doc(name), "nenhuma"
        if name in TS_MONTHLY:
            df = pd.DataFrame({"date": _decimal_year_to_date(df["time"]), name: df[name]})
            changes = "coluna 'time' (ano decimal do R) convertida em data (1º dia do mês)"
        elif name == "airquality":
            assert "1973" in doc
            df.insert(0, "Date", pd.to_datetime(dict(year=1973, month=df["Month"], day=df["Day"])))
            changes = "coluna 'Date' criada a partir de Month e Day (ano 1973, conforme a documentação)"
        src = " | ".join(x for x in (_section(doc, "Source"), _section(doc, "References")) if x)
        add(df, fname, area, desc, "pydataset (conjuntos de dados do R)", name, str(titles[name]).strip(), src, changes)

    for name, fname, area, desc in VEGA:
        ds = getattr(local_data, name.replace("-", "_"))
        refs = "; ".join(ds.references or [])
        add(ds(), fname, area, desc, "vega_datasets", name, re.sub(r"\s+", " ", ds.description or "").strip()[:160],
            refs or re.sub(r"\s+", " ", ds.description or ""))

    m = sm.datasets.macrodata
    df = m.load_pandas().data
    df.insert(0, "date", pd.PeriodIndex(year=df["year"].astype(int), quarter=df["quarter"].astype(int), freq="Q").to_timestamp())
    add(df.drop(columns=["year", "quarter"]), "Macroeconomia_EUA_trimestral", "economia", "Indicadores macroeconômicos trimestrais dos EUA",
        "statsmodels", "macrodata", m.TITLE, re.sub(r"\s+", " ", m.SOURCE).strip() + " " + m.COPYRIGHT.strip(),
        "colunas 'year' e 'quarter' substituídas por 'date' (1º dia do trimestre)")

    for loader, fname, area, desc, kw in [
        (skl.load_diabetes, "Saude_progressao_diabetes", "saúde", "Progressão do diabetes em 442 pacientes", {"scaled": False}),
        (skl.load_breast_cancer, "Saude_cancer_mama_Wisconsin", "saúde", "Diagnóstico de câncer de mama (Wisconsin)", {}),
        (skl.load_wine, "Vinhos_analise_quimica", "alimentos", "Análise química de vinhos de três cultivares", {}),
    ]:
        b = loader(as_frame=True, **kw)
        df, changes = b.frame.copy(), "nenhuma (valores originais, sem padronização)"
        if hasattr(b, "target_names") and len(getattr(b, "target_names", [])):
            df["target"] = [str(b.target_names[i]) for i in b.target]
            changes = "coluna 'target' gravada com o nome da classe em vez do código numérico"
        title = [l.strip() for l in b.DESCR.splitlines() if l.strip() and not l.startswith("..")][0]
        tail = b.DESCR[max(b.DESCR.find("References"), b.DESCR.find("Source URL")):] if "References" in b.DESCR or "Source URL" in b.DESCR else ""
        add(df, fname, area, desc, "scikit-learn", loader.__name__, title, re.sub(r"\s+", " ", tail).strip()[:600], changes)

    items.sort(key=lambda i: (i["area"] != "saúde", i["fname"].lower()))
    return items


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.xlsx"):
        old.unlink()
    items = build()
    lines = ["# Bases públicas de validação", "",
             "Geradas por `backend/scripts/make_validation_sets.py`. Não participaram da calibração dos limiares. "
             "Os textos das colunas *Título original* e *Fonte* foram copiados da documentação que acompanha cada pacote "
             "(em inglês); confira a referência original antes de citá-la na monografia.", "",
             f"Total: {len(items)} bases, das quais {sum(i['area'] == 'saúde' for i in items)} da área da saúde.", "",
             "| # | Arquivo | Área | Descrição | Linhas × colunas | Pacote / identificador | Título original | Alterações feitas | Fonte (documentação do pacote) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for n, it in enumerate(items, start=10):
        fname = f"{n:02d}_{it['fname']}.xlsx"
        it["df"].to_excel(OUT / fname, index=False)
        cell = lambda s: str(s).replace("|", "/").replace("\n", " ")
        lines.append(f"| {n} | `{fname}` | {it['area']} | {it['desc']} | {it['df'].shape[0]} × {it['df'].shape[1]} | "
                     f"{it['package']} / `{it['dataset_id']}` | {cell(it['title'])} | {it['changes']} | {cell(it['source'])} |")
        print(f"{fname:55s} {it['df'].shape}")
    (OUT / "FONTES.md").write_text("\n".join(lines) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
