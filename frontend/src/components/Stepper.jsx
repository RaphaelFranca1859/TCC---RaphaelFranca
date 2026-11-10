const STEPS = [
  { n: 1, label: 'Enviar planilha' },
  { n: 2, label: 'Revisar tipos' },
  { n: 3, label: 'Dashboard' },
]

export default function Stepper({ step, canGo, onGo }) {
  return (
    <nav className="stepper" aria-label="Etapas">
      <ol>
        {STEPS.map((s) => (
          <li key={s.n} className={s.n === step ? 'current' : s.n < step ? 'done' : ''}>
            <button
              onClick={() => onGo(s.n)}
              disabled={!canGo[s.n] || s.n === step}
              aria-current={s.n === step ? 'step' : undefined}
            >
              <span className="num">{s.n < step ? '✓' : s.n}</span>
              <span className="lbl">{s.label}</span>
            </button>
          </li>
        ))}
      </ol>
    </nav>
  )
}
