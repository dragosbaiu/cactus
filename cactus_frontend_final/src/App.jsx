import { useEffect } from 'react'
import { useGameStore } from './store/gameStore'
import { useWebSocket } from './hooks/useWebSocket'
import Lobby from './components/Lobby'
import WaitingRoom from './components/WaitingRoom'
import GameTable from './components/GameTable'
import Notifications from './components/Notifications'
import './styles/global.css'

function ConnectedGame() {
  const { roomCode, token, registerSendAction, gameState } = useGameStore()
  const { sendAction } = useWebSocket(roomCode, token)

  useEffect(() => {
    registerSendAction(sendAction)
  }, [sendAction, registerSendAction])

  // Read phase directly from gameState — this is reactive (re-renders when gameState changes)
  const phase = gameState?.game_phase ?? 'waiting'

  if (!gameState || phase === 'waiting') return <WaitingRoom />
  return <GameTable />
}

export default function App() {
  const { roomCode, token } = useGameStore()
  const hasSession = !!(roomCode && token)

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Notifications />
      {hasSession ? <ConnectedGame /> : <Lobby />}
    </div>
  )
}
