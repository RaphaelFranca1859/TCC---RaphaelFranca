import { createContext, useContext } from 'react'

// Paleta categorica de 8 matizes, em ordem fixa, validada para daltonismo (protanopia, deuteranopia e
// tritanopia) nos dois temas. As cores do tema escuro sao os mesmos matizes, ajustados para o fundo escuro.
export const THEMES = {
  light: {
    name: 'light', surface: '#ffffff', ink: '#334155', grid: 'rgba(100,116,139,0.20)',
    palette: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'],
  },
  dark: {
    name: 'dark', surface: '#1e293b', ink: '#cbd5e1', grid: 'rgba(148,163,184,0.22)',
    palette: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
  },
}

export const ThemeContext = createContext(THEMES.light)
export const useChartTheme = () => useContext(ThemeContext)

/** Leitura e escrita tolerantes a navegadores com armazenamento bloqueado. */
export const storage = {
  get(key, fallback = null) {
    try { const v = window.localStorage.getItem(key); return v === null ? fallback : v } catch { return fallback }
  },
  set(key, value) {
    try { value === null ? window.localStorage.removeItem(key) : window.localStorage.setItem(key, value) } catch { /* sem armazenamento */ }
  },
}

export function initialTheme() {
  const saved = storage.get('dashgen.theme')
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}
