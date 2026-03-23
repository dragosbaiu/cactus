import { useGameStore } from '../store/gameStore'

const TYPE_STYLES = {
  success: { bg: 'rgba(0,201,167,0.9)',   border: 'var(--teal)' },
  error:   { bg: 'rgba(255,107,107,0.9)', border: 'var(--coral)' },
  info:    { bg: 'rgba(26,107,60,0.9)',   border: 'var(--felt-shine)' },
  cactus:  { bg: 'rgba(26,107,60,0.95)', border: 'var(--gold)' },
  win:     { bg: 'rgba(124,92,191,0.9)', border: 'var(--purple)' },
}

export default function Notifications() {
  const notifications = useGameStore(s => s.notifications)
  return (
    <div style={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', gap: 8, zIndex: 200, pointerEvents: 'none', alignItems: 'center' }}>
      {notifications.map(n => {
        const s = TYPE_STYLES[n.type] || TYPE_STYLES.info
        return (
          <div key={n.id} style={{ background: s.bg, border: `1.5px solid ${s.border}`, borderRadius: 24, padding: '8px 20px', fontFamily: 'var(--font-display)', fontSize: 16, color: 'white', boxShadow: '0 4px 16px rgba(0,0,0,0.4)', whiteSpace: 'nowrap', animation: 'slideUp 0.3s ease, floatUp 0.4s ease 2.6s both', backdropFilter: 'blur(6px)' }}>
            {n.message}
          </div>
        )
      })}
    </div>
  )
}
