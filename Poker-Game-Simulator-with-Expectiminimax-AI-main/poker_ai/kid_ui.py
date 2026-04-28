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
