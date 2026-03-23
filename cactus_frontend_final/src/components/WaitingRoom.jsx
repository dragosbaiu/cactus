import { useGameStore } from '../store/gameStore'

export default function WaitingRoom() {
  const { gameState, myPlayerId, isHost, roomCode, startRound, leaveRoom } = useGameStore()
  const players = gameState?.room?.players || []
  const canStart = isHost && players.length >= 2

  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
      <div style={{ background: 'linear-gradient(160deg,rgba(26,107,60,0.97),rgba(18,77,43,0.97))', border: '2px solid rgba(240,192,64,0.4)', borderRadius: 28, padding: '40px 48px', width: 420, boxShadow: '0 32px 80px rgba(0,0,0,0.5)', animation: 'slideUp 0.4s ease' }}>

        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 8 }}>Room Code</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, color: 'var(--gold)', letterSpacing: 4, background: 'rgba(0,0,0,0.3)', borderRadius: 14, padding: '10px 24px', display: 'inline-block', border: '1px solid rgba(240,192,64,0.3)' }}>
            {roomCode}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 10 }}>Share this code with your friends</div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 }}>
            Players ({players.length}/8)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {players.map(p => (
              <div key={p.player_id} style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '9px 14px', border: p.player_id === myPlayerId ? '1px solid rgba(240,192,64,0.4)' : '1px solid rgba(255,255,255,0.07)' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: p.is_connected ? 'var(--teal)' : 'var(--text-muted)', boxShadow: p.is_connected ? '0 0 6px var(--teal)' : 'none' }} />
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: p.player_id === myPlayerId ? 'var(--gold)' : 'var(--cream)', flex: 1 }}>{p.name}</span>
                {gameState?.room?.host_id === p.player_id && <span style={{ fontSize: 11, color: 'var(--gold)', background: 'rgba(240,192,64,0.15)', borderRadius: 8, padding: '2px 8px' }}>HOST</span>}
                {p.player_id === myPlayerId && <span style={{ fontSize: 11, color: 'var(--teal)', background: 'rgba(0,201,167,0.1)', borderRadius: 8, padding: '2px 8px' }}>YOU</span>}
              </div>
            ))}
            {Array.from({ length: Math.max(0, 2 - players.length) }, (_, i) => (
              <div key={`empty-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.1)', borderRadius: 10, padding: '9px 14px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'rgba(255,255,255,0.15)' }} />
                <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.2)', fontStyle: 'italic' }}>Waiting for player...</span>
              </div>
            ))}
          </div>
        </div>

        {isHost
          ? <button onClick={startRound} disabled={!canStart} style={{ width: '100%', background: canStart ? 'linear-gradient(135deg, var(--gold-dark), var(--gold))' : 'rgba(0,0,0,0.3)', color: canStart ? 'var(--text-dark)' : 'var(--text-muted)', fontFamily: 'var(--font-display)', fontSize: 20, padding: '13px 0', borderRadius: 14, border: canStart ? 'none' : '1px solid rgba(255,255,255,0.1)', cursor: canStart ? 'pointer' : 'not-allowed', letterSpacing: 1 }}>
              {canStart ? 'Deal Cards →' : `Need ${2 - players.length} more player${2 - players.length !== 1 ? 's' : ''}...`}
            </button>
          : <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 14, padding: '12px 0' }}>⏳ Waiting for host to start...</div>
        }

        <button onClick={leaveRoom} style={{ marginTop: 12, width: '100%', background: 'none', color: 'rgba(255,255,255,0.2)', fontSize: 12, cursor: 'pointer', textDecoration: 'underline' }}>Leave room</button>
      </div>
    </div>
  )
}
