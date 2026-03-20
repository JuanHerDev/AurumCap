export default function Badge({ value, showSign = true }) {
  if (value === null || value === undefined) return null
  const positive = value >= 0
  const sign = showSign && positive ? '+' : ''

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium"
      style={{
        background: positive ? 'rgba(0,200,150,0.12)' : 'rgba(255,77,106,0.12)',
        color: positive ? 'var(--green)' : 'var(--red)',
      }}
    >
      {sign}{value.toFixed(2)}%
    </span>
  )
}