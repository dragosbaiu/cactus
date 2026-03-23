"""
actions.py — Handles all game actions sent by players over WebSocket.

HOW ACTIONS WORK:
Every message from the frontend is a JSON object with an "action" field:
    { "action": "draw_card", "player_id": "p1", ... }

The handle_action function routes to the right handler, calls the
appropriate CactusGame method, and returns an ActionResult.

After every action, main.py broadcasts the updated game state to all players.

ACTION LIST:
    start_round       — host starts the game
    done_peeking      — player skips remaining initial peeks
    initial_peek      — player peeks at one of their cards during setup
    draw_card         — active player draws from deck
    place_drawn_card  — active player places drawn card in their row
    discard_card      — active player discards a card to the pile
    react             — any player reacts to the discard
    close_reaction    — active player closes the reaction window
    use_peek          — active player uses Q ability
    start_swap        — active player selects first card for J swap
    complete_swap     — active player selects second card for J swap
    say_cactus        — active player calls Cactus
    reorder_card      — player reorders their own cards freely
"""

from game.game import CactusGame, ActionResult
from room_manager import Room


async def handle_action(room: Room, player_id: str, message: dict) -> ActionResult:
    """
    Route an incoming action message to the correct game engine method.

    Args:
        room:       The room this action is happening in
        player_id:  The player sending the action
        message:    Parsed JSON message from the WebSocket

    Returns:
        ActionResult — success/fail + any data to send back
    """
    game: CactusGame = room.game
    action: str = message.get("action", "")

    # ── Lobby / setup ──────────────────────────────────────────────────────

    if action == "start_round":
        # Only the host can start the round
        if player_id != room.host_id:
            return ActionResult.fail("Only the host can start the round.")
        if len(room.players) < 2:
            return ActionResult.fail("Need at least 2 players to start.")
        return game.start_round()

    # ── Initial peek phase ─────────────────────────────────────────────────

    elif action == "initial_peek":
        position = message.get("position")
        if position is None:
            return ActionResult.fail("Missing position.")
        return game.initial_peek(player_id, int(position))

    elif action == "done_peeking":
        return game.done_peeking(player_id)

    # ── Main turn actions ──────────────────────────────────────────────────

    elif action == "draw_card":
        return game.draw_card(player_id)

    elif action == "place_drawn_card":
        position = message.get("position")
        if position is None:
            return ActionResult.fail("Missing position.")
        return game.place_drawn_card(player_id, int(position))

    elif action == "discard_card":
        position = message.get("position")
        if position is None:
            return ActionResult.fail("Missing position.")
        return game.discard_card(player_id, int(position))

    # ── Reactions ──────────────────────────────────────────────────────────

    elif action == "react":
        position = message.get("position")
        if position is None:
            return ActionResult.fail("Missing position.")
        return game.react(player_id, int(position))

    elif action == "close_reaction":
        return game.close_reaction_window(player_id)

    # ── Special abilities ──────────────────────────────────────────────────

    elif action == "use_peek":
        target_player_id = message.get("target_player_id")
        position = message.get("position")
        if not target_player_id or position is None:
            return ActionResult.fail("Missing target_player_id or position.")
        result = game.use_peek(player_id, target_player_id, int(position))

        if not result.success:
            return result

        # Extract the private peeked card before broadcasting
        peeked_card = result.data.pop("peeked_card", None)
        peeked_player = result.data.pop("peeked_player", None)
        peeked_position = result.data.pop("peeked_position", None)

        # Broadcast state update to everyone (without the peeked card)
        await room.broadcast({
            "event": "state_update",
            "message": result.message,
        })

        # THEN send the private peek result only to the acting player
        if peeked_card:
            await room.send_to(player_id, {
                "event": "peek_result",
                "peeked_card": peeked_card,
                "peeked_player_id": peeked_player,
                "peeked_position": peeked_position,
            })

        # Return None so main.py doesn't broadcast again
        return None

    elif action == "use_swap":
        player_a_id = message.get("player_a_id")
        position_a  = message.get("position_a")
        player_b_id = message.get("player_b_id")
        position_b  = message.get("position_b")
        if None in (player_a_id, position_a, player_b_id, position_b):
            return ActionResult.fail("Missing swap parameters.")
        return game.use_swap(
            player_id,
            player_a_id, int(position_a),
            player_b_id, int(position_b),
        )

    # ── Cactus ─────────────────────────────────────────────────────────────

    elif action == "say_cactus":
        return game.say_cactus(player_id)

    elif action == "pass_turn":
        return game.pass_cactus(player_id)

    # ── Free reorder (no J needed) ─────────────────────────────────────────

    elif action == "reorder_card":
        from_pos = message.get("from_position")
        to_pos   = message.get("to_position")
        if None in (from_pos, to_pos):
            return ActionResult.fail("Missing from_position or to_position.")
        # Find the player object and reorder
        game_player = game._get_player(player_id)
        if not game_player:
            return ActionResult.fail("Player not found.")
        try:
            game_player.reorder_own_cards(int(from_pos), int(to_pos))
            return ActionResult.ok("Card reordered.")
        except IndexError as e:
            return ActionResult.fail(str(e))

    else:
        return ActionResult.fail(f"Unknown action: '{action}'.")
