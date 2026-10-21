import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function RulesDialog({ onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.rules().then(setData).catch((e) => setError(e.message))
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" role="dialog" aria-modal="true" aria-labelledby="rules-title" onClick={(e) => e.stopPropagation()}>
        <div className="row between">
          <h2 id="rules-title">Como o sistema escolhe os gráficos</h2>
          <button className="btn ghost" onClick={onClose} aria-label="Fechar">Fechar</button>
        </div>
        <p className="muted">
          A escolha segue regras explícitas, derivadas da literatura de percepção visual e visualização de dados.
          Cada gráfico do dashboard indica a regra aplicada (R1 a R7) e o motivo.
        </p>
        {error && <p className="alert error">{error}</p>}
        {data && (
          <>
            <div className="table-scroll">
              <table className="types">
                <thead><tr><th>Regra</th><th>Combinação de variáveis</th><th>Gráfico</th><th>Fundamentação</th></tr></thead>
                <tbody>
                  {data.rules.map((r) => (
                    <tr key={r.id}>
                      <td><span className="rule-badge static">{r.id}</span></td>
                      <td>{r.combination}</td>
                      <td>{r.chart}</td>
                      <td><span className="small">{r.rationale}</span><div className="muted small">{r.sources.join('; ')}</div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted small">
              Limiar entre barras e barras horizontais: {data.heuristic_thresholds.category_limit} categorias. Categorias exibidas no máximo: {data.heuristic_thresholds.top_n}.
              Os limiares são parâmetros de implementação, calibrados na etapa de demonstração.
            </p>
          </>
        )}
      </div>
    </div>
  )
}
