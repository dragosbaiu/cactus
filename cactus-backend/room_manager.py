"""
room_manager.py — Manages game rooms and player identity tokens.

WHAT IS A ROOM?
A room is one instance of a Cactus game. Players create a room,
get a 4-digit code (e.g. CACTUS-4829), and share it with friends.
Each room has its own CactusGame instance and a list of connected players.

PLAYER TOKENS:
Since we have no login system, each player gets a unique secret token
when they first join a room. This token is stored in their browser
(localStorage). If they refresh or reconnect, they send the token and
the server recognizes them and restores their session.

WEBSOCKET CONNECTIONS:
Each connected player has an active WebSocket connection. When the game
state changes, we broadcast the new state to all connections in the room.
Crucially, each player gets a PERSONALIZED view of the state — their own
cards are revealed, opponents' cards are hidden.
"""

import random
import string
import secrets
from typing import Optional
from fastapi import WebSocket
from game.game import CactusGame, GamePhase


def _generate_room_code() -> str:
    """Generate a readable 4-digit room code like CACTUS-4829."""
    digits = ''.join(random.choices(string.digits, k=4))
    return f"CACTUS-{digits}"


def _generate_token() -> str:
    """Generate a cryptographically secure player token."""
    return secrets.token_hex(16)  # 32-character hex string


class ConnectedPlayer:
    """
    Represents one player's session in a room.

    Attributes:
        player_id:  ID used inside the CactusGame engine (e.g. "p1")
        name:       Display name chosen by the player
        token:      Secret token stored in the player's browser
        websocket:  Active WebSocket connection (None if disconnected)
    """

    def __init__(self, player_id: str, name: str, token: str):
        self.player_id = player_id
        self.name = name
        self.token = token
        self.websocket: Optional[WebSocket] = None

    @property
    def is_connected(self) -> bool:
        return self.websocket is not None


class Room:
    """
    One game room — holds a CactusGame instance and all connected players.

    Attributes:
        code:     The room code (e.g. "CACTUS-4829")
        host_id:  player_id of the player who created the room
        game:     The CactusGame engine instance
        players:  List of ConnectedPlayer objects
    """

    MAX_PLAYERS = 8

    def __init__(self, code: str):
        self.code = code
        self.host_id: Optional[str] = None
        self.game = CactusGame()
        self.players: list[ConnectedPlayer] = []

    def add_player(self, name: str) -> tuple[ConnectedPlayer, bool]:
        """
        Add a new player to the room.

        Returns:
            (ConnectedPlayer, is_host) — the new player and whether they're the host
        """
        if len(self.players) >= self.MAX_PLAYERS:
            raise ValueError(f"Room is full ({self.MAX_PLAYERS} players max).")

        player_id = f"p{len(self.players) + 1}"
        token = _generate_token()
        player = ConnectedPlayer(player_id, name, token)
        self.players.append(player)

        # Add to the game engine too
        self.game.add_player(player_id, name)

        is_host = len(self.players) == 1
        if is_host:
            self.host_id = player_id

        return player, is_host

    def get_player_by_token(self, token: str) -> Optional[ConnectedPlayer]:
        return next((p for p in self.players if p.token == token), None)

    def get_player_by_id(self, player_id: str) -> Optional[ConnectedPlayer]:
        return next((p for p in self.players if p.player_id == player_id), None)

    def get_player_by_websocket(self, ws: WebSocket) -> Optional[ConnectedPlayer]:
        return next((p for p in self.players if p.websocket == ws), None)

    def connect(self, player: ConnectedPlayer, websocket: WebSocket):
        """Attach a WebSocket to a player (new connection or reconnect)."""
        player.websocket = websocket

    def disconnect(self, websocket: WebSocket):
        """Detach WebSocket when a player disconnects."""
        player = self.get_player_by_websocket(websocket)
        if player:
            player.websocket = None

    @property
    def connected_count(self) -> int:
        return sum(1 for p in self.players if p.is_connected)

    @property
    def all_connected(self) -> bool:
        return all(p.is_connected for p in self.players)

    def game_state_for(self, player_id: str) -> dict:
        """
        Build the full game state personalized for one player.
        Their own cards are revealed; opponents' cards are hidden.
        Also includes room metadata (who's connected, who's the host).
        """
        state = self.game.to_dict(perspective_player_id=player_id)
        state["room"] = {
            "code": self.code,
            "host_id": self.host_id,
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "is_connected": p.is_connected,
                }
                for p in self.players
            ],
        }
        return state

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """
        Send a message to all connected players.
        Each player gets a personalized game state.

        Args:
            message:  Base message dict (will have 'state' added per-player)
            exclude:  player_id to skip (rarely needed)
        """
        import json
        for player in self.players:
            if not player.is_connected:
                continue
            if exclude and player.player_id == exclude:
                continue
            try:
                # Each player gets their own personalized state
                personalized = {
                    **message,
                    "state": self.game_state_for(player.player_id),
                    "your_player_id": player.player_id,
                }
                await player.websocket.send_text(json.dumps(personalized))
            except Exception:
                # Connection dropped — mark as disconnected
                player.websocket = None

    async def send_to(self, player_id: str, message: dict):
        """Send a message to one specific player only."""
        import json
        player = self.get_player_by_id(player_id)
        if player and player.is_connected:
            try:
                personalized = {
                    **message,
                    "state": self.game_state_for(player_id),
                    "your_player_id": player_id,
                }
                await player.websocket.send_text(json.dumps(personalized))
            except Exception:
                player.websocket = None


class RoomManager:
    """
    Global registry of all active rooms.
    In a real production app this would be backed by Redis,
    but for our use case an in-memory dict is perfectly fine.
    """

    def __init__(self):
        self._rooms: dict[str, Room] = {}

    def create_room(self) -> Room:
        """Create a new room with a unique code."""
        # Keep generating until we get a unique code (practically instant)
        while True:
            code = _generate_room_code()
            if code not in self._rooms:
                room = Room(code)
                self._rooms[code] = room
                return room

    def get_room(self, code: str) -> Optional[Room]:
        return self._rooms.get(code.upper())

    def delete_room(self, code: str):
        self._rooms.pop(code, None)

    @property
    def active_room_count(self) -> int:
        return len(self._rooms)


# Single global instance — imported by main.py
room_manager = RoomManager()
