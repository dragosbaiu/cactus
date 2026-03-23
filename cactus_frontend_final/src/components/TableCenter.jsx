import { useEffect, useState } from 'react'
import { useGameStore } from '../store/gameStore'
import { CardFace, CardBack } from './Card'

function CountdownRing({ deadline }) {
  const [progress, setProgress] = useState(1)
  const C = 126
  useEffect(() => {
    if (!deadline) return
    const tick = () => setProgress(Math.max(0, deadline - Date.now()) / 3000)
    tick()
    const id = setInterval(tick, 50)
    return () => clearInterval(id)
  }, [deadline])
  const color = progress > 0.5 ? '#00c9a7' : progress > 0.25 ? '#f0c040' : '#ff6b6b'
  return (
    <svg width={50} height={50} style={{ position: 'absolute', top: -8, left: -8, transform: 'rotate(-90deg)' }}>
      <circle cx={25} cy={25} r={20} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={3} />
      <circle cx={25} cy={25} r={20} fill="none" stroke={color} strokeWidth={3} strokeDasharray={C} strokeDashoffset={C * (1 - progress)} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.05s linear, stroke 0.3s' }} />
    </svg>
  )
}

export default function TableCenter() {
  const { gameState, myPlayerId, drawCard, sayCactus, closeReaction, passTurn } = useGameStore()
  const [reactionDeadline, setReactionDeadline] = useState(null)

  if (!gameState) return null

  const deckCount    = gameState.deck?.cards_remaining ?? 0
  const topDiscard   = gameState.deck?.top_discard ?? null
  const drawnCard    = gameState.drawn_card ?? null
  const turnPhase    = gameState.turn_phase ?? 'draw'
  const phase        = gameState.game_phase ?? 'waiting'
  const reactionOpen = turnPhase === 'reaction'
  const myTurn       = gameState.current_player_id === myPlayerId
  const isPlaying    = phase === 'playing' || phase === 'cactus_final'
  const activeName   = gameState.players?.find(p => p.player_id === gameState.current_player_id)?.name ?? ''

  useEffect(() => {
    if (reactionOpen) setReactionDeadline(Date.now() + 3000)
    else setReactionDeadline(null)
  }, [reactionOpen])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, position: 'relative', zIndex: 1 }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, color: 'var(--text-muted)', letterSpacing: 1, textTransform: 'uppercase' }}>
        {reactionOpen ? '⚡ React now!' : myTurn && isPlaying ? '👆 Your turn' : isPlaying ? `${activeName}'s turn` : ''}
      </div>

      <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
        {/* Draw pile */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <div style={{ position: 'relative', cursor: myTurn && turnPhase === 'draw' && isPlaying ? 'pointer' : 'default', transform: myTurn && turnPhase === 'draw' && isPlaying ? 'scale(1.05)' : 'scale(1)', transition: 'transform 0.15s' }} onClick={myTurn && turnPhase === 'draw' && isPlaying ? drawCard : undefined}>
            {deckCount > 2 && <div style={{ position: 'absolute', top: -3, left: -3, width: 72, height: 100, borderRadius: 8, background: '#8B0000', opacity: 0.5 }} />}
            {deckCount > 0 && <div style={{ position: 'absolute', top: -1.5, left: -1.5, width: 72, height: 100, borderRadius: 8, background: '#a00000', opacity: 0.7 }} />}
            <CardBack style={myTurn && turnPhase === 'draw' && isPlaying ? { boxShadow: '0 0 0 3px var(--gold), 0 6px 20px rgba(240,192,64,0.4)' } : {}} />
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700 }}>{deckCount} left</span>
        </div>

        <span style={{ fontSize: 20, opacity: 0.4 }}>→</span>

        {/* Discard pile */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <div style={{ position: 'relative' }}>
            {reactionOpen && topDiscard && <CountdownRing deadline={reactionDeadline} />}
            {topDiscard
              ? <CardFace card={topDiscard} style={reactionOpen ? { boxShadow: '0 0 0 3px var(--teal), 0 6px 20px rgba(0,201,167,0.4)' } : {}} />
              : <div style={{ width: 72, height: 100, borderRadius: 8, border: '2px dashed rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, opacity: 0.4 }}>🃏</div>
            }
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700 }}>Discard</span>
        </div>

        {/* Drawn card */}
        {drawnCard && myTurn && (
          <>
            <span style={{ fontSize: 20, opacity: 0.4 }}>→</span>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{ animation: 'popIn 0.3s ease' }}>
                <CardFace card={drawnCard} style={{ boxShadow: '0 0 0 3px var(--gold), 0 8px 24px rgba(240,192,64,0.5)' }} />
              </div>
              <span style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 700 }}>Click your row to place</span>
            </div>
          </>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center' }}>
        {myTurn && turnPhase === 'cactus_option' && (
          <button
            onClick={sayCactus}
            style={{ background: 'linear-gradient(135deg, #2d7a4a, #1a6b3c)', color: 'var(--gold)', fontFamily: 'var(--font-display)', fontSize: 18, padding: '8px 22px', borderRadius: 24, border: '2px solid var(--gold)', letterSpacing: 1, boxShadow: '0 4px 12px rgba(0,0,0,0.3)', cursor: 'pointer' }}
          >
            🌵 CACTUS!
          </button>
        )}
        {myTurn && turnPhase === 'cactus_option' && (
          <button
            onClick={passTurn}
            style={{ background: 'rgba(0,0,0,0.4)', color: 'var(--cream)', fontFamily: 'var(--font-display)', fontSize: 18, padding: '8px 22px', borderRadius: 24, border: '1.5px solid rgba(255,255,255,0.2)', letterSpacing: 1, cursor: 'pointer' }}
          >
            End Turn →
          </button>
        )}
        {reactionOpen && myTurn && (
          <button
            onClick={closeReaction}
            style={{ background: 'rgba(0,0,0,0.4)', color: 'var(--text-muted)', fontFamily: 'var(--font-body)', fontSize: 13, padding: '6px 16px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.15)', cursor: 'pointer' }}
          >
            Skip reaction →
          </button>
        )}
      </div>
    </div>
  )
}
