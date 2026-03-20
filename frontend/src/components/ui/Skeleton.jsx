export default function Skeleton({ className = '', style = {} }) {
  return (
    <div
      className={`rounded-lg animate-pulse ${className}`}
      style={{
        background: 'var(--bg-tertiary)',
        ...style,
      }}
    />
  )
}