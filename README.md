# DashGen

Sistema web de código aberto que gera dashboards interativos a partir de planilhas Excel e CSV, voltado a usuários sem conhecimento técnico em análise de dados. Implementação do TCC "Desenvolvimento de um Sistema Web para Geração Automatizada de Dashboards Interativos a partir de Planilhas Eletrônicas" (IFBA, Campus Vitória da Conquista).

A contribuição científica é o **motor heurístico de seleção de gráficos** (`backend/app/heuristics.py`), que implementa as sete regras do Quadro 5 da monografia, cada uma com fundamentação bibliográfica e registro de decisão.

## Arquitetura (quatro camadas, Figura 1 da monografia)

| Camada | Tecnologia | Onde |
|---|---|---|
| Apresentação | React, Chart.js | `frontend/` |
| Aplicação | Flask, API REST em JSON | `backend/app/api.py`, `backend/app/__init__.py` |
| Processamento | Python, Pandas | `ingestion.py`, `inference.py`, `heuristics.py` |
| Persistência | MongoDB (opcional) ou arquivos JSON | `backend/app/store.py` |

Fluxo das três telas (Figura 3): **1. Enviar planilha**, **2. Revisar tipos**, **3. Dashboard** (filtros, ordenação, agregação, exportação de PNG e CSV, salvar configuração).

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

**MongoDB (opcional).** Defina `MONGO_URI` (por exemplo `mongodb://localhost:27017`). Sem a variável, ou se o servidor estiver inacessível, as configurações são gravadas em `backend/data/configs/*.json`. O endpoint `GET /api/health` informa qual armazenamento está ativo.

## Testes e análises da monografia

```bash
cd backend
python -m pytest tests -q                       # testes funcionais (seção 4.2.5)
python scripts/benchmark.py --runs 5 --out data/benchmark.json   # desempenho: 1 mil, 10 mil e 100 mil linhas
python scripts/benchmark.py --excel             # inclui arquivos .xlsx (mais lento)
python scripts/make_synthetic.py                # conjuntos sintéticos de casos-limite (seção 4.2.4)
```

Teste de ponta a ponta no navegador (Playwright), com o servidor ativo e o frontend compilado, a partir da raiz do projeto:

```bash
pip install playwright && python -m playwright install chromium
python e2e/run_e2e.py
```

## API

| Método e rota | Função (caso de uso da Figura 2) |
|---|---|
| `POST /api/upload` | Enviar planilha: devolve sessão, tipos inferidos, prévia e opções de filtro |
| `PUT /api/sessions/<id>/types` | Ajustar tipos de coluna |
| `POST /api/sessions/<id>/dashboard` | Gerar dashboard (`filters`, `agg`, `sort`) |
| `POST /api/sessions/<id>/export` | Exportar CSV filtrado |
| `POST /api/sessions/<id>/config` | Salvar configuração (nunca o conteúdo da planilha) |
| `POST /api/sessions/<id>/apply-config` | Reaplicar configuração a outra planilha |
| `GET /api/configs`, `GET /api/configs/<id>` | Listar e ler configurações |
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
3. **Linhas múltiplas (R7) com escalas muito diferentes.** O gráfico exibe um aviso quando a razão entre magnitudes passa de 10, mas não normaliza as séries. Alternativas: eixo secundário ou índice base 100.
4. **Ambiguidade numérica.** Um valor como `1.234` em coluna sem outras pistas é lido como decimal (1,234). Colunas com formato brasileiro explícito (`1.234,56`) são tratadas corretamente.
5. **Ordem de datas ambíguas.** Datas como `01/02/2024` são lidas como dia/mês (convenção brasileira) quando nenhum valor da coluna a contradiz.
6. **Excel.** Lê a primeira aba não vazia. A escolha de aba existe na API (`sheet`), mas ainda não na interface.
7. **Escala.** Sessões em memória exigem um único processo (ver Produção). Para escalar, seria necessário armazenamento externo de sessões ou afinidade de sessão.
8. **Sem autenticação.** Adequado ao escopo da pesquisa; qualquer implantação pública exige HTTPS e, idealmente, limite de requisições.
