import { useState, useEffect, useRef } from 'react'
import { useGameStore } from '../store/gameStore'
import Card from './Card'

export default function PlayerHand({
  player, isCurrentPlayer, isMe,
  onCardClick, highlightPositions, selectedPosition,
  compact = false,
}) {
  const { gameState, myPlayerId, reorderCard } = useGameStore()
  const pendingAbility = gameState?.pending_ability ?? null
  const turnPhase      = gameState?.turn_phase ?? 'draw'
  const phase          = gameState?.game_phase ?? 'waiting'
  const drawnCard      = gameState?.drawn_card ?? null
  const reactionOpen   = turnPhase === 'reaction'
  const isMyTurn       = gameState?.current_player_id === myPlayerId

  const [revealedPositions, setRevealedPositions] = useState(new Set())
  const [dragFromIdx, setDragFromIdx] = useState(null)
  const [dragOverIdx, setDragOverIdx] = useState(null)

  // Track newly added/replaced card for animation
  const handSlots = player.hand ?? []
  const prevHandRef = useRef([])
  const [animatingIdx, setAnimatingIdx] = useState(null)

  useEffect(() => {
    const prev = prevHandRef.current
    const curr = handSlots
    let changedIdx = -1

    for (let i = 0; i < curr.length; i++) {
      const prevCard = prev[i]?.card
      const currCard = curr[i]?.card
      if (currCard && prev.length > 0 && (!prevCard || prevCard.suit !== currCard.suit || prevCard.value !== currCard.value)) {
        changedIdx = i
        break
      }
    }

    if (changedIdx >= 0) {
      setAnimatingIdx(changedIdx)
      setTimeout(() => setAnimatingIdx(null), 500)
    }

    prevHandRef.current = curr
  }, [handSlots])

  function peekAt(position) {
    setRevealedPositions(prev => new Set([...prev, position]))
    setTimeout(() => {
      setRevealedPositions(prev => {
        const next = new Set(prev)
        next.delete(position)
        return next
      })
    }, 2000)
    onCardClick?.(position)
  }

  const canInteract    = isMe && (turnPhase === 'discard' || (pendingAbility && isMyTurn) || reactionOpen)
  const canInitialPeek = isMe && phase === 'initial_peek'
  const canPlace       = isMe && turnPhase === 'place_drawn' && !!drawnCard
  const opponentCanBeTargeted = !isMe && isMyTurn &&
    (pendingAbility === 'peek' || pendingAbility === 'swap')
  const clickable = canInteract || canInitialPeek || canPlace ||
    opponentCanBeTargeted || (pendingAbility === 'swap' && isMyTurn)
  const canDrag = isMe && !canPlace && !canInitialPeek &&
    turnPhase !== 'discard' && turnPhase !== 'reaction' && turnPhase !== 'special_ability'

  function handleDragStart(e, idx) {
    if (!canDrag) return
    setDragFromIdx(idx)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setDragImage(e.currentTarget, 36, 50)
  }

  function handleDragOver(e, idx) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (idx !== dragOverIdx) setDragOverIdx(idx)
  }

  function handleDrop(e, toIdx) {
    e.preventDefault()
    if (dragFromIdx === null || dragFromIdx === toIdx) {
      setDragFromIdx(null)
      setDragOverIdx(null)
      return
    }
    reorderCard(dragFromIdx, toIdx)
    setDragFromIdx(null)
    setDragOverIdx(null)
  }

  function handleDragEnd() {
    setDragFromIdx(null)
    setDragOverIdx(null)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: compact ? 6 : 10 }}>

      {/* Name badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: isCurrentPlayer ? 'rgba(240,192,64,0.25)' : 'rgba(0,0,0,0.25)', border: isCurrentPlayer ? '1.5px solid var(--gold)' : '1.5px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: compact ? '3px 10px' : '5px 14px', transition: 'all 0.3s ease', backdropFilter: 'blur(4px)' }}>
        {player.has_said_cactus && <span style={{ fontSize: compact ? 14 : 18, animation: 'cactusShout 0.6s ease' }}>🌵</span>}
        <span style={{ fontFamily: 'var(--font-display)', fontSize: compact ? 14 : 18, color: isCurrentPlayer ? 'var(--gold)' : 'var(--cream)', letterSpacing: '0.5px' }}>{player.name}</span>
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '1px 7px', fontSize: compact ? 11 : 13, color: 'var(--text-muted)', fontWeight: 700 }}>{player.score}</div>
        {isCurrentPlayer && <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gold)', boxShadow: '0 0 6px var(--gold)', animation: 'pulse 1s ease infinite' }} />}
      </div>

      {/* Drag hint */}
      {isMe && canDrag && handSlots.length > 1 && (
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)', letterSpacing: 0.5 }}>drag to reorder</div>
      )}

      {/* Cards row */}
      <div style={{ display: 'flex', gap: compact ? 6 : 8, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
        {handSlots.map((slot, idx) => {
          const position  = slot.position ?? idx
          const card      = slot.card
          const isRevealed = isMe && revealedPositions.has(position)
          const faceDown  = isMe ? !isRevealed : (card === null)
          const cardObj   = card
            ? { suit: card.suit, value: card.value, points: card.points }
            : { suit: 'spades', value: '?', points: 0 }

          const isHighlighted = opponentCanBeTargeted ||
            ((highlightPositions?.includes(position) || canInteract || canInitialPeek || canPlace) && !selectedPosition)
          const isSelected    = selectedPosition === position
          const isNewCard     = idx === animatingIdx
          const isDragTarget  = canDrag && dragOverIdx === idx && dragFromIdx !== idx

          const handleClick = canInitialPeek
            ? () => peekAt(position)
            : clickable ? () => onCardClick?.(position) : undefined

          return (
            <div
              key={position}
              draggable={canDrag}
              onDragStart={e => handleDragStart(e, idx)}
              onDragOver={e => handleDragOver(e, idx)}
              onDrop={e => handleDrop(e, idx)}
              onDragEnd={handleDragEnd}
              style={{
                transition: 'transform 0.15s ease',
                transform: isDragTarget ? 'translateX(8px)' : 'none',
                opacity: dragFromIdx === idx ? 0.4 : 1,
                cursor: canDrag ? 'grab' : 'default',
              }}
            >
              <Card
                card={cardObj}
                faceDown={faceDown}
                size={compact ? 'small' : 'normal'}
                highlighted={isHighlighted && !isSelected && !isNewCard}
                selected={isSelected}
                onClick={handleClick}
                dealDelay={0}
                style={isNewCard ? { animation: 'dealIn 0.4s ease both' } : {}}
              />
            </div>
          )
        })}

        {handSlots.length === 0 && (
          <div style={{ width: 72, height: 100, borderRadius: 8, border: '2px dashed rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, opacity: 0.5 }}>🎉</div>
        )}
      </div>
    </div>
  )
}
