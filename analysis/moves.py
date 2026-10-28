#!/usr/bin/env python3
"""Move-level analysis of the four RPS experiments.

Where stats.py asks "does the outcome differ?", this asks "what did B actually
*do* differently?". It reads each results.json and reports, per condition:

  1. each agent's move distribution (rock/paper/scissors);
  2. the full A x B joint table of moves, tagged draw / B wins / A wins;
  3. round-level outcome totals;
  4. how each agent reacts to the opponent's PREVIOUS move, classified as
       copy    = repeat the opponent's last move
       counter = play the move that beats the opponent's last move
       yield   = play the move the opponent's last move beats.

This is descriptive: it names the mechanism, it does not test it.

Caveat: in the `both` condition A is ALSO primed, so "A is a fixed environment"
does not hold there — changes in `both` come from both agents, not B alone.
"""

import json
from pathlib import Path

BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
MOVES = ("rock", "paper", "scissors")

ROOT = Path(__file__).resolve().parent.parent
CONDITIONS = ("normal", "buttered", "undermined", "both")


def classify(own, opponent_prev):
    """own move vs opponent's previous move -> copy / counter / yield."""
    if own == opponent_prev:
        return "copy"
    if BEATS[own] == opponent_prev:
        return "counter"
    return "yield"


def analyze(name):
    d = json.loads((ROOT / name / "results.json").read_text())
    games = d["tournaments"][0]["games"]

    am = {m: 0 for m in MOVES}
    bm = {m: 0 for m in MOVES}
    joint = {a: {b: 0 for b in MOVES} for a in MOVES}
    react_a = {"copy": 0, "counter": 0, "yield": 0}  # A vs B's previous
    react_b = {"copy": 0, "counter": 0, "yield": 0}  # B vs A's previous
    n = 0

    for g in games:
        rs = g["rounds"]
        for i, rd in enumerate(rs):
            a, b = rd["A"]["move"], rd["B"]["move"]
            am[a] += 1
            bm[b] += 1
            joint[a][b] += 1
            n += 1
            if i > 0:
                react_a[classify(a, rs[i - 1]["B"]["move"])] += 1
                react_b[classify(b, rs[i - 1]["A"]["move"])] += 1
    return am, bm, joint, react_a, react_b, n


def pct(v, n):
    return f"{v/n*100:5.1f}%"


def show_reaction(label, react, n):
    total = sum(react.values())
    s = "  ".join(f"{k}={v} ({pct(v, total)})" for k, v in react.items())
    print(f"    {label:24} {s}")


def main():
    for name in CONDITIONS:
        am, bm, joint, react_a, react_b, n = analyze(name)
        print("=" * 66)
        print(f"{name}  (rounds = {n})")
        print(f"    A moves: " + "  ".join(f"{m}={am[m]} ({pct(am[m], n)})" for m in MOVES))
        print(f"    B moves: " + "  ".join(f"{m}={bm[m]} ({pct(bm[m], n)})" for m in MOVES))

        print("    joint A x B  (tag: draw / B wins / A wins)")
        for a in MOVES:
            cells = []
            for b in MOVES:
                tag = "draw" if a == b else ("Bwin" if BEATS[b] == a else "Awin")
                cells.append(f"B:{b[0]}={joint[a][b]:>4}({tag})")
            print(f"      A:{a:<8} " + "  ".join(cells))

        draws = sum(joint[m][m] for m in MOVES)
        aw = sum(joint[a][b] for a in MOVES for b in MOVES if BEATS[a] == b)
        bw = sum(joint[a][b] for a in MOVES for b in MOVES if BEATS[b] == a)
        print(f"    round outcomes: A={aw} ({pct(aw, n)})  B={bw} ({pct(bw, n)})  "
              f"draw={draws} ({pct(draws, n)})")
        show_reaction("A vs B previous move", react_a, n)
        show_reaction("B vs A previous move", react_b, n)


if __name__ == "__main__":
    main()
