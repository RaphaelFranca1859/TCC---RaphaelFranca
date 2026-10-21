// Cliente da API REST. Todas as chamadas devolvem JSON ou lancam Error com a mensagem do servidor.
const BASE = import.meta.env.VITE_API_URL || ''

async function parse(res) {
  if (res.status === 204) return null
  const isJson = (res.headers.get('content-type') || '').includes('json')
  const body = isJson ? await res.json() : null
  if (!res.ok) {
    const err = new Error(body?.error || `Erro ${res.status} ao falar com o servidor.`)
    err.status = res.status
    throw err
  }
  return body
}

const json = (method, body, signal) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body ?? {}),
  signal,
})

export const api = {
  upload: (file, sheet) => {
    const form = new FormData()
    form.append('file', file)
    if (sheet) form.append('sheet', sheet)
    return fetch(`${BASE}/api/upload`, { method: 'POST', body: form }).then(parse)
  },
  setTypes: (id, types) => fetch(`${BASE}/api/sessions/${id}/types`, json('PUT', { types })).then(parse),
  dashboard: (id, params, signal) =>
    fetch(`${BASE}/api/sessions/${id}/dashboard`, json('POST', params, signal)).then(parse),
  saveConfig: (id, payload) => fetch(`${BASE}/api/sessions/${id}/config`, json('POST', payload)).then(parse),
  listConfigs: () => fetch(`${BASE}/api/configs`).then(parse),
  applyConfig: (id, configId) =>
    fetch(`${BASE}/api/sessions/${id}/apply-config`, json('POST', { config_id: configId })).then(parse),
  rules: () => fetch(`${BASE}/api/rules`).then(parse),
  async exportCsv(id, filters) {
    const res = await fetch(`${BASE}/api/sessions/${id}/export`, json('POST', { filters }))
    if (!res.ok) await parse(res)
    return res.blob()
  },
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
