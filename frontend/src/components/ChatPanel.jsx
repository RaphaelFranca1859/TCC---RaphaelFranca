import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { fmt, showCell } from '../format.js'
import { storage } from '../theme.js'

/** Sugestoes de pergunta montadas a partir das colunas da planilha (reconhecer em vez de lembrar). */
function suggestions(columns) {
  const num = columns.find((c) => c.kind === 'numeric')?.name
  const cat = columns.find((c) => c.kind === 'categorical')?.name
  const time = columns.find((c) => c.kind === 'temporal')?.name
  const out = []
  if (num && cat) out.push(`Qual ${cat} tem a maior soma de ${num}?`)
  if (num && time) out.push(`Como ${num} evoluiu mês a mês?`)
  if (cat) out.push(`Quantos registros há por ${cat}?`)
  if (num) out.push(`Qual é a média de ${num}?`)
  return out.slice(0, 4)
}

function ResultTable({ table }) {
  return (
    <details className="chat-data">
      <summary>Dados usados na resposta ({table.rows.length} linha{table.rows.length === 1 ? '' : 's'})</summary>
      <div className="table-scroll">
        <table>
          <thead><tr>{table.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {table.rows.map((r, i) => (
              <tr key={i}>{r.map((v, j) => <td key={j} className={typeof v === 'number' ? 'num' : ''}>{typeof v === 'number' ? fmt(v) : showCell(v) ?? '-'}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">Calculado pelo sistema sobre {table.rows_considered.toLocaleString('pt-BR')} registros
        {table.truncated && <> · mostrando {table.rows.length} de {table.groups_total} grupos</>}.</p>
    </details>
  )
}

export default function ChatPanel({ session, filters, messages, setMessages, onClose }) {
  const [status, setStatus] = useState(null)
  const [provider, setProvider] = useState(() => storage.get('dashgen.llm.provider', ''))
  const [model, setModel] = useState(() => storage.get('dashgen.llm.model', ''))
  const [key, setKey] = useState(() => storage.get('dashgen.llm.key', ''))
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const end = useRef(null)
  const input = useRef(null)
  const tips = useMemo(() => suggestions(session.columns), [session.columns])

  useEffect(() => {
    api.assistantStatus().then((s) => {
      setStatus(s)
      setProvider((p) => p || s.provider)
      if (!s.server_key && !storage.get('dashgen.llm.key', '')) setShowSettings(true)
    }).catch((e) => setError(e.message))
    input.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [messages, busy])

  const info = status?.providers?.[provider]
  const ready = !!status && (status.server_key || key.trim())

  function saveSettings(e) {
    e.preventDefault()
    storage.set('dashgen.llm.provider', provider)
    storage.set('dashgen.llm.model', model.trim() || null)
    storage.set('dashgen.llm.key', key.trim() || null)
    setShowSettings(false); setError(null)
    input.current?.focus()
  }

  async function send(question) {
    const q = (question ?? text).trim()
    if (!q || busy) return
    if (!ready) { setShowSettings(true); setError('Informe uma chave de API para usar o assistente.'); return }
    setError(null); setBusy(true); setText('')
    const history = messages.map((m) => ({ role: m.role, content: m.content }))
    setMessages((m) => [...m, { role: 'user', content: q }])
    try {
      const r = await api.ask(session.session_id, { question: q, history, filters,
        ...(key.trim() ? { provider, model: model.trim() } : {}) }, key.trim())
      setMessages((m) => [...m, { role: 'assistant', content: r.answer, table: r.table, model: r.model }])
    } catch (e) {
      setError(e.message)
      setMessages((m) => m.slice(0, -1)); setText(q) // devolve a pergunta ao campo para o usuario nao redigitar
    } finally { setBusy(false); input.current?.focus() }
  }

  return (
    <aside className="chat" role="complementary" aria-label="Assistente de IA">
      <header className="chat-head">
        <div>
          <h2>Assistente de IA</h2>
          <p className="muted small">Perguntas em linguagem natural sobre <strong>{session.filename}</strong>
            {filters.length > 0 && <> · respeitando {filters.length} filtro(s) ativo(s)</>}</p>
        </div>
        <button className="btn stop small" onClick={onClose}>✕ Fechar</button>
      </header>

      <div className="chat-tools">
        <button className="btn small" onClick={() => setShowSettings((v) => !v)} aria-expanded={showSettings}>⚙ Chave e modelo</button>
        {messages.length > 0 && <button className="btn stop small" onClick={() => setMessages([])}>✕ Limpar conversa</button>}
        {status && <span className="muted small">{status.server_key && !key.trim() ? `Usando a chave do servidor (${status.model})` : key.trim() ? `Usando a sua chave (${info?.label || provider})` : 'Sem chave configurada'}</span>}
      </div>

      {showSettings && status && (
        <form className="chat-settings" onSubmit={saveSettings}>
          <label>Provedor
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              {Object.entries(status.providers).map(([id, p]) => <option key={id} value={id}>{p.label}</option>)}
            </select>
          </label>
          <label>Chave de API
            <input type="password" value={key} onChange={(e) => setKey(e.target.value)} autoComplete="off"
              placeholder={status.server_key ? 'Em branco = chave do servidor' : 'Cole a sua chave aqui'} />
          </label>
          <label>Modelo (opcional)
            <input type="text" value={model} onChange={(e) => setModel(e.target.value)} placeholder={info?.default_model} />
          </label>
          <p className="muted small">
            {info && <>Crie uma chave em <a href={info.key_url} target="_blank" rel="noreferrer">{info.key_url.replace('https://', '')}</a>. </>}
            A chave fica salva apenas neste navegador e é enviada ao servidor somente para repassar a pergunta ao provedor.
          </p>
          <div className="row gap">
            <button type="submit" className="btn go small">✓ Salvar</button>
            <button type="button" className="btn stop small" onClick={() => setShowSettings(false)}>✕ Cancelar</button>
          </div>
        </form>
      )}

      <div className="chat-body" aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Pergunte algo sobre os dados. O sistema calcula os números na planilha e a IA redige a resposta.</p>
            <div className="chips">
              {tips.map((t) => <button key={t} className="chip" disabled={busy} onClick={() => send(t)}>{t}</button>)}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <span className="who">{m.role === 'user' ? 'Você' : 'Assistente'}</span>
            <p>{m.content}</p>
            {m.table && <ResultTable table={m.table} />}
          </div>
        ))}
        {busy && <div className="msg assistant pending"><span className="who">Assistente</span><p>Analisando os dados...</p></div>}
        <div ref={end} />
      </div>

      {error && <p className="alert error" role="alert">{error}</p>}

      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send() }}>
        <textarea ref={input} rows={2} value={text} maxLength={1000} placeholder="Escreva a sua pergunta..."
          aria-label="Pergunta para o assistente" onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }} />
        <button type="submit" className="btn go" disabled={busy || !text.trim()}>Enviar →</button>
      </form>
      <p className="muted small chat-note">
        Privacidade: são enviados ao provedor de IA os nomes das colunas, estatísticas resumidas, alguns valores de categorias
        e os resultados agregados das consultas. As linhas da planilha não são enviadas. Respostas de IA podem conter erros: confira na tabela de dados usados.
      </p>
    </aside>
  )
}
