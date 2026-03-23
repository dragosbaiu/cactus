import { useState } from 'react'
import { useGameStore } from '../store/gameStore'

export default function Lobby() {
  const { createRoom, joinRoom, lobbyError, isLoading } = useGameStore()
  const [mode, setMode]         = useState('choose')
  const [playerName, setName]   = useState('')
  const [roomCode, setRoomCode] = useState('')

  const inputStyle = { width: '100%', background: 'rgba(0,0,0,0.25)', border: '1.5px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '11px 14px', color: 'var(--cream)', fontFamily: 'var(--font-body)', fontSize: 15, outline: 'none' }
  const btnPrimary = { width: '100%', background: 'linear-gradient(135deg, var(--gold-dark), var(--gold))', color: 'var(--text-dark)', fontFamily: 'var(--font-display)', fontSize: 20, padding: '13px 0', borderRadius: 14, border: 'none', boxShadow: '0 4px 16px rgba(240,192,64,0.4)', letterSpacing: 1, cursor: isLoading ? 'not-allowed' : 'pointer', opacity: isLoading ? 0.7 : 1 }
  const btnBack = { background: 'none', color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer', textDecoration: 'underline' }

  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
      {['♠','♥','♦','♣'].map((s,i) => (
        <div key={i} style={{ position: 'absolute', fontSize: 120, color: i < 2 ? 'rgba(192,57,43,0.06)' : 'rgba(26,26,46,0.06)', top: ['10%','60%','20%','70%'][i], left: ['5%','8%','85%','80%'][i], transform: `rotate(${[-15,10,20,-8][i]}deg)`, pointerEvents: 'none' }}>{s}</div>
      ))}
      <div style={{ background: 'linear-gradient(160deg,rgba(26,107,60,0.97),rgba(18,77,43,0.97))', border: '2px solid rgba(240,192,64,0.4)', borderRadius: 28, padding: '44px 48px', width: 400, boxShadow: '0 32px 80px rgba(0,0,0,0.5)', animation: 'slideUp 0.5s ease' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 52, color: 'var(--gold)', lineHeight: 1, letterSpacing: 2 }}>🌵 CACTUS</div>
          <div style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 8 }}>The memory card game</div>
        </div>

        {mode === 'choose' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button style={btnPrimary} onClick={() => setMode('create')}>🏠 Create Room</button>
            <button onClick={() => setMode('join')} style={{ ...btnPrimary, background: 'rgba(0,0,0,0.3)', color: 'var(--cream)', border: '1.5px solid rgba(255,255,255,0.15)', boxShadow: 'none' }}>🔗 Join Room</button>
          </div>
        )}

        {mode === 'create' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <input style={inputStyle} placeholder="Your name" value={playerName} onChange={e => setName(e.target.value)} onKeyDown={e => e.key === 'Enter' && createRoom(playerName.trim())} maxLength={16} autoFocus />
            <button style={btnPrimary} onClick={() => createRoom(playerName.trim())} disabled={isLoading}>{isLoading ? 'Creating...' : 'Create Room →'}</button>
            <button onClick={() => setMode('choose')} style={btnBack}>← Back</button>
          </div>
        )}

        {mode === 'join' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <input style={inputStyle} placeholder="Your name" value={playerName} onChange={e => setName(e.target.value)} maxLength={16} autoFocus />
            <input style={{ ...inputStyle, fontFamily: 'var(--font-display)', fontSize: 18, letterSpacing: 2, textTransform: 'uppercase' }} placeholder="CACTUS-0000" value={roomCode} onChange={e => setRoomCode(e.target.value.toUpperCase())} onKeyDown={e => e.key === 'Enter' && joinRoom(roomCode.trim(), playerName.trim())} maxLength={11} />
            <button style={btnPrimary} onClick={() => joinRoom(roomCode.trim(), playerName.trim())} disabled={isLoading}>{isLoading ? 'Joining...' : 'Join Room →'}</button>
            <button onClick={() => setMode('choose')} style={btnBack}>← Back</button>
          </div>
        )}

        {lobbyError && (
          <div style={{ marginTop: 14, background: 'rgba(255,107,107,0.15)', border: '1px solid var(--coral)', borderRadius: 10, padding: '10px 14px', fontSize: 13, color: 'var(--coral)', textAlign: 'center' }}>{lobbyError}</div>
        )}
      </div>
    </div>
  )
}
