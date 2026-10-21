import { fmtCompact, fmt } from './format.js'

export const PALETTE = ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#f97316',
  '#64748b', '#ec4899', '#84cc16', '#06b6d4', '#a855f7', '#eab308', '#22c55e']

const grid = { color: 'rgba(100,116,139,0.18)' }
const axisTitle = (text) => ({ display: !!text, text, color: '#475569', font: { weight: '600' } })

function base(chart) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 250 },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (c) => `${c.dataset.label ? c.dataset.label + ': ' : ''}${fmt(c.parsed.y ?? c.parsed.x ?? c.parsed)}` } },
    },
  }
}

/** Converte a especificacao devolvida pelo motor heuristico em configuracao do Chart.js. */
export function buildConfig(chart, variant) {
  const type = variant || chart.chart_type
  const d = chart.data
  const xName = chart.x?.column
  const yName = chart.y?.[0]?.column
  const opts = base(chart)

  if (type === 'pie') {
    return {
      type: 'pie',
      data: { labels: d.labels, datasets: [{ data: d.values, backgroundColor: d.labels.map((_, i) => PALETTE[i % PALETTE.length]) }] },
      options: { ...opts, plugins: { ...opts.plugins, legend: { display: true, position: 'right' },
        tooltip: { callbacks: { label: (c) => `${c.label}: ${fmt(c.parsed)}` } } } },
    }
  }

  if (type === 'bar' || type === 'hbar' || type === 'histogram') {
    const horizontal = type === 'hbar'
    const isHist = type === 'histogram'
    const valueTitle = chart.agg === 'count' ? 'Frequência' : `${yName}`
    return {
      type: 'bar',
      data: {
        labels: d.labels,
        datasets: [{
          label: valueTitle,
          data: d.values,
          backgroundColor: isHist ? '#4f46e5' : (horizontal ? '#4f46e5' : d.labels.map((_, i) => PALETTE[0])),
          borderRadius: isHist ? 0 : 4,
          categoryPercentage: isHist ? 1 : 0.8,
          barPercentage: isHist ? 1 : 0.9,
        }],
      },
      options: {
        ...opts,
        indexAxis: horizontal ? 'y' : 'x',
        scales: {
          [horizontal ? 'y' : 'x']: { grid: { display: false }, title: axisTitle(isHist ? xName : xName), ticks: { maxRotation: isHist ? 60 : 45, autoSkip: true } },
          [horizontal ? 'x' : 'y']: { grid, beginAtZero: true, title: axisTitle(valueTitle), ticks: { callback: (v) => fmtCompact(v) } },
        },
      },
    }
  }

  if (type === 'line' || type === 'multiline') {
    return {
      type: 'line',
      data: {
        labels: d.labels,
        datasets: d.series.map((s, i) => ({
          label: s.name, data: s.values, borderColor: PALETTE[i % PALETTE.length],
          backgroundColor: PALETTE[i % PALETTE.length], tension: 0.25, spanGaps: false,
          pointRadius: d.labels.length > 60 ? 0 : 3, borderWidth: 2,
        })),
      },
      options: {
        ...opts,
        interaction: { mode: 'index', intersect: false },
        plugins: { ...opts.plugins, legend: { display: d.series.length > 1, position: 'bottom' } },
        scales: {
          x: { grid: { display: false }, title: axisTitle(xName), ticks: { maxTicksLimit: 12, maxRotation: 45 } },
          y: { grid, title: axisTitle(d.series.length === 1 ? d.series[0].name : null), ticks: { callback: (v) => fmtCompact(v) } },
        },
      },
    }
  }

  if (type === 'scatter') {
    return {
      type: 'scatter',
      data: { datasets: [{ label: `${yName} × ${xName}`, data: d.points, backgroundColor: 'rgba(79,70,229,0.45)', pointRadius: 3 }] },
      options: {
        ...opts,
        plugins: { ...opts.plugins, tooltip: { callbacks: { label: (c) => `${xName}: ${fmt(c.parsed.x)} | ${yName}: ${fmt(c.parsed.y)}` } } },
        scales: {
          x: { grid, title: axisTitle(xName), ticks: { callback: (v) => fmtCompact(v) } },
          y: { grid, title: axisTitle(yName), ticks: { callback: (v) => fmtCompact(v) } },
        },
      },
    }
  }
  throw new Error(`Tipo de gráfico desconhecido: ${type}`)
}
