"""E2E dos recursos novos: seletor de aba do Excel, escala das series (R7) e persistencia no MongoDB.
Requer servidor em http://localhost:5000 com frontend compilado.  Uso: python e2e/run_e2e_novos.py"""
import os, sys, json, io
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
sys.path.insert(0, "backend")
import pandas as pd, numpy as np
from playwright.sync_api import sync_playwright

os.makedirs("e2e/shots", exist_ok=True)
rng = np.random.default_rng(1)
datas = pd.date_range("2024-01-01", periods=240)
vendas = pd.DataFrame({"Data": datas, "Faturamento": rng.normal(2e6, 2e5, 240).round(2), "Clientes": rng.normal(120, 12, 240).round(0)})
estoque = pd.DataFrame({"Produto": list("ABCABC"), "Qtd": [10, 20, 30, 15, 25, 35]})
with pd.ExcelWriter("/tmp/duas_abas.xlsx") as xw:
    vendas.to_excel(xw, index=False, sheet_name="Vendas"); estoque.to_excel(xw, index=False, sheet_name="Estoque")

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: errors.append(("console", m.type, m.text)) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errors.append(("pageerror", str(e))))
    pg.on("response", lambda r: errors.append(("http", r.status, r.url)) if r.status >= 400 else None)
    pg.goto("http://localhost:5000/")
    pg.set_input_files("input[type=file]", "/tmp/duas_abas.xlsx"); pg.wait_for_selector("table.types")
    print("seletor de aba visivel:", pg.locator("select[aria-label='Aba da planilha Excel']").count() == 1)
    print("colunas aba Vendas:", pg.locator("table.types tbody tr").count())
    pg.select_option("select[aria-label='Aba da planilha Excel']", "Estoque"); pg.wait_for_selector("text=Aba “Estoque” carregada")
    print("colunas aba Estoque:", pg.locator("table.types tbody tr").count(), "|", pg.locator(".card p.muted").first.inner_text()[:90])
    pg.screenshot(path="e2e/shots/7_aba_estoque.png", full_page=True)
    pg.select_option("select[aria-label='Aba da planilha Excel']", "Vendas"); pg.wait_for_selector("text=Aba “Vendas” carregada")
    pg.click("text=Gerar dashboard"); pg.wait_for_selector(".chart-card canvas"); pg.wait_for_timeout(800)
    print("aviso de escala:", pg.locator(".chart-warning:has-text('escalas')").count())
    pg.screenshot(path="e2e/shots/8_r7_original.png", full_page=True)
    for lab, shot in [("index100", "9_r7_indice100"), ("secondary", "10_r7_secundario")]:
        pg.select_option("label:has-text('Escala das séries') select", lab); pg.wait_for_timeout(900)
        print(lab, "-> aviso de escala:", pg.locator(".chart-warning:has-text('escalas')").count())
        pg.locator(".chart-card.wide").first.screenshot(path=f"e2e/shots/{shot}.png")
    pg.click("button:has-text('Salvar configuração')"); pg.fill("input[aria-label='Nome da configuração']", "R7 eixo secundario")
    pg.click("button:has-text('Salvar'):not(:has-text('configuração'))"); pg.wait_for_selector("text=salva.")
    print("config salva:", pg.locator(".alert.ok").first.inner_text())
    b.close()
print("ERROS:", json.dumps(errors, ensure_ascii=False) if errors else "nenhum")
