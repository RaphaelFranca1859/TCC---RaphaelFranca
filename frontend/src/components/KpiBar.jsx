import { fmt } from '../format.js'

export default function KpiBar({ kpis }) {
  if (!kpis?.length) return null
  return (
    <section className="kpis" aria-label="Indicadores">
      {kpis.map((k) => (
        <div key={k.label} className="kpi">
          <span className="kpi-label">{k.label}</span>
          <strong>{fmt(k.value)}</strong>
          {k.detail && <span className="muted small">{k.detail}</span>}
        </div>
      ))}
    </section>
  )
}
