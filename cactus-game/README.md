# 🌵 Cactus — Card Game Engine

A Python implementation of the Cactus card game. This is **Phase 1** of a full multiplayer web app.

## Project Structure

```
cactus_game/
├── game/
│   ├── __init__.py
│   ├── card.py       # Card and Deck classes
│   ├── player.py     # Player class
│   └── game.py       # Core game engine (CactusGame)
├── tests/
│   └── test_game.py  # Unit tests
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the tests
python -m pytest tests/ -v
```

## How the Engine Works

The `CactusGame` class manages the entire game state. Every action returns an `ActionResult` with:
- `success` — whether the action was valid
- `message` — human-readable description
- `data` — JSON-serializable payload (for the frontend/backend)

### Turn Flow

```
DRAW → PLACE_DRAWN → DISCARD → REACTION → (SPECIAL_ABILITY) → next player's DRAW
```

### Example Usage

```python
from game.game import CactusGame

game = CactusGame()
game.add_player("p1", "Alice")
game.add_player("p2", "Bob")
game.start_round()

# Players peek at up to 2 cards during setup
game.initial_peek("p1", 0)   # Alice peeks at her card at position 0
game.initial_peek("p1", 1)   # Alice peeks at position 1
game.done_peeking("p2")      # Bob skips peeking

# Alice's turn
game.draw_card("p1")                  # Alice draws (she sees the card value)
game.place_drawn_card("p1", 2)        # She inserts it at position 2 in her row
game.discard_card("p1", 0)           # She discards the card at position 0

# Reaction window is now open — Bob can react if he has a matching card
game.react("p2", 1)                  # Bob tries to react with his card at position 1

# Alice closes the reaction window
game.close_reaction_window("p1")     # Turn advances to Bob

# Alice calls Cactus when she thinks she has the lowest sum
game.say_cactus("p1")
```

### Serialization

Every game state can be serialized for the web backend:

```python
state = game.to_dict(perspective_player_id="p1")
# Returns full game state with Alice's hand revealed (private), others hidden
```

## Phases Roadmap

- ✅ **Phase 1** — Game engine (this package)
- 🔜 **Phase 2** — React frontend (card table UI)
- 🔜 **Phase 3** — WebSocket multiplayer backend
