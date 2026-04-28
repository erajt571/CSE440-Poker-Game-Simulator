"""Kid-friendly mapping and helpers on top of the poker engine (no engine rewrites)."""

from __future__ import annotations

import random
from typing import Dict, List, Literal, Optional, Tuple

from .deck import Card, SUITS, RANKS
from .expectiminimax import ExpectiminimaxAI, SearchGameState
from .game_engine import PokerGame
from .player import Action
from .poker_rules import evaluate_7card_hand

KidChoice = Literal["give_up", "stay_in", "go_big"]


def map_kid_choice_to_engine(
    choice: KidChoice,
    legal: List[Action],
    call_amount: int,
    min_raise: int,
    max_raise: int,
) -> Tuple[Action, Optional[int]]:
    """Map child-facing buttons to engine actions."""
    can_check = "check" in legal
    if choice == "give_up":
        if "fold" not in legal:
            raise ValueError("Cannot give up right now")
        return "fold", None
    if choice == "stay_in":
        if can_check:
            return "check", None
        if "call" in legal:
            return "call", None
        raise ValueError("Cannot stay in (no check/call)")
    if choice == "go_big":
        if "raise" not in legal:
            raise ValueError("Cannot go big right now")
        # Fixed bump: prefer min legal raise; cap at all-in
        size = min(max(min_raise, min_raise), max_raise)
        return "raise", size
    raise ValueError(f"Unknown choice {choice!r}")


def get_hand_strength_label(win_prob: float) -> Dict[str, str]:
    """Map estimated win rate to a kid-facing label and CSS tone."""
    if win_prob < 0.3:
        return {"label": "Weak 😟", "tone": "red"}
    if win_prob < 0.5:
        return {"label": "Okay 🙂", "tone": "yellow"}
    if win_prob < 0.75:
        return {"label": "Strong 😃", "tone": "green"}
    return {"label": "Very strong 🔥", "tone": "purple"}


def _all_cards() -> List[Card]:
    return [Card(r, s) for s in SUITS for r in RANKS]


def monte_carlo_win_probability(
    game: PokerGame,
    human_seat: int,
    *,
    num_samples: int = 120,
    rng: Optional[random.Random] = None,
) -> float:
    """Rough P(win at showdown) vs one random opponent hand + random runout."""
    rng = rng or random.Random()
    human = game.players[human_seat]
    if human.hole_cards is None or human.has_folded:
        return 0.0
    others = [p for p in game.players if p.index != human_seat and not p.has_folded]
    if not others:
        return 1.0

    board = list(game.state.community_cards)
    known = set(board) | set(human.hole_cards)
    wins = 0
    for _ in range(num_samples):
        pool = [c for c in _all_cards() if c not in known]
        rng.shuffle(pool)
        idx = 0
        opp_holes: List[Tuple[Card, Card]] = []
        for _p in others:
            opp_holes.append((pool[idx], pool[idx + 1]))
            idx += 2
        need = 5 - len(board)
        runout = board + pool[idx : idx + need]
        idx += need
        my_best = evaluate_7card_hand(list(human.hole_cards) + runout)
        best_opp = None
        for oh in opp_holes:
            their = evaluate_7card_hand(list(oh) + runout)
            if best_opp is None or their > best_opp:
                best_opp = their
        assert best_opp is not None
        if my_best > best_opp:
            wins += 1
        elif my_best == best_opp:
            wins += 0.5
    return wins / num_samples


def build_coach_search_state(game: PokerGame, human_seat: int) -> SearchGameState:
    """Treat the human as the expectiminimax root player (same heuristic as seat 0)."""
    human = game.players[human_seat]
    assert human.hole_cards is not None
    opp_stack = sum(p.stack for p in game.players if p.index != human_seat)
    return SearchGameState(
        community_cards=list(game.state.community_cards),
        ai_hole_cards=human.hole_cards,
        pot=game.state.pot,
        ai_stack=human.stack,
        opp_stack=opp_stack,
        to_move="ai",
        stage=game.state.stage,
    )


def engine_action_to_kid_hint(action: Action) -> str:
    if action == "fold":
        return "Better to Give Up"
    if action in ("call", "check"):
        return "Stay In is a good idea"
    if action == "raise":
        return "Go Big looks strong"
    return "Stay In is a good idea"


def get_ai_coach_recommendation(
    game: PokerGame,
    ai: ExpectiminimaxAI,
    human_seat: int,
    legal: List[Action],
    call_amount: int,
    min_raise: int,
    max_raise: int,
) -> Dict[str, object]:
    """Run expectiminimax from the human's seat; return engine + kid mapping."""
    state = build_coach_search_state(game, human_seat)
    best_action, best_amount = ai.choose_action(state, legal, call_amount, min_raise, max_raise)
    kid_choice: KidChoice
    if best_action == "fold":
        kid_choice = "give_up"
    elif best_action == "raise":
        kid_choice = "go_big"
    else:
        kid_choice = "stay_in"
    return {
        "engine_action": best_action,
        "engine_amount": best_amount,
        "kid_choice": kid_choice,
        "message": engine_action_to_kid_hint(best_action),
    }


def kid_choice_from_engine_action(action: Action) -> KidChoice:
    if action == "fold":
        return "give_up"
    if action == "raise":
        return "go_big"
    return "stay_in"


def simple_pair_on_board(hole: Tuple[Card, Card], board: List[Card]) -> bool:
    ranks = [c.rank for c in hole] + [c.rank for c in board]
    return len(ranks) != len(set(ranks))


def kid_event_message(prev_pair: bool, now_pair: bool, board_grew: bool) -> Optional[str]:
    if board_grew and now_pair and not prev_pair:
        return "You matched some of the middle cards!"
    if board_grew and now_pair and prev_pair:
        return "Your cards got stronger!"
    return None


def kid_hand_coin_delta(game: PokerGame, human_seat: int) -> Optional[int]:
    """Coins gained/lost this hand for the human (needs ``kid_stack_at_hand_start``)."""
    if game.kid_stack_at_hand_start is None:
        return None
    before = game.kid_stack_at_hand_start[human_seat]
    after = game.players[human_seat].stack
    return after - before


def coach_confidence_level(game: PokerGame) -> str:
    """High / Medium / Low from spread of root EV estimates (after last ``choose_action``)."""
    rows = getattr(game.ai, "last_root_analysis", []) or []
    if len(rows) < 2:
        return "High"
    evs = sorted((float(r[2]) for r in rows), reverse=True)
    spread = evs[0] - evs[1]
    pot = max(float(game.state.pot), 1.0)
    if spread > 0.22 * pot:
        return "High"
    if spread > 0.07 * pot:
        return "Medium"
    return "Low"


def card_to_display_str(card: Card) -> str:
    return f"{card.rank}{card.suit}"


def kid_result_headline(game: PokerGame, human_seat: int) -> str:
    """Short coin headline for the result panel."""
    delta = kid_hand_coin_delta(game, human_seat)
    if delta is None:
        return "Hand finished"
    if delta > 0:
        return f"You won **+{delta}** coins 🎉"
    if delta < 0:
        return f"You lost **{abs(delta)}** coins"
    return "No coins gained or lost this hand"


def kid_result_explanation(game: PokerGame, human_seat: int) -> str:
    """Plain explanation without poker jargon."""
    summ = getattr(game, "last_hand_summary", None)
    if not summ:
        return ""
    human = game.players[human_seat]
    w = summ.get("winners") or []
    if human_seat in w:
        return "You had the better cards when everything was shown, or Buddy gave up."
    if human.has_folded:
        return "You chose to give up, so Buddy took the pile in the middle."
    return "When all the middle cards were shown, Buddy’s side was higher than yours."


def kid_simple_outcome_line(game: PokerGame, human_seat: int) -> str:
    """One-line kid result after the hand."""
    summ = getattr(game, "last_hand_summary", None)
    if not summ:
        return ""
    w = summ.get("winners") or []
    human_won = human_seat in w
    delta = kid_hand_coin_delta(game, human_seat)
    if delta is None:
        coins = ""
    elif delta > 0:
        coins = f" You gained **+{delta}** coins! 🎉"
    elif delta < 0:
        coins = f" You lost **{abs(delta)}** coins."
    else:
        coins = " Your coins stayed the same."
    if human_won:
        return "You won — your cards were stronger at the end." + coins
    if game.players[human_seat].has_folded:
        return "You gave up this round — the other player took the pot." + coins
    return "You did not win this time — the other side had stronger cards at the end." + coins
