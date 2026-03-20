export default function Card({ children, className = '', style = {} }) {
  return (
    <div
      className={`rounded-2xl border p-4 ${className}`}
      style={{
        background: 'var(--bg-card)',
        borderColor: 'var(--border)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}