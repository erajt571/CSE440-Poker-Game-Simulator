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
        self.use_expectiminimax: bool = True
        self.state = GameState()
        self.deck = Deck()
        # UI helpers: store a light-weight summary of the last completed hand
        self.last_hand_summary: Optional[dict] = None
        # Kid / interactive mode: stepwise betting (does not replace ``play_hand``)
        self.kid_interactive: bool = False
        self.kid_human_seat: int = self.config.num_players - 1
        self._kid_br: Optional[dict] = None  # {"highest": int, "acted": List[bool]}
        self.kid_stack_at_hand_start: Optional[List[int]] = None

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
        """Players still contesting the pot (not folded). All‑in players with 0 chips remain in."""
        return [p for p in self.players if not p.has_folded]

    def deal_community_cards(self, count: int) -> None:
        self.state.community_cards.extend(self.deck.draw(count))

    # --- Betting and hand flow -------------------------------------------------

    def _post_blinds(self) -> None:
        """Post small and big blinds for the new hand.

        Heads-up: the **button (dealer) posts the small blind**; the other seat posts the big blind.
        Three or more: SB is left of the button, BB is next seat (standard).
        """
        n = self.config.num_players
        if n == 2:
            sb_index = self.state.dealer_index
            bb_index = (self.state.dealer_index + 1) % n
        else:
            sb_index = (self.state.dealer_index + 1) % n
            bb_index = (self.state.dealer_index + 2) % n

        small_blind_player = self.players[sb_index]
        big_blind_player = self.players[bb_index]

        sb = min(self.config.small_blind, small_blind_player.stack)
        bb = min(self.config.big_blind, big_blind_player.stack)

        small_blind_player.stack -= sb
        big_blind_player.stack -= bb
        small_blind_player.current_bet = sb
        big_blind_player.current_bet = bb
        self.state.pot += sb + bb

        self.state.current_player_index = (bb_index + 1) % n

    def _distribute_pot(self, winners: List[Player], contested_pot: int) -> None:
        """Move all contested chips from the pot into winners' stacks (split + remainder)."""
        if contested_pot <= 0:
            self.state.pot = 0
            return
        if not winners:
            self.state.pot = 0
            return
        n_w = len(winners)
        base = contested_pot // n_w
        rem = contested_pot % n_w
        for i, w in enumerate(winners):
            w.stack += base + (1 if i < rem else 0)
        self.state.pot = 0

    def _hand_category_name(self, category: int) -> str:
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

    def _build_last_hand_summary(self, winners: List[Player], contested_pot: int) -> dict:
        """Snapshot for UI after any hand ending (fold-out or showdown)."""
        per_player: List[dict] = []
        for p in self.players:
            if p.hole_cards is None:
                continue
            cards = list(p.hole_cards) + self.state.community_cards
            if len(cards) >= 5:
                category, _ = evaluate_7card_hand(cards)
                per_player.append(
                    {
                        "player_index": p.index,
                        "name": p.name,
                        "category_index": int(category),
                        "category_name": self._hand_category_name(int(category)),
                        "stack": p.stack,
                        "ended_folded": p.has_folded,
                    }
                )
            else:
                per_player.append(
                    {
                        "player_index": p.index,
                        "name": p.name,
                        "category_index": -1,
                        "category_name": "—",
                        "stack": p.stack,
                        "ended_folded": p.has_folded,
                    }
                )
        return {
            "winners": [w.index for w in winners],
            "players": per_player,
            "final_pot": contested_pot,
            "stage": self.state.stage,
        }

    def _finish_hand(self, winners: List[Player]) -> List[Player]:
        """Award pot, clear felt pot counter, attach summary. Call when the hand is over."""
        contested_pot = self.state.pot
        self._distribute_pot(winners, contested_pot)
        self.last_hand_summary = self._build_last_hand_summary(winners, contested_pot)
        return winners

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
                    if self.use_expectiminimax and player.index == 0 and player.hole_cards is not None:
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
            return self._finish_hand(self._active_players())

        # Flop
        self.state.stage = "flop"
        self.deal_community_cards(3)
        self._run_betting_round()
        if len(self._active_players()) == 1:
            return self._finish_hand(self._active_players())

        # Turn
        self.state.stage = "turn"
        self.deal_community_cards(1)
        self._run_betting_round()
        if len(self._active_players()) == 1:
            return self._finish_hand(self._active_players())

        # River
        self.state.stage = "river"
        self.deal_community_cards(1)
        self._run_betting_round()
        if len(self._active_players()) == 1:
            return self._finish_hand(self._active_players())

        # Showdown
        self.state.stage = "showdown"
        winners = self.showdown()
        return self._finish_hand(winners)

    # --- Kid / interactive stepping (layer on top; ``play_hand`` unchanged) ----

    def kid_configure(self, human_seat: Optional[int] = None) -> None:
        """Call once when entering kid mode. Last seat is human by default."""
        if human_seat is not None:
            self.kid_human_seat = human_seat
        else:
            self.kid_human_seat = self.config.num_players - 1

    def kid_start_new_hand_interactive(self) -> str:
        """Deal a new hand and advance AI until the child must act (or street ends).

        Returns ``human_turn`` | ``round_complete`` | ``hand_over``.
        """
        self.kid_interactive = True
        for i, p in enumerate(self.players):
            p.is_human = i == self.kid_human_seat
        self.start_new_hand()
        self.kid_stack_at_hand_start = [p.stack for p in self.players]
        self._kid_begin_betting_round()
        return self._kid_betting_round_until_human_or_done()

    def _kid_begin_betting_round(self) -> None:
        n = self.config.num_players
        highest = max(p.current_bet for p in self.players)
        self._kid_br = {"highest": highest, "acted": [False] * n}

    def _kid_finish_betting_round(self) -> None:
        for p in self.players:
            p.current_bet = 0
        self._kid_br = None

    def _kid_pick_non_human_action(
        self, player: Player, legal: List[Action], call_amount: int, min_raise: int, max_raise: int
    ) -> Tuple[Action, Optional[int]]:
        if player.index == 0 and player.hole_cards is not None:
            search_state = SearchGameState(
                community_cards=list(self.state.community_cards),
                ai_hole_cards=player.hole_cards,
                pot=self.state.pot,
                ai_stack=player.stack,
                opp_stack=sum(p.stack for p in self.players if p.index != player.index),
                to_move="ai",
                stage=self.state.stage,
            )
            return self.ai.choose_action(search_state, legal, call_amount, min_raise, max_raise)
        strategy = self.strategies.get(player.index)
        if strategy is None:
            if "check" in legal:
                return "check", None
            if "call" in legal:
                return "call", None
            return "fold", None
        return strategy.choose_action(legal, call_amount, min_raise, max_raise)

    def _kid_apply_engine_action(
        self, player: Player, action: Action, amount: Optional[int], highest_holder: List[int]
    ) -> None:
        """Mutate player / pot like ``_run_betting_round`` (``highest_holder`` is [highest_bet])."""
        to_call = highest_holder[0] - player.current_bet
        legal, call_amount, min_raise, max_raise = self._legal_actions(player, to_call)
        if action not in legal:
            raise ValueError(f"Illegal action {action!r} for {player.name}; legal={legal}")
        if action == "fold":
            player.has_folded = True
        elif action in ("call", "check"):
            bet = call_amount
            player.stack -= bet
            player.current_bet += bet
            self.state.pot += bet
        elif action == "raise":
            if amount is None:
                raise ValueError("raise requires amount")
            bet = min(amount, player.stack)
            player.stack -= bet
            player.current_bet += bet
            self.state.pot += bet
            highest_holder[0] = player.current_bet
        if player.stack == 0:
            player.is_all_in = True

    def _kid_betting_round_until_human_or_done(self) -> str:
        """Run betting until human must choose, or betting round completes."""
        assert self._kid_br is not None
        n = self.config.num_players
        hh: List[int] = [self._kid_br["highest"]]
        acted: List[bool] = self._kid_br["acted"]

        while True:
            player = self.players[self.state.current_player_index]
            if not player.has_folded and not player.is_all_in:
                to_call = hh[0] - player.current_bet
                legal, call_amount, min_raise, max_raise = self._legal_actions(player, to_call)
                if not legal:
                    acted[player.index] = True
                else:
                    if player.index == self.kid_human_seat and player.is_human:
                        self._kid_br["highest"] = hh[0]
                        return "human_turn"
                    action, amount = self._kid_pick_non_human_action(
                        player, legal, call_amount, min_raise, max_raise
                    )
                    self._kid_apply_engine_action(player, action, amount, hh)
                    acted[player.index] = True
                    if action == "raise" and amount is not None:
                        acted[:] = [False] * n

            if all(
                acted[i] or self.players[i].has_folded or self.players[i].is_all_in
                for i in range(n)
            ):
                self._kid_finish_betting_round()
                return "round_complete"

            self.state.current_player_index = (self.state.current_player_index + 1) % n

    def kid_submit_engine_action(self, action: Action, amount: Optional[int]) -> str:
        """Apply the human's mapped engine action, then run opponents until pause or round end."""
        assert self.kid_interactive and self._kid_br is not None
        player = self.players[self.state.current_player_index]
        if player.index != self.kid_human_seat or not player.is_human:
            raise RuntimeError("Not human's turn")
        n = self.config.num_players
        hh: List[int] = [self._kid_br["highest"]]
        acted = self._kid_br["acted"]
        to_call = hh[0] - player.current_bet
        legal, call_amount, min_raise, max_raise = self._legal_actions(player, to_call)
        if action not in legal:
            raise ValueError(f"Illegal action {action!r}; legal={legal}")
        self._kid_apply_engine_action(player, action, amount, hh)
        self._kid_br["highest"] = hh[0]
        acted[player.index] = True
        if action == "raise" and amount is not None:
            acted[:] = [False] * n

        if all(acted[i] or self.players[i].has_folded or self.players[i].is_all_in for i in range(n)):
            self._kid_finish_betting_round()
            return "round_complete"

        self.state.current_player_index = (self.state.current_player_index + 1) % n
        return self._kid_betting_round_until_human_or_done()

    def kid_advance_street_or_end(self) -> str:
        """After a completed betting round: deal next street, showdown, or end. Returns status string."""
        if not self.kid_interactive:
            return "idle"
        if len(self._active_players()) == 1:
            self._finish_hand(self._active_players())
            self.kid_interactive = False
            self._kid_br = None
            return "hand_over"

        stage = self.state.stage
        if stage == "preflop":
            self.state.stage = "flop"
            self.deal_community_cards(3)
        elif stage == "flop":
            self.state.stage = "turn"
            self.deal_community_cards(1)
        elif stage == "turn":
            self.state.stage = "river"
            self.deal_community_cards(1)
        elif stage == "river":
            self.state.stage = "showdown"
            winners = self.showdown()
            self._finish_hand(winners)
            self.kid_interactive = False
            self._kid_br = None
            return "hand_over"

        else:
            self.kid_interactive = False
            self._kid_br = None
            return "hand_over"

        self._kid_begin_betting_round()
        return self._kid_betting_round_until_human_or_done()

    def kid_is_human_turn(self) -> bool:
        if not self.kid_interactive or self._kid_br is None:
            return False
        p = self.players[self.state.current_player_index]
        if p.index != self.kid_human_seat or not p.is_human or p.has_folded or p.is_all_in:
            return False
        to_call = self._kid_br["highest"] - p.current_bet
        legal, _, _, _ = self._legal_actions(p, to_call)
        return bool(legal)

    def kid_current_legal_bundle(self) -> Tuple[List[Action], int, int, int, int]:
        """Return (legal, call_amount, min_raise, max_raise, to_call) for human seat when it is their turn."""
        assert self._kid_br is not None
        p = self.players[self.state.current_player_index]
        to_call = self._kid_br["highest"] - p.current_bet
        legal, ca, mn, mx = self._legal_actions(p, to_call)
        return legal, ca, mn, mx, to_call
