import { useEffect, useMemo, useRef, useState } from 'react'
import { api, downloadBlob } from '../api.js'
import { AGG_LABEL, SORT_LABEL } from '../format.js'
import ChartCard from './ChartCard.jsx'
import Filters from './Filters.jsx'
import KpiBar from './KpiBar.jsx'

/** Converte o estado visual dos filtros na lista esperada pela API. */
function toApiFilters(state, columns) {
  const kinds = Object.fromEntries(columns.map((c) => [c.name, c.kind]))
  const out = []
  for (const [column, v] of Object.entries(state)) {
    if (kinds[column] === 'categorical' && v?.length) out.push({ column, values: v })
    else if (kinds[column] === 'numeric' && (v?.min !== undefined || v?.max !== undefined))
      out.push({ column, min: v.min === undefined ? null : Number(v.min), max: v.max === undefined ? null : Number(v.max) })
    else if (kinds[column] === 'temporal' && (v?.start || v?.end)) out.push({ column, start: v.start || null, end: v.end || null })
  }
  return out
}

/** Caminho inverso: filtros de uma configuracao salva para o estado visual. */
function fromApiFilters(list = []) {
  const s = {}
  for (const f of list) {
    if (f.values) s[f.column] = f.values
    else if ('min' in f || 'max' in f) s[f.column] = { min: f.min ?? undefined, max: f.max ?? undefined }
    else s[f.column] = { start: f.start ?? undefined, end: f.end ?? undefined }
  }
  return s
}

export default function DashboardStep({ session, initial, onEditTypes, onNewFile }) {
  const [filters, setFilters] = useState(() => fromApiFilters(initial?.filters))
  const [agg, setAgg] = useState(initial?.agg || 'auto')
  const [sort, setSort] = useState(initial?.sort || 'value_desc')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [name, setName] = useState('')
  const [toast, setToast] = useState(null)
  const timer = useRef(null)

  const apiFilters = useMemo(() => toApiFilters(filters, session.columns), [filters, session.columns])

  useEffect(() => {
    const ctrl = new AbortController()
    clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      setLoading(true); setError(null)
      try {
        setData(await api.dashboard(session.session_id, { filters: apiFilters, agg, sort }, ctrl.signal))
      } catch (e) {
        if (e.name !== 'AbortError') setError(e.message)
      } finally {
        if (!ctrl.signal.aborted) setLoading(false)
      }
    }, 250)
    return () => { ctrl.abort(); clearTimeout(timer.current) }
  }, [session.session_id, session.columns, apiFilters, agg, sort])

  const notify = (msg) => { setToast(msg); setTimeout(() => setToast(null), 4000) }

  async function exportCsv() {
    try { downloadBlob(await api.exportCsv(session.session_id, apiFilters), session.filename.replace(/\.[^.]+$/, '') + '_filtrado.csv') }
    catch (e) { setError(e.message) }
  }

  async function saveConfig() {
    try {
      const r = await api.saveConfig(session.session_id, { name, filters: apiFilters, agg, sort })
      setSaving(false); setName(''); notify(`Configuração “${r.name}” salva.`)
    } catch (e) { setError(e.message) }
  }

  const clear = () => setFilters({})

  return (
    <div className="dash-layout">
      <Filters options={session.filter_options} columns={session.columns} state={filters}
        onChange={(col, v) => setFilters((f) => ({ ...f, [col]: v }))} onClear={clear} />

      <section className="dash-main">
        <div className="toolbar card compact">
          <div className="row gap wrap">
            <label>Agregação <select value={agg} onChange={(e) => setAgg(e.target.value)}>
              {Object.entries(AGG_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></label>
            <label>Ordenação <select value={sort} onChange={(e) => setSort(e.target.value)}>
              {Object.entries(SORT_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></label>
          </div>
          <div className="row gap wrap">
            <button className="btn ghost" onClick={onEditTypes}>Ajustar tipos</button>
            <button className="btn ghost" onClick={exportCsv}>Exportar CSV filtrado</button>
            <button className="btn" onClick={() => setSaving((s) => !s)}>Salvar configuração</button>
            <button className="btn ghost" onClick={onNewFile}>Novo arquivo</button>
          </div>
        </div>

        {saving && (
          <div className="card compact row gap">
            <input type="text" value={name} placeholder={`Configuração de ${session.filename}`} onChange={(e) => setName(e.target.value)}
              aria-label="Nome da configuração" autoFocus />
            <button className="btn primary" onClick={saveConfig}>Salvar</button>
            <button className="btn ghost" onClick={() => setSaving(false)}>Cancelar</button>
          </div>
        )}
        {toast && <p className="alert ok" role="status">{toast}</p>}
        {error && <p className="alert error" role="alert">{error}</p>}

        {data && (
          <>
            <p className="muted small count">
              {data.meta.rows_filtered.toLocaleString('pt-BR')} de {data.meta.rows_total.toLocaleString('pt-BR')} registros
              {apiFilters.length > 0 && <> · {apiFilters.length} filtro(s) ativo(s)</>} · {data.meta.charts} gráfico(s)
              {loading && <span> · atualizando...</span>}
            </p>
            <KpiBar kpis={data.kpis} />
            {data.charts.length === 0 ? (
              <div className="card empty">
                <h3>Nenhum gráfico para exibir</h3>
                <p className="muted">
                  {data.meta.rows_filtered === 0 ? 'Nenhum registro atende aos filtros. Ajuste ou limpe os filtros.'
                    : 'Não foi possível combinar as colunas em gráficos. Revise os tipos das colunas.'}
                </p>
              </div>
            ) : (
              <div className={`grid ${loading ? 'stale' : ''}`}>
                {data.charts.map((c) => <ChartCard key={c.id} chart={c} />)}
              </div>
            )}
            <details className="card compact log">
              <summary>Como o sistema decidiu ({data.decision_log.length} registros)</summary>
              <ol>{data.decision_log.map((l, i) => <li key={i}>{l}</li>)}</ol>
            </details>
          </>
        )}
        {!data && loading && <p className="muted">Montando o dashboard...</p>}
      </section>
    </div>
  )
}
