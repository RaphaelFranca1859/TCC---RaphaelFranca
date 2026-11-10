import { useCallback, useEffect, useState } from 'react'
import Stepper from './components/Stepper.jsx'
import Sidebar from './components/Sidebar.jsx'
import Logo from './components/Logo.jsx'
import UploadStep from './components/UploadStep.jsx'
import TypesStep from './components/TypesStep.jsx'
import DashboardStep from './components/DashboardStep.jsx'
import RulesDialog from './components/RulesDialog.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import { api } from './api.js'
import { THEMES, ThemeContext, initialTheme, storage } from './theme.js'

const isWide = () => window.matchMedia('(min-width: 921px)').matches

export default function App() {
  const [step, setStep] = useState(1)
  const [session, setSession] = useState(null) // resposta de /upload ou /types
  const [applied, setApplied] = useState(null) // filtros/agg/sort vindos de uma configuracao salva
  const [showRules, setShowRules] = useState(false)
  const [theme, setTheme] = useState(initialTheme)
  // Menu: aberto por padrao em telas largas (filtros visiveis), fechado no celular; a escolha do usuario e lembrada.
  const [menuOpen, setMenuOpen] = useState(() => (isWide() ? storage.get('dashgen.menu', 'open') === 'open' : false))
  const [filtersSlot, setFiltersSlot] = useState(null)
  const [activeFilters, setActiveFilters] = useState([])
  const [chatOpen, setChatOpen] = useState(false)
  const [chat, setChat] = useState([])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    storage.set('dashgen.theme', theme)
  }, [theme])

  const toggleMenu = (value) => setMenuOpen((cur) => {
    const next = typeof value === 'boolean' ? value : !cur
    if (isWide()) storage.set('dashgen.menu', next ? 'open' : 'closed')
    return next
  })

  useEffect(() => { // Esc fecha a gaveta no celular
    const onKey = (e) => e.key === 'Escape' && !isWide() && setMenuOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const go = (n) => { setStep(n); if (!isWide()) setMenuOpen(false) }
  const reset = () => {
    setSession(null); setApplied(null); setChat([]); setChatOpen(false); setActiveFilters([])
    setStep(1)
  }
  const openChat = () => { setChatOpen(true); if (!isWide()) setMenuOpen(false) }
  const closeChat = useCallback(() => setChatOpen(false), [])
  const filterCount = step === 3 ? activeFilters.length : 0

  return (
    <ThemeContext.Provider value={THEMES[theme]}>
      <div className={`app ${chatOpen && session ? 'chat-open' : ''}`}>
        <header className="topbar">
          <button className="hamburger" onClick={() => toggleMenu()} aria-expanded={menuOpen} aria-controls="menu-lateral"
            aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'} title={menuOpen ? 'Fechar menu' : 'Abrir menu'}>
            <span className="bars" aria-hidden="true"><i /><i /><i /></span>
            {!menuOpen && filterCount > 0 && <span className="dot" title={`${filterCount} filtro(s) ativo(s)`}>{filterCount}</span>}
          </button>
          <div className="brand">
            <Logo className="logo" />
            <div>
              <h1>DashGen</h1>
              <p>Dashboards interativos a partir de planilhas, sem configuração</p>
            </div>
          </div>
          <Stepper step={step} canGo={{ 1: true, 2: !!session, 3: !!session }} onGo={go} />
          <div className="row gap top-actions">
            <button className="btn" onClick={openChat} disabled={!session}
              title={session ? 'Abrir o assistente de IA' : 'Envie uma planilha para usar o assistente'}>💬 Assistente de IA</button>
            <button className="btn icon" onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              aria-label={theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'} title={theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'}>
              <span aria-hidden="true">{theme === 'dark' ? '☀️' : '🌙'}</span>
            </button>
          </div>
        </header>

        <div className={`shell ${menuOpen ? 'menu-open' : ''}`}>
          <Sidebar open={menuOpen} step={step} canGo={{ 1: true, 2: !!session, 3: !!session }} onGo={go}
            onRules={() => { setShowRules(true); if (!isWide()) setMenuOpen(false) }} onChat={openChat} chatEnabled={!!session}
            theme={theme} onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            onClose={() => toggleMenu(false)} slotRef={setFiltersSlot} />

          <main>
            {step === 1 && (
              <UploadStep
                onLoaded={(s) => {
                  setSession(s)
                  setApplied(null)
                  setChat([])
                  setStep(2)
                }}
              />
            )}
            {step === 2 && session && (
              <TypesStep
                session={session}
                onChange={setSession}
                onApplyConfig={async (configId) => {
                  const result = await api.applyConfig(session.session_id, configId)
                  setSession(result)
                  setApplied(result.applied)
                  return result
                }}
                onBack={reset}
                onNext={() => setStep(3)}
              />
            )}
            {step === 3 && session && (
              <DashboardStep session={session} initial={applied} onEditTypes={() => setStep(2)} onNewFile={reset}
                filtersSlot={filtersSlot} onFiltersChange={setActiveFilters} onOpenMenu={() => toggleMenu(true)} />
            )}
          </main>
        </div>

        {chatOpen && session && (
          <ChatPanel session={session} filters={step === 3 ? activeFilters : []} messages={chat} setMessages={setChat} onClose={closeChat} />
        )}
        {showRules && <RulesDialog onClose={() => setShowRules(false)} />}
        <footer className="footer">
          DashGen · Trabalho de Conclusão de Curso, Bacharelado em Sistemas de Informação, IFBA Campus Vitória da Conquista.
          Os dados da planilha ficam apenas em memória e são descartados ao fim da sessão.
        </footer>
      </div>
    </ThemeContext.Provider>
  )
}
