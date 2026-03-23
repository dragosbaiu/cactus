"""
card.py — Represents a single playing card and a deck of 52 cards.

Design note: Card is intentionally a simple, immutable-like object.
The deck is a list we can shuffle, draw from, and reshuffle when empty.
"""

import random
from dataclasses import dataclass, field
from typing import Optional


# All possible suits and values in a standard deck
SUITS = ["hearts", "diamonds", "clubs", "spades"]
VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Numeric value of each card for scoring purposes
# A=1, number cards = face value, J=11, Q=12, K=13
CARD_POINTS = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13
}


@dataclass
class Card:
    """
    Represents a single playing card.

    Attributes:
        suit: One of hearts, diamonds, clubs, spades
        value: One of A, 2-10, J, Q, K
    """
    suit: str
    value: str

    @property
    def points(self) -> int:
        """Numeric point value used for scoring."""
        return CARD_POINTS[self.value]

    @property
    def is_jack(self) -> bool:
        """J allows swapping any 2 cards."""
        return self.value == "J"

    @property
    def is_queen(self) -> bool:
        """Q allows peeking at any 1 card."""
        return self.value == "Q"

    def to_dict(self) -> dict:
        """Serialize to JSON-friendly dictionary."""
        return {
            "suit": self.suit,
            "value": self.value,
            "points": self.points,
            "is_jack": self.is_jack,
            "is_queen": self.is_queen
        }

    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"

    def __repr__(self) -> str:
        return f"Card({self.value!r}, {self.suit!r})"


class Deck:
    """
    A standard 52-card deck.

    Design note: We keep a separate discard pile so that when the draw
    pile runs out, we can reshuffle the discard pile back into a new deck.
    The top card of the discard pile stays visible (it's the reference
    value for reactions).
    """

    def __init__(self):
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        self._build_and_shuffle()

    def _build_and_shuffle(self):
        """Create all 52 cards and shuffle them."""
        self.draw_pile = [
            Card(suit=suit, value=value)
            for suit in SUITS
            for value in VALUES
        ]
        random.shuffle(self.draw_pile)

    def draw(self) -> Card:
        """
        Draw the top card from the draw pile.
        If the draw pile is empty, reshuffle the discard pile into it
        (keeping the top discard card visible as the current reference).
        """
        if not self.draw_pile:
            self._reshuffle_discard()
        return self.draw_pile.pop()

    def _reshuffle_discard(self):
        """
        Move all but the top discard card back into the draw pile and shuffle.
        The top card stays so players still see the current discard value.
        """
        if len(self.discard_pile) <= 1:
            raise RuntimeError("Not enough cards to reshuffle. Game cannot continue.")

        top_card = self.discard_pile[-1]          # keep the top card visible
        self.draw_pile = self.discard_pile[:-1]   # everything else goes back
        self.discard_pile = [top_card]
        random.shuffle(self.draw_pile)

    def discard(self, card: Card):
        """Place a card face-up on the discard pile."""
        self.discard_pile.append(card)

    @property
    def top_discard(self) -> Optional[Card]:
        """The currently visible top card of the discard pile."""
        return self.discard_pile[-1] if self.discard_pile else None

    @property
    def cards_remaining(self) -> int:
        return len(self.draw_pile)

    def to_dict(self) -> dict:
        """Serialize deck state to JSON-friendly dictionary."""
        return {
            "cards_remaining": self.cards_remaining,
            "discard_pile_size": len(self.discard_pile),
            "top_discard": self.top_discard.to_dict() if self.top_discard else None
        }
