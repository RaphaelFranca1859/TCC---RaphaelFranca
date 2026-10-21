import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { KIND_LABEL, showCell } from '../format.js'

const OPTIONS = ['numeric', 'categorical', 'temporal', 'ignored']

function Preview({ preview }) {
  return (
    <div className="table-scroll">
      <table className="preview">
        <thead><tr>{preview.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {preview.rows.map((r, i) => (
            <tr key={i}>{r.map((v, j) => <td key={j}>{v === null ? <span className="muted">-</span> : String(showCell(v)).slice(0, 40)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function TypesStep({ session, onChange, onApplyConfig, onBack, onNext }) {
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [configs, setConfigs] = useState([])
  const [configId, setConfigId] = useState('')
  const [info, setInfo] = useState(null)

  useEffect(() => { api.listConfigs().then((r) => setConfigs(r.configs)).catch(() => {}) }, [])

  async function setType(col, kind) {
    setBusy(col); setError(null)
    try { onChange(await api.setTypes(session.session_id, { [col]: kind })) }
    catch (e) { setError(e.message) }
    finally { setBusy(null) }
  }

  async function applyConfig() {
    setError(null); setInfo(null); setBusy('config')
    try {
      const r = await onApplyConfig(configId)
      const a = r.applied
      setInfo(`Configuração aplicada.${a.missing_columns.length ? ` Colunas ausentes nesta planilha: ${a.missing_columns.join(', ')}.` : ''}${a.new_columns.length ? ` Colunas novas (tipos inferidos): ${a.new_columns.join(', ')}.` : ''}`)
    } catch (e) { setError(e.message) }
    finally { setBusy(null) }
  }

  const chartable = session.columns.filter((c) => c.kind !== 'ignored').length

  return (
    <section className="stack">
      <div className="card">
        <div className="row between">
          <div>
            <h2>Confira os tipos das colunas</h2>
            <p className="muted">
              <strong>{session.filename}</strong>: {session.rows.toLocaleString('pt-BR')} linhas, {session.columns.length} colunas
              {session.sheet_used && <> (aba “{session.sheet_used}”)</>}. O sistema inferiu o tipo de cada coluna; ajuste o que estiver errado.
            </p>
          </div>
          <div className="row gap">
            <button className="btn ghost" onClick={onBack}>Escolher outro arquivo</button>
            <button className="btn primary" onClick={onNext} disabled={chartable === 0}>Gerar dashboard →</button>
          </div>
        </div>

        {error && <p className="alert error" role="alert">{error}</p>}
        {info && <p className="alert ok" role="status">{info}</p>}
        {session.warnings?.map((w) => <p key={w} className="alert warn">⚠ {w}</p>)}
        {chartable === 0 && <p className="alert error">Nenhuma coluna está habilitada para gráficos. Altere o tipo de ao menos uma coluna.</p>}

        <div className="table-scroll">
          <table className="types">
            <thead>
              <tr><th>Coluna</th><th>Tipo detectado</th><th>Tipo a usar</th><th className="num">Valores distintos</th><th className="num">Ausentes</th><th>Exemplos</th></tr>
            </thead>
            <tbody>
              {session.columns.map((c) => (
                <tr key={c.name} className={c.kind === 'ignored' ? 'dim' : ''}>
                  <td>
                    <strong>{c.name}</strong>
                    {c.ignored_reason && <div className="muted small">{c.ignored_reason}</div>}
                  </td>
                  <td><span className={`badge ${c.inferred_kind}`}>{KIND_LABEL[c.inferred_kind]}</span></td>
                  <td>
                    <select value={c.kind} disabled={busy !== null} onChange={(e) => setType(c.name, e.target.value)}
                      aria-label={`Tipo da coluna ${c.name}`} className={c.overridden ? 'changed' : ''}>
                      {OPTIONS.map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}
                    </select>
                    {busy === c.name && <span className="muted small"> atualizando...</span>}
                  </td>
                  <td className="num">{c.n_unique.toLocaleString('pt-BR')}</td>
                  <td className="num">{(c.missing_ratio * 100).toFixed(c.missing_ratio > 0 && c.missing_ratio < 0.1 ? 1 : 0)}%</td>
                  <td className="muted small">{c.sample.map(showCell).join(' · ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {session.notes.length > 0 && (
        <details className="card compact">
          <summary>O que o sistema ajustou na leitura ({session.notes.length})</summary>
          <ul>{session.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </details>
      )}

      {configs.length > 0 && (
        <div className="card compact">
          <h3>Reutilizar uma configuração salva</h3>
          <p className="muted small">Aplica os tipos, filtros e preferências de uma análise anterior a esta planilha (apenas colunas com o mesmo nome).</p>
          <div className="row gap">
            <select value={configId} onChange={(e) => setConfigId(e.target.value)} aria-label="Configuração salva">
              <option value="">Selecione...</option>
              {configs.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.filename})</option>)}
            </select>
            <button className="btn" disabled={!configId || busy !== null} onClick={applyConfig}>Aplicar</button>
          </div>
        </div>
      )}

      <div className="card compact">
        <h3>Primeiras linhas</h3>
        <Preview preview={session.preview} />
      </div>
    </section>
  )
}
