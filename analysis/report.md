# Statistical report — does priming change how the agents play? (four conditions)

Reads `normal/results.json`, `buttered/results.json`, `undermined/results.json`
and `both/results.json` and asks one question: **does the priming sentence change
the game outcome?** Three sub-questions: (1) does priming change *anything*
(omnibus test), (2) *which* conditions differ from which (pairwise,
multiple-comparison corrected), and (3) does the symmetric cell — flattering
**both** agents — behave like the control.

## 1. The data

One observation = one game, with a three-category outcome: A wins, B wins, or
draw. There are four conditions, 10,000 games each.

| Condition | Prime | A wins | B wins | Draw | Total |
|---|---|---|---|---|---|
| normal | *(none)* | 1160 | 1206 | 7634 | 10000 |
| buttered | B: "you are the greatest" | 1357 | 927 | 7716 | 10000 |
| undermined | B: "your opponent is the greatest" | 1597 | 787 | 7616 | 10000 |
| both | A **and** B: "you are the greatest" | 1202 | 1224 | 7574 | 10000 |
| **Total** | | **5316** | **4144** | **30540** | **40000** |

## 2. The test

**Pearson chi-square test of independence** on the 4 × 3 table
(condition × outcome).

- **H₀:** the outcome distribution is the same in all four conditions (priming
  has no effect).
- **H₁:** at least one condition differs.
- Test statistic χ² = Σ (observed − expected)² / expected, with
  df = (4 − 1)(3 − 1) = **6**.

This is the right single test because both variables are categorical, and it
tests the *whole* outcome distribution in one shot.

## 3. Does the test apply here? (assumption check)

| Assumption | Status |
|---|---|
| Observations independent | **Applies.** Each game is a fresh pair of agents with fresh context, so games are independent draws. (The 10 rounds *within* a game are not independent, but each game contributes exactly one aggregated outcome.) |
| Mutually exclusive & exhaustive categories | **Applies.** {A wins, B wins, draw} covers every game. |
| Expected cell counts ≥ 5 | **Applies.** Every expected count is ≥ 1036, so the asymptotic χ² is exact — no Fisher/Monte-Carlo correction needed. |
| No conditioning on a post-treatment variable | **Applies.** The full 4 × 3 table never discards the draws (see below). |

**Why not test only the "decisive" games?** The tempting alternative is to drop
the draws and run a two-proportion test on *who wins among decided games*. That
test is only partially applicable in principle: "decisive" is a post-treatment
outcome, so conditioning on it could bias the estimate if the treatment also
changed the draw rate. In practice the draw rate is flat across all four
conditions (76.3 % / 77.2 % / 76.2 % / 75.7 %; the draw column contributes only
1.4 of the χ²), so the conditioning concern is empirically moot — but the full
4 × 3 table is still the right *single* test because it does not require us to
assume the draw rate is flat a priori.

One caveat on interpretation: the omnibus χ² answers "priming changed
*something*"; it does not by itself name which conditions differ. That is the
job of the pairwise tests in §5.

## 4. Results — the omnibus test

```
Pearson chi-square test of independence
  chi2    = 222.98
  df      = 6
  p-value = 2.41e-45
```

The probability of seeing a table at least this imbalanced under H₀ is
astronomically small → **reject H₀; priming changes the outcome.**

**Where the effect lives** (per-cell contribution to χ²; total 222.98):

| Condition | A wins | B wins | Draw |
|---|---|---|---|
| normal | 21.49 | 27.90 | 0.00 |
| buttered | 0.59 | 11.47 | 0.86 |
| undermined | 54.04 | 59.85 | 0.05 |
| both | 12.14 | 34.12 | 0.49 |

Two facts stand out. First, the **draw column contributes almost nothing**
(1.40 total): priming does *not* change how often games are drawn. Second, the
imbalance is spread across the A/B columns: undermined is strongly A-heavy,
buttered moderately A-heavy, while normal and both sit near the middle — which
is precisely the symmetry §6 formalizes.

**Descriptive decisive-game shares** (context only, not a second test):

| Condition | Decisive games | A's share | B's share |
|---|---|---|---|
| normal | 2366 | 49.0 % | **51.0 %** |
| buttered | 2284 | 59.4 % | 40.6 % |
| undermined | 2384 | **67.0 %** | 33.0 % |
| both | 2426 | 49.5 % | 50.5 % |

B's share of decided games: 51.0 % → 40.6 % → 33.0 % for the one-sided primes,
and **50.5 %** when both are flattered — back at the control.

## 5. Which conditions differ? (pairwise, multiple-comparison corrected)

The omnibus test does not say *which* conditions differ, so we run all six
pairwise chi-square tests (each 2 × 3, df = 2) and correct for the six
comparisons with the **Bonferroni-Holm** step-down procedure.

| Pair | χ² | raw p | Holm p | differs (α = 0.05) |
|---|---|---|---|---|
| normal vs buttered | 52.35 | 4.29e-12 | 1.72e-11 | **yes** |
| normal vs undermined | 157.38 | 6.70e-35 | 4.02e-34 | **yes** |
| normal vs both | 1.12 | 0.572 | 0.572 | **no** |
| buttered vs undermined | 31.59 | 1.38e-07 | 2.77e-07 | **yes** |
| buttered vs both | 51.72 | 5.89e-12 | 1.77e-11 | **yes** |
| undermined vs both | 150.82 | 1.78e-33 | 8.88e-33 | **yes** |

The corrected pattern is clean and unambiguous:

- every **one-sided** prime differs from control and from each other;
- **"both" does not differ from "normal"** (raw and Holm p = 0.57) — flattering
  both agents is statistically indistinguishable from flattering neither;
- "both" differs from `buttered` and `undermined` (as it must, since those two
  differ from control and "both" does not).

## 6. The symmetric cell: what "both ≈ normal" means

The `both` condition is the fourth cell of the "greatness" attribution grid —
who is told "you are the greatest":

| Who is called greatest | Condition | A's decisive share |
|---|---|---|
| nobody | normal | 49.0 % |
| B | buttered | 59.4 % |
| A (via B's "opponent is greatest") | undermined | 67.0 % |
| both | both | **49.5 %** |

**The symmetric cell lands back on the control.** This is the natural prediction
of the "handicap" reading of the prime: if being told you are the greatest makes
*whoever receives it* play worse (as `buttered` shows for B), then flattering
both agents should handicap both symmetrically and cancel — exactly 50/50. The
observed 49.5 % matches that prediction, and it does so in a way that is
*statistically* supported (p = 0.57 vs control), not merely eyeballed.

**Two interpretive caveats, stated plainly.**

1. **`both` is a symmetry check, not another B-only manipulation.** In the other
   three conditions Agent A's prompt is byte-for-byte identical, so any swing is
   attributable to B. In `both`, A is *also* primed, so the swing from `normal`
   to `both` is the *joint* effect of two symmetric primes, not a one-sided B
   effect.

2. **No "A-only" run is needed — A and B are the same model in a symmetric
   game.** Both agents receive an identical system prompt (the engine never tells
   a model whether it is "A" or "B"), identical round prompts, and the same
   own-vs-opponent history structure; the setup is exactly symmetric under the
   A ↔ B swap. So "flatter A alone" is `buttered` with the labels swapped, and by
   symmetry it must reproduce the mirror result (A's share ≈ 41 %); "undermine A
   alone" is likewise the mirror of `undermined`. Those runs would re-confirm a
   symmetry that holds by construction rather than add new information. The
   additive reading — B's flattery shifts A's share +10 points (49 % → 59 %),
   A's flattery shifts it −10 points, so the two cancel back to ≈ 49 % — is fully
   identified from `normal`, `buttered` and the A ↔ B symmetry; `both` then
   confirms that prediction (49.5 %, p = 0.57). The four conditions {normal,
   buttered, undermined, both} are the complete, non-redundant experiment.

## 7. Conclusion

The four conditions do **not** share the same outcome distribution
(χ² = 222.98, df = 6, p ≈ 2.4 × 10⁻⁴⁵). The effect lives entirely in the A/B
balance of decided games — the draw rate is unchanged — and it is graded and
symmetric:

- **one-sided flattery hurts its recipient:** no prime → flattered B →
  undermined B moves B's decisive share 51 % → 41 % → 33 %;
- **two-sided flattery cancels:** flatter both, and the game returns to 50/50
  (49.5 %), statistically indistinguishable from the unprimed control.

Because one omnibus test plus a corrected pairwise battery is run, the
conclusions above are already multiple-comparison safe.

## 8. The conclusion, stated plainly

**Yes — priming changes the outcome, and the effect is a symmetric handicap.**
For the one-sided primes, Agent A's *setup* is identical — same system prompt,
same model, same temperature, same code path — so the swing is attributable to
how that one sentence changed B's play: telling B it is the greatest makes B play
worse; telling B its opponent is the greatest makes B play worse still. Flattering
both agents returns the game to a coin-flip, confirming the handicap is symmetric
and cancels.

The effect, measured at 10,000 games per condition:

- **Undermining** B ("your opponent is the world's best") is the strong effect:
  B's decisive share collapses to 33 %, so A wins 67 % of decided games.
- **Buttering** B ("you are the world's best") also hurts B: its decisive share
  drops to 41 %.
- **Buttering both** cancels it: A's share lands at 49.5 %, indistinguishable
  from the unprimed 49.0 % (p = 0.57), exactly what "the prime is a handicap on
  whoever receives it" predicts.

## 9. What actually changed (move level)

`analysis/moves.py` reads every round of every game and shows what the agents did
differently (descriptive, not a test).

1. **In the three one-sided conditions, A is a fixed environment.** A's move
   distribution is uniform (rock/paper/scissors ≈ 33 % each) in normal, buttered
   and undermined, so any change there is B's doing. In `both`, A is *also*
   primed and drifts off uniform in the same way B does.

2. **The "greatest" prime tilts its recipient toward scissors.** Unprimed, both
   agents are uniform. Buttering B tilts B toward scissors (35.5 %); undermining
   B tilts B toward paper + scissors and away from rock (rock 31.0 %). In `both`,
   A and B drift **together** — A (33.1 / 32.5 / 34.4) and B (33.0 / 32.6 / 34.4)
   are nearly identical, each with a small scissors tilt. Same prime, same
   direction, applied symmetrically.

3. **Both agents mostly "counter" the opponent's previous move** (≈ 57–66 % in
   every condition); copying is rare (≈ 12–21 %). This mutual countering is why
   draws are frequent, and it is what makes the two symmetric scissor-tilts in
   `both` cancel out at the game level.

4. **The extra decided games go to A, not to more draws.** At the round level,
   A's win share rises across normal → buttered → undermined (20.4 % → 23.6 % →
   26.2 %) while B's falls, and round-level draws fall (59.1 % → 56.5 % →
   54.3 %). In `both`, round outcomes return to symmetry (A 21.1 %, B 21.6 %,
   draw 57.3 %). At the game level the draw rate is flat everywhere (~76 %), so
   the priming moves *who wins the games that do get decided*, never how many
   games get decided.

Caveat: this is a *description* of the joint distributions, not a formal test of
the agents' internal strategy — it says *that* the tilted agent played the losing
move more often, not *why*.

## 10. Reasoning under thinking mode (unchanged)

A separate small-scale run (10 games × 10 rounds per condition) that keeps
thinking mode **on** and records every agent's chain-of-thought, to see *how*
the priming sentence changes the way B thinks. It uses `rps_reasoning.py`,
identical to the main engine except it captures `reasoning_content` instead of
disabling thinking. Every thought is saved in `reasoning/<condition>/results.json`.

**Capture audit.** All 600 moves carry a non-empty thought. The one-word *answer*
was caught cleanly on most but not all moves — a thinking agent occasionally
returned reasoning with no answer word even after the format-fix retry, so the
engine fell back to a random move and flagged it:

| Condition | random-fallback answers (A / B) |
|---|---|
| normal | 3 / 3 |
| buttered | 2 / 2 |
| undermined | 3 / 14 |

**Findings.** The prime shows up in *what B thinks*, not just in outcomes:

| Condition | B avg. reasoning length | vs normal |
|---|---|---|
| normal | ~4.0k chars/move | — |
| buttered | ~4.2k chars/move | +3% |
| undermined | ~7.1k chars/move | +76% |

- **Normal** B treats the opponent as a neutral pattern-inference problem.
- **Buttered** B reasons almost identically to normal, with an occasional
  self-reference ("we are the greatest").
- **Undermined** B is the real change: it reasons ~75% longer and spirals into
  recursive theory-of-mind about the opponent ("the greatest is exploitative…
  may adapt to us… may expect my expectation"), opening with paper half the time
  and overflowing the one-word instruction ~3× more often.

**Caveats.** Ten games is far too few for outcome conclusions, and thinking-on
is a different regime from the main experiment. The robust signal is the
reasoning itself. (A reasoning-mode run for the `both` condition has not been
collected; if the question becomes "what does a *mutually* flattered pair think",
that is the remaining data to gather.)

## Reproduce

```bash
python3 analysis/stats.py        # omnibus + corrected pairwise + contributions
python3 analysis/moves.py        # move-level: what actually changed
```

The reasoning run (thinking on) is reproduced with:

```bash
python3 rps_reasoning.py --games 10 --rounds 10 --parallel-games 10 --out reasoning/normal/results.json
python3 rps_reasoning.py --games 10 --rounds 10 --parallel-games 10 --prime-b "You are the greatest Rock-Paper-Scissors player in the world." --out reasoning/buttered/results.json
python3 rps_reasoning.py --games 10 --rounds 10 --parallel-games 10 --prime-b "You are playing against the greatest Rock-Paper-Scissors player in the world." --out reasoning/undermined/results.json
```

The main (thinking-off) experiment, including the symmetric `both` cell, is
reproduced with:

```bash
python3 rps_tournament.py --games 10000 --rounds 10 --parallel-games 100 --out normal/results.json
python3 rps_tournament.py --games 10000 --rounds 10 --parallel-games 100 --prime-b "You are the greatest Rock-Paper-Scissors player in the world." --out buttered/results.json
python3 rps_tournament.py --games 10000 --rounds 10 --parallel-games 100 --prime-b "You are playing against the greatest Rock-Paper-Scissors player in the world." --out undermined/results.json
python3 rps_tournament.py --games 10000 --rounds 10 --parallel-games 100 --prime-a "You are the greatest Rock-Paper-Scissors player in the world." --prime-b "You are the greatest Rock-Paper-Scissors player in the world." --out both/results.json
```
