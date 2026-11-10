"""E2E da interface nova: menu recolhivel (3 barras), tema escuro, cores dos botoes e assistente de IA.
Requer servidor em http://localhost:5000 com frontend compilado. Para o assistente responder sem chave real,
suba o servidor com um modelo simulado (app.config["LLM_CALL"]); sem isso, o teste apenas confere a mensagem de erro.
Uso: python e2e/run_e2e_interface.py"""
import os, json
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

os.makedirs("e2e/shots", exist_ok=True)
errors = []
bg = lambda pg, sel: pg.eval_on_selector(sel, "e => getComputedStyle(e).backgroundColor")


def watch(pg):
    pg.on("console", lambda m: errors.append(("console", m.type, m.text)) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errors.append(("pageerror", str(e))))


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900}); watch(pg)
    pg.goto("http://localhost:5000/")
    pg.set_input_files("input[type=file]", "backend/data/synthetic/01_vendas_completo.xlsx"); pg.wait_for_selector("table.types")
    print("botao avancar (verde):", bg(pg, "button:has-text('Gerar dashboard')"), "| voltar (vermelho):", bg(pg, "button:has-text('Escolher outro arquivo')"))
    pg.screenshot(path="e2e/shots/11_tipos_botoes.png")
    pg.click("text=Gerar dashboard"); pg.wait_for_selector(".chart-card canvas"); pg.wait_for_timeout(1000)

    # menu de 3 barras: abre e fecha, e os filtros vivem dentro dele
    ham = pg.locator("button.hamburger")
    print("menu aberto por padrao:", ham.get_attribute("aria-expanded"), "| filtros visiveis:", pg.locator(".filters").is_visible())
    pg.screenshot(path="e2e/shots/12_dashboard_menu_aberto.png")
    ham.click(); pg.wait_for_timeout(400)
    print("apos clicar:", ham.get_attribute("aria-expanded"), "| filtros visiveis:", pg.locator(".filters").is_visible())
    pg.screenshot(path="e2e/shots/13_dashboard_menu_fechado.png")
    ham.click(); pg.wait_for_timeout(400)
    pg.click(".filter summary:has-text('Região')"); pg.check("label:has-text('Norte') input"); pg.wait_for_timeout(900)
    ham.click(); pg.wait_for_timeout(300)
    print("selo de filtros no botao de menu:", pg.locator(".hamburger .dot").inner_text())

    # tema escuro
    pg.click("button[aria-label='Usar tema escuro']"); pg.wait_for_timeout(700)
    print("tema:", pg.evaluate("document.documentElement.dataset.theme"), "| fundo:", bg(pg, "body"))
    pg.screenshot(path="e2e/shots/14_dashboard_escuro.png", full_page=True)

    # assistente de IA
    pg.click("button:has-text('Assistente de IA')"); pg.wait_for_selector(".chat")
    if pg.locator(".chat-settings").count():
        pg.fill(".chat-settings input[type=password]", "chave-de-teste"); pg.click(".chat-settings button:has-text('Salvar')")
    pg.locator(".chip").first.click()
    pg.wait_for_selector(".msg.assistant:not(.pending), .chat .alert.error", timeout=60000)
    if pg.locator(".msg.assistant:not(.pending)").count():
        print("resposta:", pg.locator(".msg.assistant > p").last.inner_text()[:90])
        pg.locator(".chat-data summary").last.click()
        print("linhas na tabela de dados usados:", pg.locator(".chat-data tbody tr").count())
    else:
        print("erro exibido:", pg.locator(".chat .alert.error").inner_text())
    pg.screenshot(path="e2e/shots/15_assistente_escuro.png")
    pg.click("button[aria-label='Usar tema claro']"); pg.wait_for_timeout(500)
    pg.screenshot(path="e2e/shots/16_assistente_claro.png")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    print("assistente fechou com Esc:", pg.locator(".chat").count() == 0)
    pg.close()

    # celular: menu fechado por padrao, abre como gaveta e fecha no fundo escurecido
    ctx = b.new_context(**p.devices["Pixel 7"]); m = ctx.new_page(); watch(m)
    m.goto("http://localhost:5000/")
    print("celular, menu inicia fechado:", m.locator("button.hamburger").get_attribute("aria-expanded"))
    m.click("button.hamburger"); m.wait_for_timeout(400)
    m.screenshot(path="e2e/shots/17_celular_menu.png")
    m.locator(".backdrop").click(position={"x": 380, "y": 400}); m.wait_for_timeout(300)
    print("fechou ao tocar fora:", m.locator("button.hamburger").get_attribute("aria-expanded"))
    print("rolagem horizontal no celular:", m.evaluate("document.documentElement.scrollWidth > window.innerWidth"))
    b.close()
print("ERROS:", json.dumps(errors, ensure_ascii=False, indent=1) if errors else "nenhum")
