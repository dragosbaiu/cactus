import { useGameStore } from '../store/gameStore'
import PlayerHand from './PlayerHand'
import TableCenter from './TableCenter'
import PeekOverlay from './PeekOverlay'
import Notifications from './Notifications'
import RoundResults from './RoundResults'

export default function GameTable() {
  const {
    gameState, myPlayerId, swapStep, peekReveal,
    discardCard, placeDrawnCard,
    initialPeek, donePeeking,
    react, usePeek, startSwap, completeSwap,
    passTurn,
  } = useGameStore()

  if (!gameState) return null

  const players        = gameState.players ?? []
  const phase          = gameState.game_phase ?? 'waiting'
  const turnPhase      = gameState.turn_phase ?? 'draw'
  const drawnCard      = gameState.drawn_card ?? null
  const pendingAbility = gameState.pending_ability ?? null
  const reactionOpen   = turnPhase === 'reaction'
  const activePlayerId = gameState.current_player_id
  const roundNumber    = gameState.round_number ?? 1
  const peeksRemaining = gameState.initial_peeks_remaining ?? {}

  const me        = players.find(p => p.player_id === myPlayerId)
  const opponents = players.filter(p => p.player_id !== myPlayerId)
  const isMyTurn  = activePlayerId === myPlayerId

  if (!me) return null

  function handleMyCardClick(position) {
    if (phase === 'initial_peek') {
      if ((peeksRemaining[myPlayerId] ?? 0) > 0) initialPeek(position)
      return
    }
    if (turnPhase === 'place_drawn' && drawnCard) {
      placeDrawnCard(position)
      return
    }
    if (pendingAbility === 'peek' && isMyTurn) {
      usePeek(myPlayerId, position)
      return
    }
    if (pendingAbility === 'swap' && isMyTurn) {
      if (!swapStep) startSwap(myPlayerId, position)
      else completeSwap(myPlayerId, position)
      return
    }
    if (isMyTurn && turnPhase === 'discard') {
      discardCard(position)
      return
    }
    if (reactionOpen) {
      react(position)
      return
    }
  }

  function handleOpponentCardClick(playerId, position) {
    if (pendingAbility === 'peek' && isMyTurn) {
      usePeek(playerId, position)
      return
    }
    if (pendingAbility === 'swap' && isMyTurn) {
      if (!swapStep) startSwap(playerId, position)
      else completeSwap(playerId, position)
      return
    }
    if (reactionOpen) {
      react(position)
      return
    }
  }

  function getMyHighlights() {
    const myHand = me.hand ?? []
    const allPositions = myHand.map((_, i) => i)
    if (phase === 'initial_peek' && (peeksRemaining[myPlayerId] ?? 0) > 0) return allPositions
    if (turnPhase === 'place_drawn' && drawnCard) return allPositions
    if (pendingAbility === 'peek' && isMyTurn)    return allPositions
    if (pendingAbility === 'swap' && isMyTurn)    return allPositions
    if (isMyTurn && turnPhase === 'discard')      return allPositions
    if (reactionOpen)                             return allPositions
    return []
  }

  function getHint() {
    if (phase === 'initial_peek') {
      const left = peeksRemaining[myPlayerId] ?? 0
      return left > 0 ? `👀 Click up to ${left} of your cards to peek` : '✅ Done peeking — waiting for others...'
    }
    if (pendingAbility === 'peek' && isMyTurn)
      return '👁️ Click any card to peek at it secretly'
    if (pendingAbility === 'swap' && isMyTurn)
      return swapStep ? '🔄 Now click the second card' : '🔄 Click the first card to swap'
    if (turnPhase === 'cactus_option' && isMyTurn)
      return '🌵 Call Cactus or end your turn'
    if (!isMyTurn) return null
    if (turnPhase === 'draw')        return '🃏 Click the deck to draw a card'
    if (turnPhase === 'place_drawn') return '📍 Click your row to place the drawn card'
    if (turnPhase === 'discard')     return '🗑️ Click one of your cards to discard it'
    return null
  }

  const hint = getHint()

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px 20px', zIndex: 1 }}>
      <Notifications />
      <div style={{ position: 'absolute', top: 16, right: 20, fontFamily: 'var(--font-display)', fontSize: 13, color: 'rgba(255,255,255,0.2)', letterSpacing: 1 }}>ROUND {roundNumber}</div>

      {/* Opponents */}
      <div style={{ display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap', width: '100%', paddingTop: 8 }}>
        {opponents.map(opp => (
          <PlayerHand
            key={opp.player_id}
            player={opp}
            isCurrentPlayer={opp.player_id === activePlayerId}
            isMe={false}
            compact={true}
            onCardClick={pos => handleOpponentCardClick(opp.player_id, pos)}
            selectedPosition={swapStep?.playerId === opp.player_id ? swapStep.position : undefined}
          />
        ))}
      </div>

      <TableCenter />

      {hint && (
        <div style={{ background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: '6px 18px', fontSize: 13, color: 'var(--gold)', fontWeight: 600, backdropFilter: 'blur(4px)', animation: 'slideUp 0.2s ease', marginBottom: 4 }}>
          {hint}
        </div>
      )}

      {/* My hand */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
        <PlayerHand
          player={me}
          isCurrentPlayer={isMyTurn}
          isMe={true}
          onCardClick={handleMyCardClick}
          highlightPositions={getMyHighlights()}
          selectedPosition={swapStep?.playerId === myPlayerId ? swapStep.position : undefined}
        />
        {phase === 'initial_peek' && (
          <button onClick={donePeeking} style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)', fontFamily: 'var(--font-body)', fontSize: 13, padding: '6px 18px', borderRadius: 20, border: '1px solid rgba(255,255,255,0.15)', marginTop: 4, cursor: 'pointer' }}>
            Done peeking →
          </button>
        )}
      </div>

      <PeekOverlay peekReveal={peekReveal} players={players} />
      <RoundResults />
    </div>
  )
}
