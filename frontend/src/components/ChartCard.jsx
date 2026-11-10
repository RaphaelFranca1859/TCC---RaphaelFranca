import { useEffect, useRef, useState } from 'react'
import { Chart, registerables } from 'chart.js'
import { buildConfig } from '../chartConfig.js'
import { useChartTheme } from '../theme.js'

Chart.register(...registerables)

function exportPng(canvas, name, background) {
  const out = document.createElement('canvas')
  out.width = canvas.width
  out.height = canvas.height
  const ctx = out.getContext('2d')
  ctx.fillStyle = background // fundo do tema (o canvas do grafico e transparente)
  ctx.fillRect(0, 0, out.width, out.height)
  ctx.drawImage(canvas, 0, 0)
  const a = document.createElement('a')
  a.href = out.toDataURL('image/png')
  a.download = `${name.replace(/[^\w-]+/g, '_').slice(0, 60)}.png`
  a.click()
}

export default function ChartCard({ chart, index = 0 }) {
  const theme = useChartTheme()
  const canvas = useRef(null)
  const instance = useRef(null)
  const [variant, setVariant] = useState(null)
  const [why, setWhy] = useState(false)
  const hasPie = chart.alternatives?.includes('pie')

  useEffect(() => {
    instance.current?.destroy()
    instance.current = new Chart(canvas.current, buildConfig(chart, variant, theme, index))
    return () => instance.current?.destroy()
  }, [chart, variant, theme, index])

  const wide = chart.chart_type === 'multiline' || chart.chart_type === 'line' || chart.chart_type === 'hbar'

  return (
    <article className={`chart-card ${wide ? 'wide' : ''}`}>
      <header>
        <h3>{chart.title}</h3>
        <button className="rule-badge" onClick={() => setWhy((v) => !v)} aria-expanded={why}
          title="Ver por que este gráfico foi escolhido">
          {chart.rule_id}
        </button>
      </header>

      <div className="chart-body">
        <canvas ref={canvas} role="img" aria-label={`${chart.title}. ${chart.explanation}`} />
      </div>

      {chart.warnings?.map((w) => <p key={w} className="chart-warning">⚠ {w}</p>)}

      {why && (
        <div className="why">
          <p>{chart.explanation}</p>
          <p className="muted small">Fundamentação: {chart.sources.join('; ')}.</p>
        </div>
      )}

      <footer>
        {hasPie && (
          <div className="seg" role="group" aria-label="Tipo de gráfico">
            <button className={!variant ? 'on' : ''} onClick={() => setVariant(null)}>Barras</button>
            <button className={variant === 'pie' ? 'on' : ''} onClick={() => setVariant('pie')}>Setores</button>
          </div>
        )}
        <button className="btn small" onClick={() => exportPng(canvas.current, chart.title, theme.surface)}>⬇ Baixar PNG</button>
      </footer>
    </article>
  )
}
