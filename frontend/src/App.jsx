import { useState } from 'react'
import Stepper from './components/Stepper.jsx'
import UploadStep from './components/UploadStep.jsx'
import TypesStep from './components/TypesStep.jsx'
import DashboardStep from './components/DashboardStep.jsx'
import RulesDialog from './components/RulesDialog.jsx'
import { api } from './api.js'

export default function App() {
  const [step, setStep] = useState(1)
  const [session, setSession] = useState(null) // resposta de /upload ou /types
  const [applied, setApplied] = useState(null) // filtros/agg/sort vindos de uma configuracao salva
  const [showRules, setShowRules] = useState(false)

  const reset = () => {
    setSession(null)
    setApplied(null)
    setStep(1)
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden="true">📊</span>
          <div>
            <h1>DashGen</h1>
            <p>Dashboards interativos a partir de planilhas, sem configuração</p>
          </div>
        </div>
        <Stepper step={step} canGo={{ 1: true, 2: !!session, 3: !!session }} onGo={setStep} />
        <button className="btn ghost" onClick={() => setShowRules(true)}>Como o sistema escolhe os gráficos</button>
      </header>

      <main>
        {step === 1 && (
          <UploadStep
            onLoaded={(s) => {
              setSession(s)
              setApplied(null)
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
          <DashboardStep session={session} initial={applied} onEditTypes={() => setStep(2)} onNewFile={reset} />
        )}
      </main>

      {showRules && <RulesDialog onClose={() => setShowRules(false)} />}
      <footer className="footer">
        DashGen · Trabalho de Conclusão de Curso, Bacharelado em Sistemas de Informação, IFBA Campus Vitória da Conquista.
        Os dados da planilha ficam apenas em memória e são descartados ao fim da sessão.
      </footer>
    </div>
  )
}
