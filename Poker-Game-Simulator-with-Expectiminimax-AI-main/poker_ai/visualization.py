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