# Estudos de caso (saída automática do sistema)


## 01_BCB_IPCA_mensal_2015-2024.xlsx

- Linhas: 120 | tempo total: 0.11 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Data | temporal | 120 | 0.0 |
| IPCA_mensal_pct | numeric | 88 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R5 | line | Média de IPCA_mensal_pct por mês |  |
| R1 | histogram | Distribuição de IPCA_mensal_pct |  |

## 02_BCB_Dolar_diario_2023-2024.xlsx

- Linhas: 502 | tempo total: 0.02 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Data | temporal | 502 | 0.0 |
| Dolar_venda_R$ | numeric | 489 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R5 | line | Soma de Dolar_venda_R$ por mês |  |
| R1 | histogram | Distribuição de Dolar_venda_R$ |  |

## 03_BCB_Selic_mensal_2015-2024.xlsx

- Linhas: 120 | tempo total: 0.02 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Data | temporal | 120 | 0.0 |
| Selic_pct_aa | numeric | 66 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R5 | line | Média de Selic_pct_aa por mês |  |
| R1 | histogram | Distribuição de Selic_pct_aa |  |

## 04_Superstore_vendas_varejo.xlsx

- Linhas: 10.800 | tempo total: 2.06 s
- Abas: Sheet1
- Nota de leitura: Coluna 'Order Date' convertida de texto para data.
- Nota de leitura: Coluna 'Ship Date' convertida de texto para data.

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Row ID | ignored (Texto livre ou identificador (quase todos os valores são únicos).) | 10001 | 0.0 |
| Order ID | categorical | 5015 | 0.0 |
| Order Date | temporal | 1236 | 7.5 |
| Ship Date | temporal | 1334 | 7.5 |
| Ship Mode | categorical | 4 | 7.5 |
| Customer ID | categorical | 793 | 7.5 |
| Customer Name | categorical | 793 | 7.5 |
| Segment | categorical | 3 | 7.5 |
| Country | categorical | 1 | 7.5 |
| City | categorical | 531 | 7.5 |
| State | categorical | 49 | 7.5 |
| Postal Code | ignored (Parece um código (CEP, ISO etc.): somar ou tirar a média não faz sentido.) | 630 | 7.6 |
| Region | categorical | 4 | 7.5 |
| Product ID | categorical | 1862 | 7.5 |
| Category | categorical | 3 | 7.5 |
| Sub-Category | categorical | 17 | 7.5 |
| Product Name | categorical | 1850 | 7.5 |
| Sales | numeric | 5825 | 7.5 |
| Quantity | numeric | 14 | 7.5 |
| Discount | numeric | 12 | 7.5 |
| Profit | numeric | 7287 | 7.5 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Soma de Sales, soma de Quantity, média de Discount, soma de Profit por mês | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Soma de Sales por Ship Mode |  |
| R6 | bar | Soma de Quantity por Ship Mode |  |
| R6 | bar | Soma de Sales por Segment |  |
| R6 | bar | Soma de Quantity por Segment |  |
| R2 | bar | Frequência de Ship Mode |  |
| R2 | bar | Frequência de Segment |  |
| R1 | histogram | Distribuição de Sales |  |
| R1 | histogram | Distribuição de Quantity |  |
| R1 | histogram | Distribuição de Discount |  |
| R4 | scatter | Profit versus Sales | Amostra de 2000 pontos para manter a legibilidade. |
| R4 | scatter | Profit versus Discount | Amostra de 2000 pontos para manter a legibilidade. |

## 05_Gapminder_paises_1952-2007.xlsx

- Linhas: 1.704 | tempo total: 0.14 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| country | categorical | 142 | 0.0 |
| continent | categorical | 5 | 0.0 |
| year | temporal | 12 | 0.0 |
| lifeExp | numeric | 1626 | 0.0 |
| pop | numeric | 1704 | 0.0 |
| gdpPercap | numeric | 1704 | 0.0 |
| iso_alpha | categorical | 141 | 0.0 |
| iso_num | ignored (Parece um código (CEP, ISO etc.): somar ou tirar a média não faz sentido.) | 141 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Média de lifeExp, soma de pop, média de gdpPercap por ano | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Média de lifeExp por continent |  |
| R6 | bar | Soma de pop por continent |  |
| R6 | hbar | Média de lifeExp por country | Exibidas as 15 maiores categorias de 142. |
| R6 | hbar | Soma de pop por country | Exibidas as 15 maiores categorias de 142. |
| R2 | bar | Frequência de continent |  |
| R3 | hbar | Frequência de country | Exibidas as 15 categorias mais frequentes de 142. |
| R3 | hbar | Frequência de iso_alpha | Exibidas as 15 categorias mais frequentes de 141. |
| R1 | histogram | Distribuição de lifeExp |  |
| R1 | histogram | Distribuição de pop |  |
| R1 | histogram | Distribuição de gdpPercap |  |
| R4 | scatter | gdpPercap versus lifeExp |  |

## 06_Clima_Seattle_2012-2015.xlsx

- Linhas: 1.461 | tempo total: 0.15 s
- Abas: Sheet1
- Nota de leitura: Coluna 'date' convertida de texto para data.

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| date | temporal | 1461 | 0.0 |
| precipitation | numeric | 111 | 0.0 |
| temp_max | numeric | 67 | 0.0 |
| temp_min | numeric | 55 | 0.0 |
| wind | numeric | 79 | 0.0 |
| weather | categorical | 5 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Soma de precipitation, média de temp_max, média de temp_min, média de wind por mês | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Soma de precipitation por weather |  |
| R6 | bar | Média de temp_max por weather |  |
| R2 | bar | Frequência de weather |  |
| R1 | histogram | Distribuição de precipitation |  |
| R1 | histogram | Distribuição de temp_max |  |
| R1 | histogram | Distribuição de temp_min |  |
| R4 | scatter | temp_min versus temp_max |  |
| R4 | scatter | wind versus precipitation |  |

## 07_COVID19_America_Latina.xlsx

- Linhas: 4.896 | tempo total: 0.24 s
- Abas: Sheet1
- Nota de leitura: Coluna 'Date' convertida de texto para data.

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Date | temporal | 816 | 0.0 |
| Country | categorical | 6 | 0.0 |
| Confirmed | numeric | 4432 | 0.0 |
| Recovered | numeric | 2766 | 0.0 |
| Deaths | numeric | 4351 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Soma de Confirmed, Recovered, Deaths por mês | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Soma de Confirmed por Country |  |
| R6 | bar | Soma de Recovered por Country |  |
| R2 | bar | Frequência de Country |  |
| R1 | histogram | Distribuição de Confirmed |  |
| R1 | histogram | Distribuição de Recovered |  |
| R1 | histogram | Distribuição de Deaths |  |
| R4 | scatter | Deaths versus Confirmed | Amostra de 2000 pontos para manter a legibilidade. |
| R4 | scatter | Recovered versus Confirmed | Amostra de 2000 pontos para manter a legibilidade. |

## 08_Tips_restaurante.xlsx

- Linhas: 244 | tempo total: 0.06 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| total_bill | numeric | 229 | 0.0 |
| tip | numeric | 123 | 0.0 |
| sex | categorical | 2 | 0.0 |
| smoker | categorical | 2 | 0.0 |
| day | categorical | 4 | 0.0 |
| time | categorical | 2 | 0.0 |
| size | categorical | 6 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R6 | bar | Soma de total_bill por sex |  |
| R6 | bar | Soma de tip por sex |  |
| R6 | bar | Soma de total_bill por smoker |  |
| R6 | bar | Soma de tip por smoker |  |
| R2 | bar | Frequência de sex |  |
| R2 | bar | Frequência de smoker |  |
| R2 | bar | Frequência de day |  |
| R1 | histogram | Distribuição de total_bill |  |
| R1 | histogram | Distribuição de tip |  |
| R4 | scatter | tip versus total_bill |  |

## 09_Passageiros_aereos_1949-1960.xlsx

- Linhas: 144 | tempo total: 0.03 s
- Abas: Sheet1

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| year | temporal | 12 | 0.0 |
| month | categorical | 12 | 0.0 |
| passengers | numeric | 118 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R5 | line | Soma de passengers por ano |  |
| R6 | hbar | Soma de passengers por month |  |
| R3 | hbar | Frequência de month |  |
| R1 | histogram | Distribuição de passengers |  |

## 01_vendas_completo.xlsx

- Linhas: 500 | tempo total: 0.11 s
- Abas: Dados

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Data | temporal | 275 | 0.0 |
| Região | categorical | 5 | 0.0 |
| Produto | categorical | 8 | 0.0 |
| Vendedor | categorical | 25 | 0.0 |
| Quantidade | numeric | 19 | 0.0 |
| Receita | numeric | 499 | 0.0 |
| Preço | numeric | 459 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Soma de Quantidade, soma de Receita, média de Preço por mês | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Soma de Quantidade por Região |  |
| R6 | bar | Soma de Receita por Região |  |
| R6 | bar | Soma de Quantidade por Produto |  |
| R6 | bar | Soma de Receita por Produto |  |
| R2 | bar | Frequência de Região |  |
| R2 | bar | Frequência de Produto |  |
| R3 | hbar | Frequência de Vendedor | Exibidas as 15 categorias mais frequentes de 25. |
| R1 | histogram | Distribuição de Quantidade |  |
| R1 | histogram | Distribuição de Receita |  |
| R1 | histogram | Distribuição de Preço |  |
| R4 | scatter | Receita versus Quantidade |  |

## 02_csv_brasileiro_latin1.csv

- Linhas: 5 | tempo total: 0.14 s
- Nota de leitura: Codificação detectada: Windows-1252.
- Nota de leitura: Coluna 'Data' convertida de texto para data.
- Nota de leitura: Coluna 'Valor' convertida de texto para número (formato brasileiro).
- Nota de leitura: Coluna 'Variação' convertida de texto para número (vírgula decimal).

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Data | temporal | 5 | 0.0 |
| Cidade | categorical | 3 | 0.0 |
| Valor | numeric | 5 | 0.0 |
| Variação | numeric | 5 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R7 | multiline | Soma de Valor, Variação por mês | As séries têm escalas muito diferentes; as de menor magnitude podem ficar pouco visíveis. Use 'Índice base 100' ou 'Eixo secundário' na barra de ferramentas. |
| R6 | bar | Soma de Valor por Cidade |  |
| R6 | bar | Soma de Variação por Cidade |  |
| R2 | bar | Frequência de Cidade |  |
| R1 | histogram | Distribuição de Valor |  |
| R1 | histogram | Distribuição de Variação |  |
| R4 | scatter | Variação versus Valor |  |

## 03_planilha_suja.csv

- Linhas: 5 | tempo total: 0.03 s
- Nota de leitura: Nome de coluna duplicado 'Nome' renomeado para 'Nome (2)'.
- Nota de leitura: 1 linha(s) totalmente vazia(s) removida(s).
- Nota de leitura: 1 coluna(s) totalmente vazia(s) removida(s).
- Nota de leitura: Coluna 'Idade' convertida de texto para número (inteiros).
- Nota de leitura: Coluna 'Cadastro' convertida de texto para data.

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Nome | categorical | 4 | 20.0 |
| Nome (2) | categorical | 5 | 0.0 |
| Idade | numeric | 4 | 20.0 |
| Cadastro | temporal | 5 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R5 | line | Média de Idade por mês |  |
| R6 | bar | Média de Idade por Nome (2) |  |
| R6 | bar | Média de Idade por Nome |  |
| R2 | bar | Frequência de Nome (2) |  |
| R2 | bar | Frequência de Nome |  |
| R1 | histogram | Distribuição de Idade |  |

## 04_uma_coluna.csv

- Linhas: 100 | tempo total: 0.01 s
- Nota de leitura: Coluna 'Valor' convertida de texto para número (ponto decimal).

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Valor | numeric | 100 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R1 | histogram | Distribuição de Valor |  |

## 05_coluna_constante.csv

- Linhas: 50 | tempo total: 0.02 s
- Nota de leitura: Coluna 'Fixo' convertida de texto para número (ponto decimal).

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Fixo | numeric | 1 | 0.0 |
| Grupo | categorical | 2 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R6 | bar | Soma de Fixo por Grupo |  |
| R2 | bar | Frequência de Grupo |  |

## 06_alta_cardinalidade.csv

- Linhas: 400 | tempo total: 0.02 s
- Nota de leitura: Coluna 'Valor' convertida de texto para número (ponto decimal).

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| Cliente | categorical | 114 | 0.0 |
| Valor | numeric | 397 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R6 | hbar | Soma de Valor por Cliente | Exibidas as 15 maiores categorias de 114. |
| R3 | hbar | Frequência de Cliente | Exibidas as 15 categorias mais frequentes de 114. |
| R1 | histogram | Distribuição de Valor |  |

## 07_identificadores_e_texto.csv

- Linhas: 60 | tempo total: 0.03 s
- Nota de leitura: Coluna 'ID' convertida de texto para número (inteiros).
- Nota de leitura: Coluna 'Valor' convertida de texto para número (ponto decimal).

| Coluna | Tipo inferido | Distintos | Ausentes (%) |
|---|---|---:|---:|
| ID | ignored (Parece um identificador (valores únicos).) | 60 | 0.0 |
| Descrição | ignored (Texto livre ou identificador (quase todos os valores são únicos).) | 60 | 0.0 |
| Valor | numeric | 58 | 0.0 |
| Categoria | categorical | 3 | 0.0 |

| Regra | Gráfico | Título | Avisos |
|---|---|---|---|
| R6 | bar | Soma de Valor por Categoria |  |
| R2 | bar | Frequência de Categoria |  |
| R1 | histogram | Distribuição de Valor |  |
