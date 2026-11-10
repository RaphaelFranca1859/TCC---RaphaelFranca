"""Gera uma captura do dashboard de cada dataset (insumo das figuras da secao 4.2.4).
Requer servidor em http://localhost:5000 com frontend compilado.  Uso: python e2e/capturas_estudos_de_caso.py"""
import os, sys
from pathlib import Path
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

out = Path("docs/capturas"); out.mkdir(parents=True, exist_ok=True)
files = sorted(Path("backend/data/real").glob("*.xlsx"))
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in files:
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.on("pageerror", lambda e: errors.append((f.name, str(e))))
        pg.on("response", lambda r, n=f.name: errors.append((n, r.status, r.url)) if r.status >= 400 else None)
        pg.goto("http://localhost:5000/")
        pg.set_input_files("input[type=file]", str(f)); pg.wait_for_selector("table.types", timeout=60000)
        pg.screenshot(path=str(out / f"{f.stem}_tipos.png"), full_page=True)
        pg.click("text=Gerar dashboard"); pg.wait_for_selector(".chart-card canvas", timeout=60000); pg.wait_for_timeout(1500)
        pg.screenshot(path=str(out / f"{f.stem}_dashboard.png"), full_page=True)
        print(f.name, "graficos:", pg.locator(".chart-card").count())
        pg.close()
    b.close()
print("ERROS:", errors or "nenhum")
