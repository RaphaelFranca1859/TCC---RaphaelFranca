# Execução do sistema nas bases de data/validacao

Gerado por `backend/scripts/check_validation_sets.py`. Cada base passou por leitura, inferência de tipos e motor de gráficos, com as opções padrão e sem ajuste manual de tipos. A tabela registra apenas o que o sistema fez; se os tipos e os gráficos escolhidos são adequados a cada base é uma avaliação que ainda precisa ser feita, base a base. Os tempos são de uma única execução no ambiente de desenvolvimento e não substituem o benchmark da seção 4.2.5.

Bases executadas: 38. Falhas: 0.

| Arquivo | Linhas | Colunas | Numéricas | Categóricas | Temporais | Ignoradas | Gráficos | Regras disparadas | Tempo (s) | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| `10_Saude_baixo_peso_ao_nascer.xlsx` | 189 | 10 | 3 | 7 | 0 | 0 | 11 | R1×3, R2×3, R4×1, R6×4 | 0.12 | ok |
| `11_Saude_biopsias_cancer_mama.xlsx` | 699 | 11 | 10 | 1 | 0 | 0 | 8 | R1×3, R2×1, R4×2, R6×2 | 0.07 | ok |
| `12_Saude_cancer_esofago_fumo_alcool.xlsx` | 88 | 5 | 2 | 3 | 0 | 0 | 10 | R1×2, R2×3, R4×1, R6×4 | 0.03 | ok |
| `13_Saude_cancer_mama_Wisconsin.xlsx` | 569 | 31 | 30 | 1 | 0 | 0 | 8 | R1×3, R2×1, R4×2, R6×2 | 0.15 | ok |
| `14_Saude_cancer_pulmao_NCCTG.xlsx` | 228 | 10 | 6 | 4 | 0 | 0 | 11 | R1×3, R2×3, R4×1, R6×4 | 0.04 | ok |
| `15_Saude_cirrose_biliar_Mayo.xlsx` | 418 | 20 | 12 | 7 | 0 | 1 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.08 | ok |
| `16_Saude_crises_epilepsia.xlsx` | 236 | 9 | 6 | 3 | 0 | 0 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.04 | ok |
| `17_Saude_diabetes_mulheres_Pima.xlsx` | 332 | 8 | 7 | 1 | 0 | 0 | 8 | R1×3, R2×1, R4×2, R6×2 | 0.04 | ok |
| `18_Saude_infertilidade_pos_aborto.xlsx` | 248 | 8 | 3 | 5 | 0 | 0 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.04 | ok |
| `19_Saude_mortes_doencas_pulmonares_UK.xlsx` | 72 | 2 | 1 | 0 | 1 | 0 | 2 | R1×1, R5×1 | 0.01 | ok |
| `20_Saude_progressao_diabetes.xlsx` | 442 | 11 | 10 | 1 | 0 | 0 | 8 | R1×3, R2×1, R4×2, R6×2 | 0.06 | ok |
| `21_Saude_quimioterapia_cancer_colon.xlsx` | 1858 | 16 | 4 | 12 | 0 | 0 | 8 | R1×3, R2×2, R4×1, R6×2 | 0.24 | ok |
| `22_Saude_sobrevida_AIDS_Australia.xlsx` | 2843 | 7 | 3 | 4 | 0 | 0 | 11 | R1×3, R2×3, R4×1, R6×4 | 0.17 | ok |
| `23_Saude_sobrevida_melanoma.xlsx` | 205 | 7 | 3 | 3 | 1 | 0 | 12 | R1×3, R2×3, R4×1, R6×4, R7×1 | 0.04 | ok |
| `24_Acoes_tecnologia_2000-2010.xlsx` | 560 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R2×1, R5×1, R6×1 | 0.03 | ok |
| `25_Carros_a_venda_1993.xlsx` | 93 | 27 | 19 | 6 | 0 | 2 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.08 | ok |
| `26_Carros_desempenho_1970-82.xlsx` | 406 | 9 | 5 | 3 | 1 | 0 | 12 | R1×3, R2×2, R3×1, R4×1, R6×4, R7×1 | 0.07 | ok |
| `27_Cereais_nutricao_EUA.xlsx` | 65 | 11 | 8 | 3 | 0 | 0 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.04 | ok |
| `28_Consumo_combustivel_carros.xlsx` | 234 | 11 | 3 | 7 | 1 | 0 | 12 | R1×3, R2×3, R4×1, R6×4, R7×1 | 0.06 | ok |
| `29_Demografia_meio_oeste_EUA.xlsx` | 437 | 28 | 24 | 4 | 0 | 0 | 12 | R1×3, R2×2, R3×1, R4×2, R6×4 | 0.11 | ok |
| `30_Economia_series_EUA.xlsx` | 478 | 6 | 5 | 0 | 1 | 0 | 6 | R1×3, R4×2, R7×1 | 0.05 | ok |
| `31_Emprego_EUA_por_setor.xlsx` | 120 | 24 | 23 | 0 | 1 | 0 | 6 | R1×3, R4×2, R7×1 | 0.06 | ok |
| `32_Filmes_IMDB.xlsx` | 58788 | 24 | 15 | 8 | 0 | 1 | 12 | R1×3, R2×3, R4×2, R6×4 | 7.34 | ok |
| `33_Geracao_eletrica_Iowa.xlsx` | 51 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R2×1, R5×1, R6×1 | 0.02 | ok |
| `34_Intencao_voto_Chile_1988.xlsx` | 2700 | 8 | 4 | 4 | 0 | 0 | 11 | R1×3, R2×3, R4×1, R6×4 | 0.21 | ok |
| `35_Macroeconomia_EUA_trimestral.xlsx` | 203 | 13 | 12 | 0 | 1 | 0 | 6 | R1×3, R4×2, R7×1 | 0.04 | ok |
| `36_Mortes_motoristas_GB_1969-84.xlsx` | 192 | 2 | 1 | 0 | 1 | 0 | 2 | R1×1, R5×1 | 0.02 | ok |
| `37_Notas_escolas_California.xlsx` | 420 | 17 | 14 | 2 | 0 | 1 | 11 | R1×3, R2×1, R3×1, R4×2, R6×4 | 0.08 | ok |
| `38_Passageiros_Titanic.xlsx` | 1316 | 4 | 0 | 4 | 0 | 0 | 3 | R2×3 | 0.06 | ok |
| `39_Precos_casas_Windsor.xlsx` | 546 | 12 | 2 | 10 | 0 | 0 | 10 | R1×2, R2×3, R4×1, R6×4 | 0.09 | ok |
| `40_Precos_diamantes.xlsx` | 53940 | 10 | 7 | 3 | 0 | 0 | 12 | R1×3, R2×3, R4×2, R6×4 | 3.27 | ok |
| `41_Producao_cevada_Minnesota.xlsx` | 120 | 4 | 1 | 2 | 1 | 0 | 6 | R1×1, R2×2, R5×1, R6×2 | 0.03 | ok |
| `42_Qualidade_do_ar_Nova_York.xlsx` | 153 | 7 | 5 | 1 | 1 | 0 | 9 | R1×3, R2×1, R4×2, R6×2, R7×1 | 0.03 | ok |
| `43_Salarios_professores.xlsx` | 397 | 6 | 3 | 3 | 0 | 0 | 12 | R1×3, R2×3, R4×2, R6×4 | 0.04 | ok |
| `44_Sono_mamiferos.xlsx` | 83 | 11 | 6 | 3 | 0 | 2 | 12 | R1×3, R2×2, R3×1, R4×2, R6×4 | 0.04 | ok |
| `45_Terremotos_Fiji.xlsx` | 1000 | 5 | 5 | 0 | 0 | 0 | 5 | R1×3, R4×2 | 0.05 | ok |
| `46_Trabalho_e_renda_Canada.xlsx` | 7425 | 5 | 3 | 2 | 0 | 0 | 11 | R1×3, R2×2, R4×2, R6×4 | 0.27 | ok |
| `47_Vinhos_analise_quimica.xlsx` | 178 | 14 | 13 | 1 | 0 | 0 | 8 | R1×3, R2×1, R4×2, R6×2 | 0.04 | ok |
