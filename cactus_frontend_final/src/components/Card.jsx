import { useState, useEffect } from 'react'

const SUIT_SYMBOL = {
  hearts:   { symbol: '♥', color: 'var(--red)' },
  diamonds: { symbol: '♦', color: 'var(--red)' },
  clubs:    { symbol: '♣', color: 'var(--black)' },
  spades:   { symbol: '♠', color: 'var(--black)' },
}

export function CardBack({ size = 'normal', style = {} }) {
  const w = size === 'small' ? 52 : size === 'large' ? 90 : 72
  const h = size === 'small' ? 72 : size === 'large' ? 126 : 100
  return (
    <div style={{ width: w, height: h, borderRadius: 8, background: `linear-gradient(135deg, var(--card-back) 0%, var(--card-back2) 100%)`, border: '2px solid rgba(255,255,255,0.15)', boxShadow: '0 3px 8px var(--card-shadow)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', ...style }}>
      <div style={{ position: 'absolute', inset: 5, border: '1.5px solid rgba(255,255,255,0.2)', borderRadius: 4 }} />
      <div style={{ position: 'absolute', inset: 0, backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 6px, rgba(255,255,255,0.05) 6px, rgba(255,255,255,0.05) 7px)' }} />
      <span style={{ fontSize: size === 'small' ? 18 : 24, opacity: 0.4 }}>🌵</span>
    </div>
  )
}

export function CardFace({ card, size = 'normal', style = {} }) {
  const w = size === 'small' ? 52 : size === 'large' ? 90 : 72
  const h = size === 'small' ? 72 : size === 'large' ? 126 : 100
  const { symbol, color } = SUIT_SYMBOL[card?.suit] || { symbol: '?', color: '#333' }
  const fontSize = size === 'small' ? 11 : size === 'large' ? 18 : 14
  const centerSize = size === 'small' ? 18 : size === 'large' ? 32 : 26
  return (
    <div style={{ width: w, height: h, borderRadius: 8, background: 'var(--card-bg)', border: '2px solid var(--card-border)', boxShadow: '0 3px 8px var(--card-shadow)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '4px 5px', color, position: 'relative', overflow: 'hidden', ...style }}>
      <div style={{ lineHeight: 1 }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize, fontWeight: 700 }}>{card?.value}</div>
        <div style={{ fontSize: fontSize - 3 }}>{symbol}</div>
      </div>
      <div style={{ textAlign: 'center', fontSize: centerSize, lineHeight: 1 }}>{symbol}</div>
      <div style={{ lineHeight: 1, textAlign: 'right', transform: 'rotate(180deg)' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize, fontWeight: 700 }}>{card?.value}</div>
        <div style={{ fontSize: fontSize - 3 }}>{symbol}</div>
      </div>
    </div>
  )
}

export default function Card({ card, faceDown, size = 'normal', onClick, highlighted, selected, dimmed, dealDelay = 0, shake, style = {} }) {
  const [animating, setAnimating] = useState(false)
  const showBack = faceDown !== undefined ? faceDown : card?.faceDown

  useEffect(() => {
    if (shake) {
      setAnimating(true)
      const t = setTimeout(() => setAnimating(false), 500)
      return () => clearTimeout(t)
    }
  }, [shake])

  let ringStyle = {}
  if (selected)     ringStyle = { boxShadow: '0 0 0 3px var(--teal), 0 4px 12px rgba(0,201,167,0.4)', borderRadius: 8 }
  else if (highlighted) ringStyle = { boxShadow: '0 0 0 3px var(--gold), 0 4px 12px rgba(240,192,64,0.4)', borderRadius: 8, animation: 'pulse 1.5s ease infinite' }

  return (
    <div
      style={{ display: 'inline-block', cursor: onClick ? 'pointer' : 'default', opacity: dimmed ? 0.4 : 1, transition: 'transform 0.15s ease, opacity 0.2s', animation: animating ? 'shake 0.5s ease' : 'none', position: 'relative', ...style, ...ringStyle }}
      onClick={onClick}
    >
      {showBack ? <CardBack size={size} /> : <CardFace card={card} size={size} />}
    </div>
  )
}
