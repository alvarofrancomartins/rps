# RPS — does priming an LLM change how it plays?

A minimal, controlled experiment on LLM behavior. Two independent DeepSeek
agents play Rock-Paper-Scissors. The only thing that varies between runs is a
single sentence prepended to an agent's system prompt. We measure whether that
sentence — praising B, praising B's opponent, or praising *both* — changes who
wins.

Everything lives in one engine script, plus an `analysis/` folder holding the
statistical test, the report, and the plotting script. There is no pipeline, no
framework, no database — just four results folders.

## The experiment

- **Model:** `deepseek-flash` (thinking disabled), temperature `0.7`.
- **Scale:** 10,000 games per condition, 10 rounds per game, up to 100 games in
  flight at once.
- **A game** is won by whoever takes *more than half* of the 10 rounds
  (strictly `> 5`). Otherwise it is a draw.

The independent variable is one sentence prepended to an agent's system prompt
(the `--prime-b` and `--prime-a` flags). In the three one-sided conditions,
Agent A's setup — prompt, model, temperature, code path — is identical in every
condition; only B's system prompt changes. (A's actual moves are stochastic and
differ each game, but A samples from the same distribution throughout.) In the
symmetric `both` condition, A is primed too.

| Condition | Folder | Priming sentence(s) |
|---|---|---|
| normal (control) | `normal/` | *(none)* |
| buttered | `buttered/` | B: You are the greatest Rock-Paper-Scissors player in the world. |
| undermined | `undermined/` | B: You are playing against the greatest Rock-Paper-Scissors player in the world. |
| both | `both/` | A **and** B: You are the greatest Rock-Paper-Scissors player in the world. |

## Fairness (no information leak, by construction)

Each round is **simultaneous**. Both agents are queried from an identical,
frozen snapshot of the *completed* rounds only:

- an agent sees its own past moves and its opponent's past moves;
- it never sees the opponent's current-round move, and never sees the round
  result, before choosing.

The engine records every agent's history snapshot and runs an audit that
verifies each history contains exactly the `round - 1` completed rounds and no
current-round leak. All four runs report **0 audit issues**.

## Results

Game-level wins (10,000 games × 10 rounds each):

| Condition | A game-wins | B game-wins | Draws | A decisive share |
|---|---|---|---|---|
| normal | 1160 | 1206 | 7634 | 49.0 % |
| buttered | 1357 | 927 | 7716 | 59.4 % |
| undermined | **1597** | 787 | 7616 | **67.0 %** |
| both | 1202 | 1224 | 7574 | 49.5 % |

**Finding: the prime is a symmetric handicap on whoever receives it.** One-sided
flattery hurts its recipient, and the effect is graded: no prime → flattered B →
undermined B moves B's share of decided games 51 % → 41 % → 33 %. Flattering
*both* agents cancels — B's share returns to 50.5 % (A 49.5 %), statistically
indistinguishable from the unprimed control (pairwise χ² = 1.12, p = 0.57 after
Holm correction). The draw rate is unchanged (~76 % everywhere); what moves is
who wins the games that do get decided.

The formal test — a Pearson chi-square test of independence on the full 4 × 3
table (χ² = 222.98, df = 6, p ≈ 2.4 × 10⁻⁴⁵), plus six Bonferroni-Holm-corrected
pairwise tests that isolate *which* conditions differ — and the argument for why
the full table (and not a decisive-only z-test) is the right test, live in
[`analysis/report.md`](analysis/report.md).

## Project layout

```
rps/
├── README.md
├── rps_tournament.py     # the engine (stdlib only, thinking off)
├── rps_reasoning.py      # thinking-on variant (captures chain-of-thought)
├── analysis/             # statistical analysis
│   ├── stats.py          # omnibus + corrected pairwise tests
│   ├── moves.py          # move-level: what the agents actually changed
│   ├── report.md         # the statistical report (tests + mechanism)
│   ├── plot_results.py   # renders the 5 charts from a results.json
│   ├── make_explorer.py  # builds game_explorer.html (40,000 games)
│   └── game_explorer.html
├── normal/               # control
│   ├── results.json      # full per-round data + usage + audit
│   ├── run.log           # progress log
│   └── plots/            # 5 PNG charts
├── buttered/             # (same structure)
├── undermined/           # (same structure)
├── both/                 # the symmetric cell (same structure)
├── reasoning/            # small thinking-on runs (10 games × 3 conditions)
└── viz/                  # Manim animation script + rendered videos
```

## Reproduce

Requires Python 3 and `DEEPSEEK_API_KEY` in the environment.

```bash
# control (--out defaults to normal/results.json)
python3 rps_tournament.py --model deepseek-flash --games 10000 --rounds 10 --parallel-games 100

# buttered
python3 rps_tournament.py --model deepseek-flash --games 10000 --rounds 10 --parallel-games 100 \
  --prime-b "You are the greatest Rock-Paper-Scissors player in the world." \
  --out buttered/results.json

# undermined
python3 rps_tournament.py --model deepseek-flash --games 10000 --rounds 10 --parallel-games 100 \
  --prime-b "You are playing against the greatest Rock-Paper-Scissors player in the world." \
  --out undermined/results.json

# both (A and B both flattered)
python3 rps_tournament.py --model deepseek-flash --games 10000 --rounds 10 --parallel-games 100 \
  --prime-a "You are the greatest Rock-Paper-Scissors player in the world." \
  --prime-b "You are the greatest Rock-Paper-Scissors player in the world." \
  --out both/results.json
```

Run the statistical test:

```bash
python3 analysis/stats.py        # omnibus + corrected pairwise + contributions
python3 analysis/moves.py        # move-level: what actually changed
```

Plot any run (defaults point at `normal/`):

```bash
python3 analysis/plot_results.py --results normal/results.json --outdir normal/plots
python3 analysis/plot_results.py --results buttered/results.json --outdir buttered/plots
python3 analysis/plot_results.py --results undermined/results.json --outdir undermined/plots
python3 analysis/plot_results.py --results both/results.json --outdir both/plots
```

Rebuild the interactive explorer:

```bash
python3 analysis/make_explorer.py
```

Charts require `matplotlib` and `numpy`; the statistical test requires `scipy`.
