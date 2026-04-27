## Poker Game Simulator with Expectiminimax AI

### Project Overview

This project implements a simplified Texas Hold'em poker simulator with an AI agent that uses the **Expectiminimax** algorithm to make strategic decisions under uncertainty. It is designed as an academic project for a university AI course (similar scope to CSE440).

The system includes:

- **Game environment**: deck, cards, players, betting rounds, pot management, and hand evaluation.
- **AI agent**: Expectiminimax with chance nodes and depth-limited search.
- **Opponents**: random strategy opponents (easy baseline).
- **Visualization**: interactive Streamlit web UI showing cards, chips, pot, and winners.
- **Simulation & evaluation**: tools to run many automated games and measure AI performance.

### Tech Stack

- **Language**: Python 3.9+
- **UI**: Streamlit
- **Core libs**: `numpy`, `pandas`, `matplotlib`

### Project Structure

```text
poker_ai/
  __init__.py
  deck.py            # Card and deck utilities
  player.py          # Player state and strategies
  poker_rules.py     # Hand evaluation and comparison
  game_engine.py     # Game flow: dealing, betting, showdown
  expectiminimax.py  # Expectiminimax AI and search state
  evaluation.py      # Simulation and metrics collection
  visualization.py   # Streamlit rendering helpers

main.py              # Streamlit app entry point
requirements.txt
README.md
```

### How to Install and Run

1. **Create / activate a virtual environment (recommended)**

```bash
cd cse327-poker-ai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the Streamlit app**

```bash
streamlit run main.py
```

This will open a browser window with two tabs:

- **Play Game**: play / observe single hands with the Expectiminimax AI.
- **Simulation & Evaluation**: run many automated hands and see metrics.

### Using the UI

#### Play Game tab

- Seat **0** is the **Expectiminimax AI**.
- Seat **1** is a **random strategy** opponent.
- The table view shows:
  - Player names, stacks, current bets, and status (active/folded/all‑in).
  - Hole cards (for debugging / demonstration).
  - Community cards (board), pot, and current stage (preflop / flop / turn / river / showdown).
- Click **“Play new hand”** to:
  - Deal cards, run all betting rounds, and resolve the pot.
  - See who won the last hand.

#### Simulation & Evaluation tab

- Choose **number of hands** (e.g., 200–1000).
- Click **“Run simulation”** to:
  - Run that many heads‑up games (AI vs random).
  - Record AI profit per hand and decision time.
- View:
  - **Win rate / loss rate**.
  - **Average profit per hand**.
  - **Average decision time**.
  - **Cumulative profit over hands** (line chart).
  - **Profit distribution** (bar chart of per‑hand results).

### Expectiminimax Algorithm (High Level)

The AI uses a depth‑limited Expectiminimax search tailored for poker:

- **MAX nodes (AI decisions)**:
  - Consider actions: *fold*, *call/check*, and a small set of **discrete raise sizes**.
  - For each action, compute an estimated expected value (EV).

- **MIN nodes (opponent decisions)**:
  - Use a simple **opponent policy** based on pot odds (call/continue vs fold).
  - This approximates adversarial behavior without exploding the tree.

- **CHANCE nodes (uncertainty)**:
  - Unknown opponent hole cards and future community cards (flop / turn / river).
  - Approximated via **Monte Carlo sampling** from the remaining deck.

- **Leaf / depth‑limit evaluation**:
  - Run multiple random simulations:
    - Sample opponent hole cards and any missing board cards.
    - Evaluate both hands with `evaluate_7card_hand`.
    - Treat win / loss / tie as +/- current pot (simplified chip EV).
  - Return the average as the heuristic value for that state.

The chosen action is the one with the **highest estimated EV** at the root.

### Limitations and Simplifications

To keep the project focused and tractable for an academic assignment:

- No side pots (all players start equal stacks; all‑in is simplified).
- Fixed‑structure betting (one round per street; limited raise sizing).
- Two‑player (heads‑up) evaluation in simulations (easier to analyze).
- Simple opponent model (not full opponent modeling / learning).

These choices can be clearly discussed as design trade‑offs in a report.

### How to Extend for a Course Project

- Add more **opponent types**:
  - Rule‑based tight / loose players.
  - Different personalities for experiments.
- Add **config controls** to the UI:
  - Expectiminimax depth.
  - Number of Monte Carlo samples.
  - Opponent type selection.
- Visualize a **small portion of the decision tree**:
  - For the chosen action, show a few top branches with EVs.
- Log hands and decisions to a file for offline analysis.

### Credits and References

- Inspired by previous course project: `Poker-game-simulator-` on GitHub by Tajul et al. (`https://github.com/tajul06/Poker-game-simulator-`).
- Classic Expectiminimax and game AI references:
  - Russell & Norvig, *Artificial Intelligence: A Modern Approach*.
  - Various academic works on poker AI and imperfect‑information games.

