main.py
import streamlit as st

from poker_ai.evaluation import run_simulation, summarize_results
from poker_ai.game_engine import PokerGame
from poker_ai.kid_ui import render_kid_play_tab
from poker_ai.visualization import inject_styles, render_last_hand_report, render_table


def render_new_player_help(game: PokerGame) -> None:
    """Right-side help panel for users who do not know poker."""
    st.markdown("#### New to poker? Start here")
    with st.expander("Quick guide: how this game works", expanded=True):
        st.markdown(
            """
            - **Goal**: Win chips by ending the hand with the best 5‑card poker hand or by making the opponent fold.
            - **Cards you use**:
              - You get **2 private cards** (your hand).
              - Up to **5 shared cards** appear in the middle (the board).
              - Your best 5‑card hand can use any combination of your 2 + 5 board cards.
            - **Stages**:
              - **Pre‑flop**: Only your 2 private cards are visible.
              - **Flop**: 3 board cards appear.
              - **Turn**: 4th board card appears.
              - **River**: 5th board card appears, then **showdown**.
            - **Your actions**:
              - **Fold**: Give up this hand and lose what you already put in the pot.
              - **Check**: Pass without betting (only when no bet is required).
              - **Call**: Match the current bet to stay in the hand.
              - **Raise**: Increase the bet, forcing the opponent to pay more to continue.
            """
        )

    stage_help = {
        "preflop": "Look at your two starting cards. High pairs (A‑A, K‑K, Q‑Q) and big cards of same suit are strong.",
        "flop": "Three board cards are visible. Check if you hit a pair, straight or flush draws, or strong made hands.",
        "turn": "Fourth board card. The pot is usually bigger; be more careful calling big raises.",
        "river": "Fifth and final board card. No more cards to come – decide if your hand is strong enough to win.",
        "showdown": "All cards are revealed. The best 5‑card hand wins the pot.",
    }

    st.markdown("#### What to look at this moment")
    current_stage = game.state.stage
    hint = stage_help.get(current_stage, "")
    if hint:
        st.markdown(f"- **Stage:** `{current_stage}`  \n- **Tip:** {hint}")

    st.markdown("#### About the AI decision panel")
    st.markdown(
        """
        - The **AI root decision analysis** lists each action and its estimated **EV (expected value)** in chips.
        - The AI chooses the action with the **highest EV**, based on many simulated future games.
        """
    )


def main() -> None:
    st.set_page_config(page_title="Poker Game Simulator with Expectiminimax AI", layout="wide")
    inject_styles()
    st.markdown("### Poker Game Simulator with **Expectiminimax AI**")

    if "game" not in st.session_state:
        st.session_state.game = PokerGame(num_players=2)
    game: PokerGame = st.session_state.game

    tab_play, tab_kid, tab_sim = st.tabs(["Play Game", "Kid Play 🎈", "Simulation & Evaluation"])

    with tab_play:

        col_left, col_right = st.columns([3, 2])

        with col_left:
            render_table(game)
            render_last_hand_report(game)

        with col_right:
            render_new_player_help(game)

            st.subheader("Controls")
            depth = st.slider("AI search depth", min_value=1, max_value=4, value=2, step=1)
            samples = st.slider("Monte Carlo samples", min_value=16, max_value=256, value=64, step=16)
            game.ai.max_depth = depth
            game.ai.num_samples = samples

            if st.button("Play new hand"):
                winners = game.play_hand()
                st.session_state.last_winners = [w.name for w in winners]

            if "last_winners" in st.session_state:
                st.markdown("**Last hand winners:** " + ", ".join(st.session_state.last_winners))

            st.markdown("---")
            st.markdown("**AI root decision analysis (estimated EV per action)**")
            analysis = getattr(game.ai, "last_root_analysis", [])
            if analysis:
                for action, amount, ev in analysis:
                    if amount is not None:
                        label = f"{action} ({amount})"
                    else:
                        label = action
                    st.write(f"- {label}: EV ≈ {ev:.1f}")
            else:
                st.write("_Play a hand to see analysis._")

    with tab_kid:
        render_kid_play_tab(game)

    with tab_sim:
        st.subheader("Automated Simulation")
        num_hands = st.slider("Number of hands", min_value=50, max_value=1000, value=200, step=50)
        depth = st.slider("AI search depth (simulation)", min_value=1, max_value=4, value=2, step=1)
        samples = st.slider("Monte Carlo samples (simulation)", min_value=16, max_value=256, value=64, step=16)
        compare_modes = st.checkbox("Compare with normal logic (side by side)", value=False)
        if st.button("Run simulation"):
            if compare_modes:
                df_ai = run_simulation(
                    num_hands=num_hands,
                    max_depth=depth,
                    num_samples=samples,
                    mode="expectiminimax",
                )
                df_normal = run_simulation(
                    num_hands=num_hands,
                    max_depth=depth,
                    num_samples=samples,
                    mode="normal",
                )
                st.session_state.sim_compare = {"expectiminimax": df_ai, "normal": df_normal}
                st.session_state.sim_df = None
            else:
                df = run_simulation(
                    num_hands=num_hands,
                    max_depth=depth,
                    num_samples=samples,
                    mode="expectiminimax",
                )
                st.session_state.sim_df = df
                st.session_state.sim_compare = None

        compare = st.session_state.get("sim_compare")
        df = st.session_state.get("sim_df")
        if compare:
            df_ai = compare["expectiminimax"]
            df_normal = compare["normal"]
            if not df_ai.empty and not df_normal.empty:
                s_ai = summarize_results(df_ai)
                s_normal = summarize_results(df_normal)
                st.markdown("#### Side-by-side output")
                left, right = st.columns(2)
                with left:
                    st.markdown("**Expectiminimax**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Win rate", f"{s_ai['win_rate']*100:.1f}%")
                    c2.metric("Loss rate", f"{s_ai['loss_rate']*100:.1f}%")
                    c3.metric("Avg profit / hand", f"{s_ai['avg_profit']:.1f}")
                    c4.metric("Avg decision time (s)", f"{s_ai['avg_decision_time']:.3f}")
                with right:
                    st.markdown("**Normal logic**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Win rate", f"{s_normal['win_rate']*100:.1f}%")
                    c2.metric("Loss rate", f"{s_normal['loss_rate']*100:.1f}%")
                    c3.metric("Avg profit / hand", f"{s_normal['avg_profit']:.1f}")
                    c4.metric("Avg decision time (s)", f"{s_normal['avg_decision_time']:.3f}")

                st.markdown("#### Delta (Expectiminimax - Normal)")
                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Win rate delta", f"{(s_ai['win_rate'] - s_normal['win_rate']) * 100:.1f}%")
                d2.metric("Loss rate delta", f"{(s_ai['loss_rate'] - s_normal['loss_rate']) * 100:.1f}%")
                d3.metric("Profit delta", f"{s_ai['avg_profit'] - s_normal['avg_profit']:.1f}")
                d4.metric("Decision time delta (s)", f"{s_ai['avg_decision_time'] - s_normal['avg_decision_time']:.3f}")

                st.markdown("#### Cumulative profit comparison")
                cmp_plot = df_ai[["hand", "ai_delta"]].copy()
                cmp_plot["expectiminimax"] = cmp_plot["ai_delta"].cumsum()
                cmp_plot["normal"] = df_normal["ai_delta"].cumsum()
                st.line_chart(cmp_plot.set_index("hand")[["expectiminimax", "normal"]])

        elif df is not None and not df.empty:
            summary = summarize_results(df)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Win rate", f"{summary['win_rate']*100:.1f}%")
            col2.metric("Loss rate", f"{summary['loss_rate']*100:.1f}%")
            col3.metric("Avg profit / hand", f"{summary['avg_profit']:.1f}")
            col4.metric("Avg decision time (s)", f"{summary['avg_decision_time']:.3f}")

            st.markdown("#### Win/Loss over time")
            df_plot = df.copy()
            df_plot["cum_profit"] = df_plot["ai_delta"].cumsum()
            st.line_chart(df_plot.set_index("hand")[["cum_profit"]])

            st.markdown("#### Profit distribution")
            st.bar_chart(df["ai_delta"].value_counts().sort_index())


if __name__ == "__main__":
    main()



 
poker_ai/game_engine.py
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
 
poker_ai/expectiminimax.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import random

from .deck import Card, Deck
from .poker_rules import evaluate_7card_hand


Action = str  # "fold", "call", "check", "raise"


@dataclass
class SearchGameState:
    """Abstract game state used by the Expectiminimax search.

    This is intentionally simpler than the full engine state so we can:
    - copy it efficiently
    - randomize unknown cards for Monte Carlo rollouts
    """

    community_cards: List[Card]
    ai_hole_cards: Tuple[Card, Card]
    pot: int
    ai_stack: int
    opp_stack: int
    to_move: str  # "ai" or "opp" or "chance"
    stage: str  # "preflop", "flop", "turn", "river", "showdown"


class ExpectiminimaxAI:
    """Entry point for AI decisions.

    Full tree search and heuristic evaluation will be implemented in the next step.
    This stub returns a fixed safe action to keep integration simple.
    """

    def __init__(self, max_depth: int = 2, num_samples: int = 64, rng: Optional[random.Random] = None) -> None:
        self.max_depth = max_depth
        self.num_samples = num_samples
        self._rng = rng or random.Random()
        # Stores analysis of the last root decision for visualization
        self.last_root_analysis: List[Tuple[Action, Optional[int], float]] = []

    def choose_action(
        self,
        state: SearchGameState,
        legal_actions: List[Action],
        call_amount: int,
        min_raise: int,
        max_raise: int,
    ) -> Tuple[Action, Optional[int]]:
        """Choose action using depth-limited expectiminimax approximation.

        To keep the branching factor manageable in this project setting we:
        - restrict to a small discrete set of raise sizes
        - approximate chance nodes via Monte Carlo sampling of unknown cards
        - approximate opponent decisions with a simple policy that reacts to pot odds
        """
        if not legal_actions:
            return "fold", None

        best_ev = float("-inf")
        best: Tuple[Action, Optional[int]] = (legal_actions[0], None)
        self.last_root_analysis = []

        candidate_actions: List[Tuple[Action, Optional[int]]] = []
        for a in legal_actions:
            if a != "raise":
                candidate_actions.append((a, None))
            else:
                # Discretise raise sizes: call+small, call+big, all-in
                mid = min_raise + (max_raise - min_raise) // 2
                for size in {min_raise, mid, max_raise}:
                    if size >= min_raise and size <= max_raise:
                        candidate_actions.append(("raise", size))

        for action, amount in candidate_actions:
            ev = self._expectiminimax(state, action, amount, depth=self.max_depth)
            self.last_root_analysis.append((action, amount, ev))
            if ev > best_ev:
                best_ev = ev
                best = (action, amount)

        return best

    # --- Internal search -----------------------------------------------------

    def _expectiminimax(
        self,
        state: SearchGameState,
        action: Action,
        amount: Optional[int],
        depth: int,
    ) -> float:
        """Evaluate EV of taking `action` at root for the AI."""
        next_state = self._apply_ai_action(state, action, amount)
        return self._eval_state(next_state, depth - 1)

    def _eval_state(self, state: SearchGameState, depth: int) -> float:
        # Terminal approximation: showdown or depth limit
        if depth <= 0 or state.stage == "showdown" or state.ai_stack == 0 or state.opp_stack == 0:
            return self._heuristic_value(state)

        # Chance node: deal remaining board cards
        if state.to_move == "chance":
            return self._chance_node_value(state, depth)

        # Opponent node: simple reactive strategy
        if state.to_move == "opp":
            return self._opponent_node_value(state, depth)

        # AI internal node (only occurs after chance/opp in deeper levels)
        return self._ai_internal_node_value(state, depth)

    def _heuristic_value(self, state: SearchGameState) -> float:
        """Estimate EV using Monte Carlo sampling of unknown opponent cards and board."""
        # Build a deck of unseen cards
        used: List[Card] = list(state.community_cards) + list(state.ai_hole_cards)
        deck = Deck(self._rng)
        deck.cards = [c for c in deck.cards if c not in used]

        total_ev = 0.0
        samples = max(8, self.num_samples // 2)
        for _ in range(samples):
            # Sample opponent hole cards
            opp_hole = deck.draw(2)
            # Complete board if needed
            community = list(state.community_cards)
            needed = 5 - len(community)
            if needed > 0:
                community.extend(deck.draw(needed))

            ai_score = evaluate_7card_hand(list(state.ai_hole_cards) + community)
            opp_score = evaluate_7card_hand(opp_hole + community)
            if ai_score > opp_score:
                outcome = state.pot  # wins current pot
            elif ai_score < opp_score:
                outcome = -state.pot
            else:
                outcome = 0.0
            total_ev += outcome

            # Reset deck for next sample
            deck = Deck(self._rng)
            deck.cards = [c for c in deck.cards if c not in used]

        return total_ev / samples

    def _chance_node_value(self, state: SearchGameState, depth: int) -> float:
        """Sample future boards until river and evaluate."""
        used: List[Card] = list(state.community_cards) + list(state.ai_hole_cards)
        deck = Deck(self._rng)
        deck.cards = [c for c in deck.cards if c not in used]

        total = 0.0
        for _ in range(self.num_samples):
            community = list(state.community_cards)
            needed = 5 - len(community)
            if needed > 0:
                community.extend(deck.draw(needed))

            sample_state = SearchGameState(
                community_cards=community,
                ai_hole_cards=state.ai_hole_cards,
                pot=state.pot,
                ai_stack=state.ai_stack,
                opp_stack=state.opp_stack,
                to_move="showdown",
                stage="showdown",
            )
            total += self._heuristic_value(sample_state)

            deck = Deck(self._rng)
            deck.cards = [c for c in deck.cards if c not in used]

        return total / self.num_samples

    def _opponent_node_value(self, state: SearchGameState, depth: int) -> float:
        """Very simple opponent model: call with decent pot odds, otherwise fold."""
        # If pot is attractive, assume call; otherwise, fold.
        # This keeps implementation compact for the academic project.
        pot_odds_good = state.pot > (state.ai_stack + state.opp_stack) * 0.1
        if pot_odds_good:
            # Opponent continues; move to next stage/chance
            next_state = SearchGameState(
                community_cards=list(state.community_cards),
                ai_hole_cards=state.ai_hole_cards,
                pot=state.pot,
                ai_stack=state.ai_stack,
                opp_stack=state.opp_stack,
                to_move="chance",
                stage=state.stage,
            )
            return self._eval_state(next_state, depth - 1)
        # Opponent folds: AI wins pot immediately
        return state.pot

    def _ai_internal_node_value(self, state: SearchGameState, depth: int) -> float:
        # At deeper levels we just consider check/call vs fold to limit branching
        actions: List[Tuple[Action, Optional[int]]] = [("call", None), ("fold", None)]
        best = float("-inf")
        for a, amt in actions:
            nxt = self._apply_ai_action(state, a, amt)
            val = self._eval_state(nxt, depth - 1)
            best = max(best, val)
        return best

    def _apply_ai_action(self, state: SearchGameState, action: Action, amount: Optional[int]) -> SearchGameState:
        pot = state.pot
        ai_stack = state.ai_stack
        opp_stack = state.opp_stack

        if action == "fold":
            return SearchGameState(
                community_cards=list(state.community_cards),
                ai_hole_cards=state.ai_hole_cards,
                pot=pot,
                ai_stack=ai_stack,
                opp_stack=opp_stack,
                to_move="showdown",
                stage="showdown",
            )
        if action in ("call", "check"):
            # Call/check does not change stacks in this abstract model; we fold cost into heuristic
            next_to_move = "opp"
            return SearchGameState(
                community_cards=list(state.community_cards),
                ai_hole_cards=state.ai_hole_cards,
                pot=pot,
                ai_stack=ai_stack,
                opp_stack=opp_stack,
                to_move=next_to_move,
                stage=state.stage,
            )
        if action == "raise" and amount is not None:
            bet = min(amount, ai_stack)
            ai_stack -= bet
            pot += bet
            return SearchGameState(
                community_cards=list(state.community_cards),
                ai_hole_cards=state.ai_hole_cards,
                pot=pot,
                ai_stack=ai_stack,
                opp_stack=opp_stack,
                to_move="opp",
                stage=state.stage,
            )
        return state

 
poker_ai/visualization.py
from __future__ import annotations

import html as html_module
from typing import List

import streamlit as st

from .deck import Card
from .game_engine import PokerGame


def card_to_str(card: Card) -> str:
    return f"{card.rank}{card.suit}"


def inject_styles() -> None:
    """Inject custom CSS for a more polished, beginner-friendly poker table UI."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@700;900&family=Montserrat:wght@600;700;800&display=swap');

        /* Overall app tweaks */
        .main {
            background: radial-gradient(circle at top, #1b2938 0, #02040a 55%, #000000 100%);
            color: #f5f7fa;
        }

        /* --- Clubhouse-style hold'em table (ph- prefix) --- */
        .ph-table-root {
            font-family: "Montserrat", system-ui, -apple-system, sans-serif;
            max-width: 920px;
            margin: 0 auto;
        }

        .ph-top-bar {
            background: linear-gradient(180deg, #0f2744 0%, #0a1c33 100%);
            border-radius: 12px 12px 0 0;
            padding: 0.55rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid rgba(255,255,255,0.08);
            border-bottom: none;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
        }

        .ph-brand {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            font-size: 0.95rem;
        }

        .ph-brand-chip {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: conic-gradient(#c41e3a 0 25%, #1a1a1a 25% 50%, #c41e3a 50% 75%, #1a1a1a 75% 100%);
            border: 2px solid #f5f5f5;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }

        .ph-brand-text { color: #fff; }
        .ph-brand-accent { color: #e63946; margin-left: 2px; }

        .ph-icon-btn {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: #0d0d0d;
            border: 1px solid rgba(255,255,255,0.12);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #eee;
            font-size: 1rem;
        }

        .ph-felt {
            position: relative;
            background:
              radial-gradient(ellipse 85% 70% at 50% 45%, #1a6b3c 0%, #0d4a28 42%, #063015 100%),
              repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
            border-radius: 0 0 28px 28px;
            border: 3px solid #1a472a;
            box-shadow:
              inset 0 0 80px rgba(0,40,20,0.35),
              0 24px 48px rgba(0,0,0,0.55);
            padding: 1.25rem 1.5rem 1.5rem;
            min-height: 420px;
        }

        .ph-felt::before {
            content: "";
            position: absolute;
            inset: 12px;
            border: 2px dashed rgba(255,255,255,0.12);
            border-radius: 50%;
            pointer-events: none;
        }

        .ph-inner {
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.65rem;
        }

        .ph-pot-wrap {
            text-align: center;
            margin-top: 0.25rem;
        }

        .ph-pot-chips {
            display: flex;
            justify-content: center;
            gap: 0;
            margin-bottom: 0.15rem;
        }

        .ph-pot-chip {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 3px solid #fff;
            margin-left: -8px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.35);
        }

        .ph-pot-chip:first-child { margin-left: 0; }
        .ph-pot-chip--grey { background: linear-gradient(145deg, #9ca3af, #4b5563); }
        .ph-pot-chip--blue { background: linear-gradient(145deg, #60a5fa, #1d4ed8); }

        .ph-pot-amount {
            font-family: "Merriweather", Georgia, serif;
            font-weight: 900;
            font-size: 2rem;
            color: #fff;
            text-shadow:
              2px 2px 0 #000,
              -1px -1px 0 #000,
              1px -1px 0 #000,
              -1px 1px 0 #000;
            line-height: 1.1;
        }

        .ph-pot-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: rgba(255,255,255,0.55);
            margin-top: 0.15rem;
        }

        .ph-cards-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.35rem;
        }

        .ph-playing-card {
            width: 48px;
            height: 68px;
            background: linear-gradient(180deg, #fff 0%, #f3f4f6 100%);
            border-radius: 6px;
            border: 1px solid #d1d5db;
            box-shadow: 0 4px 10px rgba(0,0,0,0.35);
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1rem;
            line-height: 1;
            color: #111;
        }

        .ph-playing-card--red { color: #b91c1c; }
        .ph-playing-card .ph-suit { font-size: 1.35rem; margin-top: 2px; }

        .ph-card-back {
            width: 48px;
            height: 68px;
            border-radius: 6px;
            background:
              repeating-linear-gradient(
                45deg,
                #1e3a5f,
                #1e3a5f 4px,
                #2563eb 4px,
                #2563eb 8px
              );
            border: 2px solid #1e40af;
            box-shadow: 0 4px 10px rgba(0,0,0,0.35);
        }

        .ph-opponents {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 1.5rem 2.5rem;
            width: 100%;
            margin: 0.5rem 0 0.25rem;
        }

        .ph-seat {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 100px;
            position: relative;
        }

        .ph-seat--user {
            margin-top: 0.35rem;
        }

        .ph-fold-watermark {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -65%) rotate(-8deg);
            font-size: 2.2rem;
            font-weight: 800;
            color: rgba(100,116,139,0.35);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            pointer-events: none;
            white-space: nowrap;
        }

        .ph-seat-cards {
            display: flex;
            gap: 2px;
            margin-bottom: 0.35rem;
            min-height: 68px;
            align-items: center;
            justify-content: center;
        }

        .ph-seat-cards--mucked {
            border: 1px dashed rgba(148, 163, 184, 0.25);
            border-radius: 6px;
            background: rgba(0, 0, 0, 0.12);
        }

        .ph-ribbon {
            background: linear-gradient(180deg, #dc2626 0%, #991b1b 100%);
            color: #fff;
            font-family: "Merriweather", Georgia, serif;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 0.2rem 1.1rem;
            border-radius: 4px;
            box-shadow: 0 3px 0 rgba(0,0,0,0.25);
            margin-bottom: -4px;
            z-index: 2;
            position: relative;
        }

        .ph-nameplate {
            background: #6b7280;
            color: #fff;
            font-weight: 700;
            font-size: 0.8rem;
            padding: 0.35rem 1.25rem;
            border-radius: 4px;
            border: 2px solid rgba(0,0,0,0.2);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            position: relative;
        }

        .ph-nameplate--you {
            background: #ca8a04;
            border-color: #a16207;
        }

        .ph-nameplate--folded {
            opacity: 0.55;
        }

        .ph-dealer {
            position: absolute;
            right: -14px;
            bottom: 2px;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #fff;
            color: #111;
            font-size: 0.65rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #d1d5db;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .ph-user-highlight {
            padding: 0.5rem 1.5rem 0.75rem;
            border-radius: 50%;
            border: 2px dashed rgba(255,255,255,0.35);
            margin-top: 0.25rem;
        }

        .ph-stage-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            justify-content: center;
            margin-bottom: 0.25rem;
        }

        .ph-stage-pill {
            font-size: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: 0.15rem 0.45rem;
            border-radius: 999px;
            background: rgba(0,0,0,0.25);
            color: rgba(255,255,255,0.75);
            border: 1px solid rgba(255,255,255,0.15);
        }

        .ph-stage-pill--on {
            background: rgba(255,255,255,0.95);
            color: #065f46;
            font-weight: 800;
            border-color: transparent;
        }

        .ph-actions {
            display: flex;
            justify-content: center;
            gap: 0.75rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }

        .ph-action-pill {
            background: #0a0a0a;
            color: #fff;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 0.55rem 1.75rem;
            border-radius: 999px;
            border: 2px solid #262626;
            box-shadow: 0 4px 0 #000, 0 6px 16px rgba(0,0,0,0.4);
            letter-spacing: 0.03em;
        }

        .ph-action-note {
            text-align: center;
            font-size: 0.7rem;
            color: rgba(255,255,255,0.5);
            margin-top: 0.5rem;
        }

        .ph-empty-hint {
            color: rgba(255,255,255,0.45);
            font-size: 0.85rem;
            font-style: italic;
            padding: 1rem;
        }

        /* Table container */
        .poker-table {
            background: radial-gradient(circle, #14532d 0%, #052e16 55%, #020617 100%);
            border-radius: 24px;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 18px 40px rgba(0,0,0,0.45);
            border: 1px solid rgba(148, 163, 184, 0.35);
        }

        .poker-board {
            background: rgba(15, 23, 42, 0.75);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.75rem;
        }

        .poker-chip {
            font-weight: 600;
            color: #facc15;
        }

        .poker-chip-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #e5e7eb;
        }

        .poker-player-card {
            background: rgba(15, 23, 42, 0.90);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.5rem;
            border: 1px solid rgba(148, 163, 184, 0.45);
        }

        .poker-player-name {
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .poker-player-name-ai {
            color: #38bdf8;
        }

        .poker-status-pill {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.6);
            margin-left: 0.35rem;
        }

        .poker-status-pill-folded {
            border-color: rgba(248, 113, 113, 0.9);
            color: #fecaca;
        }

        .poker-status-pill-allin {
            border-color: rgba(250, 204, 21, 0.95);
            color: #fef9c3;
        }

        .poker-cards {
            font-size: 1.1rem;
        }

        .poker-card {
            display: inline-block;
            padding: 0.15rem 0.45rem;
            margin-right: 0.2rem;
            border-radius: 6px;
            background: #020617;
            border: 1px solid rgba(148, 163, 184, 0.7);
            font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        .poker-card-red {
            color: #fecaca;
            border-color: rgba(248, 113, 113, 0.9);
        }

        .poker-card-black {
            color: #e5e7eb;
        }

        /* Stage indicator */
        .poker-stage-track {
            display: flex;
            gap: 0.4rem;
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
            font-size: 0.75rem;
        }

        .poker-stage-pill {
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.85);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .poker-stage-pill--active {
            border-color: #38bdf8;
            background: linear-gradient(135deg, #0ea5e9, #22c55e);
            color: #0f172a;
            font-weight: 700;
        }

        .poker-stage-pill--completed {
            border-color: #22c55e;
            color: #bbf7d0;
        }

        /* Large action buttons */
        .poker-action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            font-size: 1rem;
            border-radius: 999px;
            padding-top: 0.6rem !important;
            padding-bottom: 0.6rem !important;
            font-weight: 600;
        }

        .poker-action-btn span.emoji {
            font-size: 1.1rem;
        }

        .poker-action-btn--fold {
            background: #991b1b !important;
            border-color: #fecaca !important;
            color: #fee2e2 !important;
        }

        .poker-action-btn--call {
            background: #1d4ed8 !important;
            border-color: #bfdbfe !important;
            color: #eff6ff !important;
        }

        .poker-action-btn--raise {
            background: #15803d !important;
            border-color: #bbf7d0 !important;
            color: #ecfdf5 !important;
        }

        .poker-action-btn--check {
            background: #1d4ed8 !important;
            border-color: #bfdbfe !important;
            color: #eff6ff !important;
        }

        .poker-hint {
            font-size: 0.9rem;
            padding: 0.5rem 0.7rem;
            border-radius: 0.75rem;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.5);
            margin-bottom: 0.35rem;
        }

        .poker-hint--safe {
            border-color: #4ade80;
            color: #bbf7d0;
        }

        .poker-hint--warning {
            border-color: #f97316;
            color: #ffedd5;
        }

        .poker-hint--danger {
            border-color: #fca5a5;
            color: #fee2e2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card_span(card: Card) -> str:
    cls = "poker-card-red" if card.suit in {"♥", "♦"} else "poker-card-black"
    return f'<span class="poker-card {cls}">{card_to_str(card)}</span>'


def _playing_card_face_html(card: Card) -> str:
    red = " ph-playing-card--red" if card.suit in {"♥", "♦"} else ""
    return (
        f'<div class="ph-playing-card{red}">'
        f'<span>{html_module.escape(card.rank)}</span>'
        f'<span class="ph-suit">{html_module.escape(card.suit)}</span>'
        "</div>"
    )


def _playing_card_back_html() -> str:
    return '<div class="ph-card-back" aria-hidden="true"></div>'


def _ph_stage_row_html(stage: str) -> str:
    order = ["preflop", "flop", "turn", "river", "showdown"]
    labels = {
        "preflop": "Pre-Flop",
        "flop": "Flop",
        "turn": "Turn",
        "river": "River",
        "showdown": "Showdown",
    }
    if stage not in order:
        stage = "preflop"
    si = order.index(stage)
    parts: List[str] = []
    for i, key in enumerate(order):
        cls = "ph-stage-pill" + (" ph-stage-pill--on" if i == si else "")
        parts.append(f'<span class="{cls}">{labels[key]}</span>')
    return '<div class="ph-stage-pill-row">' + "".join(parts) + "</div>"


def _seat_hole_cards_html(player, is_user: bool, reveal_opponent: bool) -> str:
    """Hole cards: folded hands are mucked (no faces). Otherwise user sees faces; opponents backs until showdown."""
    from .player import Player

    p: Player = player
    if p.hole_cards is None:
        return '<div class="ph-seat-cards"></div>'
    if p.has_folded:
        return '<div class="ph-seat-cards ph-seat-cards--mucked" title="Folded — cards mucked"></div>'
    c1, c2 = p.hole_cards
    if is_user:
        inner = _playing_card_face_html(c1) + _playing_card_face_html(c2)
    elif reveal_opponent:
        inner = _playing_card_face_html(c1) + _playing_card_face_html(c2)
    else:
        inner = _playing_card_back_html() + _playing_card_back_html()
    return f'<div class="ph-seat-cards">{inner}</div>'


def _seat_block_html(player, *, is_user: bool, dealer_index: int, reveal_opponent: bool) -> str:
    from .player import Player

    p: Player = player
    safe_name = html_module.escape(p.name)
    folded = p.has_folded
    # Use &#36; not raw $ — Streamlit markdown still parses $…$ as math and corrupts HTML.
    ribbon = f'<div class="ph-ribbon">&#36;{p.stack}</div>'
    np_cls = "ph-nameplate"
    if is_user:
        np_cls += " ph-nameplate--you"
    if folded:
        np_cls += " ph-nameplate--folded"
    dealer_btn = ""
    if p.index == dealer_index:
        dealer_btn = '<span class="ph-dealer" title="Dealer">D</span>'
    fold_wm = '<div class="ph-fold-watermark">Fold</div>' if folded else ""
    seat_cls = "ph-seat" + (" ph-seat--user" if is_user else "")
    label = "You" if is_user else safe_name
    return (
        f'<div class="{seat_cls}">'
        f"{fold_wm}"
        f'{_seat_hole_cards_html(p, is_user=is_user, reveal_opponent=reveal_opponent)}'
        f"{ribbon}"
        f'<div class="{np_cls}">{label}{dealer_btn}</div>'
        "</div>"
    )


def render_stage_track(stage: str) -> None:
    """Visual stage indicator for Pre-flop → Showdown."""
    order = ["preflop", "flop", "turn", "river", "showdown"]
    labels = {
        "preflop": "Pre-Flop",
        "flop": "Flop",
        "turn": "Turn",
        "river": "River",
        "showdown": "Showdown",
    }
    html_parts: List[str] = []
    if stage not in order:
        stage = "preflop"
    stage_index = order.index(stage)
    for idx, key in enumerate(order):
        cls = "poker-stage-pill"
        if idx < stage_index:
            cls += " poker-stage-pill--completed"
        elif idx == stage_index:
            cls += " poker-stage-pill--active"
        html_parts.append(f'<span class="{cls}">{labels[key]}</span>')
    html = '<div class="poker-stage-track">' + " ".join(html_parts) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_table(game: PokerGame, beginner_mode: bool = False) -> None:
    """Top-down Texas Hold'em table (green felt, pot, board, seats, action bar).

    Last seat is **You**; other seats are opponents. Opponent hole cards use
    blue backs until ``showdown`` (then faces match the reference reveal).
    """
    del beginner_mode  # reserved; table is fully custom HTML

    summary = getattr(game, "last_hand_summary", None)
    if getattr(game, "kid_interactive", False):
        pot_display = int(game.state.pot)
    else:
        pot_display = int(summary["final_pot"]) if summary else int(game.state.pot)
    stage = game.state.stage
    reveal_opponent = stage == "showdown"
    dealer_index = int(game.state.dealer_index)

    board_cards = game.state.community_cards
    if board_cards:
        board_html = "".join(_playing_card_face_html(c) for c in board_cards)
    else:
        board_html = '<span class="ph-empty-hint">Community cards appear after the flop.</span>'

    ai_players = [p for p in game.players if p.index != len(game.players) - 1]
    user = game.players[-1] if game.players else None

    opponents_html = ""
    if ai_players:
        seats = "".join(
            _seat_block_html(p, is_user=False, dealer_index=dealer_index, reveal_opponent=reveal_opponent)
            for p in ai_players
        )
        opponents_html = f'<div class="ph-opponents">{seats}</div>'

    user_block = ""
    if user is not None:
        user_block = (
            '<div class="ph-user-highlight">'
            + _seat_block_html(user, is_user=True, dealer_index=dealer_index, reveal_opponent=reveal_opponent)
            + "</div>"
        )

    if user is not None and user.hole_cards is None and not board_cards:
        if getattr(game, "kid_interactive", False):
            felt_hint = '<p class="ph-empty-hint">Use <strong>New kid hand</strong> in the Kid Play tab.</p>'
        else:
            felt_hint = '<p class="ph-empty-hint">Click <strong>Play new hand</strong> on the right to deal.</p>'
    else:
        felt_hint = ""

    if getattr(game, "kid_interactive", False):
        kid_actions = ""
        kid_note = '<p class="ph-action-note">Use the big buttons under the table in the Kid Play tab.</p>'
    else:
        kid_actions = """
      <div class="ph-actions">
        <span class="ph-action-pill">Fold</span>
        <span class="ph-action-pill">Check</span>
        <span class="ph-action-pill">Raise</span>
      </div>
      <p class="ph-action-note">Hands run automatically here; use the sidebar to play a new hand.</p>"""
        kid_note = ""

    full = f"""
<div class="ph-table-root">
  <div class="ph-top-bar">
    <div class="ph-brand">
      <span class="ph-brand-chip" aria-hidden="true"></span>
      <span><span class="ph-brand-text">HOLD&apos;EM</span><span class="ph-brand-accent">TABLE</span></span>
    </div>
    <div>
      <span class="ph-icon-btn" title="Home">&#127968;</span>
      <span class="ph-icon-btn" style="margin-left:0.35rem" title="Sound">&#128266;</span>
    </div>
  </div>
  <div class="ph-felt">
    <div class="ph-inner">
      {_ph_stage_row_html(stage)}
      {opponents_html}
      <div class="ph-pot-wrap">
        <div class="ph-pot-chips" aria-hidden="true">
          <span class="ph-pot-chip ph-pot-chip--grey"></span>
          <span class="ph-pot-chip ph-pot-chip--blue"></span>
        </div>
        <div class="ph-pot-amount">&#36;{pot_display}</div>
        <div class="ph-pot-label">Pot</div>
      </div>
      <div class="ph-cards-row">{board_html}</div>
      {felt_hint}
      {user_block}
      {kid_actions}{kid_note}
    </div>
  </div>
</div>
"""
    st.markdown(full, unsafe_allow_html=True)

    if user is not None and user.is_all_in and not user.has_folded and not getattr(
        game, "kid_interactive", False
    ):
        st.caption("All-in: this player put their remaining stack in the pot.")


def render_last_hand_report(game: PokerGame) -> None:
    """Text recap of the last completed hand (pot, winner, stacks, hole cards if shown)."""
    st.markdown("#### Last hand report")
    summary = getattr(game, "last_hand_summary", None)
    if not summary:
        st.caption("_Play a hand to generate a report._")
        return

    names = {p.index: p.name for p in game.players}
    win_ix = summary.get("winners") or []
    win_names = ", ".join(names.get(i, f"Seat {i}") for i in win_ix) or "(none)"
    st.markdown(f"- **End stage:** `{summary['stage']}`")
    # Escape $ so Streamlit does not treat amounts as LaTeX math (breaks bold + numbers).
    fp = int(summary["final_pot"])
    st.markdown(rf"- **Pot awarded:** \${fp}")
    st.markdown(f"- **Winner(s):** {win_names}")

    total_stack = sum(p.stack for p in game.players)
    expected = game.config.starting_stack * game.config.num_players
    st.markdown(
        rf"- **Chip conservation:** stacks sum to **\${total_stack}** "
        rf"(expected **\${expected}** with no rake)."
    )
    if total_stack != expected:
        st.warning(
            rf"Chip total (\${total_stack}) does not match starting chips (\${expected}). "
            "That should not happen after a normal hand — try a fresh **Play new hand** or restart the app."
        )

    st.markdown("- **Players:**")
    for row in summary.get("players", []):
        p = game.players[row["player_index"]]
        folded = row.get("ended_folded", False)
        if p.hole_cards and not folded:
            hole = " ".join(card_to_str(c) for c in p.hole_cards)
            hole_line = f" hole cards: `{hole}`"
        elif folded:
            hole_line = " folded (**mucked** — hole cards not shown on table)"
        else:
            hole_line = ""
        cat = row.get("category_name", "—")
        stk = int(row["stack"])
        st.markdown(
            rf"  - **{row['name']}**: stack **\${stk}**; best category at end: **{cat}**{hole_line}"
        )


def render_hand_rankings_panel() -> None:
    """Show the standard poker hand rankings with tiny visual examples."""
    st.markdown("#### Poker Hand Rankings (best → worst)")
    st.markdown(
        """
        These are the **10 standard poker hands**. The top one is the strongest.
        """
    )

    def example(row: str) -> str:
        return f"<span class='poker-cards'>{row}</span>"

    rankings = [
        ("Royal Flush", example("🂱 🂭 🂮 🂫 🂪")),  # A K Q J 10 same suit (hearts icon set)
        ("Straight Flush", example("9♠ 8♠ 7♠ 6♠ 5♠")),
        ("Four of a Kind", example("K♣ K♦ K♥ K♠ 3♣")),
        ("Full House", example("Q♠ Q♥ Q♦ 9♣ 9♦")),
        ("Flush", example("A♦ J♦ 8♦ 4♦ 2♦")),
        ("Straight", example("10♣ 9♦ 8♣ 7♥ 6♠")),
        ("Three of a Kind", example("J♣ J♦ J♥ 5♠ 2♦")),
        ("Two Pair", example("10♠ 10♦ 4♣ 4♥ 7♣")),
        ("One Pair", example("A♠ A♦ 9♣ 5♥ 3♦")),
        ("High Card", example("A♣ J♦ 8♠ 5♥ 2♣")),
    ]

    for name, ex in rankings:
        st.markdown(f"- **{name}** &nbsp;&nbsp; {ex}", unsafe_allow_html=True)


def render_beginner_hint(game: PokerGame, beginner_mode: bool) -> None:
    """Very lightweight textual hint about the user's strength."""
    if not beginner_mode:
        return
    if not game.players:
        return
    user = game.players[-1]
    if user.hole_cards is None:
        return

    from .poker_rules import evaluate_7card_hand

    cards = list(user.hole_cards) + game.state.community_cards
    if len(cards) < 5:
        st.markdown(
            '<div class="poker-hint poker-hint--safe">'
            "Tip: The early cards are being dealt. It is usually fine to **wait and see** the community cards."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    category, _ = evaluate_7card_hand(cards)
    if category >= 4:
        css = "poker-hint poker-hint--safe"
        text = "Tip: You have a **strong made hand**. Calling or even raising is often safe here."
    elif category >= 2:
        css = "poker-hint poker-hint--warning"
        text = "Tip: You have a **decent hand** (like pairs or two pair). Calling can be okay, but huge raises are risky."
    elif category == 1:
        css = "poker-hint poker-hint--warning"
        text = "Tip: You only have **one pair**. Be careful with big pots; calling small bets can be fine."
    else:
        css = "poker-hint poker-hint--danger"
        text = "Tip: Your cards are **weak high-card only**. Folding early can reduce your losses."

    st.markdown(f'<div class="{css}">{text}</div>', unsafe_allow_html=True)
 
poker_ai/kid_ui.py
"""Streamlit kid play: polished table UI + coach + actions (engine untouched)."""

from __future__ import annotations

import html as html_module
from typing import List, cast

import streamlit as st

from .deck import Card
from .game_engine import PokerGame
from .kid_layer import (
    KidChoice,
    coach_confidence_level,
    get_ai_coach_recommendation,
    get_hand_strength_label,
    kid_event_message,
    kid_hand_coin_delta,
    kid_result_explanation,
    kid_result_headline,
    map_kid_choice_to_engine,
    monte_carlo_win_probability,
    simple_pair_on_board,
)


def inject_kid_polish_styles() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&display=swap');

          .kid-scope {
            font-family: "Nunito", system-ui, sans-serif;
            max-width: 720px;
            margin: 0 auto;
          }
          .kid-felt {
            background: radial-gradient(ellipse 100% 80% at 50% 30%, #147a4a 0%, #0b3d2e 55%, #062a1f 100%);
            border-radius: 28px;
            padding: 1.35rem 1.5rem 1.6rem;
            box-shadow: 0 20px 50px rgba(0,0,0,0.45), inset 0 0 60px rgba(0,0,0,0.2);
            border: 4px solid #0a3028;
          }
          .kid-section-label {
            text-align: center;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.55);
            margin-bottom: 0.35rem;
          }
          .kid-opp-row, .kid-board-row, .kid-pot-row, .kid-you-row {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.85rem;
          }
          .kc-card {
            width: 52px;
            height: 74px;
            border-radius: 10px;
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
            border: 2px solid #e2e8f0;
            box-shadow: 0 6px 14px rgba(0,0,0,0.35);
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 1.05rem;
            line-height: 1;
            color: #0f172a;
            animation: kcFade 0.45s ease-out both;
          }
          .kc-card--red { color: #b91c1c; border-color: #fecaca; }
          .kc-card--delay-0 { animation-delay: 0s; }
          .kc-card--delay-1 { animation-delay: 0.06s; }
          .kc-card--delay-2 { animation-delay: 0.12s; }
          .kc-card--delay-3 { animation-delay: 0.18s; }
          .kc-card--delay-4 { animation-delay: 0.24s; }
          @keyframes kcFade {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .kc-back {
            width: 52px;
            height: 74px;
            border-radius: 10px;
            background: repeating-linear-gradient(135deg, #1e3a8a, #1e3a8a 5px, #3b82f6 5px, #3b82f6 10px);
            border: 2px solid #1d4ed8;
            box-shadow: 0 6px 14px rgba(0,0,0,0.35);
            animation: kcFade 0.4s ease-out both;
          }
          .kc-muck {
            width: 52px;
            height: 74px;
            border-radius: 10px;
            background: rgba(15, 23, 42, 0.35);
            border: 2px dashed rgba(148, 163, 184, 0.4);
          }
          .kc-suit { font-size: 1.25rem; margin-top: 2px; }
          .kid-pot {
            text-align: center;
            margin: 0.5rem 0 0.75rem;
          }
          .kid-pot-label {
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: rgba(255,255,255,0.65);
            text-transform: uppercase;
          }
          .kid-pot-value {
            font-size: 2.15rem;
            font-weight: 900;
            color: #fefce8;
            text-shadow: 0 2px 0 #000, 0 0 18px rgba(250, 204, 21, 0.35);
          }
          .kid-stack-row {
            display: flex;
            justify-content: center;
            gap: 1.25rem;
            flex-wrap: wrap;
            margin: 0.5rem 0 0.25rem;
            font-size: 1.05rem;
            font-weight: 800;
            color: #ecfdf5;
          }
          .kid-stack-pill {
            background: rgba(0,0,0,0.25);
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.15);
          }
          .kid-stack-delta-pos { color: #86efac; font-weight: 900; margin-left: 0.35rem; }
          .kid-stack-delta-neg { color: #fca5a5; font-weight: 900; margin-left: 0.35rem; }
          .kid-bar-wrap {
            margin: 0.5rem auto 0.25rem;
            max-width: 420px;
            background: rgba(0,0,0,0.25);
            border-radius: 999px;
            height: 22px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.12);
          }
          .kid-bar-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.35s ease;
            background: linear-gradient(90deg, #ef4444 0%, #eab308 45%, #22c55e 100%);
            background-size: 100% 100%;
          }
          .kid-bar-label {
            text-align: center;
            font-weight: 800;
            font-size: 0.95rem;
            color: #fefce8;
            margin-top: 0.25rem;
          }
          .kid-coach-banner {
            background: linear-gradient(135deg, rgba(219,234,254,0.95), rgba(254,243,199,0.95));
            border: 3px solid #38bdf8;
            border-radius: 16px;
            padding: 0.85rem 1.1rem;
            margin: 0.75rem auto 0.5rem;
            max-width: 640px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
          }
          .kid-coach-msg { font-size: 1.15rem; font-weight: 900; color: #0c4a6e; }
          .kid-coach-sub { font-size: 0.95rem; font-weight: 700; color: #0369a1; margin-top: 0.25rem; }
          button[aria-label="Give Up"] {
            background: linear-gradient(180deg, #f87171, #dc2626) !important;
            color: white !important;
            border: none !important;
            min-height: 3.6rem !important;
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            border-radius: 16px !important;
          }
          button[aria-label="Stay In"] {
            background: linear-gradient(180deg, #fde047, #eab308) !important;
            color: #422006 !important;
            border: none !important;
            min-height: 3.6rem !important;
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            border-radius: 16px !important;
          }
          button[aria-label="Go Big"] {
            background: linear-gradient(180deg, #4ade80, #16a34a) !important;
            color: white !important;
            border: none !important;
            min-height: 3.6rem !important;
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            border-radius: 16px !important;
          }
          button[aria-label="Help Me"] {
            background: linear-gradient(180deg, #60a5fa, #2563eb) !important;
            color: white !important;
            border: none !important;
            min-height: 3.6rem !important;
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            border-radius: 16px !important;
          }
          .kid-result-card {
            background: linear-gradient(180deg, #f8fafc, #e2e8f0);
            border-radius: 20px;
            padding: 1.25rem 1.5rem;
            border: 3px solid #94a3b8;
            max-width: 520px;
            margin: 0 auto 1rem;
            text-align: center;
            box-shadow: 0 16px 40px rgba(0,0,0,0.15);
          }
          .kid-result-title { font-size: 1.5rem; font-weight: 900; color: #0f172a; }
          .kid-result-body { font-size: 1.05rem; font-weight: 700; color: #334155; margin-top: 0.5rem; }
          .kid-hands-badge {
            display: inline-block;
            background: #0f172a;
            color: #f8fafc;
            padding: 0.2rem 0.6rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 800;
            margin-left: 0.35rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card_face_html(card: Card, delay_cls: str = "") -> str:
    red = " kc-card--red" if card.suit in {"♥", "♦"} else ""
    d = f" {delay_cls}" if delay_cls else ""
    return (
        f'<div class="kc-card{red}{d}">'
        f'<span>{html_module.escape(card.rank)}</span>'
        f'<span class="kc-suit">{html_module.escape(card.suit)}</span></div>'
    )


def _card_back_html(delay_cls: str = "") -> str:
    return f'<div class="kc-back {delay_cls.strip()}"></div>'


def _card_muck_html() -> str:
    return '<div class="kc-muck" title="Folded"></div>'


def _render_kid_table_html(
    game: PokerGame,
    *,
    human_seat: int,
    show_opponent_holes: bool,
) -> str:
    """Single centered felt card: Buddy, board, pot, You + stacks."""
    opp = next(p for p in game.players if p.index != human_seat)
    you = game.players[human_seat]
    board = game.state.community_cards
    pot = int(game.state.pot)
    showdown = game.state.stage == "showdown"

    def opp_hole_html() -> str:
        if opp.has_folded:
            return _card_muck_html() + _card_muck_html()
        if show_opponent_holes and showdown and opp.hole_cards:
            return "".join(_card_face_html(c) for c in opp.hole_cards)
        if opp.hole_cards:
            return _card_back_html("kc-card--delay-0") + _card_back_html("kc-card--delay-1")
        return ""

    def your_hole_html() -> str:
        if you.has_folded or you.hole_cards is None:
            return _card_muck_html() + _card_muck_html()
        return "".join(_card_face_html(c) for c in you.hole_cards)

    board_parts: List[str] = []
    for i, c in enumerate(board):
        board_parts.append(_card_face_html(c, f"kc-card--delay-{min(i, 4)}"))
    board_html = "".join(board_parts) if board_parts else (
        '<span style="color:rgba(255,255,255,0.45);font-weight:700;">Middle cards appear soon…</span>'
    )

    ob = opp.stack
    yb = you.stack
    d_opp = st.session_state.get("kid_prev_opp_stack")
    d_you = st.session_state.get("kid_prev_you_stack")
    extra_opp = ""
    extra_you = ""
    if d_opp is not None and d_opp != ob:
        ch = ob - d_opp
        cls = "kid-stack-delta-pos" if ch > 0 else "kid-stack-delta-neg"
        extra_opp = f'<span class="{cls}">({ch:+d})</span>'
    if d_you is not None and d_you != yb:
        ch = yb - d_you
        cls = "kid-stack-delta-pos" if ch > 0 else "kid-stack-delta-neg"
        extra_you = f'<span class="{cls}">({ch:+d})</span>'

    return f"""
<div class="kid-scope">
  <div class="kid-felt">
    <div class="kid-section-label">Buddy</div>
    <div class="kid-opp-row">{opp_hole_html()}</div>
    <div class="kid-section-label">Middle cards</div>
    <div class="kid-board-row">{board_html}</div>
    <div class="kid-pot">
      <div class="kid-pot-label">Pot</div>
      <div class="kid-pot-value">{pot} coins</div>
    </div>
    <div class="kid-stack-row">
      <span class="kid-stack-pill">Buddy: {ob} coins{extra_opp}</span>
      <span class="kid-stack-pill">You: {yb} coins{extra_you}</span>
    </div>
    <div class="kid-section-label">Your cards</div>
    <div class="kid-you-row">{your_hole_html()}</div>
  </div>
</div>
"""


def kid_resolve_auto_streets(game: PokerGame, status: str) -> str:
    s = status
    guard = 0
    while s == "round_complete" and game.kid_interactive and guard < 8:
        s = game.kid_advance_street_or_end()
        guard += 1
    return s


def _ensure_kid_display_names(game: PokerGame) -> None:
    if len(game.players) >= 2:
        game.players[0].name = "Buddy"
        game.players[-1].name = "You"


def _snapshot_stacks_for_delta(game: PokerGame, human_seat: int) -> None:
    opp = next(p for p in game.players if p.index != human_seat)
    you = game.players[human_seat]
    st.session_state.kid_prev_opp_stack = opp.stack
    st.session_state.kid_prev_you_stack = you.stack


def _render_result_screen(game: PokerGame, human_seat: int) -> None:
    inject_kid_polish_styles()
    summ = game.last_hand_summary
    if not summ:
        return
    show_holes = str(summ.get("stage")) == "showdown"
    st.markdown(_render_kid_table_html(game, human_seat=human_seat, show_opponent_holes=show_holes), unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="kid-result-card">
  <div class="kid-result-title">{kid_result_headline(game, human_seat)}</div>
  <div class="kid-result-body">{kid_result_explanation(game, human_seat)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if show_holes:
        st.caption("Both sides are shown because the hand went to the very end.")

    if st.button("👉 Next Hand", type="primary", use_container_width=True, key="kid_next_hand"):
        st.session_state.kid_show_result = False
        st.session_state.kid_result_seen_sig = None
        st.session_state.kid_prev_pair = False
        st.session_state.kid_prev_board_len = 0
        st.session_state.kid_coach_pick = None
        st.session_state.kid_action_feedback = None
        st.session_state.kid_hands_played = int(st.session_state.get("kid_hands_played", 0)) + 1
        st2 = game.kid_start_new_hand_interactive()
        kid_resolve_auto_streets(game, st2)
        _snapshot_stacks_for_delta(game, human_seat)
        st.rerun()


def render_kid_play_tab(game: PokerGame) -> None:
    inject_kid_polish_styles()
    game.kid_configure()
    _ensure_kid_display_names(game)
    hs = game.kid_human_seat

    if "kid_prev_pair" not in st.session_state:
        st.session_state.kid_prev_pair = False
    if "kid_prev_board_len" not in st.session_state:
        st.session_state.kid_prev_board_len = 0
    if "kid_toast" not in st.session_state:
        st.session_state.kid_toast = None
    if "kid_result_seen_sig" not in st.session_state:
        st.session_state.kid_result_seen_sig = None
    if "kid_show_result" not in st.session_state:
        st.session_state.kid_show_result = False
    if "kid_hands_played" not in st.session_state:
        st.session_state.kid_hands_played = 0
    if "kid_total_delta" not in st.session_state:
        st.session_state.kid_total_delta = 0
    if "kid_session_active" not in st.session_state:
        st.session_state.kid_session_active = False
    if "kid_coach_pick" not in st.session_state:
        st.session_state.kid_coach_pick = None
    if "kid_action_feedback" not in st.session_state:
        st.session_state.kid_action_feedback = None

    title = "## 🎮 Kid table"
    if st.session_state.kid_session_active:
        title += f' <span class="kid-hands-badge">Hand #{st.session_state.kid_hands_played}</span>'
    st.markdown(title, unsafe_allow_html=True)
    if st.session_state.kid_session_active:
        st.caption(
            f"Session coins (You): **{game.players[hs].stack}** · "
            f"Running change since Kid start: **{st.session_state.kid_total_delta:+d}**"
        )

    if st.session_state.kid_toast:
        st.success(st.session_state.kid_toast)
        st.session_state.kid_toast = None

    if st.session_state.kid_action_feedback:
        st.info(st.session_state.kid_action_feedback)
        st.session_state.kid_action_feedback = None

    # Result pause
    if st.session_state.kid_show_result and not game.kid_interactive and game.last_hand_summary:
        _render_result_screen(game, hs)
        return

    show_opp_cards = game.state.stage == "showdown"
    st.markdown(_render_kid_table_html(game, human_seat=hs, show_opponent_holes=show_opp_cards), unsafe_allow_html=True)

    human = game.players[hs]

    if not game.kid_interactive and not st.session_state.kid_show_result:
        st.info("Tap **Start kid game** below, then use the big buttons when it is your turn.")

    # Strength meter
    if game.kid_interactive and not human.has_folded and human.hole_cards:
        try:
            pwin = monte_carlo_win_probability(game, hs, num_samples=72)
        except Exception:
            pwin = 0.5
        lab = get_hand_strength_label(pwin)
        pct = max(0.0, min(1.0, pwin)) * 100.0
        st.markdown(
            f"""
<div class="kid-scope">
  <div class="kid-bar-wrap"><div class="kid-bar-fill" style="width:{pct:.0f}%;"></div></div>
  <div class="kid-bar-label">{lab["label"]} · about {pct:.0f}% strong</div>
</div>
""",
            unsafe_allow_html=True,
        )

    coach_rec = None
    conf = "Medium"
    if game.kid_is_human_turn():
        legal, ca, mn, mx, _tc = game.kid_current_legal_bundle()
        coach_rec = get_ai_coach_recommendation(game, game.ai, hs, legal, ca, mn, mx)
        conf = coach_confidence_level(game)
        st.session_state.kid_coach_pick = coach_rec["kid_choice"]
        rec = cast(KidChoice, coach_rec["kid_choice"])
        pick_label = {"give_up": "Give Up", "stay_in": "Stay In", "go_big": "Go Big"}[rec]
        st.markdown(
            f"""
<div class="kid-scope kid-coach-banner">
  <div class="kid-coach-msg">💡 {coach_rec["message"]}</div>
  <div class="kid-coach-sub">Buddy confidence: <b>{conf}</b> · Try <b>{pick_label}</b> first</div>
</div>
""",
            unsafe_allow_html=True,
        )

        can_fold = "fold" in legal
        can_stay = "check" in legal or "call" in legal
        can_big = "raise" in legal

        def do(choice: KidChoice, *, from_help: bool = False) -> None:
            if from_help:
                st.session_state.kid_action_feedback = "Buddy picked the best move for you! ✨"
            else:
                coach = st.session_state.get("kid_coach_pick")
                if coach is not None and choice == coach:
                    st.session_state.kid_action_feedback = "Good choice 👍"
                elif coach is not None:
                    st.session_state.kid_action_feedback = "That was a little risky 😬"
            legal2, ca2, mn2, mx2, _ = game.kid_current_legal_bundle()
            act, amt = map_kid_choice_to_engine(choice, legal2, ca2, mn2, mx2)
            st2 = game.kid_submit_engine_action(act, amt)
            st2 = kid_resolve_auto_streets(game, st2)
            _kid_update_toasts_after_action(game, hs)
            if not game.kid_interactive and st.session_state.kid_session_active:
                summ = game.last_hand_summary
                if summ:
                    sig = (tuple(summ.get("winners", [])), int(summ.get("final_pot", 0)), str(summ.get("stage", "")))
                    if st.session_state.kid_result_seen_sig != sig:
                        st.session_state.kid_result_seen_sig = sig
                        d = kid_hand_coin_delta(game, hs) or 0
                        st.session_state.kid_total_delta += d
                        st.session_state.kid_show_result = True
                        st.session_state.kid_toast = None
            st.session_state.kid_coach_pick = None
            _snapshot_stacks_for_delta(game, hs)
            st.rerun()

        st.markdown('<div class="kid-scope">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Give Up", disabled=not can_fold, use_container_width=True, key="kid_give"):
                do(cast(KidChoice, "give_up"))
        with c2:
            if st.button("Stay In", disabled=not can_stay, use_container_width=True, key="kid_stay"):
                do(cast(KidChoice, "stay_in"))
        with c3:
            if st.button("Go Big", disabled=not can_big, use_container_width=True, key="kid_big"):
                do(cast(KidChoice, "go_big"))
        with c4:
            if st.button("Help Me", use_container_width=True, key="kid_help"):
                legal2, ca2, mn2, mx2, _ = game.kid_current_legal_bundle()
                rec = get_ai_coach_recommendation(game, game.ai, hs, legal2, ca2, mn2, mx2)
                st.session_state.kid_coach_pick = rec["kid_choice"]
                do(cast(KidChoice, rec["kid_choice"]), from_help=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif game.kid_interactive and human.is_all_in and not human.has_folded:
        st.warning("You are **all in**. Buddy will finish the middle cards — watch the table update.")

    with st.expander("Buddy settings", expanded=False):
        depth = st.slider("Buddy brain depth", 1, 4, 2, key="kid_depth")
        samples = st.slider("Buddy samples", 16, 128, 48, step=16, key="kid_samples")
        game.ai.max_depth = depth
        game.ai.num_samples = samples

    c_start, _ = st.columns([1, 2])
    with c_start:
        if st.button("🌟 Start kid game", type="primary", key="kid_new"):
            st.session_state.kid_session_active = True
            st.session_state.kid_show_result = False
            st.session_state.kid_result_seen_sig = None
            st.session_state.kid_prev_pair = False
            st.session_state.kid_prev_board_len = 0
            st.session_state.kid_coach_pick = None
            st.session_state.kid_action_feedback = None
            st.session_state.kid_hands_played = 1
            st.session_state.kid_total_delta = 0
            st2 = game.kid_start_new_hand_interactive()
            st2 = kid_resolve_auto_streets(game, st2)
            if not game.kid_interactive and game.last_hand_summary:
                summ = game.last_hand_summary
                sig = (tuple(summ.get("winners", [])), int(summ.get("final_pot", 0)), str(summ.get("stage", "")))
                st.session_state.kid_result_seen_sig = sig
                st.session_state.kid_total_delta += kid_hand_coin_delta(game, hs) or 0
                st.session_state.kid_show_result = True
            _snapshot_stacks_for_delta(game, hs)
            st.session_state.kid_toast = "Here we go — good luck!"
            st.rerun()

    st.markdown("---")
    st.markdown("**Buddy’s last numbers (for grown-ups)**")
    analysis = getattr(game.ai, "last_root_analysis", [])
    if analysis:
        for action, amount, ev in analysis[:6]:
            lab = amount if amount is not None else ""
            st.write(f"- {action} {lab}: ≈ {ev:.0f}")
    else:
        st.caption("_Shows after Buddy plans a move._")


def _kid_update_toasts_after_action(game: PokerGame, human_seat: int) -> None:
    human = game.players[human_seat]
    board = game.state.community_cards
    now_len = len(board)
    prev_len = st.session_state.kid_prev_board_len
    if now_len > prev_len and human.hole_cards and not human.has_folded:
        prev_p = st.session_state.kid_prev_pair
        now_p = simple_pair_on_board(human.hole_cards, board)
        msg = kid_event_message(prev_p, now_p, True)
        if msg:
            st.session_state.kid_toast = msg
        st.session_state.kid_prev_pair = now_p
        st.session_state.kid_prev_board_len = now_len
 
poker_ai/deck.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List


SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Deck:
    """Standard 52-card deck."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self.cards: List[Card] = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        self.shuffle()

    def shuffle(self) -> None:
        self._rng.shuffle(self.cards)

    def draw(self, n: int = 1) -> List[Card]:
        if n > len(self.cards):
            raise ValueError("Not enough cards left in deck")
        drawn = self.cards[:n]
        self.cards = self.cards[n:]
        return drawn

 
poker_ai/player.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .deck import Card


Action = str  # "fold", "call", "check", "raise"


@dataclass
class Player:
    name: str
    stack: int
    index: int
    is_human: bool = False
    hole_cards: Optional[Tuple[Card, Card]] = None
    current_bet: int = 0
    has_folded: bool = False
    is_all_in: bool = False

    def reset_for_new_hand(self) -> None:
        self.hole_cards = None
        self.current_bet = 0
        self.has_folded = False
        self.is_all_in = False


class BaseStrategy:
    """Base class for non-human strategies."""

    def choose_action(
        self,
        legal_actions: List[Action],
        call_amount: int,
        min_raise: int,
        max_raise: int,
    ) -> Tuple[Action, Optional[int]]:
        raise NotImplementedError


class RandomStrategy(BaseStrategy):
    """Placeholder random strategy. Concrete implementation will be added later."""

    def __init__(self, rng=None) -> None:
        import random

        self._rng = rng or random.Random()

    def choose_action(
        self,
        legal_actions: List[Action],
        call_amount: int,
        min_raise: int,
        max_raise: int,
    ) -> Tuple[Action, Optional[int]]:
        action = self._rng.choice(legal_actions)
        if action == "raise":
            amount = self._rng.randint(min_raise, max_raise) if max_raise >= min_raise else min_raise
            return action, amount
        return action, None

 
poker_ai/poker_rules.py
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable, List, Tuple

from .deck import Card, RANKS


HandRank = Tuple[int, List[int]]


def evaluate_7card_hand(cards: Iterable[Card]) -> HandRank:
    """
    Evaluate best 5-card hand out of up to 7 cards.
    Returns (category, tiebreaker_values) where higher is better.
    Categories (lower is worse):
      0: High card
      1: One pair
      2: Two pair
      3: Three of a kind
      4: Straight
      5: Flush
      6: Full house
      7: Four of a kind
      8: Straight flush
    """
    best: HandRank | None = None
    for combo in combinations(list(cards), 5):
        rank = _evaluate_5card_hand(combo)
        if best is None or rank > best:
            best = rank
    if best is None:
        raise ValueError("Need at least 5 cards")
    return best


def _evaluate_5card_hand(cards: Tuple[Card, ...]) -> HandRank:
    ranks = sorted((RANKS.index(c.rank) for c in cards), reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1
    is_straight, straight_high = _is_straight(ranks)

    counts = Counter(ranks)
    ordered = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    groups = [c for c, _ in ordered]
    freqs = sorted(counts.values(), reverse=True)

    if is_straight and is_flush:
        return 8, [straight_high]
    if freqs == [4, 1]:
        return 7, groups + [g for g in ranks if g not in groups]
    if freqs == [3, 2]:
        return 6, groups
    if is_flush:
        return 5, ranks
    if is_straight:
        return 4, [straight_high]
    if freqs == [3, 1, 1]:
        return 3, groups + [g for g in ranks if g not in groups]
    if freqs == [2, 2, 1]:
        return 2, groups + [g for g in ranks if g not in groups]
    if freqs == [2, 1, 1, 1]:
        return 1, groups + [g for g in ranks if g not in groups]
    return 0, ranks


def _is_straight(sorted_ranks_desc: List[int]) -> Tuple[bool, int]:
    """Return (is_straight, high_rank_index)."""
    ranks = sorted(set(sorted_ranks_desc), reverse=True)
    # Wheel: A-2-3-4-5
    if set(ranks) >= {12, 0, 1, 2, 3}:
        return True, 3
    if len(ranks) < 5:
        return False, -1
    for i in range(len(ranks) - 4):
        window = ranks[i : i + 5]
        if window[0] - window[4] == 4:
            return True, window[0]
    return False, -1


def compare_hands(cards1: Iterable[Card], cards2: Iterable[Card]) -> int:
    """Compare two 7-card hands. Returns 1 if hand1 wins, -1 if hand2 wins, 0 if tie."""
    r1 = evaluate_7card_hand(cards1)
    r2 = evaluate_7card_hand(cards2)
    return (r1 > r2) - (r1 < r2)

 
poker_ai/evaluation.py
from __future__ import annotations

import time
from typing import Dict, List, Literal

import pandas as pd

from .game_engine import PokerGame


def run_simulation(
    num_hands: int = 200,
    max_depth: int = 2,
    num_samples: int = 64,
    mode: Literal["expectiminimax", "normal"] = "expectiminimax",
) -> pd.DataFrame:
    """Run many automated games and collect metrics.

    Currently compares:
      - Seat 0: Expectiminimax AI
      - Seat 1: Random strategy
    """
    game = PokerGame(num_players=2)
    game.ai.max_depth = max_depth
    game.ai.num_samples = num_samples
    game.use_expectiminimax = mode == "expectiminimax"
    if not game.use_expectiminimax:
        # Seat 0 fallback uses existing baseline logic: check/call-first, fold otherwise.
        game.strategies[0] = None
    results: List[Dict] = []

    initial_stacks = [p.stack for p in game.players]

    for hand_idx in range(1, num_hands + 1):
        stacks_before = [p.stack for p in game.players]
        t0 = time.perf_counter()
        winners = game.play_hand()
        dt = time.perf_counter() - t0
        stacks_after = [p.stack for p in game.players]

        ai_delta = stacks_after[0] - stacks_before[0]

        results.append(
            {
                "hand": hand_idx,
                "mode": mode,
                "ai_delta": ai_delta,
                "ai_stack": stacks_after[0],
                "opp_stack": stacks_after[1],
                "decision_time": dt,
                "winner": ",".join(w.name for w in winners),
            }
        )

    df = pd.DataFrame(results)
    return df


def summarize_results(df: pd.DataFrame) -> Dict[str, float]:
    """Compute summary statistics for AI performance."""
    if df.empty:
        return {}
    win_rate = (df["ai_delta"] > 0).mean()
    loss_rate = (df["ai_delta"] < 0).mean()
    avg_profit = df["ai_delta"].mean()
    avg_decision_time = df["decision_time"].mean()
    return {
        "win_rate": float(win_rate),
        "loss_rate": float(loss_rate),
        "avg_profit": float(avg_profit),
        "avg_decision_time": float(avg_decision_time),
    }

