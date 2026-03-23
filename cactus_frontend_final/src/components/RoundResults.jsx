import { useGameStore } from '../store/gameStore'
import { CardFace } from './Card'

const POINTS_LABEL = {
  1: { color: 'var(--teal)',  label: '🥇 Winner' },
  2: { color: 'var(--gold)',  label: '🥈 Runner-up' },
  3: { color: 'var(--coral)', label: '🏆 Empty hand!' },
}

export default function RoundResults() {
  const { gameState, startRound, isHost } = useGameStore()
  if (!gameState || gameState.game_phase !== 'round_end') return null

  const players         = gameState.players ?? []
  const roundNumber     = gameState.round_number ?? 1
  const scoresThisRound = gameState.scores_this_round ?? {}
  const nextStarter     = gameState.next_round_starter_id ?? null
  const cactusPlayerId  = gameState.cactus_player_id ?? null

  const sorted = [...players].sort((a, b) =>
    (scoresThisRound[a.player_id] ?? 99) - (scoresThisRound[b.player_id] ?? 99)
  )

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 150 }}>
      <div style={{ background: 'linear-gradient(160deg, #1a6b3c, #124d2b)', border: '2px solid var(--gold)', borderRadius: 24, padding: '32px 40px', minWidth: 360, maxWidth: 500, boxShadow: '0 24px 60px rgba(0,0,0,0.6)', animation: 'popIn 0.4s ease' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, color: 'var(--gold)', letterSpacing: 1 }}>Round {roundNumber} Over!</div>
          {cactusPlayerId && <div style={{ fontSize: 14, color: 'var(--text-muted)', marginTop: 4 }}>🌵 {players.find(p => p.player_id === cactusPlayerId)?.name} said Cactus</div>}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
          {sorted.map((player, rank) => {
            const pts     = scoresThisRound[player.player_id] ?? 0
            const ptsInfo = POINTS_LABEL[pts]
            const slots   = player.hand ?? []
            return (
              <div key={player.player_id} style={{ display: 'flex', alignItems: 'center', gap: 12, background: rank === 0 ? 'rgba(240,192,64,0.1)' : 'rgba(0,0,0,0.2)', border: rank === 0 ? '1px solid rgba(240,192,64,0.3)' : '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '10px 14px', animation: `slideUp 0.3s ease ${rank * 100}ms both` }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, color: rank === 0 ? 'var(--gold)' : 'var(--text-muted)', width: 28, textAlign: 'center' }}>{rank + 1}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, color: player.player_id === cactusPlayerId ? 'var(--teal)' : 'var(--cream)' }}>
                    {player.name}
                    {player.player_id === cactusPlayerId && ' 🌵'}
                    {player.player_id === nextStarter && ' ⭐'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Total: {player.score}</div>
                </div>
                <div style={{ display: 'flex', gap: 3 }}>
                  {slots.map((slot, i) => slot.card ? <CardFace key={i} card={slot.card} size="small" /> : null)}
                </div>
                <div style={{ textAlign: 'right', minWidth: 60 }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, color: ptsInfo?.color || 'var(--coral)' }}>+{pts}</div>
                  {ptsInfo && <div style={{ fontSize: 10, color: ptsInfo.color }}>{ptsInfo.label}</div>}
                </div>
              </div>
            )
          })}
        </div>

        {nextStarter && <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>⭐ {players.find(p => p.player_id === nextStarter)?.name} starts next round</div>}

        {isHost
          ? <button onClick={startRound} style={{ width: '100%', background: 'linear-gradient(135deg, var(--gold-dark), var(--gold))', color: 'var(--text-dark)', fontFamily: 'var(--font-display)', fontSize: 20, padding: '12px 0', borderRadius: 14, border: 'none', boxShadow: '0 4px 14px rgba(240,192,64,0.4)', letterSpacing: 1, cursor: 'pointer' }}>Next Round →</button>
          : <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 14, padding: '12px 0' }}>⏳ Waiting for host to start next round...</div>
        }
      </div>
    </div>
  )
}
