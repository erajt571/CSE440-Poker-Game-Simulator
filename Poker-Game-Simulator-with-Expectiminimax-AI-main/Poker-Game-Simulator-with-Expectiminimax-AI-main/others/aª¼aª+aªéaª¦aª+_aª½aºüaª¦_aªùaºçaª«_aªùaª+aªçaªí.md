# Poker Game Simulator (Bangla Full Guide)

## প্রজেক্টের লক্ষ্য

এই প্রজেক্টে একটি **simplified Texas Hold'em Poker simulator** বানানো হয়েছে, যেখানে AI প্লেয়ার **Expectiminimax** ব্যবহার করে uncertainty (অজানা কার্ড + chance event) এর মধ্যে সিদ্ধান্ত নেয়।

আপনার প্রজেক্টের মূল তিনটা অংশ:

1. **Environment design** (ডেক, প্লেয়ার, pot, round flow)
2. **AI decision engine** (Expectiminimax)
3. **Performance evaluation** (simulation metrics দিয়ে compare)

---

## কীভাবে রান করবেন (Run Instructions)

প্রজেক্টটি Streamlit-based। সঠিকভাবে চালাতে:

```bash
cd /Users/eloneflax/cse440-poker-ai
source .venv/bin/activate
streamlit run main.py
```

তারপর ব্রাউজারে খুলুন: `http://localhost:8501`

> নোট: `python main.py` দিলে warning আসবে, কারণ এটা Streamlit app।

---

## অ্যাপে মোট কয়টা ভার্সন/মোড আছে?

UI তে ৩টি tab আছে:

1. **Play Game**  
   - মূল full hand auto-play mode  
   - AI vs opponent hand-by-hand দেখা যায়

2. **Kid Play 🎈**  
   - step-by-step interactive mode  
   - human turn এ action দিতে পারেন

3. **Simulation & Evaluation**  
   - অনেক hand auto-run করে metrics দেখায়  
   - Expectiminimax বনাম normal logic compare করা যায়

---

## গেমের সেটআপ (Environment/Components)

### 1) Game Config
- Players: সাধারণত 2 (heads-up)
- Starting stack: 1000 chips
- Small blind: 10
- Big blind: 20

### 2) Core Components
- `Deck` (52 cards, shuffled, duplicate ছাড়া draw)
- `Player` (stack, current bet, hole cards, fold/all-in status)
- `GameState`:
  - `community_cards`
  - `pot`
  - `current_player_index`
  - `dealer_index`
  - `stage` = preflop/flop/turn/river/showdown
- `PokerGame` engine (round flow চালায়)
- `ExpectiminimaxAI` (AI সিদ্ধান্ত নেয়)
- `evaluate_7card_hand` (winner determine করে)

---

## Poker রুলস (এই প্রজেক্টে যেভাবে ব্যবহার হয়েছে)

### কার্ড
- প্রত্যেক প্লেয়ার 2টা hole/private card পায়।
- টেবিলে মোট 5টা community card আসে (flop 3, turn 1, river 1)।
- best 5-card combination winner নির্ধারণ করে।

### স্টেজ/রাউন্ড ফ্লো
1. **Preflop**: hole cards deal + blinds post + betting
2. **Flop**: 3 community cards + betting
3. **Turn**: 1 community card + betting
4. **River**: 1 community card + betting
5. **Showdown**: folded নয় এমন players এর best hand compare

### Action Rules
- `fold`: hand ছেড়ে দেওয়া
- `check`: bet না করে turn pass (to_call = 0 হলে)
- `call`: current bet match করা
- `raise`: bet বাড়ানো (project-এ simplified sizing)

### হাতের র‍্যাঙ্কিং (উচ্চ থেকে নিম্ন)
Straight Flush > Four of a Kind > Full House > Flush > Straight > Three of a Kind > Two Pair > One Pair > High Card

---

## Step-by-Step: একদম শুরু থেকে hand শেষ পর্যন্ত

### ধাপ 1: New hand শুরু
- ডেক reset/shuffle হয়
- dealer rotate হয়
- সবাই reset হয় (fold/bet status)
- 2টা করে hole card deal হয়

### ধাপ 2: Blinds post
- heads-up এ dealer small blind দেয়, অন্যজন big blind দেয়
- pot এ blind যোগ হয়

### ধাপ 3: Preflop betting
- active player action নেয় (fold/call/raise/check)
- raise হলে অন্যদের আবার act করতে হয়
- যদি 1 জন বাকি থাকে => hand সেখানেই শেষ

### ধাপ 4: Flop
- 3টা community card open
- betting round

### ধাপ 5: Turn
- 1টা card open
- betting round

### ধাপ 6: River
- শেষ card open
- final betting round

### ধাপ 7: Showdown
- active players এর 7-card (2 hole + 5 board) evaluate
- winner pot পায় (tie হলে split)

---

## Play Game tab কীভাবে ব্যবহার করবেন

1. `AI search depth` সেট করুন (1–4)
2. `Monte Carlo samples` সেট করুন (16–256)
3. `Play new hand` চাপুন
4. দেখুন:
   - table state
   - pot/chips
   - last hand winners
   - **AI root decision analysis (EV per action)**

### EV panel কী বোঝায়?
- AI action-wise expected value (EV) estimate করে।
- যেটার EV বেশি, সাধারণত AI সেটা pick করে।

---

## Kid Play tab কীভাবে ব্যবহার করবেন

এখানে খেলাটা step-by-step pause হয়:

1. নতুন hand শুরু হবে
2. AI/non-human automatic চলবে
3. human turn এ legal actions দেখাবে
4. আপনি action দিলে game আবার এগোবে
5. round complete হলে next street যাবে
6. শেষ পর্যন্ত showdown/hand over

এটা demo/presentation এ rules শেখানোর জন্য খুব useful।

---

## Simulation & Evaluation tab কীভাবে ব্যবহার করবেন

1. `Number of hands` সেট করুন (যেমন 200/500/1000)
2. search depth ও samples সেট করুন
3. Compare চাইলে `Compare with normal logic` tick দিন
4. `Run simulation` চাপুন

### মেট্রিক্স
- Win rate
- Loss rate
- Avg profit per hand
- Avg decision time
- Cumulative profit chart
- Profit distribution

---

## Expectiminimax কীভাবে কাজ করছে (এই প্রজেক্টে)

AI tree-তে 3 ধরনের node:

1. **MAX node (AI turn)**  
   AI নিজের best action choose করে (EV maximize)

2. **MIN/Opponent node (Opponent reaction)**  
   opponent response model করা হয় (simplified policy)

3. **CHANCE node (Random uncertainty)**  
   unknown future cards sampling করে expected outcome নেয়

### Practical simplification
- raise size discrete করা হয়েছে (min/mid/max)
- chance event Monte Carlo sampling দিয়ে approximate
- depth-limited search (runtime control)

---

## Expectiminimax vs Normal Logic (তফাৎ)

## 1) Decision quality
- **Expectiminimax**: ভবিষ্যৎ random event + opponent response নিয়ে EV estimate করে
- **Normal logic**: সহজ fallback behavior (প্রধানত check/call-first style)

## 2) Uncertainty handling
- **Expectiminimax**: chance nodes explicitly consider করে
- **Normal logic**: uncertainty-aware search করে না

## 3) Explainability
- **Expectiminimax**: action-wise EV analysis panel দেয়
- **Normal logic**: এমন EV breakdown থাকে না

## 4) Cost
- **Expectiminimax**: decision time বেশি হতে পারে
- **Normal logic**: দ্রুত কিন্তু সাধারণত কম strategic

---

## Algorithm Performance কিভাবে Evaluate করবেন

প্রেজেন্টেশনের জন্য প্র্যাকটিকাল plan:

1. একই setting এ 200/500 hand চালান
2. mode = `expectiminimax` vs `normal` compare করুন
3. collect করুন:
   - Win rate delta
   - Profit delta
   - Decision time delta
4. cumulative profit chart দেখান
5. conclusion দিন:
   - Expectiminimax কি quality বাড়িয়েছে?
   - runtime trade-off কত?

---

## প্রজেক্টে ব্যবহৃত simplifications (report-এ mention করবেন)

- 2-player focus (evaluation সহজ করার জন্য)
- betting abstraction simplified
- side-pot logic full version নয়
- opponent model fully learned নয় (rule-based/simple)

এইগুলো limitation হিসেবে mention করলে report আরও professional দেখাবে।

---

## End-to-End Quick Demo Script (Presentation friendly)

1. App run (`streamlit run main.py`)
2. Play Game tab: 1টা hand চালান
3. EV analysis দেখান (AI কেন move নিল)
4. Kid Play tab: human action দিয়ে ১–২ step দেখান
5. Simulation tab: compare mode দিয়ে 200 hands run
6. metrics + chart থেকে final takeaway বলুন

---

## জরুরি চেকলিস্ট (Game demo day)

- [ ] App run হচ্ছে (`localhost:8501`)
- [ ] Play Game tab কাজ করছে
- [ ] Kid Play tab এ legal action দেখা যাচ্ছে
- [ ] Simulation compare চালিয়ে metrics আসছে
- [ ] এক মিনিট demo video ready
- [ ] GitHub এ latest code push করা আছে

