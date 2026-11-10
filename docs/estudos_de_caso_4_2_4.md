# Estudos de caso (rascunho para a seção 4.2.4)

Saída gerada por `python backend/scripts/case_studies.py backend/data/real backend/data/synthetic --out docs/estudos_de_caso` e capturas em `docs/capturas/` (geradas por `e2e/capturas_estudos_de_caso.py`). As colunas "Resultado" e "Observações" são uma avaliação minha, feita olhando os gráficos e os registros de decisão. **Revise antes de usar: é a sua análise que vale na monografia.**

Os nove arquivos reais vêm de seis fontes públicas (Banco Central do Brasil e cinco repositórios do GitHub), em oito domínios diferentes. Nenhum veio do Kaggle ou do dados.gov.br, que não consegui acessar daqui; para ampliar a diversidade, vale incluir ao menos um de cada.

## Resumo

| # | Dataset | Domínio | Linhas | Resultado | Gráficos (regras) |
|---|---|---|---:|---|---|
| 1 | BCB_IPCA_mensal_2015-2024 | Economia (inflação) | 120 | Acerto | 2 (R1, R5) |
| 2 | BCB_Dolar_diario_2023-2024 | Economia (câmbio) | 502 | Ajuste manual | 2 (R1, R5) |
| 3 | BCB_Selic_mensal_2015-2024 | Economia (juros) | 120 | Acerto | 2 (R1, R5) |
| 4 | Superstore_vendas_varejo | Varejo (vendas) | 10.800 | Acerto parcial | 12 (R1, R2, R4, R6, R7) |
| 5 | Gapminder_paises_1952-2007 | Demografia e desenvolvimento | 1.704 | Acerto parcial | 12 (R1, R2, R3, R4, R6, R7) |
| 6 | Clima_Seattle_2012-2015 | Meteorologia | 1.461 | Acerto | 9 (R1, R2, R4, R6, R7) |
| 7 | COVID19_America_Latina | Saúde pública | 4.896 | Ajuste manual | 9 (R1, R2, R4, R6, R7) |
| 8 | Tips_restaurante | Serviços (restaurante) | 244 | Acerto | 10 (R1, R2, R4, R6) |
| 9 | Passageiros_aereos_1949-1960 | Transportes | 144 | Ajuste manual | 4 (R1, R3, R5, R6) |

## Detalhe por caso

### 01_BCB_IPCA_mensal_2015-2024.xlsx

- Fonte: BCB, SGS série 433. Entrada: 120 linhas, 2 colunas.
- Tipos inferidos: Data (temporal); IPCA_mensal_pct (numeric).
- Gráficos e regras: R5, Média de IPCA_mensal_pct por mês; R1, Distribuição de IPCA_mensal_pct.
- Resultado: **Acerto**. Série mensal exibida em granularidade mensal (120 pontos) com média; histograma da distribuição.
- Observações: Antes da calibração mostrava soma por ano, o que perdia o detalhe e somava taxas.
- Captura: `docs/capturas/01_BCB_IPCA_mensal_2015-2024_dashboard.png`

### 02_BCB_Dolar_diario_2023-2024.xlsx

- Fonte: BCB, SGS série 1. Entrada: 502 linhas, 2 colunas.
- Tipos inferidos: Data (temporal); Dolar_venda_R$ (numeric).
- Gráficos e regras: R5, Soma de Dolar_venda_R$ por mês; R1, Distribuição de Dolar_venda_R$.
- Resultado: **Ajuste manual**. Linha mensal e histograma gerados corretamente.
- Observações: A agregação automática usa soma para "Dolar_venda_R$", porque o nome da coluna não sugere taxa. É preciso escolher "Média" na barra de ferramentas. Limitação aberta da heurística por nome.
- Captura: `docs/capturas/02_BCB_Dolar_diario_2023-2024_dashboard.png`

### 03_BCB_Selic_mensal_2015-2024.xlsx

- Fonte: BCB, SGS série 4189. Entrada: 120 linhas, 2 colunas.
- Tipos inferidos: Data (temporal); Selic_pct_aa (numeric).
- Gráficos e regras: R5, Média de Selic_pct_aa por mês; R1, Distribuição de Selic_pct_aa.
- Resultado: **Acerto**. Série mensal com média (120 pontos).
- Observações: Antes da calibração: soma por ano.
- Captura: `docs/capturas/03_BCB_Selic_mensal_2015-2024_dashboard.png`

### 04_Superstore_vendas_varejo.xlsx

- Fonte: leonism/sample-superstore (GitHub). Entrada: 10.800 linhas, 21 colunas.
- Tipos inferidos: Row ID (ignored); Order ID (categorical); Order Date (temporal); Ship Date (temporal); Ship Mode (categorical); Customer ID (categorical); Customer Name (categorical); Segment (categorical); Country (categorical); City (categorical); State (categorical); Postal Code (ignored); Region (categorical); Product ID (categorical); Category (categorical); Sub-Category (categorical); Product Name (categorical); Sales (numeric); Quantity (numeric); Discount (numeric); Profit (numeric).
- Gráficos e regras: R7, Soma de Sales, soma de Quantity, média de Discount, soma de Profit por mês; R6, Soma de Sales por Ship Mode; R6, Soma de Quantity por Ship Mode; R6, Soma de Sales por Segment; R6, Soma de Quantity por Segment; R2, Frequência de Ship Mode; R2, Frequência de Segment; R1, Distribuição de Sales; R1, Distribuição de Quantity; R1, Distribuição de Discount; R4, Profit versus Sales; R4, Profit versus Discount.
- Resultado: **Acerto parcial**. 12 gráficos: R7 mensal com 4 medidas, R6, R2, R1 e R4. "Postal Code" passou a ser ignorada (era somada no R7). As 2 colunas de data foram tratadas e a de maior cobertura (Order Date) foi usada.
- Observações: Dos 13 campos categóricos, as barras R6 e R2 usam apenas Ship Mode e Segment, e não Category ou Region, que seriam mais informativos: a escolha segue a ordem das colunas. Escalas muito diferentes no R7 geram o aviso (resolvido com índice base 100 ou eixo secundário). Arquivo contém linhas duplicadas.
- Captura: `docs/capturas/04_Superstore_vendas_varejo_dashboard.png`

### 05_Gapminder_paises_1952-2007.xlsx

- Fonte: plotly/datasets (GitHub). Entrada: 1.704 linhas, 8 colunas.
- Tipos inferidos: country (categorical); continent (categorical); year (temporal); lifeExp (numeric); pop (numeric); gdpPercap (numeric); iso_alpha (categorical); iso_num (ignored).
- Gráficos e regras: R7, Média de lifeExp, soma de pop, média de gdpPercap por ano; R6, Média de lifeExp por continent; R6, Soma de pop por continent; R6, Média de lifeExp por country; R6, Soma de pop por country; R2, Frequência de continent; R3, Frequência de country; R3, Frequência de iso_alpha; R1, Distribuição de lifeExp; R1, Distribuição de pop; R1, Distribuição de gdpPercap; R4, gdpPercap versus lifeExp.
- Resultado: **Acerto parcial**. Coluna "year" inteira tratada como temporal (era a falha que derrubava o dashboard). Médias para lifeExp e gdpPercap; "iso_num" ignorada.
- Observações: "country" e "iso_alpha" são redundantes e geram dois gráficos de frequência de pouco valor (cada país aparece 12 vezes). Histograma de "pop" fica ilegível por causa da cauda longa. R7 mistura escalas muito diferentes (aviso).
- Captura: `docs/capturas/05_Gapminder_paises_1952-2007_dashboard.png`

### 06_Clima_Seattle_2012-2015.xlsx

- Fonte: vega/vega-datasets (GitHub). Entrada: 1.461 linhas, 6 colunas.
- Tipos inferidos: date (temporal); precipitation (numeric); temp_max (numeric); temp_min (numeric); wind (numeric); weather (categorical).
- Gráficos e regras: R7, Soma de precipitation, média de temp_max, média de temp_min, média de wind por mês; R6, Soma de precipitation por weather; R6, Média de temp_max por weather; R2, Frequência de weather; R1, Distribuição de precipitation; R1, Distribuição de temp_max; R1, Distribuição de temp_min; R4, temp_min versus temp_max; R4, wind versus precipitation.
- Resultado: **Acerto**. R7 mensal com soma de precipitação e média de temperaturas e vento. R6 por tipo de clima.
- Observações: Antes da calibração: série anual com apenas 4 pontos e soma de temperaturas.
- Captura: `docs/capturas/06_Clima_Seattle_2012-2015_dashboard.png`

### 07_COVID19_America_Latina.xlsx

- Fonte: datasets/covid-19 (GitHub). Entrada: 4.896 linhas, 5 colunas.
- Tipos inferidos: Date (temporal); Country (categorical); Confirmed (numeric); Recovered (numeric); Deaths (numeric).
- Gráficos e regras: R7, Soma de Confirmed, Recovered, Deaths por mês; R6, Soma de Confirmed por Country; R6, Soma de Recovered por Country; R2, Frequência de Country; R1, Distribuição de Confirmed; R1, Distribuição de Recovered; R1, Distribuição de Deaths; R4, Deaths versus Confirmed; R4, Recovered versus Confirmed.
- Resultado: **Ajuste manual**. R7 mensal, R6 por país e dispersões gerados; escalas diferentes sinalizadas.
- Observações: Os valores são acumulados por dia. Somar acumulados por mês e por país produz números sem significado epidemiológico. O sistema não detecta séries acumuladas; limitação registrada, sem solução implementada.
- Captura: `docs/capturas/07_COVID19_America_Latina_dashboard.png`

### 08_Tips_restaurante.xlsx

- Fonte: mwaskom/seaborn-data (GitHub). Entrada: 244 linhas, 7 colunas.
- Tipos inferidos: total_bill (numeric); tip (numeric); sex (categorical); smoker (categorical); day (categorical); time (categorical); size (categorical).
- Gráficos e regras: R6, Soma de total_bill por sex; R6, Soma de tip por sex; R6, Soma de total_bill por smoker; R6, Soma de tip por smoker; R2, Frequência de sex; R2, Frequência de smoker; R2, Frequência de day; R1, Distribuição de total_bill; R1, Distribuição de tip; R4, tip versus total_bill.
- Resultado: **Acerto**. Sem coluna temporal: R6, R2, R1 e R4. "size" (1 a 6) foi tratada como categórica.
- Observações: Nenhuma observação relevante.
- Captura: `docs/capturas/08_Tips_restaurante_dashboard.png`

### 09_Passageiros_aereos_1949-1960.xlsx

- Fonte: mwaskom/seaborn-data (GitHub). Entrada: 144 linhas, 3 colunas.
- Tipos inferidos: year (temporal); month (categorical); passengers (numeric).
- Gráficos e regras: R5, Soma de passengers por ano; R6, Soma de passengers por month; R3, Frequência de month; R1, Distribuição de passengers.
- Resultado: **Ajuste manual**. R5 anual (12 pontos), R6 e R1 gerados; "year" tratada como temporal.
- Observações: O mês vem como texto ("January") e não é combinado com o ano: a série mensal de 144 pontos, a sazonalidade, não aparece. R6 ordena os meses por valor, não por calendário.
- Captura: `docs/capturas/09_Passageiros_aereos_1949-1960_dashboard.png`

## Casos sintéticos de limite (já existentes)

Os 7 arquivos de `backend/data/synthetic/` seguem com o comportamento esperado após as calibrações: CSV brasileiro em Latin-1 lido corretamente, planilha suja com cabeçalho duplicado tratada, coluna constante sem histograma, identificadores e texto livre ignorados, alta cardinalidade limitada às 15 maiores categorias. Detalhes em `docs/estudos_de_caso.md`.

## Contagem para a seção de resultados

Com a minha avaliação: 4 acertos, 2 acertos parciais e 3 que exigem ajuste manual, em 9 datasets reais. Com apenas 9 casos e sem avaliação independente, trate esses números como ilustrativos, não como taxa de acerto do sistema.
