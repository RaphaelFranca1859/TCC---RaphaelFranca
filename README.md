# DashGen

Sistema web de código aberto que gera dashboards interativos a partir de planilhas Excel e CSV, voltado a usuários sem conhecimento técnico em análise de dados. Implementação do TCC "Desenvolvimento de um Sistema Web para Geração Automatizada de Dashboards Interativos a partir de Planilhas Eletrônicas" (IFBA, Campus Vitória da Conquista).

A contribuição científica é o **motor heurístico de seleção de gráficos** (`backend/app/heuristics.py`), que implementa as sete regras do Quadro 5 da monografia, cada uma com fundamentação bibliográfica e registro de decisão.

## Arquitetura (quatro camadas, Figura 1 da monografia)

| Camada | Tecnologia | Onde |
|---|---|---|
| Apresentação | React, Chart.js | `frontend/` |
| (complementar) Assistente de IA | API de chat do Groq ou da xAI | `backend/app/assistant.py` |
| Aplicação | Flask, API REST em JSON | `backend/app/api.py`, `backend/app/__init__.py` |
| Processamento | Python, Pandas | `ingestion.py`, `inference.py`, `heuristics.py` |
| Persistência | MongoDB (opcional) ou arquivos JSON | `backend/app/store.py` |

Fluxo das três telas (Figura 3): **1. Enviar planilha**, **2. Revisar tipos**, **3. Dashboard** (filtros, ordenação, agregação, exportação de PNG e CSV, salvar configuração).

## Interface

- **Menu lateral recolhível.** O botão de três barras no topo abre e fecha o menu, que reúne as etapas, as ferramentas e, na tela do dashboard, os filtros. No computador o menu empurra o conteúdo e a escolha (aberto ou fechado) é lembrada; no celular ele vira uma gaveta sobreposta, que fecha ao tocar fora ou com Esc. Com o menu fechado, um selo no botão mostra quantos filtros estão ativos.
- **Cores dos botões.** Verde para aceitar, avançar e salvar; vermelho para cancelar, voltar, fechar e descartar; azul-índigo para ações neutras (exportar, abrir painel). Todo botão tem preenchimento próprio, visível sem passar o mouse, e leva um ícone ou seta além da cor, para que a cor não seja a única pista (daltonismo).
- **Identidade visual.** O logo é um quadrado de planilha (grade) com três barras ascendentes, em índigo e verde, desenhado em SVG (`frontend/public/favicon.svg`, usado como ícone da aba, e `frontend/src/components/Logo.jsx`, usado no cabeçalho). Por ser vetorial, fica nítido em qualquer tamanho e funciona nos dois temas.
- **Tema claro e escuro.** Alternado no topo ou no menu; segue a preferência do sistema na primeira visita.
- **Paleta dos gráficos.** Oito matizes em ordem fixa, ajustados para cada tema. Gráficos de série única recebem um matiz por gráfico; gráficos de setores e de linhas múltiplas usam um matiz por categoria ou série.
- **Assistente de IA.** Painel lateral de perguntas em linguagem natural (ver seção própria).

## Como executar

Requisitos: Python 3.12 e Node 20 ou superior.

```bash
# 1. Backend
cd backend
pip install -r requirements-dev.txt

# 2. Frontend (compila para frontend/dist, que o Flask passa a servir)
cd ../frontend
npm install
npm run build

# 3. Servidor de desenvolvimento
cd ../backend
flask --app app:create_app run --port 5000      # abrir http://localhost:5000
```

Desenvolvimento com recarga automática da interface: `npm run dev` em `frontend/` (porta 5173, com proxy para o Flask na 5000).

**Produção.** Use **um único worker com threads**, porque as sessões ficam na memória do processo:

```bash
gunicorn --chdir backend -b 0.0.0.0:8000 -w 1 --threads 8 wsgi:app
```

Com vários workers, o upload e o dashboard podem cair em processos diferentes e a sessão "some" (verificado: 4 de 8 requisições retornaram 404 com 2 workers).

**MongoDB (opcional).** Defina `MONGO_URI` (por exemplo `mongodb://localhost:27017`). Sem a variável, ou se o servidor estiver inacessível, as configurações são gravadas em `backend/data/configs/*.json`. O endpoint `GET /api/health` informa qual armazenamento está ativo (`config_backend`).

**Docker com MongoDB real.** Um comando sobe a aplicação e o MongoDB 7:

```bash
docker compose up --build        # abrir http://localhost:8000
curl localhost:8000/api/health   # deve informar "config_backend":"MongoDB"
```

O `Dockerfile` compila o frontend e roda o gunicorn com 1 worker e 8 threads, na porta `$PORT` (8000 se não definida). As configurações ficam no volume `mongo_data`. Os arquivos Docker ainda não foram executados por quem os escreveu (não havia Docker no ambiente de desenvolvimento): o que foi testado contra um MongoDB 7.0.14 real, sem Docker, foi a persistência (teste `test_config_store_mongodb_real` e fluxo completo no navegador).

Teste contra um MongoDB real: `MONGO_TEST_URI=mongodb://localhost:27017 python -m pytest tests -q`.

## Testes e análises da monografia

```bash
cd backend
python -m pytest tests -q                       # testes funcionais (seção 4.2.5)
python scripts/benchmark.py --runs 5 --out data/benchmark.json   # desempenho: 1 mil, 10 mil e 100 mil linhas
python scripts/benchmark.py --excel             # inclui arquivos .xlsx (mais lento)
python scripts/case_studies.py data/real data/synthetic --out ../docs/estudos_de_caso   # estudos de caso (4.2.4)
python scripts/make_synthetic.py                # conjuntos sintéticos de casos-limite (seção 4.2.4)
```

Teste de ponta a ponta no navegador (Playwright), com o servidor ativo e o frontend compilado, a partir da raiz do projeto:

```bash
pip install playwright && python -m playwright install chromium
python e2e/run_e2e.py
python e2e/run_e2e_novos.py            # seletor de aba, escala do R7 e persistência
python e2e/run_e2e_interface.py        # menu recolhível, tema escuro, cores dos botões e assistente de IA
python e2e/capturas_estudos_de_caso.py # capturas dos dashboards dos datasets reais
```

Documentos para a monografia: `docs/estudos_de_caso_4_2_4.md`, `docs/desempenho_4_2_5.md` e `docs/calibracao.md`. Os datasets reais (com fontes) estão em `backend/data/real/`.

## Assistente de IA (recurso complementar)

Fora do escopo do Quadro 5 e do motor heurístico: é um recurso de apoio, não a contribuição da monografia.

**Como funciona.** O modelo de linguagem não recebe a planilha nem executa código. (1) Ele recebe o esquema das colunas (nomes, tipos, estatísticas resumidas) e a pergunta, e devolve em JSON uma consulta de agregação (agrupar, agregar, filtrar, ordenar). (2) O backend valida e executa a consulta em Pandas e devolve o resultado ao modelo, que redige a resposta. A tabela usada aparece junto da resposta ("Dados usados na resposta"), então os números vêm sempre do Pandas. O assistente respeita os filtros ativos no dashboard.

**Provedores.** Qualquer um dos dois, pela API de chat compatível com a da OpenAI:

| Provedor | `LLM_PROVIDER` | Custo | Onde criar a chave |
|---|---|---|---|
| Groq | `groq` (padrão) | tem plano gratuito, com limites de requisições | console.groq.com/keys |
| xAI (Grok) | `xai` | pago por uso (a documentação não lista plano gratuito) | console.x.ai |

Atenção aos nomes: **Groq** (empresa de inferência, com plano gratuito) e **Grok** (modelo da xAI, pago) são coisas diferentes.

**Chave.** Duas formas: (a) o usuário cola a própria chave em "Chave e modelo" no painel (fica só no navegador dele e segue no cabeçalho `X-LLM-Key` a cada pergunta; o servidor não grava); (b) o servidor define `LLM_API_KEY` (e opcionalmente `LLM_PROVIDER`, `LLM_MODEL`), e todos os visitantes usam essa chave. Na opção (b), em um site público, qualquer visitante consome a sua cota.

**Privacidade.** São enviados ao provedor: nomes das colunas, estatísticas resumidas, até 8 valores mais frequentes de cada coluna categórica e os resultados agregados das consultas. As linhas da planilha não são enviadas. Isso muda a decisão de projeto 1 (dados só em memória) apenas para quem usa o assistente, e a interface avisa.

**Limitações.** Só consultas de agregação com até 2 colunas de agrupamento e 50 linhas de resultado; sem cálculos encadeados (ex.: variação percentual entre períodos); a redação final é do modelo e pode conter erros de interpretação; os nomes dos modelos padrão (`backend/app/assistant.py`) mudam com o tempo e podem precisar de atualização. O assistente foi testado com um modelo simulado (`tests/test_assistant.py` e `e2e/run_e2e_interface.py`); **não foi testado contra a API real do Groq nem da xAI por quem o escreveu**.

## Publicação gratuita

O backend guarda as sessões na memória de um único processo e aceita envios de até 20 MB. Por isso precisa de uma hospedagem que mantenha um processo vivo (contêiner), e não de funções serverless.

**Render (recomendado).** O repositório traz `render.yaml` e o `Dockerfile` já usa a porta `$PORT`.

1. Suba o projeto para um repositório no GitHub.
2. Em render.com: New > Blueprint > selecione o repositório (ou New > Web Service, runtime Docker, plano Free).
3. Opcional: preencha `LLM_API_KEY` e `MONGO_URI` nas variáveis de ambiente.
4. Ao final do build, o endereço `https://<nome>.onrender.com` abre o sistema.

Limites do plano gratuito do Render (documentação oficial): o serviço é suspenso após 15 minutos sem acesso e leva cerca de 1 minuto para voltar; 750 horas por mês; o disco é efêmero. Consequências aqui: a primeira visita depois de um período parado é lenta, as sessões em memória somem quando o serviço dorme, e as configurações salvas em arquivo JSON se perdem a cada reinício. Para manter as configurações, use `MONGO_URI` com um MongoDB externo (ex.: Atlas M0).

**Vercel.** Não serve para o backend como ele está: as funções têm limite de 4,5 MB por requisição (o sistema aceita planilhas de 20 MB) e não há garantia de que upload e dashboard caiam no mesmo processo, o que quebra as sessões em memória. Dá para usar a Vercel só para o frontend estático (`frontend/`, com `VITE_API_URL=https://<nome>.onrender.com` no build) e deixar a API no Render; o ganho é pequeno, porque o backend continua dormindo no plano gratuito.

## API

| Método e rota | Função (caso de uso da Figura 2) |
|---|---|
| `POST /api/upload` | Enviar planilha: devolve sessão, tipos inferidos, prévia e opções de filtro |
| `PUT /api/sessions/<id>/types` | Ajustar tipos de coluna |
| `POST /api/sessions/<id>/sheet` | Trocar a aba lida de um Excel com várias abas |
| `POST /api/sessions/<id>/dashboard` | Gerar dashboard (`filters`, `agg`, `sort`, `scale`) |
| `POST /api/sessions/<id>/export` | Exportar CSV filtrado |
| `POST /api/sessions/<id>/config` | Salvar configuração (nunca o conteúdo da planilha) |
| `POST /api/sessions/<id>/apply-config` | Reaplicar configuração a outra planilha |
| `GET /api/configs`, `GET /api/configs/<id>` | Listar e ler configurações |
| `GET /api/assistant/status` | Provedores disponíveis e se o servidor tem chave própria (a chave nunca é exposta) |
| `POST /api/sessions/<id>/assistant` | Pergunta em linguagem natural (`question`, `history`, `filters`; chave opcional em `X-LLM-Key`) |
| `GET /api/rules` | Regras R1 a R7 e limiares vigentes (auditabilidade) |
| `GET /api/health` | Estado do serviço |

## Regras heurísticas (Quadro 5)

| Regra | Combinação | Gráfico |
|---|---|---|
| R1 | 1 numérica contínua | Histograma |
| R2 | 1 categórica (≤ 10 categorias) | Barras (padrão) ou setores |
| R3 | 1 categórica (> 10 categorias) | Barras horizontais ordenadas |
| R4 | 2 numéricas | Dispersão |
| R5 | 1 numérica × 1 temporal | Linha |
| R6 | 1 numérica × 1 categórica | Barras agrupadas |
| R7 | 1 temporal + 2 ou mais numéricas | Linhas múltiplas |

Todos os limiares (limite de 10 categorias, top 15, correlação mínima, limiares da inferência de tipos) ficam em `HeuristicConfig` e `InferenceConfig`, para serem calibrados na etapa de demonstração.

## Decisões de projeto e limitações conhecidas

1. **Dados só em memória.** O conteúdo das planilhas nunca é persistido; sessões expiram em 2 horas (`SESSION_TTL`) e há teto de 50 sessões simultâneas.
2. **Agregação automática.** Fora do Quadro 5. No modo "Automática" (padrão), colunas cujo nome sugere valor unitário ou taxa (preço, taxa, nota, idade, desconto...) usam média; as demais usam soma. O usuário pode forçar soma, média ou mediana. A decisão aparece no registro de decisões. **Ponto a discutir com o orientador.**
3. **Linhas múltiplas (R7) com escalas muito diferentes.** Quando a razão entre magnitudes passa de 10, o gráfico avisa. O usuário escolhe na barra de ferramentas entre valores originais (padrão), índice base 100 (cada série dividida pelo seu primeiro valor não nulo) ou eixo secundário (séries de menor magnitude à direita). O padrão continua "original" para não alterar silenciosamente os dados.
4. **Ambiguidade numérica.** Um valor como `1.234` em coluna sem outras pistas é lido como decimal (1,234). Colunas com formato brasileiro explícito (`1.234,56`) são tratadas corretamente.
5. **Ordem de datas ambíguas.** Datas como `01/02/2024` são lidas como dia/mês (convenção brasileira) quando nenhum valor da coluna a contradiz.
6. **Excel.** Lê a primeira aba não vazia e, se houver mais de uma aba, a interface mostra um seletor na tela de tipos. Trocar de aba descarta os ajustes de tipo feitos na aba anterior. O arquivo original fica em memória só para planilhas com mais de uma aba.
7. **Escala.** Sessões em memória exigem um único processo (ver Produção). Para escalar, seria necessário armazenamento externo de sessões ou afinidade de sessão.
8. **Sem autenticação.** Adequado ao escopo da pesquisa; qualquer implantação pública exige HTTPS e, idealmente, limite de requisições.
9. **Limitações observadas nos dados reais** (detalhes em `docs/calibracao.md`): séries acumuladas são somadas, a agregação automática depende do nome da coluna, o mês em texto não é combinado com o ano e a escolha das categóricas segue a ordem das colunas.
