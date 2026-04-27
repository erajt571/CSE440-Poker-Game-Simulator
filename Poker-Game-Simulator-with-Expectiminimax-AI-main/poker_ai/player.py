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

