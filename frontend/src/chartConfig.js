import { fmtCompact, fmt } from './format.js'

import { THEMES } from './theme.js'

export const PALETTE = THEMES.light.palette

/** Cor da fatia/serie i. Alem de 8 itens, os matizes se repetem com transparencia (nunca um matiz gerado). */
function slot(palette, i) {
  const hex = palette[i % palette.length]
  return i < palette.length ? hex : hex + '99'
}

function base(theme) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 250 },
    color: theme.ink,
    plugins: {
      legend: { display: false, labels: { color: theme.ink } },
      tooltip: { callbacks: { label: (c) => `${c.dataset.label ? c.dataset.label + ': ' : ''}${fmt(c.parsed.y ?? c.parsed.x ?? c.parsed)}` } },
    },
  }
}

/** Converte a especificacao devolvida pelo motor heuristico em configuracao do Chart.js. */
export function buildConfig(chart, variant, theme = THEMES.light, index = 0) {
  const type = variant || chart.chart_type
  const PALETTE = theme.palette
  const grid = { color: theme.grid }
  const ticks = { color: theme.ink }
  const axisTitle = (text) => ({ display: !!text, text, color: theme.ink, font: { weight: '600' } })
  const hue = PALETTE[index % PALETTE.length] // um matiz por grafico de serie unica: variedade sem codificar nada falso
  const d = chart.data
  const xName = chart.x?.column
  const yName = chart.y?.[0]?.column
  const opts = base(theme)

  if (type === 'pie') {
    return {
      type: 'pie',
      data: { labels: d.labels, datasets: [{ data: d.values, backgroundColor: d.labels.map((_, i) => slot(PALETTE, i)), borderColor: theme.surface, borderWidth: 2 }] },
      options: { ...opts, plugins: { ...opts.plugins, legend: { display: true, position: 'right', labels: { color: theme.ink } },
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
          backgroundColor: hue,
          borderRadius: isHist ? 0 : 4,
          categoryPercentage: isHist ? 1 : 0.8,
          barPercentage: isHist ? 1 : 0.9,
        }],
      },
      options: {
        ...opts,
        indexAxis: horizontal ? 'y' : 'x',
        scales: {
          [horizontal ? 'y' : 'x']: { grid: { display: false }, title: axisTitle(isHist ? xName : xName), ticks: { ...ticks, maxRotation: isHist ? 60 : 45, autoSkip: true } },
          [horizontal ? 'x' : 'y']: { grid, beginAtZero: true, title: axisTitle(valueTitle), ticks: { ...ticks, callback: (v) => fmtCompact(v) } },
        },
      },
    }
  }

  if (type === 'line' || type === 'multiline') {
    const hasY2 = d.series.some((s) => s.axis === 'y2')
    const isIndex = chart.scale === 'index100'
    const leftNames = d.series.filter((s) => s.axis !== 'y2').map((s) => s.name)
    const rightNames = d.series.filter((s) => s.axis === 'y2').map((s) => s.name)
    const scales = {
      x: { grid: { display: false }, title: axisTitle(xName), ticks: { ...ticks, maxTicksLimit: 12, maxRotation: 45 } },
      y: { grid, title: axisTitle(isIndex ? 'Índice (base 100)' : (hasY2 ? leftNames.join(', ') : (d.series.length === 1 ? d.series[0].name : null))),
        ticks: { ...ticks, callback: (v) => fmtCompact(v) }, position: 'left' },
    }
    if (hasY2) {
      scales.y2 = { position: 'right', grid: { drawOnChartArea: false }, title: axisTitle(rightNames.join(', ')),
        ticks: { ...ticks, callback: (v) => fmtCompact(v) } }
    }
    return {
      type: 'line',
      data: {
        labels: d.labels,
        datasets: d.series.map((s, i0) => { const i = d.series.length === 1 ? index : i0; return ({
          label: hasY2 ? `${s.name} (${s.axis === 'y2' ? 'eixo direito' : 'eixo esquerdo'})` : s.name,
          data: s.values, borderColor: PALETTE[i % PALETTE.length], yAxisID: s.axis || 'y',
          backgroundColor: PALETTE[i % PALETTE.length], tension: 0.25, spanGaps: false,
          pointRadius: d.labels.length > 60 ? 0 : 3, borderWidth: 2,
        }) }),
      },
      options: {
        ...opts,
        interaction: { mode: 'index', intersect: false },
        plugins: { ...opts.plugins, legend: { display: d.series.length > 1, position: 'bottom', labels: { color: theme.ink } } },
        scales,
      },
    }
  }

  if (type === 'scatter') {
    return {
      type: 'scatter',
      data: { datasets: [{ label: `${yName} × ${xName}`, data: d.points, backgroundColor: hue + '80', pointRadius: 3 }] },
      options: {
        ...opts,
        plugins: { ...opts.plugins, tooltip: { callbacks: { label: (c) => `${xName}: ${fmt(c.parsed.x)} | ${yName}: ${fmt(c.parsed.y)}` } } },
        scales: {
          x: { grid, title: axisTitle(xName), ticks: { ...ticks, callback: (v) => fmtCompact(v) } },
          y: { grid, title: axisTitle(yName), ticks: { ...ticks, callback: (v) => fmtCompact(v) } },
        },
      },
    }
  }
  throw new Error(`Tipo de gráfico desconhecido: ${type}`)
}
