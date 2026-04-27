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

