import streamlit as st

from poker_ai.evaluation import run_simulation, summarize_results
from poker_ai.game_engine import PokerGame
from poker_ai.visualization import inject_styles, render_table


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
    st.markdown(
        "### Poker Game Simulator with **Expectiminimax AI**",
    )

    tab_play, tab_sim = st.tabs(["Play Game", "Simulation & Evaluation"])

    with tab_play:
        if "game" not in st.session_state:
            st.session_state.game = PokerGame(num_players=2)

        game: PokerGame = st.session_state.game

        col_left, col_right = st.columns([3, 2])

        with col_left:
            render_table(game)

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

    with tab_sim:
        st.subheader("Automated Simulation")
        num_hands = st.slider("Number of hands", min_value=50, max_value=1000, value=200, step=50)
        depth = st.slider("AI search depth (simulation)", min_value=1, max_value=4, value=2, step=1)
        samples = st.slider("Monte Carlo samples (simulation)", min_value=16, max_value=256, value=64, step=16)
        if st.button("Run simulation"):
            df = run_simulation(num_hands=num_hands, max_depth=depth, num_samples=samples)
            st.session_state.sim_df = df

        df = st.session_state.get("sim_df")
        if df is not None and not df.empty:
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



