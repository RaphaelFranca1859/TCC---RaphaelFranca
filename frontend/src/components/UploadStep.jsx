import { useRef, useState } from 'react'
import { api } from '../api.js'

const ACCEPT = '.xlsx,.xlsm,.csv,.tsv,.txt'

export default function UploadStep({ onLoaded }) {
  const input = useRef(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function send(file) {
    if (!file) return
    setError(null)
    setBusy(true)
    try {
      onLoaded(await api.upload(file))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card upload" aria-labelledby="t-upload">
      <h2 id="t-upload">Envie sua planilha</h2>
      <p className="muted">Aceitamos arquivos Excel (.xlsx) e CSV de até 20 MB. O sistema lê os dados, identifica o tipo de cada coluna e monta o dashboard para você.</p>

      <div
        className={`dropzone ${drag ? 'drag' : ''} ${busy ? 'busy' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); send(e.dataTransfer.files?.[0]) }}
        onClick={() => input.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current?.click()}
        aria-label="Área para soltar ou selecionar a planilha"
      >
        <span className="dz-icon" aria-hidden="true">{busy ? '⏳' : '📄'}</span>
        <strong>{busy ? 'Lendo a planilha...' : 'Arraste o arquivo aqui ou clique para escolher'}</strong>
        <span className="muted">.xlsx, .xlsm ou .csv</span>
        <input ref={input} type="file" accept={ACCEPT} hidden onChange={(e) => send(e.target.files?.[0])} />
      </div>

      {error && <p className="alert error" role="alert">{error}</p>}

      <ul className="hints">
        <li>Funciona com números em formato brasileiro (1.234,56) e datas dd/mm/aaaa.</li>
        <li>Colunas vazias, cabeçalhos repetidos e linhas em branco são tratados automaticamente.</li>
        <li>Na próxima etapa você poderá conferir e ajustar o tipo de cada coluna.</li>
      </ul>
    </section>
  )
}
