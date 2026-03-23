# 🌵 Cactus — Multiplayer Card Game

A fully functional real-time multiplayer implementation of the card game **Cactus**, built entirely through a conversational session with **Claude Sonnet 4.6** as an experiment in AI-assisted software development.

> This project was built to test Claude Sonnet 4.6's ability to design, architect, and implement a complete full-stack application from scratch — including game logic, a real-time backend, and a polished React frontend — through natural conversation alone, with no pre-written code.

---

## 🃏 About the Game

Cactus is a memory card game played with a standard 52-card deck. The goal is to have the **lowest sum of cards** in your hand.

### Rules
- Each player receives **4 face-down cards**
- At the start, each player may secretly peek at **up to 2** of their cards
- On your turn:
  1. Draw a card from the deck (you see its value)
  2. Choose where to insert it in your row
  3. Discard one card from your hand face-up to the pile
  4. If the discarded card is a **J** → swap any 2 cards between players
  5. If the discarded card is a **Q** → secretly peek at any 1 card
  6. After discarding, a **reaction window** opens — any player can discard a matching card
  7. At the end of your turn, you may call **🌵 CACTUS** if you believe you have the lowest sum
- Calling Cactus ends the round — all other players get one more turn
- **Scoring (lower is better, like golf):**
  - Cactus caller has the lowest sum → **1 point**
  - Cactus caller doesn't have the lowest sum → **0 points**, winner(s) get **2 points**
  - Player empties their hand before Cactus → **3 points**, others get **0**
- The winner of each round starts the next one

---

## 🏗️ Project Structure

```
cactus/
├── cactus-game/          # Phase 1 — Python game engine
│   ├── game/
│   │   ├── card.py       # Card and Deck classes
│   │   ├── player.py     # Player class
│   │   └── game.py       # Core game engine (CactusGame)
│   └── tests/
│       └── test_game.py  # 28 unit tests
│
├── cactus-backend/       # Phase 3 — FastAPI + WebSocket server
│   ├── game/             # Copy of game engine (imported by server)
│   ├── main.py           # FastAPI app, WebSocket endpoint
│   ├── room_manager.py   # Room creation, player tokens, broadcasting
│   ├── actions.py        # Game action routing
│   ├── requirements.txt
│   └── Procfile          # Railway deployment
│
└── cactus_frontend_final/ # Phase 2+3 — React + Vite frontend
    ├── src/
    │   ├── components/
    │   │   ├── GameTable.jsx     # Main game table
    │   │   ├── PlayerHand.jsx    # Card row with drag-to-reorder
    │   │   ├── TableCenter.jsx   # Deck, discard pile, action buttons
    │   │   ├── Card.jsx          # Individual card component
    │   │   ├── Lobby.jsx         # Create/join room screen
    │   │   ├── WaitingRoom.jsx   # Pre-game lobby
    │   │   ├── RoundResults.jsx  # End-of-round scores
    │   │   ├── PeekOverlay.jsx   # Private Q ability reveal
    │   │   └── Notifications.jsx # Toast messages
    │   ├── store/
    │   │   └── gameStore.js      # Zustand state management
    │   ├── hooks/
    │   │   └── useWebSocket.js   # WebSocket connection lifecycle
    │   └── styles/
    │       └── global.css        # CSS variables, animations, felt table
    ├── .env.development
    └── .env.production
```

---

## 🚀 Running Locally

### Backend

```bash
cd cactus-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# Runs at http://localhost:8000
```

### Frontend

```bash
cd cactus_frontend_final
npm install
npm run dev
# Runs at http://localhost:5173
```

### Testing the game engine

```bash
cd cactus-game
python3 -m venv venv
source venv/bin/activate
pip install pytest
python -m pytest tests/ -v
# 28 tests, all passing
```

---

## 🌐 How Multiplayer Works

1. One player creates a room → gets a code like `CACTUS-4829`
2. Friends enter the code from any device anywhere in the world
3. Each player gets a **secret token** stored in their browser for reconnection
4. All game actions are sent over **WebSockets** to the Python backend
5. The backend validates every action using the game engine
6. The server broadcasts a **personalized game state** to each player — your cards are visible to you, opponents' cards are hidden

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Game engine | Python 3.13 |
| Backend | FastAPI + WebSockets |
| Frontend | React 18 + Vite |
| State management | Zustand |
| Deployment | Railway (backend) + Vercel (frontend) |
| Fonts | Boogaloo + Nunito (Google Fonts) |

---

## 🤖 Built with Claude Sonnet 4.6

This entire project — from the initial game engine design to the real-time multiplayer architecture to the polished UI — was built in a single conversational session with **Claude Sonnet 4.6**.

The goal was to test Claude's ability to:
- **Architect** a non-trivial full-stack application from scratch
- **Translate** natural language game rules into working, tested code
- **Debug** errors from terminal output and browser console logs
- **Iterate** on a real codebase across multiple phases without losing context
- **Teach** React and Python concepts to a first-year CS student along the way

---

## 📋 Development Phases

- ✅ **Phase 1** — Python game engine with full rule implementation and 28 unit tests
- ✅ **Phase 2** — React frontend with mock local state (single device)
- ✅ **Phase 3** — Real-time multiplayer with FastAPI, WebSockets, room codes and player tokens
- 🔜 **Phase 4** — Deploy to Railway + Vercel for public access

---

## 📄 License

MIT — do whatever you want with it.
