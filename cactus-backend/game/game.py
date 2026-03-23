"""
game.py — Core game engine for Cactus.

This module manages the full game state and enforces all rules.
It is intentionally stateless between method calls — every action
returns an updated state dict so it can plug cleanly into a web backend.

Turn flow:
  1. Active player draws a card (sees its value, chooses where to place it)
  2. Active player discards one card from their hand to the central pile
  3. If discarded card is J or Q → reaction phase first, then special ability
  4. Any player (including active) can react to the discard if they have a match
  5. Reactions are processed first-come-first-served
  6. Next player's turn (clockwise)
"""

from __future__ import annotations
import random
from enum import Enum, auto
from typing import Optional
from game.card import Card, Deck
from game.player import Player


# ------------------------------------------------------------------ #
#  Enums for game and turn phases                                     #
# ------------------------------------------------------------------ #

class GamePhase(str, Enum):
    WAITING         = "waiting"          # Lobby, waiting for players
    INITIAL_PEEK    = "initial_peek"     # Players peeking at their 2 cards
    PLAYING         = "playing"          # Main game loop
    CACTUS_FINAL    = "cactus_final"     # Last round after Cactus is called
    ROUND_END       = "round_end"        # Scoring, about to start new round
    GAME_OVER       = "game_over"        # Players decided to stop


class TurnPhase(str, Enum):
    DRAW            = "draw"             # Player must draw a card
    PLACE_DRAWN     = "place_drawn"      # Player chooses where to insert drawn card
    DISCARD         = "discard"          # Player chooses which card to discard
    SPECIAL_ABILITY = "special_ability"  # J or Q ability being resolved
    REACTION        = "reaction"         # Open window for other players to react
    CACTUS_OPTION   = "cactus_option"
    DONE            = "done"             # Turn complete, move to next player


class SpecialAbility(str, Enum):
    PEEK = "peek"   # Q: look at one card
    SWAP = "swap"   # J: swap two cards


# ------------------------------------------------------------------ #
#  Action result — every public method returns one of these          #
# ------------------------------------------------------------------ #

class ActionResult:
    """Wraps the outcome of any game action."""

    def __init__(self, success: bool, message: str, data: Optional[dict] = None):
        self.success = success
        self.message = message
        self.data = data or {}

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data
        }

    @classmethod
    def ok(cls, message: str, data: Optional[dict] = None) -> "ActionResult":
        return cls(True, message, data)

    @classmethod
    def fail(cls, message: str) -> "ActionResult":
        return cls(False, message)


# ------------------------------------------------------------------ #
#  Main Game class                                                    #
# ------------------------------------------------------------------ #

class CactusGame:
    """
    Manages a full Cactus game session.

    Usage:
        game = CactusGame()
        game.add_player("p1", "Alice")
        game.add_player("p2", "Bob")
        game.start_round()
        # ... players take actions via the public methods below
    """

    CARDS_PER_PLAYER    = 4
    INITIAL_PEEK_COUNT  = 2
    MIN_PLAYERS         = 2
    MAX_PLAYERS         = 8
    REACTION_WINDOW_SEC = 3   # seconds UI should wait for reactions

    def __init__(self):
        self.players: list[Player] = []
        self.deck: Optional[Deck] = None
        self.game_phase: GamePhase = GamePhase.WAITING
        self.turn_phase: TurnPhase = TurnPhase.DRAW
        self.current_player_index: int = 0
        self.cactus_player_id: Optional[str] = None
        self.cactus_laps_remaining: int = 0  # how many players still get their last turn
        self.drawn_card: Optional[Card] = None        # card drawn this turn, not yet placed
        self.pending_ability: Optional[SpecialAbility] = None
        self.round_number: int = 0
        self.initial_peeks_remaining: dict[str, int] = {}  # player_id → peeks left
        self.next_round_starter_id: Optional[str] = None   # who starts the next round
        self._last_round_scores: dict = {} 
        self._reaction_passes: set = set()


    # ------------------------------------------------------------------ #
    #  Setup                                                              #
    # ------------------------------------------------------------------ #

    def add_player(self, player_id: str, name: str) -> ActionResult:
        """Add a player to the lobby before the game starts."""
        if self.game_phase != GamePhase.WAITING:
            return ActionResult.fail("Cannot add players after the game has started.")
        if len(self.players) >= self.MAX_PLAYERS:
            return ActionResult.fail(f"Maximum {self.MAX_PLAYERS} players allowed.")
        if any(p.player_id == player_id for p in self.players):
            return ActionResult.fail(f"Player ID '{player_id}' is already in the game.")

        self.players.append(Player(player_id, name))
        return ActionResult.ok(f"{name} joined the game.")

    def start_round(self) -> ActionResult:
        """
        Deal cards and enter the initial peek phase.
        Can be called at game start or to begin a new round.
        """
        if len(self.players) < self.MIN_PLAYERS:
            return ActionResult.fail(
                f"Need at least {self.MIN_PLAYERS} players to start."
            )

        self.round_number += 1
        self.deck = Deck()
        self.cactus_player_id = None
        self.cactus_laps_remaining = 0
        self.drawn_card = None
        self.pending_ability = None
        self._reaction_passes = set()
        self.turn_phase = TurnPhase.DRAW

        # Determine who starts this round
        if self.next_round_starter_id is None:
            # Round 1: pick randomly
            self.current_player_index = random.randrange(len(self.players))
        else:
            starter = self._get_player(self.next_round_starter_id)
            if starter:
                self.current_player_index = self.players.index(starter)
            else:
                self.current_player_index = random.randrange(len(self.players))
        self.next_round_starter_id = None  # reset until end of round

        # Reset each player's hand and cactus flag
        for player in self.players:
            player.hand = []
            player.reset_cactus_flag()

        # Deal 4 cards to each player
        for _ in range(self.CARDS_PER_PLAYER):
            for player in self.players:
                player.receive_card(self.deck.draw())

        # Each player may peek at up to 2 of their cards
        self.initial_peeks_remaining = {
            p.player_id: self.INITIAL_PEEK_COUNT for p in self.players
        }
        self.game_phase = GamePhase.INITIAL_PEEK

        starter_name = self.players[self.current_player_index].name
        return ActionResult.ok(
            f"Round {self.round_number} started. {starter_name} goes first. "
            f"Each player may peek at up to {self.INITIAL_PEEK_COUNT} of their cards.",
            {
                "round_number": self.round_number,
                "first_player": self.players[self.current_player_index].player_id
            }
        )

    # ------------------------------------------------------------------ #
    #  Initial peek phase                                                 #
    # ------------------------------------------------------------------ #

    def initial_peek(self, player_id: str, position: int) -> ActionResult:
        """
        During setup, a player privately looks at one of their cards.
        Each player can do this up to INITIAL_PEEK_COUNT times.
        """
        if self.game_phase != GamePhase.INITIAL_PEEK:
            return ActionResult.fail("Not in the initial peek phase.")

        player = self._get_player(player_id)
        if not player:
            return ActionResult.fail(f"Player '{player_id}' not found.")

        peeks_left = self.initial_peeks_remaining.get(player_id, 0)
        if peeks_left <= 0:
            return ActionResult.fail(
                f"{player.name} has already used all {self.INITIAL_PEEK_COUNT} peeks."
            )

        try:
            card = player.peek_card(position)
        except IndexError as e:
            return ActionResult.fail(str(e))

        self.initial_peeks_remaining[player_id] -= 1

        # If all players have used or waived their peeks, start playing
        if all(v == 0 for v in self.initial_peeks_remaining.values()):
            self.game_phase = GamePhase.PLAYING

        return ActionResult.ok(
            f"{player.name} peeked at position {position}.",
            {
                "card": card.to_dict(),
                "position": position,
                "peeks_remaining": self.initial_peeks_remaining[player_id]
            }
        )

    def done_peeking(self, player_id: str) -> ActionResult:
        """Player chooses to stop peeking early (waive remaining peeks)."""
        if self.game_phase != GamePhase.INITIAL_PEEK:
            return ActionResult.fail("Not in the initial peek phase.")

        self.initial_peeks_remaining[player_id] = 0

        if all(v == 0 for v in self.initial_peeks_remaining.values()):
            self.game_phase = GamePhase.PLAYING

        return ActionResult.ok("Done peeking.")

    # ------------------------------------------------------------------ #
    #  Main turn actions                                                  #
    # ------------------------------------------------------------------ #

    def draw_card(self, player_id: str) -> ActionResult:
        """
        Active player draws a card from the deck.
        They see its value. It's held temporarily until they choose where to place it.
        """
        if not self._is_active_player(player_id):
            return ActionResult.fail("It's not your turn.")
        if self.turn_phase != TurnPhase.DRAW:
            return ActionResult.fail("You must draw a card first.")

        self.drawn_card = self.deck.draw()
        self.turn_phase = TurnPhase.PLACE_DRAWN

        return ActionResult.ok(
            f"{self._active_player.name} drew a card.",
            {
                "card": self.drawn_card.to_dict(),   # only sent to the drawing player
                "deck_state": self.deck.to_dict()
            }
        )

    def place_drawn_card(self, player_id: str, position: int) -> ActionResult:
        """
        Active player chooses where in their row to insert the drawn card.
        After placing, they must choose a card to discard.
        """
        if not self._is_active_player(player_id):
            return ActionResult.fail("It's not your turn.")
        if self.turn_phase != TurnPhase.PLACE_DRAWN:
            return ActionResult.fail("You need to draw a card before placing.")
        if self.drawn_card is None:
            return ActionResult.fail("No drawn card to place.")

        player = self._active_player
        player.receive_card(self.drawn_card, position)
        self.drawn_card = None
        self.turn_phase = TurnPhase.DISCARD

        return ActionResult.ok(
            f"{player.name} placed their drawn card at position {position}.",
            {"position": position, "card_count": player.card_count}
        )

    def discard_card(self, player_id: str, position: int) -> ActionResult:
        """
        Active player discards one card from their row to the central pile.
        If it's a J or Q, opens the special ability phase after reactions.
        """
        if not self._is_active_player(player_id):
            return ActionResult.fail("It's not your turn.")
        if self.turn_phase != TurnPhase.DISCARD:
            return ActionResult.fail("Not in the discard phase.")

        player = self._active_player
        try:
            card = player.remove_card(position)
        except IndexError as e:
            return ActionResult.fail(str(e))

        self.deck.discard(card)

        # Determine if a special ability is triggered
        if card.is_queen:
            self.pending_ability = SpecialAbility.PEEK
        elif card.is_jack:
            self.pending_ability = SpecialAbility.SWAP
        else:
            self.pending_ability = None

        # Check if player has emptied their hand (instant round win)
        if player.has_no_cards:
            return self._handle_empty_hand(player)

        # Open reaction window
        self.turn_phase = TurnPhase.REACTION

        return ActionResult.ok(
            f"{player.name} discarded {card}.",
            {
                "discarded_card": card.to_dict(),
                "pending_ability": self.pending_ability,
                "reaction_window_seconds": self.REACTION_WINDOW_SEC
            }
        )

    # ------------------------------------------------------------------ #
    #  Reaction phase                                                     #
    # ------------------------------------------------------------------ #

    def react(self, player_id: str, position: int) -> ActionResult:
        """
        Any player reacts to the current discard by playing a matching card.
        If the card matches → it's discarded. If not → card returns to hand,
        player draws a penalty card they see privately.

        Reactions are first-come-first-served.
        """
        if self.turn_phase != TurnPhase.REACTION:
            return ActionResult.fail("No reaction window is currently open.")
        if self.game_phase not in (GamePhase.PLAYING, GamePhase.CACTUS_FINAL):
            return ActionResult.fail("Game is not in a playable phase.")

        player = self._get_player(player_id)
        if not player:
            return ActionResult.fail(f"Player '{player_id}' not found.")

        top_card = self.deck.top_discard
        if not top_card:
            return ActionResult.fail("No card on the discard pile to react to.")

        try:
            reacted_card = player.remove_card(position)
        except IndexError as e:
            return ActionResult.fail(str(e))

        # Correct reaction
        if reacted_card.value == top_card.value:
            self.deck.discard(reacted_card)

            if player.has_no_cards:
                return self._handle_empty_hand(player)

            return ActionResult.ok(
                f"{player.name} successfully reacted with {reacted_card}!",
                {
                    "reacted_card": reacted_card.to_dict(),
                    "correct": True,
                    "card_count": player.card_count
                }
            )

        # Wrong reaction — card goes back, player draws a penalty card
        player.hand.insert(position, reacted_card)  # restore to original position
        penalty_card = self.deck.draw()
        player.receive_card(penalty_card)            # appended to end

        return ActionResult.ok(
            f"{player.name} reacted incorrectly! {reacted_card} doesn't match "
            f"{top_card}. Drew a penalty card.",
            {
                "reacted_card": reacted_card.to_dict(),
                "correct": False,
                "penalty_card": penalty_card.to_dict(),  # only sent to this player
                "card_count": player.card_count
            }
        )

    def close_reaction_window(self, player_id: str) -> ActionResult:
        """
        Any player can signal they're done reacting.
        The window closes when ALL players have passed, or the active
        player explicitly skips (acts as 'close for everyone').
        """
        if self.turn_phase != TurnPhase.REACTION:
            return ActionResult.fail("No reaction window is open.")

        # Track who has passed
        if not hasattr(self, '_reaction_passes'):
            self._reaction_passes = set()
        self._reaction_passes.add(player_id)

        # Active player skipping = close immediately for everyone
        # OR all players have passed
        active_passed = self._is_active_player(player_id)
        all_passed    = len(self._reaction_passes) >= len(self.players)

        if not active_passed and not all_passed:
            return ActionResult.ok(
                f"{self._get_player(player_id).name} passed reaction.",
                {"passed": player_id, "waiting_for": len(self.players) - len(self._reaction_passes)}
            )

        # Close the window
        self._reaction_passes = set()
        if self.pending_ability:
            self.turn_phase = TurnPhase.SPECIAL_ABILITY
            return ActionResult.ok(
                "Reaction window closed. Resolve ability.",
                {"pending_ability": self.pending_ability}
            )
        return self._end_turn()

    # ------------------------------------------------------------------ #
    #  Special abilities (J and Q)                                       #
    # ------------------------------------------------------------------ #

    def use_peek(
        self,
        acting_player_id: str,
        target_player_id: str,
        position: int
    ) -> ActionResult:
        """
        Q ability: acting player privately looks at one card
        (their own or an opponent's).
        """
        if self.turn_phase != TurnPhase.SPECIAL_ABILITY:
            return ActionResult.fail("Not in the special ability phase.")
        if self.pending_ability != SpecialAbility.PEEK:
            return ActionResult.fail("Current ability is not a peek.")
        if not self._is_active_player(acting_player_id):
            return ActionResult.fail("Only the active player can use the ability.")

        target = self._get_player(target_player_id)
        if not target:
            return ActionResult.fail(f"Target player '{target_player_id}' not found.")

        try:
            card = target.peek_card(position)
        except IndexError as e:
            return ActionResult.fail(str(e))

        self.pending_ability = None
        result = self._end_turn()
        result.data["peeked_card"] = card.to_dict()    # only sent to acting player
        result.data["peeked_position"] = position
        result.data["peeked_player"] = target_player_id
        return result

    def use_swap(
        self,
        acting_player_id: str,
        player_a_id: str,
        position_a: int,
        player_b_id: str,
        position_b: int
    ) -> ActionResult:
        """
        J ability: swap any two cards between any two players
        (can be the same player, for reordering, but that's usually done freely).
        At least one player must not be the acting player, otherwise use reorder.
        """
        if self.turn_phase != TurnPhase.SPECIAL_ABILITY:
            return ActionResult.fail("Not in the special ability phase.")
        if self.pending_ability != SpecialAbility.SWAP:
            return ActionResult.fail("Current ability is not a swap.")
        if not self._is_active_player(acting_player_id):
            return ActionResult.fail("Only the active player can use the ability.")

        player_a = self._get_player(player_a_id)
        player_b = self._get_player(player_b_id)

        if not player_a:
            return ActionResult.fail(f"Player '{player_a_id}' not found.")
        if not player_b:
            return ActionResult.fail(f"Player '{player_b_id}' not found.")

        try:
            card_a = player_a.peek_card(position_a)
            card_b = player_b.peek_card(position_b)
        except IndexError as e:
            return ActionResult.fail(str(e))

        # Perform the swap
        player_a.hand[position_a] = card_b
        player_b.hand[position_b] = card_a

        self.pending_ability = None
        result = self._end_turn()
        result.data["swapped"] = {
            "player_a": player_a_id, "position_a": position_a,
            "player_b": player_b_id, "position_b": position_b
        }
        return result

    # ------------------------------------------------------------------ #
    #  Cactus declaration                                                 #
    # ------------------------------------------------------------------ #

    def say_cactus(self, player_id: str) -> ActionResult:
        """
        Player calls Cactus at the end of their turn (CACTUS_OPTION phase).
        All other players get one more turn, then cards are revealed.
        """
        if self.game_phase != GamePhase.PLAYING:
            return ActionResult.fail("Cactus can only be called during normal play.")
        if not self._is_active_player(player_id):
            return ActionResult.fail("You can only call Cactus on your own turn.")
        if self.turn_phase != TurnPhase.CACTUS_OPTION:
            return ActionResult.fail("Cactus can only be called at the end of your turn.")

        player = self._get_player(player_id)
        player.say_cactus()
        self.cactus_player_id = player_id
        self.game_phase = GamePhase.CACTUS_FINAL
        self.cactus_laps_remaining = len(self.players) - 1

        # Advance to next player immediately
        self._advance_turn()
        self.turn_phase = TurnPhase.DRAW

        return ActionResult.ok(
            f"{player.name} said CACTUS! Each other player gets one more turn.",
            {"cactus_player": player_id}
        )

    def pass_cactus(self, player_id: str) -> ActionResult:
        """Player chooses not to call Cactus — just end the turn normally."""
        if not self._is_active_player(player_id):
            return ActionResult.fail("Not your turn.")
        if self.turn_phase != TurnPhase.CACTUS_OPTION:
            return ActionResult.fail("Not in cactus option phase.")
        return self._advance_to_next_player()

    # ------------------------------------------------------------------ #
    #  Round end and scoring                                              #
    # ------------------------------------------------------------------ #

    def _handle_empty_hand(self, player: Player) -> ActionResult:
        """Called when a player reaches 0 cards mid-round (instant win)."""
        self.game_phase = GamePhase.ROUND_END
        self.turn_phase = TurnPhase.DONE
        scores = self._calculate_scores(empty_hand_winner_id=player.player_id)
        self._apply_scores(scores)
        self._determine_next_starter(scores)

        return ActionResult.ok(
            f"{player.name} eliminated all their cards! Round over.",
            {
                "winner": player.player_id,
                "win_type": "empty_hand",
                "scores": scores
            }
        )

    def _calculate_scores(
        self,
        empty_hand_winner_id: Optional[str] = None
    ) -> dict[str, int]:
        """
        Points are BAD (like golf). Lower total score = better.

        Empty hand win:
            - Winner: 3 points, everyone else: 0

        Cactus win:
            - Cactus caller has lowest sum  → caller: 1 pt, others: 0
            - Cactus caller NOT lowest sum  → caller: 0 pt, lowest non-cactus: 2 pts, others: 0
        """
        scores = {p.player_id: 0 for p in self.players}  # default everyone to 0

        if empty_hand_winner_id:
            scores[empty_hand_winner_id] = 3
            return scores

        # Cactus scoring
        cactus_player = self._get_player(self.cactus_player_id)
        cactus_sum    = cactus_player.hand_sum
        min_sum       = min(p.hand_sum for p in self.players)

        if cactus_sum == min_sum:
            # Cactus caller won
            scores[self.cactus_player_id] = 1
        else:
            # Someone else won — give them 2 points each if tied
            for p in self.players:
                if p.player_id != self.cactus_player_id and p.hand_sum == min_sum:
                    scores[p.player_id] = 2

        return scores

    def _apply_scores(self, scores: dict[str, int]):
        """Add calculated round scores to each player's total."""
        self._last_round_scores = scores 
        for player in self.players:
            player.add_round_score(scores.get(player.player_id, 0))

    def _determine_next_starter(self, scores: dict[str, int]):
        """
        Winner (lowest score this round) starts next round.
        If tied on score, lowest hand sum starts.
        If still tied, random.
        """
        min_score = min(scores.values())
        winners = [p for p in self.players if scores[p.player_id] == min_score]

        if len(winners) == 1:
            self.next_round_starter_id = winners[0].player_id
        else:
            # Tiebreak by hand sum — lowest hand sum starts
            min_hand = min(p.hand_sum for p in winners)
            top = [p for p in winners if p.hand_sum == min_hand]
            self.next_round_starter_id = random.choice(top).player_id

    def end_round_after_cactus(self) -> ActionResult:
        """
        Called when the last player (before the cactus caller) has finished
        their turn. Reveals all hands and calculates scores.
        """
        if self.game_phase != GamePhase.CACTUS_FINAL:
            return ActionResult.fail("Not in the Cactus final phase.")

        self.game_phase = GamePhase.ROUND_END
        self.turn_phase = TurnPhase.DONE
        scores = self._calculate_scores()
        self._apply_scores(scores)
        self._determine_next_starter(scores)

        hands = {
            p.player_id: {
                "name": p.name,
                "hand_sum": p.hand_sum,
                "hand": [c.to_dict() for c in p.hand]
            }
            for p in self.players
        }

        return ActionResult.ok(
            "Round over! Cards revealed.",
            {
                "scores_this_round": scores,
                "hands": hands,
                "totals": {p.player_id: p.score for p in self.players}
            }
        )

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _end_turn(self) -> ActionResult:
        """
        Wrap up the current turn. First offer the active player
        a chance to call Cactus, then advance to next player.
        """
        self.turn_phase = TurnPhase.CACTUS_OPTION
        return ActionResult.ok(
            f"{self._active_player.name} may call Cactus or pass.",
            {"cactus_option": True}
        )

    def _advance_to_next_player(self) -> ActionResult:
        """Actually move to the next player after cactus option is resolved."""
        self.turn_phase = TurnPhase.DONE

        if self.game_phase == GamePhase.CACTUS_FINAL:
            self.cactus_laps_remaining -= 1
            if self.cactus_laps_remaining <= 0:
                return self.end_round_after_cactus()

        self._advance_turn()
        self.turn_phase = TurnPhase.DRAW

        return ActionResult.ok(
            f"It's now {self._active_player.name}'s turn.",
            {"next_player": self._active_player.player_id}
        )

    def _advance_turn(self):
        """Move to the next player clockwise."""
        self.current_player_index = (
            self.current_player_index + 1
        ) % len(self.players)

    def _get_player(self, player_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.player_id == player_id), None)

    def _is_active_player(self, player_id: str) -> bool:
        return (
            self.players[self.current_player_index].player_id == player_id
            if self.players else False
        )

    @property
    def _active_player(self) -> Player:
        return self.players[self.current_player_index]

    # ------------------------------------------------------------------ #
    #  Full state serialization                                           #
    # ------------------------------------------------------------------ #

    def to_dict(self, perspective_player_id: Optional[str] = None) -> dict:
        """
        Serialize the full game state.

        Args:
            perspective_player_id: If provided, that player's hand is revealed
                                   to them privately. All others remain hidden.
        """
        players_data = []
        for p in self.players:
            reveal = (
                self.game_phase == GamePhase.ROUND_END or
                p.player_id == perspective_player_id
            )
            players_data.append(p.to_dict(reveal_hand=reveal))

        return {
            "round_number": self.round_number,
            "game_phase": self.game_phase,
            "turn_phase": self.turn_phase,
            "current_player_id": (
                self._active_player.player_id if self.players else None
            ),
            "cactus_player_id": self.cactus_player_id,
            "cactus_laps_remaining": self.cactus_laps_remaining,
            "pending_ability": self.pending_ability,
            "deck": self.deck.to_dict() if self.deck else None,
            "drawn_card": self.drawn_card.to_dict() if self.drawn_card else None,
            "players": players_data,
            "reaction_window_seconds": self.REACTION_WINDOW_SEC,
            "initial_peeks_remaining": self.initial_peeks_remaining,
            "scores_this_round": self._last_round_scores,
            "next_round_starter_id": self.next_round_starter_id,
        }
