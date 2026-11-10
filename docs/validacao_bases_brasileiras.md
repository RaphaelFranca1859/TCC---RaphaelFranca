# Execução do sistema nas bases de data/brasil

Gerado por `backend/scripts/check_validation_sets.py`. Cada base passou por leitura, inferência de tipos e motor de gráficos, com as opções padrão e sem ajuste manual de tipos. A tabela registra apenas o que o sistema fez; se os tipos e os gráficos escolhidos são adequados a cada base é uma avaliação que ainda precisa ser feita, base a base. Os tempos são de uma única execução no ambiente de desenvolvimento e não substituem o benchmark da seção 4.2.5.

Bases executadas: 38. Falhas: 0.

| Arquivo | Linhas | Colunas | Numéricas | Categóricas | Temporais | Ignoradas | Gráficos | Regras disparadas | Tempo (s) | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| `50_Saude_obitos_por_UF_e_ano.xlsx` | 837 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.12 | ok |
| `51_Saude_obitos_por_capitulo_CID10_e_ano.xlsx` | 620 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `52_Saude_obitos_por_faixa_etaria_e_sexo_2023.xlsx` | 39 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R2×1, R3×1, R6×2 | 0.02 | ok |
| `53_Saude_obitos_infantis_por_UF_e_ano.xlsx` | 837 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.04 | ok |
| `54_Saude_obitos_causas_externas_por_grupo_e_ano.xlsx` | 248 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R2×1, R4×1, R6×2 | 0.02 | ok |
| `55_Saude_obitos_maternos_por_UF_e_ano.xlsx` | 837 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.04 | ok |
| `56_Saude_nascidos_vivos_por_UF_e_ano.xlsx` | 891 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.04 | ok |
| `57_Saude_nascidos_vivos_idade_mae_e_gestacao_2023.xlsx` | 98 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R2×1, R3×1, R6×2 | 0.02 | ok |
| `58_Saude_internacoes_SUS_por_mes_e_regiao.xlsx` | 300 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R2×1, R5×1, R6×1 | 0.03 | ok |
| `59_Saude_internacoes_SUS_por_UF_e_capitulo_CID10.xlsx` | 540 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R3×2, R6×2 | 0.03 | ok |
| `60_Saude_dengue_casos_por_UF_e_ano.xlsx` | 392 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `61_Saude_dengue_casos_por_mes_e_ano.xlsx` | 168 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.02 | ok |
| `62_Saude_chikungunya_casos_por_UF_e_ano.xlsx` | 351 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `63_Saude_tuberculose_casos_por_UF_e_ano.xlsx` | 700 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `64_Saude_hanseniase_casos_por_UF_e_ano.xlsx` | 1404 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.08 | ok |
| `65_Saude_malaria_casos_por_UF_e_ano.xlsx` | 360 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `66_Saude_animais_peconhentos_por_UF_e_ano.xlsx` | 1323 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.05 | ok |
| `67_Saude_sifilis_gestante_por_UF_e_ano.xlsx` | 513 | 3 | 2 | 1 | 0 | 0 | 6 | R1×2, R3×1, R4×1, R6×2 | 0.03 | ok |
| `68_Saude_leitos_internacao_por_UF_e_esfera.xlsx` | 189 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R2×1, R3×1, R6×2 | 0.02 | ok |
| `69_Saude_estabelecimentos_por_UF_e_tipo.xlsx` | 1026 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R3×2, R6×2 | 0.04 | ok |
| `70_Saude_populacao_por_faixa_etaria_e_sexo_2021.xlsx` | 22 | 3 | 1 | 2 | 0 | 0 | 5 | R1×1, R2×1, R3×1, R6×2 | 0.02 | ok |
| `71_Populacao_estimada_por_UF_e_ano.xlsx` | 594 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R3×1, R5×1, R6×1 | 0.03 | ok |
| `72_PIB_e_valor_adicionado_por_UF_e_ano.xlsx` | 594 | 7 | 5 | 1 | 1 | 0 | 9 | R1×3, R3×1, R4×2, R6×2, R7×1 | 0.06 | ok |
| `73_PIB_Brasil_serie_anual.xlsx` | 29 | 9 | 8 | 0 | 1 | 0 | 6 | R1×3, R4×2, R7×1 | 0.03 | ok |
| `74_Taxa_desocupacao_por_UF_e_trimestre.xlsx` | 1566 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R3×1, R5×1, R6×1 | 0.06 | ok |
| `75_Rendimento_medio_por_sexo_e_trimestre.xlsx` | 100 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R2×1, R5×1, R6×1 | 0.02 | ok |
| `76_Censo2022_populacao_area_densidade_municipios.xlsx` | 5570 | 5 | 3 | 1 | 0 | 1 | 7 | R1×3, R3×1, R4×1, R6×2 | 0.25 | ok |
| `77_Censo2022_populacao_por_sexo_idade_e_UF.xlsx` | 1134 | 4 | 1 | 3 | 0 | 0 | 6 | R1×1, R2×1, R3×2, R6×2 | 0.06 | ok |
| `78_Censo_populacao_por_cor_ou_raca_e_UF.xlsx` | 270 | 4 | 1 | 2 | 1 | 0 | 6 | R1×1, R2×1, R3×1, R5×1, R6×2 | 0.03 | ok |
| `79_Producao_agricola_por_produto_e_ano.xlsx` | 850 | 4 | 2 | 1 | 1 | 0 | 7 | R1×2, R3×1, R4×1, R6×2, R7×1 | 0.05 | ok |
| `80_Rebanhos_por_tipo_UF_e_ano.xlsx` | 2700 | 4 | 1 | 2 | 1 | 0 | 6 | R1×1, R2×1, R3×1, R5×1, R6×2 | 0.11 | ok |
| `81_Producao_origem_animal_valor_por_UF_e_ano.xlsx` | 1620 | 4 | 1 | 2 | 1 | 0 | 6 | R1×1, R2×1, R3×1, R5×1, R6×2 | 0.07 | ok |
| `82_Producao_industrial_mensal_Brasil.xlsx` | 3240 | 8 | 6 | 1 | 1 | 0 | 9 | R1×3, R3×1, R4×2, R6×2, R7×1 | 0.20 | ok |
| `83_Volume_servicos_mensal_Brasil.xlsx` | 376 | 8 | 6 | 1 | 1 | 0 | 9 | R1×3, R2×1, R4×2, R6×2, R7×1 | 0.05 | ok |
| `84_Vendas_comercio_mensal_Brasil.xlsx` | 568 | 8 | 6 | 1 | 1 | 0 | 9 | R1×3, R2×1, R4×2, R6×2, R7×1 | 0.06 | ok |
| `85_Registro_civil_nascidos_vivos_por_UF_e_ano.xlsx` | 270 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R3×1, R5×1, R6×1 | 0.02 | ok |
| `86_Registro_civil_obitos_por_UF_e_ano.xlsx` | 270 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R3×1, R5×1, R6×1 | 0.02 | ok |
| `87_Registro_civil_casamentos_por_UF_e_ano.xlsx` | 270 | 3 | 1 | 1 | 1 | 0 | 4 | R1×1, R3×1, R5×1, R6×1 | 0.03 | ok |
