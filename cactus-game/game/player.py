"""
player.py — Represents a player in Cactus.

Design note: A player's hand is an ORDERED list of face-down cards.
Position matters — players remember where each card is.
Cards are always face-down to opponents; only the player (or via Q peek)
can know a card's value at a given position.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.card import Card


class Player:
    """
    Represents one player in a Cactus game.

    Attributes:
        player_id:   Unique identifier (e.g. "player_1" or a username)
        name:        Display name
        hand:        Ordered list of cards (face-down row in front of player)
        score:       Accumulated points across all rounds (lower is better)
        has_said_cactus: Whether this player triggered the final round
    """

    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.hand: list[Card] = []
        self.score: int = 0
        self.has_said_cactus: bool = False

    # ------------------------------------------------------------------ #
    #  Hand management                                                     #
    # ------------------------------------------------------------------ #

    def receive_card(self, card: Card, position: Optional[int] = None):
        """
        Add a card to the player's hand at a specific position.
        If no position is given, append to the end.

        Args:
            card:     The card to add
            position: Index where the card should be inserted (0-based).
                      If None, card is appended to the right end.
        """
        if position is None or position >= len(self.hand):
            self.hand.append(card)
        else:
            self.hand.insert(position, card)

    def remove_card(self, position: int) -> Card:
        """
        Remove and return the card at the given position.

        Args:
            position: Index of the card to remove (0-based)

        Returns:
            The removed Card

        Raises:
            IndexError: If position is out of range
        """
        if not (0 <= position < len(self.hand)):
            raise IndexError(
                f"Invalid position {position}. Player '{self.name}' "
                f"has {len(self.hand)} cards (indices 0–{len(self.hand)-1})."
            )
        return self.hand.pop(position)

    def reorder_own_cards(self, from_position: int, to_position: int):
        """
        Move one of the player's own cards to a new position.
        Players can do this freely (no J needed).

        Args:
            from_position: Current index of the card
            to_position:   Target index
        """
        if not (0 <= from_position < len(self.hand)):
            raise IndexError(f"Invalid from_position {from_position}.")
        if not (0 <= to_position < len(self.hand)):
            raise IndexError(f"Invalid to_position {to_position}.")

        card = self.hand.pop(from_position)
        self.hand.insert(to_position, card)

    def peek_card(self, position: int) -> Card:
        """
        Look at a card without removing it (used for initial peek and Q ability).
        Returns the card so the caller can know its value, but it stays in hand.

        Args:
            position: Index of the card to peek at

        Returns:
            The Card at that position (still in hand)
        """
        if not (0 <= position < len(self.hand)):
            raise IndexError(
                f"Invalid position {position}. Player '{self.name}' "
                f"has {len(self.hand)} cards."
            )
        return self.hand[position]

    # ------------------------------------------------------------------ #
    #  Scoring helpers                                                     #
    # ------------------------------------------------------------------ #

    @property
    def hand_sum(self) -> int:
        """Total point value of all cards currently in hand."""
        return sum(card.points for card in self.hand)

    @property
    def card_count(self) -> int:
        """Number of cards currently in hand."""
        return len(self.hand)

    @property
    def has_no_cards(self) -> bool:
        """True if the player has eliminated all their cards."""
        return len(self.hand) == 0

    def add_round_score(self, points: int):
        """Add points to this player's cumulative score."""
        self.score += points

    # ------------------------------------------------------------------ #
    #  Cactus declaration                                                  #
    # ------------------------------------------------------------------ #

    def say_cactus(self):
        """Mark that this player has declared Cactus."""
        self.has_said_cactus = True

    def reset_cactus_flag(self):
        """Reset at the start of each new round."""
        self.has_said_cactus = False

    # ------------------------------------------------------------------ #
    #  Serialization                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self, reveal_hand: bool = False) -> dict:
        """
        Serialize player state.

        Args:
            reveal_hand: If True, include card details (used at round end
                         or for the player's own private view).
                         If False, only reveal card count (opponent view).
        """
        hand_data = []
        for i, card in enumerate(self.hand):
            if reveal_hand:
                hand_data.append({"position": i, "card": card.to_dict()})
            else:
                hand_data.append({"position": i, "card": None})  # face-down

        return {
            "player_id": self.player_id,
            "name": self.name,
            "score": self.score,
            "card_count": self.card_count,
            "has_said_cactus": self.has_said_cactus,
            "hand": hand_data
        }

    def __repr__(self) -> str:
        return f"Player(id={self.player_id!r}, name={self.name!r}, cards={self.card_count})"
