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

