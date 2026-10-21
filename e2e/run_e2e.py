"""Teste de ponta a ponta no navegador (Playwright). Requer o servidor em http://localhost:5000 com o frontend compilado.
Uso, a partir da raiz do projeto:  python e2e/run_e2e.py"""
import os, sys, json
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: errors.append(("console", m.type, m.text)) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errors.append(("pageerror", str(e))))
    pg.on("response", lambda r: errors.append(("http", r.status, r.url)) if r.status >= 400 else None)

    pg.goto("http://localhost:5000/")
    pg.screenshot(path="e2e/shots/1_upload.png")

    pg.set_input_files("input[type=file]", "backend/data/synthetic/01_vendas_completo.xlsx")
    pg.wait_for_selector("table.types")
    pg.screenshot(path="e2e/shots/2_tipos.png", full_page=True)

    # ajusta um tipo e confere que a interface reflete
    pg.select_option("select[aria-label='Tipo da coluna Quantidade']", "categorical")
    pg.wait_for_selector("select.changed")
    print("tipo ajustado ->", pg.input_value("select[aria-label='Tipo da coluna Quantidade']"))
    pg.select_option("select[aria-label='Tipo da coluna Quantidade']", "numeric")
    pg.wait_for_timeout(500)

    pg.click("text=Gerar dashboard")
    pg.wait_for_selector(".chart-card canvas")
    pg.wait_for_timeout(1200)
    n = pg.locator(".chart-card").count()
    print("graficos:", n, "| kpis:", pg.locator(".kpi").count())
    pg.screenshot(path="e2e/shots/3_dashboard.png", full_page=True)

    # filtro categorico
    pg.click(".filter summary:has-text('Região')")
    pg.check("label:has-text('Norte') input")
    pg.wait_for_timeout(900)
    print("contagem:", pg.locator(".count").inner_text())
    pg.screenshot(path="e2e/shots/4_filtrado.png", full_page=True)

    # alternancia barras/setores e explicacao
    if pg.locator("button:has-text('Setores')").count():
        pg.locator("button:has-text('Setores')").first.click()
    pg.locator(".rule-badge").first.click()
    pg.wait_for_timeout(500)
    pg.screenshot(path="e2e/shots/5_setores_porque.png", full_page=True)

    # regras
    pg.click("text=Como o sistema escolhe os gráficos")
    pg.wait_for_selector(".dialog table")
    pg.screenshot(path="e2e/shots/6_regras.png")
    pg.keyboard.press("Escape")

    # salvar configuracao
    pg.click("button:has-text('Salvar configuração')")
    pg.fill("input[aria-label='Nome da configuração']", "Vendas por região")
    pg.click("button:has-text('Salvar'):not(:has-text('configuração'))")
    pg.wait_for_selector("text=salva.")
    print("config:", pg.locator(".alert.ok").first.inner_text())
    b.close()

print("ERROS:", json.dumps(errors, ensure_ascii=False, indent=1) if errors else "nenhum")
