import { CardFace } from './Card'

export default function PeekOverlay({ peekReveal, players }) {
  if (!peekReveal) return null
  const target = players?.find(p => p.player_id === peekReveal.playerId || p.id === peekReveal.playerId)
  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)', zIndex: 100, backdropFilter: 'blur(4px)', animation: 'popIn 0.3s ease' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, background: 'rgba(26,107,60,0.95)', border: '2px solid var(--gold)', borderRadius: 20, padding: '28px 36px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--gold)', letterSpacing: 1 }}>👁️ Secret peek</div>
        <div style={{ animation: 'popIn 0.3s ease 0.1s both' }}>
          <CardFace card={peekReveal.card} size="large" style={{ boxShadow: '0 0 0 3px var(--gold), 0 12px 30px rgba(240,192,64,0.4)' }} />
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>
          {target?.name}'s card at position {(peekReveal.position ?? 0) + 1}
        </div>
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)' }}>Only you can see this</div>
      </div>
    </div>
  )
}
