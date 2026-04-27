from __future__ import annotations

from typing import List, Optional

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
        /* Overall app tweaks */
        .main {
            background: radial-gradient(circle at top, #1b2938 0, #02040a 55%, #000000 100%);
            color: #f5f7fa;
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
    """Render a beginner-friendly poker-style table view.

    The user is treated as the last seat (bottom of the table) while AI seats
    appear "around" the top/side visually.
    """
    with st.container():
        st.markdown('<div class="poker-table">', unsafe_allow_html=True)

        pot_col, stage_col = st.columns([2, 1])
        pot_col.markdown(
            f'<div class="poker-chip-label">Pot</div><div class="poker-chip">💰 {game.state.pot}</div>',
            unsafe_allow_html=True,
        )
        with stage_col:
            st.markdown("**Game flow**")
            render_stage_track(game.state.stage)

        # Community cards
        st.markdown('<div class="poker-board">', unsafe_allow_html=True)
        st.markdown("**Community cards**", unsafe_allow_html=True)
        if game.state.community_cards:
            cards_html = " ".join(render_card_span(c) for c in game.state.community_cards)
            st.markdown(f'<div class="poker-cards">{cards_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown("_No community cards yet_", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Players: AI around table, user at the bottom.
        ai_players = [p for p in game.players if p.index != len(game.players) - 1]
        user: Optional[object] = None
        if game.players:
            user = game.players[-1]

        # Top row: AI players
        if ai_players:
            cols = st.columns(len(ai_players))
            for col, p in zip(cols, ai_players):
                with col:
                    _render_player_panel(p, is_user=False)

        # Bottom row: user
        if user is not None:
            st.markdown("---")
            st.markdown("#### You (bottom of the table)")
            _render_player_panel(user, is_user=True, beginner_mode=beginner_mode)

        st.markdown("</div>", unsafe_allow_html=True)


def _render_player_panel(player, is_user: bool, beginner_mode: bool = False) -> None:
    """Small helper so AI and user use the same visual language."""
    from .player import Player  # local import to avoid cycles

    p: Player = player
    with st.container():
        st.markdown('<div class="poker-player-card">', unsafe_allow_html=True)
        name_cls = "poker-player-name"
        labels: List[str] = []
        if is_user:
            labels.append("You")
        else:
            name_cls += " poker-player-name-ai"
            labels.append("AI")

        name_html = f'<span class="{name_cls}">{p.name}</span>'
        for lbl in labels:
            name_html += f" <span class='poker-status-pill'>{lbl}</span>"

        status_pills: List[str] = []
        if p.has_folded:
            status_pills.append('<span class="poker-status-pill poker-status-pill-folded">Folded</span>')
        if p.is_all_in:
            status_pills.append('<span class="poker-status-pill poker-status-pill-allin">All‑in</span>')
        status_html = " ".join(status_pills)

        header_cols = st.columns([3, 2, 2])
        header_cols[0].markdown(name_html + (" " + status_html if status_html else ""), unsafe_allow_html=True)
        header_cols[1].metric("Chips", f"{p.stack}")
        header_cols[2].metric("This round bet", f"{p.current_bet}")

        if p.hole_cards is not None:
            cards_html = " ".join(render_card_span(c) for c in p.hole_cards)
        else:
            cards_html = '<span class="poker-cards">[hidden]</span>'

        header_cols[0].markdown(cards_html, unsafe_allow_html=True)

        if is_user and beginner_mode and not p.has_folded:
            st.caption("We show your cards at the bottom. The AI's cards stay hidden until showdown.")

        st.markdown("</div>", unsafe_allow_html=True)


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