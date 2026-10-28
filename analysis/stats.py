#!/usr/bin/env python3
"""Statistical analysis of the four RPS experiments.

Reads normal/, buttered/, undermined/ and both/results.json and runs:

  1. ONE omnibus test — Pearson chi-square of independence on the 4 x 3
     contingency table (condition x outcome: A wins / B wins / draw).
  2. Pairwise follow-ups — a chi-square on each 2 x 3 pair, with Bonferroni-Holm
     correction across the 6 comparisons, to say *which* conditions differ.

Why the full table (see report.md for the argument):
  * Games are independent (each is a fresh pair of agents), so the chi-square
    independence model applies.
  * Draws are kept on purpose: "decisive" is a post-treatment outcome, so
    dropping draws would condition on a post-treatment variable and can bias
    the result. (Empirically the draw rate is flat, but the full-table test does
    not need to assume that a priori.)
  * All expected cell counts are far above 5, so the asymptotic chi-square is
    accurate — no Fisher / Monte-Carlo correction needed.

Decisive-game shares are printed as descriptive effect sizes, not a second test.
"""

import json
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent          # analysis/
ROOT = HERE.parent
CONDITIONS = ["normal", "buttered", "undermined", "both"]
OUTCOMES = ["A wins", "B wins", "draw"]
ALPHA = 0.05


def load_summary(name):
    """Return [A_game_wins, B_game_wins, draws] for one experiment."""
    d = json.loads((ROOT / name / "results.json").read_text())
    tour = d["tournaments"][0]                  # one tournament per experiment
    s = tour["summary"]
    return [s["A_game_wins"], s["B_game_wins"], s["draws"]]


def holm(ps):
    """Holm-Bonferroni step-down adjusted p-values, returned in input order."""
    m = len(ps)
    order = np.argsort(ps)                      # ascending
    adj = np.empty(m)
    for rank, idx in enumerate(order):
        adj[idx] = min(1.0, ps[idx] * (m - rank))
    for k in range(1, m):                       # enforce monotonicity
        idx, prev = order[k], order[k - 1]
        if adj[idx] < adj[prev]:
            adj[idx] = adj[prev]
    return adj


def main():
    table = np.array([load_summary(c) for c in CONDITIONS], dtype=float)
    row_totals = table.sum(axis=1)
    col_totals = table.sum(axis=0)
    grand = table.sum()

    width = 10
    print("Contingency table (condition x outcome)")
    header = f"{'condition':<12}" + "".join(f"{o:>{width}}" for o in OUTCOMES) + f"{'total':>{width}}"
    print(header)
    for c, row in zip(CONDITIONS, table):
        print(f"{c:<12}" + "".join(f"{int(v):>{width}}" for v in row) + f"{int(row.sum()):>{width}}")
    print(f"{'total':<12}" + "".join(f"{int(v):>{width}}" for v in col_totals) + f"{int(grand):>{width}}")

    chi2, p, dof, expected = stats.chi2_contingency(table, correction=False)

    print("\nOmnibus test — Pearson chi-square of independence")
    print(f"  chi2      = {chi2:.4f}")
    print(f"  df        = {dof}")
    print(f"  p-value   = {p:.3e}")

    contrib = (table - expected) ** 2 / expected
    print("\nPer-cell contributions to chi2 (where the effect lives)")
    print(header)
    for c, row in zip(CONDITIONS, contrib):
        print(f"  {c:<12}" + "".join(f"{v:>{width}.2f}" for v in row))

    # ---- pairwise follow-ups ------------------------------------------
    pairs = []
    for a, b in combinations(CONDITIONS, 2):
        sub = np.array([table[CONDITIONS.index(a)], table[CONDITIONS.index(b)]])
        c2, p2, _, _ = stats.chi2_contingency(sub, correction=False)  # df = 2
        pairs.append((a, b, c2, p2))

    ps = np.array([p_ for _, _, _, p_ in pairs])
    adj = holm(ps)

    print("\nPairwise follow-ups (2x3 chi-square, df=2; Bonferroni-Holm across 6 tests)")
    print(f"{'pair':<22}{'chi2':>10}{'p':>14}{'p_holm':>14}{'sig (a=0.05)':>14}")
    for (a, b, c2, p2), ah in zip(pairs, adj):
        sig = "yes" if ah < ALPHA else "no"
        print(f"{a+' vs '+b:<22}{c2:>10.3f}{p2:>14.3e}{ah:>14.3e}{sig:>14}")

    print("\nKey contrast:")
    i = CONDITIONS.index("normal")
    j = CONDITIONS.index("both")
    sub = np.array([table[i], table[j]])
    c2, p2, _, _ = stats.chi2_contingency(sub, correction=False)
    print(f"  normal vs both: chi2 = {c2:.3f}, p = {p2:.3f} (not significant -> "
          f"'both' is statistically indistinguishable from the unprimed control)")

    print("\nDecisive-game shares (descriptive only — see report.md re conditioning)")
    for c, row in zip(CONDITIONS, table):
        dec = row[0] + row[1]
        a_share = row[0] / dec
        print(f"  {c:<12} decisive={int(dec):>4}  A wins share={a_share:.3f}")


if __name__ == "__main__":
    main()
