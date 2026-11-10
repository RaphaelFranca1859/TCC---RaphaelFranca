/** Logo do DashGen: quadrado de planilha (grade) com tres barras ascendentes.
 *  O mesmo desenho esta em public/favicon.svg (icone da aba do navegador). */
export default function Logo({ className = '', size = 40 }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="dg-logo-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#6366f1" />
          <stop offset="1" stopColor="#3730a3" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="url(#dg-logo-bg)" />
      <path d="M12 22h40M12 36h40M25.3 12v38M38.7 12v38" stroke="#fff" strokeOpacity=".22" strokeWidth="1.5" fill="none" />
      <path d="M14.2 50V40.6a2.6 2.6 0 0 1 2.6 -2.6h3.8a2.6 2.6 0 0 1 2.6 2.6V50Z" fill="#a5b4fc" />
      <path d="M27.5 50V30.6a2.6 2.6 0 0 1 2.6 -2.6h3.8a2.6 2.6 0 0 1 2.6 2.6V50Z" fill="#ffffff" />
      <path d="M40.8 50V18.6a2.6 2.6 0 0 1 2.6 -2.6h3.8a2.6 2.6 0 0 1 2.6 2.6V50Z" fill="#4ade80" />
      <path d="M11 50.5h42" stroke="#fff" strokeOpacity=".6" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
