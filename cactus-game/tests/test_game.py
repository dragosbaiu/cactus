"""
test_game.py — Unit tests for the Cactus game engine.

Run with:  python -m pytest tests/test_game.py -v
"""

import pytest
from game.card import Card, Deck, CARD_POINTS
from game.player import Player
from game.game import CactusGame, GamePhase, TurnPhase, SpecialAbility


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def make_game_with_players(n: int = 2) -> CactusGame:
    """Create a game with n players already added."""
    game = CactusGame()
    for i in range(1, n + 1):
        game.add_player(f"p{i}", f"Player{i}")
    return game


def start_game(n: int = 2) -> CactusGame:
    """Create a game, start the round, and skip the peek phase."""
    game = make_game_with_players(n)
    game.start_round()
    # Skip all peeks
    for p in game.players:
        game.done_peeking(p.player_id)
    return game


# ------------------------------------------------------------------ #
#  Card tests                                                         #
# ------------------------------------------------------------------ #

class TestCard:
    def test_points(self):
        assert Card("hearts", "A").points == 1
        assert Card("hearts", "K").points == 13
        assert Card("hearts", "10").points == 10

    def test_is_jack_queen(self):
        assert Card("clubs", "J").is_jack
        assert Card("clubs", "Q").is_queen
        assert not Card("clubs", "K").is_jack
        assert not Card("clubs", "K").is_queen

    def test_to_dict(self):
        c = Card("spades", "7")
        d = c.to_dict()
        assert d["suit"] == "spades"
        assert d["value"] == "7"
        assert d["points"] == 7


# ------------------------------------------------------------------ #
#  Deck tests                                                         #
# ------------------------------------------------------------------ #

class TestDeck:
    def test_52_cards(self):
        deck = Deck()
        assert deck.cards_remaining == 52

    def test_draw_reduces_count(self):
        deck = Deck()
        deck.draw()
        assert deck.cards_remaining == 51

    def test_discard_and_top(self):
        deck = Deck()
        card = deck.draw()
        deck.discard(card)
        assert deck.top_discard == card

    def test_reshuffle_when_empty(self):
        deck = Deck()
        # Draw all cards
        drawn = [deck.draw() for _ in range(52)]
        # Discard all back
        for c in drawn:
            deck.discard(c)
        # Draw one more — should trigger reshuffle
        new_card = deck.draw()
        assert new_card is not None
        assert deck.cards_remaining > 0


# ------------------------------------------------------------------ #
#  Player tests                                                       #
# ------------------------------------------------------------------ #

class TestPlayer:
    def test_receive_and_remove(self):
        p = Player("p1", "Alice")
        c1 = Card("hearts", "3")
        c2 = Card("spades", "7")
        p.receive_card(c1)
        p.receive_card(c2)
        assert p.card_count == 2
        removed = p.remove_card(0)
        assert removed == c1
        assert p.card_count == 1

    def test_receive_at_position(self):
        p = Player("p1", "Alice")
        c1 = Card("hearts", "3")
        c2 = Card("spades", "7")
        c3 = Card("clubs", "K")
        p.receive_card(c1)
        p.receive_card(c2)
        p.receive_card(c3, position=1)  # insert between c1 and c2
        assert p.hand[1] == c3

    def test_hand_sum(self):
        p = Player("p1", "Alice")
        p.receive_card(Card("hearts", "A"))   # 1
        p.receive_card(Card("hearts", "3"))   # 3
        assert p.hand_sum == 4

    def test_reorder(self):
        p = Player("p1", "Alice")
        c1 = Card("hearts", "2")
        c2 = Card("hearts", "5")
        c3 = Card("hearts", "9")
        p.receive_card(c1)
        p.receive_card(c2)
        p.receive_card(c3)
        p.reorder_own_cards(0, 2)
        assert p.hand[2] == c1

    def test_peek_does_not_remove(self):
        p = Player("p1", "Alice")
        c = Card("diamonds", "Q")
        p.receive_card(c)
        peeked = p.peek_card(0)
        assert peeked == c
        assert p.card_count == 1


# ------------------------------------------------------------------ #
#  Game setup tests                                                   #
# ------------------------------------------------------------------ #

class TestGameSetup:
    def test_add_players(self):
        game = CactusGame()
        r = game.add_player("p1", "Alice")
        assert r.success
        assert len(game.players) == 1

    def test_duplicate_player_id(self):
        game = CactusGame()
        game.add_player("p1", "Alice")
        r = game.add_player("p1", "Bob")
        assert not r.success

    def test_max_players(self):
        game = CactusGame()
        for i in range(8):
            game.add_player(f"p{i}", f"Player{i}")
        r = game.add_player("p9", "Extra")
        assert not r.success

    def test_start_round_deals_4_cards(self):
        game = make_game_with_players(3)
        game.start_round()
        for p in game.players:
            assert p.card_count == 4

    def test_initial_peek(self):
        game = make_game_with_players(2)
        game.start_round()
        r = game.initial_peek("p1", 0)
        assert r.success
        assert "card" in r.data
        assert r.data["peeks_remaining"] == 1

    def test_peek_limit(self):
        game = make_game_with_players(2)
        game.start_round()
        game.initial_peek("p1", 0)
        game.initial_peek("p1", 1)
        r = game.initial_peek("p1", 2)
        assert not r.success  # used all peeks


# ------------------------------------------------------------------ #
#  Turn flow tests                                                    #
# ------------------------------------------------------------------ #

class TestTurnFlow:
    def test_draw_then_place_then_discard(self):
        game = start_game(2)
        pid = game._active_player.player_id

        r = game.draw_card(pid)
        assert r.success
        assert game.turn_phase == TurnPhase.PLACE_DRAWN

        r = game.place_drawn_card(pid, 0)
        assert r.success
        assert game.turn_phase == TurnPhase.DISCARD

        r = game.discard_card(pid, 0)
        assert r.success
        assert game.turn_phase == TurnPhase.REACTION

    def test_wrong_player_cannot_draw(self):
        game = start_game(2)
        active_id = game._active_player.player_id
        non_active = next(p.player_id for p in game.players if p.player_id != active_id)
        r = game.draw_card(non_active)
        assert not r.success

    def test_close_reaction_ends_turn(self):
        game = start_game(2)
        pid = game._active_player.player_id
        game.draw_card(pid)
        game.place_drawn_card(pid, 0)

        # Force discard a non-special card
        # Place a known non-special card at position 0
        game._active_player.hand[0] = Card("hearts", "5")
        game.discard_card(pid, 0)

        r = game.close_reaction_window(pid)
        assert r.success
        # Turn should have advanced
        assert game._active_player.player_id != pid

    def test_reaction_correct(self):
        game = start_game(2)
        pid1 = game.players[0].player_id
        pid2 = game.players[1].player_id

        # Set up known cards
        game.players[0].hand[0] = Card("hearts", "5")
        game.players[1].hand[0] = Card("spades", "5")

        game.draw_card(pid1)
        game.place_drawn_card(pid1, 0)
        game.discard_card(pid1, 1)  # discard the 5 of hearts (now at index 1 after insert)

        # Force top discard to be a 5
        game.deck.discard_pile[-1] = Card("hearts", "5")

        r = game.react(pid2, 0)
        assert r.success
        assert r.data["correct"] is True

    def test_reaction_wrong_card_penalty(self):
        game = start_game(2)
        pid1 = game.players[0].player_id
        pid2 = game.players[1].player_id

        game.players[0].hand[0] = Card("hearts", "5")
        game.players[1].hand[0] = Card("spades", "7")

        game.draw_card(pid1)
        game.place_drawn_card(pid1, 0)
        game.deck.discard_pile.append(Card("hearts", "5"))  # set top discard
        game.turn_phase = TurnPhase.REACTION

        r = game.react(pid2, 0)
        assert r.success
        assert r.data["correct"] is False
        # Player should have drawn a penalty card
        assert game.players[1].card_count == 5


# ------------------------------------------------------------------ #
#  Cactus scoring tests                                               #
# ------------------------------------------------------------------ #

class TestScoring:
    def test_cactus_winner_gets_1_point(self):
        game = start_game(2)
        game.current_player_index = 0
        cactus_pid = game.players[0].player_id
        other_pid  = game.players[1].player_id

        game.players[0].hand = [Card("hearts", "A"), Card("hearts", "2"),
                                  Card("hearts", "3"), Card("hearts", "A")]  # sum=7
        game.players[1].hand = [Card("spades", "K"), Card("spades", "K"),
                                  Card("spades", "K"), Card("spades", "K")]  # sum=52

        game.say_cactus(cactus_pid)
        assert game._active_player.player_id == other_pid
        game.draw_card(other_pid)
        game.place_drawn_card(other_pid, 0)
        game.players[1].hand[0] = Card("spades", "2")
        game.discard_card(other_pid, 0)
        game.close_reaction_window(other_pid)

        assert game.players[0].score == 1
        assert game.players[1].score == 0

    def test_cactus_loser_gets_2_points(self):
        game = start_game(2)
        game.current_player_index = 0
        cactus_pid = game.players[0].player_id
        other_pid  = game.players[1].player_id

        game.players[0].hand = [Card("spades", "K"), Card("spades", "K"),
                                  Card("spades", "K"), Card("spades", "K")]  # sum=52
        game.players[1].hand = [Card("hearts", "A"), Card("hearts", "2"),
                                  Card("hearts", "3"), Card("hearts", "A")]  # sum=7

        game.say_cactus(cactus_pid)
        assert game._active_player.player_id == other_pid
        game.draw_card(other_pid)
        game.place_drawn_card(other_pid, 0)
        game.players[1].hand[0] = Card("spades", "2")
        game.discard_card(other_pid, 0)
        game.close_reaction_window(other_pid)

        assert game.players[0].score == 0
        assert game.players[1].score == 2


class TestNextRoundStarter:
    def _finish_round_with_cactus(self, game: CactusGame, cactus_idx: int):
        game.current_player_index = cactus_idx
        game.turn_phase = TurnPhase.DRAW
        game.game_phase = GamePhase.PLAYING

        cactus_pid = game.players[cactus_idx].player_id
        other_pids = [p.player_id for i, p in enumerate(game.players) if i != cactus_idx]

        game.say_cactus(cactus_pid)

        for pid in other_pids:
            game.current_player_index = next(
                i for i, p in enumerate(game.players) if p.player_id == pid
            )
            game.turn_phase = TurnPhase.DRAW
            game.draw_card(pid)
            game.place_drawn_card(pid, 0)
            game.discard_card(pid, 0)
            game.close_reaction_window(pid)
            if game.game_phase == GamePhase.ROUND_END:
                break

    def test_round_1_starter_is_random(self):
        game = make_game_with_players(2)
        assert game.next_round_starter_id is None
        game.start_round()
        assert game._active_player is not None

    def test_winner_starts_next_round(self):
        game = start_game(2)
        game.players[0].hand = [Card("h", "A")] * 4
        game.players[1].hand = [Card("s", "K")] * 4

        self._finish_round_with_cactus(game, cactus_idx=0)

        assert game.game_phase == GamePhase.ROUND_END
        assert game.next_round_starter_id == game.players[0].player_id

        for p in game.players:
            p.hand = []
            p.reset_cactus_flag()
        game.start_round()
        assert game._active_player.player_id == game.players[0].player_id

    def test_tie_same_points_random_starter(self):
        """When tied winners have the same points, starter is random among them."""
        game = CactusGame()
        game.add_player('p1', 'Player1')
        game.add_player('p2', 'Player2')
        game.add_player('p3', 'Player3')
        game.start_round()
        for p in game.players: game.done_peeking(p.player_id)

        game.current_player_index = 0
        game.players[0].hand = [Card("s", "K")] * 4   # sum=52, loses
        game.players[1].hand = [Card("h", "A")] * 4   # sum=4,  wins
        game.players[2].hand = [Card("h", "A")] * 4   # sum=4,  wins

        game.say_cactus('p1')

        for pid in ['p2', 'p3']:
            idx = next(i for i, p in enumerate(game.players) if p.player_id == pid)
            game.current_player_index = idx
            game.turn_phase = TurnPhase.DRAW
            game.draw_card(pid)
            game.place_drawn_card(pid, 0)
            game.discard_card(pid, 0)
            if game.game_phase != GamePhase.ROUND_END:
                game.close_reaction_window(pid)

        assert game.next_round_starter_id in ('p2', 'p3')