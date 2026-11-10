"""Baixa bases publicas brasileiras (DATASUS/TabNet e IBGE/SIDRA) e grava em data/brasil, com FONTES.md.

De onde vem cada dado:
- DATASUS: consultas ao TabNet (http://tabnet.datasus.gov.br), o mesmo tabulador usado no navegador.
  O script le o formulario de cada base, envia a consulta (linha, coluna, conteudo, periodos) e le a
  tabela devolvida em formato separado por ';'.
- IBGE: API de dados do SIDRA (https://apisidra.ibge.gov.br/values/...), em JSON.

Regras deste script (integridade dos dados):
- nenhum valor e inventado, estimado ou arredondado;
- linhas e colunas "Total" sao removidas (sao somas das demais) e a tabela e gravada em formato longo
  (uma linha por combinacao), que e o formato que o sistema espera;
- convencao de sinais das duas fontes: "-" e zero; "...", ".." e "X" (nao disponivel, nao se aplica,
  sigilo) ficam vazios;
- periodos viram data (1o dia do mes, trimestre ou ano) quando o rotulo da fonte permite;
- cada base registra em FONTES.md a consulta exata, a data de acesso e as transformacoes.

Os numeros do DATASUS para os anos mais recentes sao preliminares e o ano corrente e parcial.

Requer apenas: curl, pandas e openpyxl.   Uso, a partir de backend/:  python scripts/make_brazil_sets.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "brasil"
TODAY = dt.date.today().isoformat()
MESES = {m: i for i, m in enumerate(
    ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"], 1)}
MESES["marco"] = 3


def _curl(args: list[str], encoding: str) -> str:
    out = subprocess.run(["curl", "-sS", "-m", "240", "-A", "DashGen (pesquisa academica, TCC IFBA)"] + args,
                         capture_output=True).stdout
    time.sleep(1.2)                       # intervalo entre consultas, para nao sobrecarregar os servidores
    return out.decode(encoding, "replace")


def _number(v):
    if v is None:
        return None
    v = str(v).strip()
    if v == "-":
        return 0
    if v in ("", "...", "..", "X", "x"):
        return None
    try:
        f = float(v.replace(".", "").replace(",", ".")) if "," in v else float(v)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


# ------------------------------------------------------------------ DATASUS / TabNet
TABNET = "http://tabnet.datasus.gov.br/cgi/"


def tabnet_form(defpath: str):
    h = _curl([TABNET + "deftohtm.exe?" + defpath], "latin-1")
    sel = {}
    for m in re.finditer(r"<select[^>]*name=\"?([^\" >]+)\"?[^>]*>(.*?)</select>", h, re.S | re.I):
        opts = re.findall(r"<option\s+value=\"([^\"]*)\"[^>]*>([^<]*)", m.group(2), re.I)
        sel[m.group(1)] = [(v, html.unescape(t).strip()) for v, t in opts]
    title = re.search(r"<title>(.*?)</title>", h, re.S | re.I)
    title = re.sub(r"^TabNet Win32 [\d.]+:\s*", "", html.unescape(title.group(1)).strip()) if title else defpath
    return sel, title


def _pick(options, text):
    for v, t in options:
        if t.lower() == text.lower():
            return v
    raise KeyError(f"opcao {text!r} nao existe; disponiveis: {[t for _, t in options]}")


def tabnet(defpath, linha, coluna, conteudo, periodos):
    """periodos: int (os N mais recentes), lista de rotulos (ex.: ['2023']) ou None (todos)."""
    sel, title = tabnet_form(defpath)
    files = sel["Arquivos"]
    if isinstance(periodos, int):
        chosen = files[:periodos]
    elif periodos:
        chosen = [f for f in files if f[1] in periodos]
    else:
        chosen = files
    pairs = [("Linha", _pick(sel["Linha"], linha)), ("Coluna", _pick(sel["Coluna"], coluna)),
             ("Incremento", _pick(sel["Incremento"], conteudo))] + [("Arquivos", v) for v, _ in chosen]
    pairs += [(n, "TODAS_AS_CATEGORIAS__") for n in sel if n.startswith("S")]
    pairs += [("formato", "prn"), ("mostre", "Mostra")]
    body = "&".join(f"{urllib.parse.quote(k, encoding='latin-1')}={urllib.parse.quote(v, encoding='latin-1')}" for k, v in pairs)
    h = _curl(["-X", "POST", "-H", "Content-Type: application/x-www-form-urlencoded", "--data-raw", body,
               TABNET + "tabcgi.exe?" + defpath], "latin-1")
    m = re.search(r"<pre>(.*?)</pre>", h, re.S | re.I)
    if not m:
        raise RuntimeError("o TabNet nao devolveu tabela: " + re.sub(r"<[^>]+>|\s+", " ", h)[:200])
    rows = [[c.strip().strip('"') for c in l.split(";")] for l in html.unescape(m.group(1)).splitlines() if l.strip()]
    head = rows[0]
    rows = [r for r in rows[1:] if len(r) == len(head)]
    wide = pd.DataFrame(rows, columns=head)
    labels = [t for _, t in chosen]
    return wide, title, f"{labels[-1]} a {labels[0]}" if len(labels) > 1 else labels[0]


def tabnet_long(spec: dict) -> dict:
    wide, title, span = tabnet(spec["def"], spec["linha"], spec["coluna"], spec["conteudo"], spec.get("periodos"))
    first = wide.columns[0]
    wide = wide[wide[first].str.strip().str.lower() != "total"].drop(columns=[c for c in wide.columns if c.strip().lower() == "total"])
    changes = ["removidas a linha e a coluna 'Total'", "tabela convertida para formato longo", "'-' gravado como 0"]
    if "/mês" in spec["linha"]:           # linhas de mes vem como "Janeiro/2024"; as linhas so com o ano sao subtotais
        wide = wide[wide[first].str.fullmatch(r"\.*\s*[^\W\d]+/\d{4}")].copy()
        mes = wide[first].str.lstrip(". ").str.split("/", expand=True)
        wide[first] = pd.to_datetime(dict(year=mes[1].astype(int), month=mes[0].str.lower().map(MESES), day=1))
        changes.append("subtotais anuais removidos e rótulo 'Mês/Ano' convertido em data (1º dia do mês)")
    long = wide.melt(id_vars=[first], var_name=spec["coluna"], value_name=spec["conteudo"])
    long[spec["conteudo"]] = long[spec["conteudo"]].map(_number)
    if spec["coluna"].lower().startswith("ano"):
        long = long[long[spec["coluna"]].str.fullmatch(r"\d{4}")]
        long[spec["coluna"]] = long[spec["coluna"]].astype(int)
    if first.lower().startswith("mês") and "/" not in first:
        long = long[long[first].str.lower().isin(MESES)]
        changes.append("linha 'Ign/Branco' de mês removida")
    return dict(df=long.reset_index(drop=True), origem="DATASUS / TabNet", titulo=title,
                consulta=f"{TABNET}deftohtm.exe?{spec['def']} | Linha: {spec['linha']}; Coluna: {spec['coluna']}; "
                         f"Conteúdo: {spec['conteudo']}; Períodos: {span}; demais seleções: todas as categorias",
                alteracoes="; ".join(changes))


# ------------------------------------------------------------------------ IBGE / SIDRA
def sidra(spec: dict) -> dict:
    url = "https://apisidra.ibge.gov.br/values" + spec["path"]
    data = json.loads(_curl([url], "utf8"))
    head, df = data[0], pd.DataFrame(data[1:])
    names = {k: v for k, v in head.items() if re.fullmatch(r"D\d+N", k)}
    changes = ["'-' gravado como 0; '...', '..' e 'X' gravados como vazio"]
    variables = list(df[[k for k, v in names.items() if v == "Variável"][0]].unique())
    for k, name in names.items():           # periodo -> data, a partir do codigo do periodo (AAAA, AAAATT ou AAAAMM)
        code = df[k[:-1] + "C"]
        if name == "Ano" and code.str.fullmatch(r"\d{4}").all():
            df[k] = code.astype(int)
        elif name == "Trimestre":
            df[k] = pd.to_datetime(dict(year=code.str[:4].astype(int), month=(code.str[4:].astype(int) - 1) * 3 + 1, day=1))
            changes.append("trimestre convertido em data (1º dia do trimestre)")
        elif name == "Mês":
            df[k] = pd.to_datetime(dict(year=code.str[:4].astype(int), month=code.str[4:].astype(int), day=1))
            changes.append("mês convertido em data (1º dia do mês)")
    df["V"] = df["V"].map(_number)
    for col, pattern in spec.get("keep", {}).items():
        k = [k for k, v in names.items() if v == col][0]
        df = df[df[k].str.fullmatch(pattern)]
        changes.append(f"mantidas em '{col}' apenas as categorias que casam com /{pattern}/")
    if spec.get("drop_percentual"):
        vk = [k for k, v in names.items() if v == "Variável"][0]
        df = df[~df[vk].str.contains("percentual", case=False)]
        variables = [v for v in variables if "percentual" not in v.lower()]
        changes.append("removida a variável de percentual do total (derivada)")
    for col in spec.get("drop_total", []):
        k = [k for k, v in names.items() if v == col][0]
        df = df[df[k] != "Total"]
        changes.append(f"removida a categoria 'Total' de '{col}'")
    dims = [k for k, v in names.items() if v != "Variável" and df[k].nunique() > 1]
    vcol = [k for k, v in names.items() if v == "Variável"][0]
    units = df.groupby(vcol)["MN"].agg(lambda s: "/".join(sorted(set(s))))
    if df[vcol].nunique() > 1:
        out = df.pivot_table(index=dims, columns=vcol, values="V", aggfunc="first", dropna=False).reset_index()
        out.columns.name = None
        out = out.rename(columns={v: f"{v} ({units[v]})" if units[v] else v for v in units.index})
        changes.append("variáveis passadas de linhas para colunas")
    else:
        v = df[vcol].iloc[0]
        out = df[dims + ["V"]].rename(columns={"V": f"{v} ({units[v]})" if units[v] else v})
    out = out.rename(columns={k: names[k] for k in dims})
    if "Ano" in out.columns and pd.api.types.is_float_dtype(out["Ano"]):
        out["Ano"] = out["Ano"].astype(int)
    if spec.get("split_municipio"):
        parts = out["Município"].str.rsplit(" - ", n=1, expand=True)
        out.insert(0, "UF", parts[1])
        out["Município"] = parts[0]
        changes.append("rótulo 'Município - UF' separado em duas colunas")
    return dict(df=out.reset_index(drop=True), origem=f"IBGE / SIDRA, tabela {spec['path'].split('/')[2]}",
                titulo="Variáveis: " + "; ".join(variables), consulta=url, alteracoes="; ".join(dict.fromkeys(changes)))


UF, ANO = "Unidade da Federação", "Ano do Óbito"
DATASUS = [
    ("Saude_obitos_por_UF_e_ano", "Óbitos por UF de residência e ano (SIM)", dict(def_="sim/cnv/obt10uf.def", linha=UF, coluna=ANO, conteudo="Óbitos p/Residênc")),
    ("Saude_obitos_por_capitulo_CID10_e_ano", "Óbitos por capítulo da CID-10 e ano (SIM)", dict(def_="sim/cnv/obt10uf.def", linha="Capítulo CID-10", coluna=ANO, conteudo="Óbitos p/Residênc")),
    ("Saude_obitos_por_faixa_etaria_e_sexo_2023", "Óbitos por faixa etária e sexo em 2023 (SIM)", dict(def_="sim/cnv/obt10uf.def", linha="Faixa Etária", coluna="Sexo", conteudo="Óbitos p/Residênc", periodos=["2023"])),
    ("Saude_obitos_infantis_por_UF_e_ano", "Óbitos infantis por UF e ano (SIM)", dict(def_="sim/cnv/inf10uf.def", linha=UF, coluna=ANO, conteudo="Óbitos p/Residênc")),
    ("Saude_obitos_causas_externas_por_grupo_e_ano", "Óbitos por causas externas, por grande grupo e ano (SIM)", dict(def_="sim/cnv/ext10uf.def", linha="Grande Grupo CID10", coluna=ANO, conteudo="Óbitos p/Residênc")),
    ("Saude_obitos_maternos_por_UF_e_ano", "Óbitos maternos por UF e ano (SIM)", dict(def_="sim/cnv/mat10uf.def", linha=UF, coluna=ANO, conteudo="Óbitos maternos")),
    ("Saude_nascidos_vivos_por_UF_e_ano", "Nascidos vivos por UF de residência da mãe e ano (SINASC)", dict(def_="sinasc/cnv/nvuf.def", linha=UF, coluna="Ano do nascimento", conteudo="Nascim p/resid.mãe")),
    ("Saude_nascidos_vivos_idade_mae_e_gestacao_2023", "Nascidos vivos por idade da mãe e duração da gestação em 2023 (SINASC)", dict(def_="sinasc/cnv/nvuf.def", linha="Idade da mãe", coluna="Duração gestação", conteudo="Nascim p/resid.mãe", periodos=["2023"])),
    ("Saude_internacoes_SUS_por_mes_e_regiao", "Internações no SUS por mês de processamento e região, últimos 60 meses (SIH)", dict(def_="sih/cnv/niuf.def", linha="Ano/mês processamento", coluna="Região", conteudo="Internações", periodos=60)),
    ("Saude_internacoes_SUS_por_UF_e_capitulo_CID10", "Internações no SUS por UF e capítulo da CID-10, últimos 12 meses processados (SIH)", dict(def_="sih/cnv/niuf.def", linha=UF, coluna="Capítulo CID-10", conteudo="Internações", periodos=12)),
    ("Saude_dengue_casos_por_UF_e_ano", "Dengue: casos prováveis por UF de notificação e ano (SINAN)", dict(def_="sinannet/cnv/denguebbr.def", linha="UF de notificação", coluna="Ano 1º Sintoma(s)", conteudo="Casos Prováveis")),
    ("Saude_dengue_casos_por_mes_e_ano", "Dengue: casos prováveis por mês e ano dos primeiros sintomas (SINAN)", dict(def_="sinannet/cnv/denguebbr.def", linha="Mês 1º Sintoma(s)", coluna="Ano 1º Sintoma(s)", conteudo="Casos Prováveis")),
    ("Saude_chikungunya_casos_por_UF_e_ano", "Chikungunya: casos por UF de notificação e ano (SINAN)", dict(def_="sinannet/cnv/chikunbr.def", linha="UF de notificação", coluna="Ano 1º Sintoma(s)", conteudo="Todos os casos")),
    ("Saude_tuberculose_casos_por_UF_e_ano", "Tuberculose: casos confirmados por UF e ano de diagnóstico (SINAN)", dict(def_="sinannet/cnv/tubercbr.def", linha="UF de notificação", coluna="Ano Diagnóstico", conteudo="Casos confirmados")),
    ("Saude_hanseniase_casos_por_UF_e_ano", "Hanseníase: casos por UF e ano de diagnóstico (SINAN)", dict(def_="sinannet/cnv/hanswbr.def", linha="UF de notificação", coluna="Ano Diagnóstico", conteudo="Frequência")),
    ("Saude_malaria_casos_por_UF_e_ano", "Malária: casos confirmados por UF e ano de notificação (SINAN)", dict(def_="sinannet/cnv/malabr.def", linha="UF de notificação", coluna="Ano notificação", conteudo="Casos confirmados")),
    ("Saude_animais_peconhentos_por_UF_e_ano", "Acidentes por animais peçonhentos por UF e ano (SINAN)", dict(def_="sinannet/cnv/animaisbr.def", linha="UF de notificação", coluna="Ano acidente", conteudo="Notificações")),
    ("Saude_sifilis_gestante_por_UF_e_ano", "Sífilis em gestante: casos por UF e ano de diagnóstico (SINAN)", dict(def_="sinannet/cnv/sifilisgestantebr.def", linha="UF de notificação", coluna="Ano de Diagnóstico", conteudo="Casos confirmados")),
    ("Saude_leitos_internacao_por_UF_e_esfera", "Leitos de internação por UF e esfera jurídica, mês mais recente (CNES)", dict(def_="cnes/cnv/leiintbr.def", linha=UF, coluna="Esfera Jurídica", conteudo="Quantidade existente", periodos=1)),
    ("Saude_estabelecimentos_por_UF_e_tipo", "Estabelecimentos de saúde por UF e tipo, mês mais recente (CNES)", dict(def_="cnes/cnv/estabbr.def", linha=UF, coluna="Tipo de Estabelecimento", conteudo="Quantidade", periodos=1)),
    ("Saude_populacao_por_faixa_etaria_e_sexo_2021", "População residente por faixa etária e sexo em 2021 (estimativas usadas pelo DATASUS)", dict(def_="ibge/cnv/popsvsbr.def", linha="Faixa Etária 1", coluna="Sexo", conteudo="População residente", periodos=["2021"])),
]
IBGE = [
    ("Populacao_estimada_por_UF_e_ano", "População residente estimada por UF e ano", dict(path="/t/6579/n3/all/v/9324/p/all")),
    ("PIB_e_valor_adicionado_por_UF_e_ano", "PIB e valor adicionado por setor, por UF e ano", dict(path="/t/5938/n3/all/v/37,513,517,6575,525/p/all")),
    ("PIB_Brasil_serie_anual", "PIB do Brasil: valores, variação e PIB per capita por ano", dict(path="/t/6784/n1/all/v/all/p/all")),
    ("Taxa_desocupacao_por_UF_e_trimestre", "Taxa de desocupação por UF e trimestre (PNAD Contínua)", dict(path="/t/4099/n3/all/v/4099/p/all")),
    ("Rendimento_medio_por_sexo_e_trimestre", "Rendimento médio real do trabalho por sexo e trimestre (PNAD Contínua)", dict(path="/t/5436/n1/all/v/5932/p/all/c2/all", drop_total=["Sexo"])),
    ("Censo2022_populacao_area_densidade_municipios", "Censo 2022: população, área e densidade dos 5.570 municípios", dict(path="/t/4714/n6/all/v/all/p/all", split_municipio=True)),
    ("Censo2022_populacao_por_sexo_idade_e_UF", "Censo 2022: população por sexo, grupo de idade (5 em 5 anos) e UF", dict(path="/t/9514/n3/all/v/93/p/all/c2/all/c287/all", drop_total=["Sexo"], keep={"Idade": r"(\d+) a (\d+) anos|100 anos ou mais"}, quinquenal=True)),
    ("Censo_populacao_por_cor_ou_raca_e_UF", "Censos 2010 e 2022: população por cor ou raça e UF", dict(path="/t/9605/n3/all/v/93/p/all/c86/all", drop_total=["Cor ou raça"])),
    ("Producao_agricola_por_produto_e_ano", "Produção agrícola do Brasil: valor e área colhida por produto, últimos 10 anos (PAM)", dict(path="/t/5457/n1/all/v/215,216/p/last%2010/c782/all", drop_total=["Produto das lavouras temporárias e permanentes"])),
    ("Rebanhos_por_tipo_UF_e_ano", "Efetivo dos rebanhos por tipo, UF e ano, últimos 10 anos (PPM)", dict(path="/t/3939/n3/all/v/105/p/last%2010/c79/all")),
    ("Producao_origem_animal_valor_por_UF_e_ano", "Valor da produção de origem animal por tipo de produto, UF e ano, últimos 10 anos (PPM)", dict(path="/t/74/n3/all/v/215/p/last%2010/c80/all", drop_total=["Tipo de produto de origem animal"])),
    ("Producao_industrial_mensal_Brasil", "Produção industrial mensal do Brasil por seção e atividade: índices e variações, últimos 120 meses (PIM-PF)", dict(path="/t/8888/n1/all/v/all/p/last%20120/c544/all")),
    ("Volume_servicos_mensal_Brasil", "Serviços do Brasil, mensal: índices de receita e de volume e variações (PMS)", dict(path="/t/5906/n1/all/v/all/p/all/c11046/all")),
    ("Vendas_comercio_mensal_Brasil", "Comércio varejista ampliado do Brasil, mensal: índices de receita e de volume e variações (PMC)", dict(path="/t/8881/n1/all/v/all/p/all/c11046/all")),
    ("Registro_civil_nascidos_vivos_por_UF_e_ano", "Nascidos vivos registrados por UF e ano, últimos 10 anos (Registro Civil)", dict(path="/t/2612/n3/all/v/218/p/last%2010")),
    ("Registro_civil_obitos_por_UF_e_ano", "Óbitos registrados por UF e ano, últimos 10 anos (Registro Civil)", dict(path="/t/2681/n3/all/v/343/p/last%2010")),
    ("Registro_civil_casamentos_por_UF_e_ano", "Casamentos registrados por UF e ano, últimos 10 anos (Registro Civil)", dict(path="/t/2759/n3/all/v/all/p/last%2010", drop_percentual=True)),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    items, failed = [], []
    for fname, desc, spec in DATASUS:
        spec = {("def" if k == "def_" else k): v for k, v in spec.items()}
        try:
            items.append(dict(fname=fname, desc=desc, **tabnet_long(spec)))
        except Exception as exc:
            failed.append((fname, f"{type(exc).__name__}: {str(exc)[:160]}"))
        print(fname, "ok" if items and items[-1]["fname"] == fname else "FALHOU", flush=True)
    for fname, desc, spec in IBGE:
        try:
            it = sidra(spec)
            if spec.get("quinquenal"):      # mantem so os grupos de 5 anos (0 a 4, 5 a 9, ...), que nao se sobrepoem
                m = it["df"]["Idade"].str.extract(r"(\d+) a (\d+) anos").astype(float)
                it["df"] = it["df"][(m[1] - m[0] == 4) & (m[0] % 5 == 0) | (it["df"]["Idade"] == "100 anos ou mais")].reset_index(drop=True)
                it["alteracoes"] += "; mantidos apenas os grupos quinquenais de idade (sem sobreposição)"
            items.append(dict(fname=fname, desc=desc, **it))
        except Exception as exc:
            failed.append((fname, f"{type(exc).__name__}: {str(exc)[:160]}"))
        print(fname, "ok" if items and items[-1]["fname"] == fname else "FALHOU", flush=True)

    for old in OUT.glob("*.xlsx"):
        old.unlink()
    cell = lambda s: str(s).replace("|", "/").replace("\n", " ")
    lines = ["# Bases públicas brasileiras (DATASUS e IBGE)", "",
             f"Geradas por `backend/scripts/make_brazil_sets.py` em {TODAY}. Cada linha registra a consulta exata feita à fonte. "
             "Os dados do DATASUS para os anos mais recentes são preliminares e o ano corrente é parcial; "
             "os valores podem mudar se o script for executado em outra data.", "",
             f"Total: {len(items)} bases ({sum(i['origem'].startswith('DATASUS') for i in items)} do DATASUS e "
             f"{sum(i['origem'].startswith('IBGE') for i in items)} do IBGE).", "",
             "| # | Arquivo | Descrição | Linhas × colunas | Origem | Título / variáveis na fonte | Consulta | Acesso | Transformações |",
             "|---|---|---|---|---|---|---|---|---|"]
    for n, it in enumerate(items, start=50):
        f = f"{n:02d}_{it['fname']}.xlsx"
        it["df"].to_excel(OUT / f, index=False)
        lines.append(f"| {n} | `{f}` | {it['desc']} | {it['df'].shape[0]} × {it['df'].shape[1]} | {it['origem']} | {cell(it['titulo'])} | "
                     f"{cell(it['consulta'])} | {TODAY} | {cell(it['alteracoes'])} |")
    if failed:
        lines += ["", "## Consultas que falharam nesta execução", ""] + [f"- `{f}`: {e}" for f, e in failed]
    (OUT / "FONTES.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(f"\n{len(items)} bases gravadas; {len(failed)} falharam")
    for f, e in failed:
        print("  FALHOU:", f, e)


if __name__ == "__main__":
    main()
