import { create } from 'zustand'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useGameStore = create((set, get) => ({

  // ── Session (persisted in localStorage) ──────────────────────────────────
  roomCode:   localStorage.getItem('cactus_room')         || null,
  token:      localStorage.getItem('cactus_token')        || null,
  myPlayerId: localStorage.getItem('cactus_pid')          || null,
  isHost:     localStorage.getItem('cactus_host') === 'true',

  // ── Connection ────────────────────────────────────────────────────────────
  connectionStatus: 'disconnected',

  // ── Game state (from server) ──────────────────────────────────────────────
  gameState:     null,
  notifications: [],

  // ── Local UI only ─────────────────────────────────────────────────────────
  peekReveal: null,
  swapStep:   null,
  lobbyError: null,
  isLoading:  false,

  // ── WebSocket send fn (injected by useWebSocket hook) ─────────────────────
  _sendAction: null,
  registerSendAction: (fn) => set({ _sendAction: fn }),
  send(action, data = {}) {
    const fn = get()._sendAction
    if (fn) fn(action, data)
    else console.warn('WebSocket not ready:', action)
  },

  // ── Handle incoming server messages ───────────────────────────────────────
  handleServerMessage(message) {
    const { event, state, message: msg, your_player_id } = message
    if (state)          set({ gameState: state })
    if (your_player_id) set({ myPlayerId: your_player_id })

    if (event === 'peek_result') {
      set({ peekReveal: { card: message.peeked_card, playerId: message.peeked_player_id, position: message.peeked_position } })
      setTimeout(() => set({ peekReveal: null }), 2500)
      return
    }

    if (event === 'error') {
      if (msg) get().addNotification(`❌ ${msg}`, 'error')
      if (message.fatal) get().leaveRoom()
      return
    }

    const notifMap = {
      connected:           ['success', msg],
      state_update:        ['info',    msg],
      player_connected:    ['info',    `🟢 ${msg}`],
      player_disconnected: ['error',   `🔴 ${msg}`],
    }
    const [type, text] = notifMap[event] || []
    if (text) get().addNotification(text, type)
  },

  setConnectionStatus(status) {
    set({ connectionStatus: status })
    if (status === 'disconnected') get().addNotification('🔌 Reconnecting...', 'error')
  },

  // ── Lobby HTTP calls ───────────────────────────────────────────────────────
  async createRoom(playerName) {
    set({ isLoading: true, lobbyError: null })
    try {
      const res  = await fetch(`${API_BASE}/rooms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: playerName }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to create room.')
      get()._saveSession(data)
      return data
    } catch (e) {
      set({ lobbyError: e.message })
      return null
    } finally {
      set({ isLoading: false })
    }
  },

  async joinRoom(roomCode, playerName) {
    set({ isLoading: true, lobbyError: null })
    try {
      const res  = await fetch(`${API_BASE}/rooms/${roomCode.toUpperCase()}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: playerName }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to join room.')
      get()._saveSession(data)
      return data
    } catch (e) {
      set({ lobbyError: e.message })
      return null
    } finally {
      set({ isLoading: false })
    }
  },

  _saveSession(data) {
    localStorage.setItem('cactus_room',  data.room_code)
    localStorage.setItem('cactus_token', data.token)
    localStorage.setItem('cactus_pid',   data.player_id)
    localStorage.setItem('cactus_host',  data.is_host ? 'true' : 'false')
    set({ roomCode: data.room_code, token: data.token, myPlayerId: data.player_id, isHost: data.is_host })
  },

  leaveRoom() {
    ['cactus_room','cactus_token','cactus_pid','cactus_host'].forEach(k => localStorage.removeItem(k))
    set({ roomCode: null, token: null, myPlayerId: null, isHost: false, gameState: null, peekReveal: null, swapStep: null })
  },

  // ── Game actions over WebSocket ────────────────────────────────────────────
  startRound:     ()         => get().send('start_round'),
  drawCard:       ()         => get().send('draw_card'),
  placeDrawnCard: (pos)      => get().send('place_drawn_card',  { position: pos }),
  discardCard:    (pos)      => get().send('discard_card',      { position: pos }),
  react:          (pos)      => get().send('react',             { position: pos }),
  closeReaction:  ()         => get().send('close_reaction'),
  sayCactus:      ()         => get().send('say_cactus'),
  donePeeking:    ()         => get().send('done_peeking'),
  initialPeek:    (pos)      => get().send('initial_peek',      { position: pos }),
  reorderCard:    (from, to) => get().send('reorder_card',      { from_position: from, to_position: to }),
  usePeek:        (tid, pos) => get().send('use_peek',          { target_player_id: tid, position: pos }),
  passTurn: () => get().send('pass_turn'),
  
  startSwap(playerId, position) { set({ swapStep: { playerId, position } }) },
  completeSwap(playerId, position) {
    const s = get().swapStep
    if (!s) return
    get().send('use_swap', { player_a_id: s.playerId, position_a: s.position, player_b_id: playerId, position_b: position })
    set({ swapStep: null })
  },

  // ── Notifications ──────────────────────────────────────────────────────────
  addNotification(message, type = 'info') {
    const id = Date.now() + Math.random()
    set(s => ({ notifications: [...s.notifications, { id, message, type }] }))
    setTimeout(() => set(s => ({ notifications: s.notifications.filter(n => n.id !== id) })), 3000)
  },
}))
