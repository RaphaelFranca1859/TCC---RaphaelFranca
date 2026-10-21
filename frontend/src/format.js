const nf = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })
const compact = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })

export const fmt = (v) => (v === null || v === undefined ? '-' : nf.format(v))
export const fmtCompact = (v) => (typeof v === 'number' ? compact.format(v) : v)

export const KIND_LABEL = {
  numeric: 'Numérica',
  categorical: 'Categórica',
  temporal: 'Temporal',
  ignored: 'Ignorar',
}
export const AGG_LABEL = { auto: 'Automática', sum: 'Soma', mean: 'Média', median: 'Mediana' }
export const SORT_LABEL = { value_desc: 'Maior valor primeiro', value_asc: 'Menor valor primeiro', label: 'Ordem alfabética' }

/** Exibe datas ISO (AAAA-MM-DD) no formato brasileiro; outros valores permanecem como estao. */
export function showCell(v) {
  if (typeof v !== 'string') return v
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}:\d{2}):\d{2})?$/)
  return m ? `${m[3]}/${m[2]}/${m[1]}${m[4] ? ' ' + m[4] : ''}` : v
}
