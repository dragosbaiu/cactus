"""
main.py — FastAPI server for Cactus.

ENDPOINTS:
    POST /rooms              — Create a new room, join as host
    POST /rooms/{code}/join  — Join an existing room
    WS   /rooms/{code}/ws   — WebSocket connection for real-time gameplay

HOW THE WEBSOCKET WORKS:
1. Player connects to /rooms/{code}/ws?token=<their_token>
2. Server verifies token, attaches WebSocket to their session
3. Server sends them the current game state immediately
4. Player sends action messages: { "action": "draw_card", ... }
5. Server processes action, broadcasts updated state to ALL players
6. Repeat until round ends

CORS:
We allow all origins in development. In production, restrict this to
your actual frontend domain.
"""

import json
import sys
import os

# Make the game engine importable — it lives in the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from room_manager import room_manager
from actions import handle_action

app = FastAPI(title="Cactus Game Server")

# ── CORS ───────────────────────────────────────────────────────────────────
# This allows the React frontend (running on a different port) to talk to us.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your Railway URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST endpoints ─────────────────────────────────────────────────────────

class CreateRoomRequest(BaseModel):
    player_name: str

class JoinRoomRequest(BaseModel):
    player_name: str


@app.get("/health")
def health():
    """Railway uses this to check the server is alive."""
    return {"status": "ok", "rooms": room_manager.active_room_count}


@app.post("/rooms")
def create_room(body: CreateRoomRequest):
    """
    Create a new room. The creating player becomes the host.

    Returns:
        room_code:  e.g. "CACTUS-4829"
        token:      secret token to store in the browser
        player_id:  this player's ID in the game engine
    """
    room = room_manager.create_room()
    player, is_host = room.add_player(body.player_name.strip() or "Host")

    return {
        "room_code": room.code,
        "token": player.token,
        "player_id": player.player_id,
        "is_host": is_host,
    }


@app.post("/rooms/{code}/join")
def join_room(code: str, body: JoinRoomRequest):
    """
    Join an existing room by code.

    Returns:
        token:      secret token to store in the browser
        player_id:  this player's ID in the game engine
    """
    room = room_manager.get_room(code.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    from game.game import GamePhase
    if room.game.game_phase != GamePhase.WAITING:
        raise HTTPException(status_code=400, detail="Game already started.")

    try:
        player, is_host = room.add_player(body.player_name.strip() or "Player")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "room_code": room.code,
        "token": player.token,
        "player_id": player.player_id,
        "is_host": is_host,
    }


# ── WebSocket endpoint ─────────────────────────────────────────────────────

@app.websocket("/rooms/{code}/ws")
async def websocket_endpoint(websocket: WebSocket, code: str, token: str):
    """
    Main real-time connection for gameplay.

    The token is passed as a query parameter:
        ws://server/rooms/CACTUS-4829/ws?token=abc123...

    Message format (client → server):
        { "action": "draw_card", ... }

    Message format (server → client):
        {
            "event": "state_update",
            "state": { ...personalized game state... },
            "your_player_id": "p1",
            "message": "Alice drew a card."
        }
    """
    # Must accept before sending anything (including close frames)
    await websocket.accept()

    # Verify room exists
    room = room_manager.get_room(code.upper())
    if not room:
        await websocket.send_text(json.dumps({
            "event": "error", "message": "Room not found. Please rejoin.", "fatal": True
        }))
        await websocket.close(code=4004)
        return

    # Verify token
    player = room.get_player_by_token(token)
    if not player:
        await websocket.send_text(json.dumps({
            "event": "error", "message": "Session expired. Please rejoin.", "fatal": True
        }))
        await websocket.close(code=4001)
        return

    room.connect(player, websocket)

    # Send current state immediately on connect
    await room.send_to(player.player_id, {
        "event": "connected",
        "message": f"Welcome, {player.name}! You are {'the host' if player.player_id == room.host_id else 'connected'}.",
    })

    # Notify others that this player connected
    await room.broadcast(
        {"event": "player_connected", "message": f"{player.name} connected."},
        exclude=player.player_id,
    )

    # ── Main message loop ──────────────────────────────────────────────────
    try:
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "message": "Invalid JSON."
                }))
                continue

            # Handle the action
            result = await handle_action(room, player.player_id, message)

            if result is None:
                pass  # action handled its own broadcasting
            elif not result.success:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "message": result.message,
                    "state": room.game_state_for(player.player_id),
                    "your_player_id": player.player_id,
                }))
            else:
                await room.broadcast({
                    "event": "state_update",
                    "message": result.message,
                })

    except WebSocketDisconnect:
        room.disconnect(websocket)
        await room.broadcast({
            "event": "player_disconnected",
            "message": f"{player.name} disconnected.",
        })
