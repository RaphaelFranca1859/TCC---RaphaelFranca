# Prompts de IA usados no projeto

Este documento registra, para transparência e reprodutibilidade, os prompts de inteligência artificial ligados ao DashGen. São dois usos diferentes, que convém não misturar na monografia:

1. **Busca das bases de validação**: prompt escrito pelo autor para pedir a um assistente de IA que localizasse bases públicas.
2. **Assistente de IA do sistema**: prompts internos que o DashGen envia ao modelo de linguagem quando o usuário faz uma pergunta sobre a planilha.

## 1. Prompt da busca das bases de validação

**Ferramenta:** Claude (Anthropic), no aplicativo de desktop, em sessão de 10/11/2026. A sessão estava configurada com o modelo `claude-fable-5-2`.

**Prompt, transcrito como foi digitado:**

> vamos deixar pra outro momento, o que eu preciso agora é que você procure mais base de dados publicos pra que eu possa rodar, pelo menos mais uns 30 e procuro pelo menos 10 desses 30 na area da saude por favor, inclusive o meu professor pediu pra mim adicionar no tcc o prompt que eu criei pra colocar você pra consultar esses dados, faça isso.

**O que a IA fez a partir dele** (para a seção de método):

- Selecionou conjuntos de dados clássicos, publicados e distribuídos com pacotes Python de código aberto (`pydataset`, que reúne os conjuntos de dados do R; `vega_datasets`; `statsmodels`; `scikit-learn`), em vez de baixar arquivos de sites avulsos. Assim, cada base tem identificador e documentação de origem verificáveis.
- Critérios de seleção: não repetir as 9 bases já usadas na calibração; pelo menos 10 da área da saúde; variedade de tamanho (de 51 a 58.788 linhas) e de tipos de coluna (numéricas, categóricas e temporais).
- Resultado: 38 bases, 14 delas da área da saúde, gravadas em `backend/data/validacao/` com o arquivo `FONTES.md`.
- Alterações nos dados: apenas as listadas na coluna "Alterações feitas" do `FONTES.md` (conversão de colunas de tempo em data e nome de classe no lugar de código). Nenhum valor foi inventado ou estimado.
- A geração é reproduzível por `backend/scripts/make_validation_sets.py`; a execução de cada base no sistema, por `backend/scripts/check_validation_sets.py` (resultado em `docs/validacao_novas_bases.md`).

**Versão organizada do mesmo pedido** (opcional, caso o orientador prefira um prompt reproduzível; o conteúdo é o do prompt original, apenas estruturado):

```text
Procure pelo menos 30 bases de dados públicas, diferentes das que já uso no projeto,
para eu executar no meu sistema de geração automática de dashboards.
Requisitos:
- pelo menos 10 das 30 devem ser da área da saúde;
- cada base deve ter fonte identificável e documentada;
- não invente nem estime dados; registre qualquer alteração feita nos arquivos;
- entregue os arquivos em formato de planilha e uma lista com a fonte de cada um.
```

### 1.1 Segundo pedido: bases brasileiras

Feito na mesma sessão, depois do primeiro resultado (que só trouxe bases internacionais).

**Prompt, transcrito como foi digitado:**

> Busque agora bases brasileiras principalmente no DATASUS e IBGE

**O que a IA fez a partir dele:**

- DATASUS: consultou o TabNet (http://tabnet.datasus.gov.br), o mesmo tabulador disponível no navegador, enviando para cada base a linha, a coluna, o conteúdo e os períodos desejados. Sistemas consultados: SIM (mortalidade), SINASC (nascidos vivos), SIH (internações), SINAN (agravos de notificação), CNES (leitos e estabelecimentos) e estimativas populacionais.
- IBGE: consultou a API de dados do SIDRA (https://apisidra.ibge.gov.br), com tabelas de população, Censo 2022, PIB, PNAD Contínua, pesquisas agropecuárias, pesquisas mensais de indústria, serviços e comércio e Registro Civil.
- Resultado: 38 bases (21 do DATASUS e 17 do IBGE), gravadas em `backend/data/brasil/` com o arquivo `FONTES.md`, que registra a consulta exata de cada uma e a data de acesso.
- Transformações: remoção de totais (que são somas das demais linhas), passagem para formato longo, conversão de períodos em data e aplicação da convenção de sinais das fontes ("-" é zero; "...", ".." e "X" ficam vazios). Nenhum valor foi inventado ou estimado.
- Reprodução: `backend/scripts/make_brazil_sets.py`. Como as fontes são atualizadas continuamente, uma nova execução pode devolver valores diferentes, sobretudo nos anos recentes do DATASUS, que são preliminares.

## 2. Prompts internos do assistente de IA do DashGen

Estes textos estão em `backend/app/assistant.py` e são enviados ao modelo de linguagem (Groq ou xAI) a cada pergunta. Foram redigidos com apoio de IA durante o desenvolvimento e ficam sob revisão do autor. Os trechos entre chaves são preenchidos pelo sistema em tempo de execução.

### 2.1 Prompt de sistema (primeira etapa: planejar a consulta)

O modelo recebe este texto, o histórico recente da conversa e a pergunta do usuário. `{schema}` é o resumo das colunas (nome, tipo e estatísticas), nunca as linhas da planilha.

```text
Você é o assistente de análise do DashGen. O usuário enviou uma planilha e faz perguntas sobre ela em português.
Você NÃO vê as linhas da planilha: conhece apenas o esquema abaixo. Para obter números, peça uma consulta; o sistema executa e devolve o resultado.

Responda SEMPRE com um único objeto JSON, sem texto fora dele, em um destes formatos:
1) {"action": "query", "query": {"group_by": [até 2 colunas], "period": "year|month|day", "metric": "coluna ou null", "op": "sum|mean|median|min|max|count|nunique", "filters": [...], "sort": "desc|asc|label", "limit": 1 a 50}}
2) {"action": "answer", "answer": "texto em português"}

Regras:
- Use exatamente os nomes de coluna do esquema. "period" só vale para colunas temporais em group_by.
- "op": "count" sem "metric" conta registros. Para total geral, deixe group_by vazio.
- Filtros: categórica {"column": c, "values": [..]}; numérica {"column": c, "min": n, "max": n}; temporal {"column": c, "start": "AAAA-MM-DD", "end": "AAAA-MM-DD"}.
- Use "answer" direto só quando o esquema já responde (ex.: quais colunas existem) ou quando a pergunta não puder ser respondida com esses dados; nesse caso, explique o motivo e sugira uma pergunta possível.
- Nunca invente números.

Esquema da planilha "{filename}" ({rows} registros considerados{filter_note}):
{schema}
```

### 2.2 Prompt da segunda etapa (redigir a resposta)

Enviado depois que o sistema executa a consulta em Pandas. `{table}` é o resultado agregado.

```text
Resultado da consulta (calculado pelo sistema sobre {n} registros):
{table}

Agora responda à pergunta do usuário em português, em até 5 frases, citando os números do resultado. Não invente valores que não estejam no resultado. Se houver uma limitação relevante (dados truncados, poucos registros), diga. Responda em texto simples, sem JSON e sem tabelas.
```

### 2.3 Parâmetros

- Temperatura: 0,1.
- Modo JSON na primeira etapa, quando o modelo aceita.
- Histórico: até 6 mensagens anteriores; pergunta com até 1000 caracteres; resultado com até 50 linhas.
- Modelos padrão: `openai/gpt-oss-120b` (Groq) e `grok-4.3` (xAI).
