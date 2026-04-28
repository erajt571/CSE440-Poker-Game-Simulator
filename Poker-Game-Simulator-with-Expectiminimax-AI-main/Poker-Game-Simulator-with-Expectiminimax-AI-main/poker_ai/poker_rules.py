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

