from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .deck import Card, Deck
from .expectiminimax import ExpectiminimaxAI, SearchGameState
from .player import Action, Player, RandomStrategy
from .poker_rules import evaluate_7card_hand


@dataclass
class GameConfig:
    num_players: int = 2
    starting_stack: int = 1000
    small_blind: int = 10
    big_blind: int = 20


@dataclass
class GameState:
    community_cards: List[Card] = field(default_factory=list)
    pot: int = 0
    current_player_index: int = 0
    dealer_index: int = 0
    stage: str = "preflop"  # preflop, flop, turn, river, showdown


class PokerGame:
    """Simplified Texas Hold'em game engine (2–4 players).

    This engine is intentionally minimal but complete for heads-up play:
    - posts blinds
    - deals hole and community cards
    - runs one betting round per street
    - resolves the pot at showdown
    """

    def __init__(self, num_players: int = 2, config: Optional[GameConfig] = None) -> None:
        if num_players < 2 or num_players > 4:
            raise ValueError("Supports 2–4 players")
        self.config = config or GameConfig(num_players=num_players)
        self.players: List[Player] = [
            Player(name=f"Player {i+1}", stack=self.config.starting_stack, index=i)
            for i in range(self.config.num_players)
        ]
        self.strategies = {p.index: RandomStrategy() for p in self.players}
        # Seat 0 is the Expectiminimax AI by default
        self.ai = ExpectiminimaxAI(max_depth=2, num_samples=64)
        self.state = GameState()
        self.deck = Deck()
        # UI helpers: store a light-weight summary of the last completed hand
        self.last_hand_summary: Optional[dict] = None

    def start_new_hand(self) -> None:
        self.deck = Deck()
        self.state = GameState(
            community_cards=[],
            pot=0,
            current_player_index=(self.state.dealer_index + 1) % self.config.num_players,
            dealer_index=(self.state.dealer_index + 1) % self.config.num_players,
            stage="preflop",
        )

        for p in self.players:
            p.reset_for_new_hand()

        # Deal hole cards
        for p in self.players:
            cards = self.deck.draw(2)
            p.hole_cards = (cards[0], cards[1])

        self._post_blinds()

    def _active_players(self) -> List[Player]:
        return [p for p in self.players if not p.has_folded and p.stack > 0]

    def deal_community_cards(self, count: int) -> None:
        self.state.community_cards.extend(self.deck.draw(count))

    # --- Betting and hand flow -------------------------------------------------

    def _post_blinds(self) -> None:
        """Post small and big blinds for the new hand."""
        sb_index = (self.state.dealer_index + 1) % self.config.num_players
        bb_index = (self.state.dealer_index + 2) % self.config.num_players

        small_blind_player = self.players[sb_index]
        big_blind_player = self.players[bb_index]

        sb = min(self.config.small_blind, small_blind_player.stack)
        bb = min(self.config.big_blind, big_blind_player.stack)

        small_blind_player.stack -= sb
        big_blind_player.stack -= bb
        small_blind_player.current_bet = sb
        big_blind_player.current_bet = bb
        self.state.pot += sb + bb

        self.state.current_player_index = (bb_index + 1) % self.config.num_players

    def _legal_actions(self, player: Player, to_call: int) -> Tuple[List[Action], int, int, int]:
        """Return (legal_actions, call_amount, min_raise, max_raise)."""
        if player.has_folded or player.is_all_in or player.stack == 0:
            return [], 0, 0, 0

        legal: List[Action] = []
        call_amount = min(to_call, player.stack)
        if to_call == 0:
            legal.append("check")
        else:
            legal.append("fold")
            legal.append("call")

        # Simple fixed raise sizing for now: min = big blind, max = all-in
        if player.stack > call_amount + self.config.big_blind:
            legal.append("raise")
        min_raise = call_amount + self.config.big_blind if "raise" in legal else 0
        max_raise = player.stack
        return legal, call_amount, min_raise, max_raise

    def _run_betting_round(self) -> None:
        """Run a single betting round with naive logic (no side pots)."""
        highest_bet = max(p.current_bet for p in self.players)
        players_to_act = [p for p in self.players if not p.has_folded and not p.is_all_in]
        if len(players_to_act) <= 1:
            return

        start_index = self.state.current_player_index
        acted = [False] * self.config.num_players

        while True:
            player = self.players[self.state.current_player_index]
            if not player.has_folded and not player.is_all_in:
                to_call = highest_bet - player.current_bet
                legal, call_amount, min_raise, max_raise = self._legal_actions(player, to_call)
                if not legal:
                    acted[player.index] = True
                else:
                    action: Action
                    amount: Optional[int]
                    if player.index == 0 and player.hole_cards is not None:
                        # Expectiminimax AI decision
                        search_state = SearchGameState(
                            community_cards=list(self.state.community_cards),
                            ai_hole_cards=player.hole_cards,
                            pot=self.state.pot,
                            ai_stack=player.stack,
                            opp_stack=sum(p.stack for p in self.players if p.index != player.index),
                            to_move="ai",
                            stage=self.state.stage,
                        )
                        action, amount = self.ai.choose_action(
                            search_state,
                            legal,
                            call_amount,
                            min_raise,
                            max_raise,
                        )
                    else:
                        strategy = self.strategies.get(player.index)
                        if strategy is None or player.is_human:
                            # For now, non-UI path: always call/check if possible.
                            if "check" in legal:
                                action, amount = "check", None
                            elif "call" in legal:
                                action, amount = "call", None
                            else:
                                action, amount = "fold", None
                        else:
                            action, amount = strategy.choose_action(legal, call_amount, min_raise, max_raise)

                    if action == "fold":
                        player.has_folded = True
                    elif action in ("call", "check"):
                        bet = call_amount
                        player.stack -= bet
                        player.current_bet += bet
                        self.state.pot += bet
                    elif action == "raise" and amount is not None:
                        bet = min(amount, player.stack)
                        player.stack -= bet
                        player.current_bet += bet
                        self.state.pot += bet
                        highest_bet = player.current_bet
                        # After a raise, everyone needs to act again
                        acted = [False] * self.config.num_players

                    if player.stack == 0:
                        player.is_all_in = True
                    acted[player.index] = True

            if all(acted[i] or self.players[i].has_folded or self.players[i].is_all_in for i in range(self.config.num_players)):
                break

            self.state.current_player_index = (self.state.current_player_index + 1) % self.config.num_players

        # Reset per-round bets (they are now in the pot)
        for p in self.players:
            p.current_bet = 0

    def showdown(self) -> List[Player]:
        """Determine winner(s) at showdown. Returns list of winners."""
        active = self._active_players()
        if len(active) == 1:
            return active
        best_score = None
        winners: List[Player] = []
        for p in active:
            assert p.hole_cards is not None
            cards = list(p.hole_cards) + self.state.community_cards
            score = evaluate_7card_hand(cards)
            if best_score is None:
                best_score = score
                winners = [p]
            else:
                if score > best_score:
                    best_score = score
                    winners = [p]
                elif score == best_score:
                    winners.append(p)
        return winners

    def play_hand(self) -> List[Player]:
        """Play a full hand automatically with current strategies.

        Returns list of winners and updates ``last_hand_summary`` for UI.
        """
        self.start_new_hand()

        # Preflop betting
        self._run_betting_round()
        if len(self._active_players()) == 1:
            winners = self._active_players()
            return winners

        # Flop
        self.state.stage = "flop"
        self.deal_community_cards(3)
        self._run_betting_round()
        if len(self._active_players()) == 1:
            winners = self._active_players()
            return winners

        # Turn
        self.state.stage = "turn"
        self.deal_community_cards(1)
        self._run_betting_round()
        if len(self._active_players()) == 1:
            winners = self._active_players()
            return winners

        # River
        self.state.stage = "river"
        self.deal_community_cards(1)
        self._run_betting_round()

        # Showdown
        self.state.stage = "showdown"
        winners = self.showdown()
        # Split pot equally among winners (integer division)
        if winners:
            share = self.state.pot // len(winners)
            for w in winners:
                w.stack += share

        # --- Lightweight summary for the Streamlit end-of-hand screen -------
        # We only depend on public fields so this remains UI-only sugar.
        from .poker_rules import evaluate_7card_hand

        def _hand_category_name(category: int) -> str:
            names = {
                8: "Straight Flush",
                7: "Four of a Kind",
                6: "Full House",
                5: "Flush",
                4: "Straight",
                3: "Three of a Kind",
                2: "Two Pair",
                1: "One Pair",
                0: "High Card",
            }
            return names.get(category, "Unknown")

        per_player = []
        for p in self.players:
            if p.hole_cards is None:
                continue
            cards = list(p.hole_cards) + self.state.community_cards
            category, _ = evaluate_7card_hand(cards)
            per_player.append(
                {
                    "player_index": p.index,
                    "name": p.name,
                    "category_index": int(category),
                    "category_name": _hand_category_name(int(category)),
                    "stack": p.stack,
                    "ended_folded": p.has_folded,
                }
            )

        self.last_hand_summary = {
            "winners": [w.index for w in winners],
            "players": per_player,
            "final_pot": self.state.pot,
            "stage": self.state.stage,
        }

        return winners
