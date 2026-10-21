import { useState } from 'react'

function CategoricalFilter({ name, opt, value = [], onChange }) {
  const [q, setQ] = useState('')
  const shown = opt.values.filter((v) => v.toLowerCase().includes(q.toLowerCase()))
  const toggle = (v) => onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v])
  return (
    <details className="filter" open={value.length > 0}>
      <summary>{name}{value.length > 0 && <span className="pill">{value.length}</span>}</summary>
      {opt.values.length > 8 && (
        <input type="search" placeholder="Buscar..." value={q} onChange={(e) => setQ(e.target.value)} aria-label={`Buscar em ${name}`} />
      )}
      <div className="checks">
        {shown.map((v) => (
          <label key={v}><input type="checkbox" checked={value.includes(v)} onChange={() => toggle(v)} /> {v}</label>
        ))}
        {opt.truncated && <p className="muted small">Mostrando os valores mais frequentes.</p>}
      </div>
      {value.length > 0 && <button className="link" onClick={() => onChange([])}>Limpar</button>}
    </details>
  )
}

function RangeFilter({ name, type, opt, value = {}, onChange }) {
  const isDate = type === 'date'
  const [lo, hi] = isDate ? ['start', 'end'] : ['min', 'max']
  const set = (k, v) => onChange({ ...value, [k]: v === '' ? undefined : v })
  const active = value[lo] !== undefined || value[hi] !== undefined
  return (
    <details className="filter" open={active}>
      <summary>{name}{active && <span className="pill">•</span>}</summary>
      <div className="range">
        <label>De
          <input type={isDate ? 'date' : 'number'} value={value[lo] ?? ''} min={opt.min} max={opt.max}
            placeholder={String(opt.min)} onChange={(e) => set(lo, e.target.value)} />
        </label>
        <label>Até
          <input type={isDate ? 'date' : 'number'} value={value[hi] ?? ''} min={opt.min} max={opt.max}
            placeholder={String(opt.max)} onChange={(e) => set(hi, e.target.value)} />
        </label>
      </div>
      {!isDate && <p className="muted small">Intervalo dos dados: {opt.min} a {opt.max}</p>}
      {isDate && <p className="muted small">Período dos dados: {opt.min} a {opt.max}</p>}
    </details>
  )
}

export default function Filters({ options, columns, state, onChange, onClear }) {
  const names = columns.filter((c) => options[c.name]).map((c) => c.name)
  const active = Object.values(state).filter((v) => (Array.isArray(v) ? v.length : Object.values(v).some((x) => x !== undefined))).length
  return (
    <aside className="filters" aria-label="Filtros">
      <div className="filters-head">
        <h2>Filtros</h2>
        {active > 0 && <button className="link" onClick={onClear}>Limpar tudo ({active})</button>}
      </div>
      {names.length === 0 && <p className="muted">Nenhuma coluna disponível para filtrar.</p>}
      {names.map((name) => {
        const opt = options[name]
        const set = (v) => onChange(name, v)
        if (opt.kind === 'categorical') return <CategoricalFilter key={name} name={name} opt={opt} value={state[name]} onChange={set} />
        if (opt.kind === 'numeric') return <RangeFilter key={name} name={name} type="number" opt={opt} value={state[name]} onChange={set} />
        return <RangeFilter key={name} name={name} type="date" opt={opt} value={state[name]} onChange={set} />
      })}
    </aside>
  )
}
