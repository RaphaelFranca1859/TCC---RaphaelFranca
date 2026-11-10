# Desempenho (insumo da seção 4.2.5)

**Status: medição preliminar feita em ambiente de teste, não no notebook descrito na seção 4.1.** Eu não tenho acesso ao seu notebook; para a monografia, rode o comando abaixo nele e substitua a tabela.

```bash
cd backend
pip install psutil   # opcional, só para registrar a memória RAM
python scripts/benchmark.py --runs 5 --excel --out data/benchmark_notebook.json
```

Ambiente desta medição preliminar: Python 3.12.3, Intel Xeon a 2,1 GHz, 1 núcleo, 3,9 GB de RAM, Linux em container. Cada tempo é a mediana de 5 execuções (3 para 100 mil linhas). Dados sintéticos de vendas (`app/synthetic.py`).

| Linhas | Formato | Tamanho (KB) | Ingestão (s) | Inferência (s) | Dashboard (s) | Com filtro (s) | Total (s) |
|---:|:---:|---:|---:|---:|---:|---:|---:|
| 1.000 | csv | 53 | 0,0416 | 0,0022 | 0,031 | 0,0252 | 0,0748 |
| 1.000 | xlsx | 44 | 0,1124 | 0,0033 | 0,0348 | 0,0273 | 0,1505 |
| 10.000 | csv | 528 | 0,095 | 0,0038 | 0,0788 | 0,056 | 0,1775 |
| 10.000 | xlsx | 381 | 0,7287 | 0,0041 | 0,077 | 0,0533 | 0,8099 |
| 100.000 | csv | 5.284 | 0,7341 | 0,0174 | 0,4803 | 0,2375 | 1,2318 |
| 100.000 | xlsx | 3.728 | 7,4894 | 0,0169 | 0,4773 | 0,2592 | 7,9836 |

**Leitura dos números desta medição preliminar:**
- A ingestão domina o tempo total, principalmente em Excel: com 100 mil linhas, ler o .xlsx leva 7,49 s contra 0,73 s do CSV equivalente.
- A inferência de tipos é desprezível (menos de 0,02 s em todos os tamanhos).
- Gerar o dashboard com 100 mil linhas leva cerca de 0,48 s, e refazê-lo com filtro, cerca de 0,26 s.
- No estudo de caso Superstore (10.800 linhas em .xlsx, dados reais), do arquivo ao dashboard foram 1,84 s, na mesma máquina.

**Limitações a declarar no texto:** uma única máquina com 1 núcleo, dados sintéticos, sem medição de uso de memória nem de usuários simultâneos.
