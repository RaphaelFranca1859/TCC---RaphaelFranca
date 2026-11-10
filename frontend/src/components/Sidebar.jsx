const STEPS = [
  { n: 1, label: 'Enviar planilha' },
  { n: 2, label: 'Revisar tipos' },
  { n: 3, label: 'Dashboard' },
]

/** Menu lateral recolhivel. No celular vira gaveta sobreposta; no computador empurra o conteudo. */
export default function Sidebar({ open, step, canGo, onGo, onRules, onChat, chatEnabled, theme, onToggleTheme, onClose, slotRef }) {
  return (
    <>
      <div className={`backdrop ${open ? 'show' : ''}`} onClick={onClose} aria-hidden="true" />
      <aside id="menu-lateral" className={`sidebar ${open ? 'open' : ''}`} aria-label="Menu" aria-hidden={!open} inert={open ? undefined : ''}>
        <nav aria-label="Navegação">
          <h2 className="side-title">Etapas</h2>
          <ul className="side-nav">
            {STEPS.map((s) => (
              <li key={s.n}>
                <button className={`side-item ${s.n === step ? 'current' : ''}`} disabled={!canGo[s.n]}
                  aria-current={s.n === step ? 'page' : undefined} onClick={() => onGo(s.n)}>
                  <span className="num">{s.n < step ? '✓' : s.n}</span>{s.label}
                </button>
              </li>
            ))}
          </ul>
          <h2 className="side-title">Ferramentas</h2>
          <ul className="side-nav">
            <li><button className="side-item" onClick={onChat} disabled={!chatEnabled}
              title={chatEnabled ? undefined : 'Envie uma planilha para usar o assistente'}><span className="ico" aria-hidden="true">💬</span>Assistente de IA</button></li>
            <li><button className="side-item" onClick={onRules}><span className="ico" aria-hidden="true">📐</span>Como o sistema escolhe os gráficos</button></li>
            <li><button className="side-item" onClick={onToggleTheme} role="switch" aria-checked={theme === 'dark'}>
              <span className="ico" aria-hidden="true">{theme === 'dark' ? '☀️' : '🌙'}</span>{theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'}</button></li>
          </ul>
        </nav>
        <div ref={slotRef} className="side-slot" />
      </aside>
    </>
  )
}
