# Calibração dos limiares e regras (demonstração)

Cada mudança abaixo veio de um problema observado ao rodar o sistema nos datasets reais. Comparação antes e depois em `docs/estudos_de_caso.json`.

| # | Problema observado | Dataset | Ajuste | Onde |
|---|---|---|---|---|
| 1 | Coluna inteira "year" inferida como temporal mas mantida como número, o que quebrava o dashboard (erro interno) | Gapminder, Passageiros aéreos | Anos inteiros passam a ser convertidos para data (1º de janeiro) | `inference.py`, `apply_overrides` |
| 2 | Séries com 4 a 10 anos de dados mensais ou diários viravam 4 a 10 pontos anuais | IPCA, Selic, Seattle, Superstore | Novo parâmetro `max_monthly_points = 120`: a série fica mensal até 120 meses; antes o corte era 3 anos | `heuristics.py`, `_grain` |
| 3 | Taxas, temperaturas e indicadores per capita eram somados | IPCA, Selic, Seattle, Gapminder | Dicionário de nomes da agregação automática ampliado (pct, temp, wind, percap, cotação, câmbio, juros, expectativa de vida, entre outros) e separação de camelCase ("lifeExp") | `heuristics.py`, `resolve_agg` |
| 4 | Códigos numéricos (CEP, código ISO) eram tratados como medidas e somados | Superstore, Gapminder | Colunas inteiras com nome de código (postal, zip, cep, code, código, iso, telefone) passam a "ignorada" | `inference.py`, `_CODE_HINT` |
| 5 | KPI "Soma de" exibido para taxas | Gapminder | O KPI de soma só aparece para colunas somáveis | `heuristics.py`, `_kpis` |

**Riscos que você deve mencionar ao orientador.**
- Os ajustes 3 e 4 foram feitos olhando os próprios datasets da demonstração. Isso pode ser sobreajuste: para validar, rode datasets novos que não participaram da calibração.
- São heurísticas por nome de coluna (em português e inglês). Colunas com nomes opacos (ex.: "V1") não são cobertas, e o usuário continua podendo ajustar a agregação e os tipos.
- Falhas ainda abertas: soma de séries acumuladas (COVID), câmbio sem palavra-chave no nome (Dólar), mês em texto separado do ano (Passageiros) e escolha de categóricas por ordem de coluna (Superstore).
