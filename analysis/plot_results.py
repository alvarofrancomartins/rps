#!/usr/bin/env python3
"""Plot Rock-Paper-Scissors tournament results.

Reads a results JSON (produced by ../rps_tournament.py) and writes PNG charts
into the experiment's plots/ folder. Works for any number of games/tournaments.

Color follows the validated default palette (dataviz skill, light mode), with a
fixed identity convention used across every chart:
    Agent A -> blue   (#2a78d6, categorical slot 1)
    Agent B -> orange (#eb6834, categorical slot 2)
    draws / neutral -> gray (#898781, muted ink - not a data hue)
    game margin uses a diverging blue <-> red ramp with a gray midpoint.
"""

import argparse
import collections
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --- palette (light mode, from the dataviz reference palette) ---
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_SEC = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"    # Agent A
ORANGE = "#eb6834"  # Agent B
RED = "#e34948"     # diverging pole (B-led)
GRAY = "#898781"    # neutral / draws

MOVES = ("rock", "paper", "scissors")

HERE = Path(__file__).resolve().parent          # analysis/
OUTDIR = HERE.parent / "normal" / "plots"       # normal/plots
DEFAULT_RESULTS = HERE.parent / "normal" / "results.json"  # normal/results.json


def apply_style(ax, grid_axis="y"):
    ax.set_facecolor(SURFACE)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, length=0, labelsize=9)
    ax.set_axisbelow(True)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=1.0, zorder=0)
    else:
        ax.grid(False)


def set_title(ax, text):
    ax.set_title(text, loc="left", fontsize=13, fontweight="bold", color=INK, pad=12)


def derive(data):
    a_wins = b_wins = draws = 0
    a_game = b_game = d_game = 0
    games = []
    a_moves = {m: 0 for m in MOVES}
    b_moves = {m: 0 for m in MOVES}
    cum_a, cum_b = [], []
    ca = cb = 0
    for tour in data["tournaments"]:
        for g in tour["games"]:
            ga, gb, gd = g["score"]["A"], g["score"]["B"], g["score"]["draw"]
            games.append({"margin": ga - gb, "winner": g["winner"]})
            a_wins += ga
            b_wins += gb
            draws += gd
            if g["winner"] == "A":
                a_game += 1
            elif g["winner"] == "B":
                b_game += 1
            else:
                d_game += 1
            for rd in g["rounds"]:
                a_moves[rd["A"]["move"]] += 1
                b_moves[rd["B"]["move"]] += 1
                if rd["result"] == "A":
                    ca += 1
                elif rd["result"] == "B":
                    cb += 1
                cum_a.append(ca)
                cum_b.append(cb)
    return {
        "a_rounds": a_wins, "b_rounds": b_wins, "draws": draws,
        "a_games": a_game, "b_games": b_game, "d_games": d_game,
        "games": games,
        "a_moves": a_moves, "b_moves": b_moves,
        "cum_a": cum_a, "cum_b": cum_b,
        "n_rounds": len(cum_a),
    }


def horizontal_bars(ax, cats, vals, cols):
    """Horizontal bars, ascending top-to-bottom, value at the tip."""
    order = np.argsort(vals)
    labels = [cats[i] for i in order]
    values = [vals[i] for i in order]
    colors = [cols[i] for i in order]
    ypos = np.arange(len(values))[::-1]
    for yp, val, col in zip(ypos, values, colors):
        ax.barh(yp, val, height=0.52, color=col, zorder=3)
        ax.text(val + max(values) * 0.015, yp, f"{val:,}",
                va="center", ha="left", fontsize=11, fontweight="bold", color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=10, color=INK)
    ax.set_xlim(0, max(values) * 1.14)
    ax.xaxis.set_visible(False)


def chart_game_outcomes(d):
    fig, ax = plt.subplots(figsize=(7, 2.8))
    apply_style(ax, grid_axis=None)
    horizontal_bars(ax, ["Draws", "A wins", "B wins"],
                    [d["d_games"], d["a_games"], d["b_games"]],
                    [GRAY, BLUE, ORANGE])
    set_title(ax, "Game outcomes")
    fig.savefig(OUTDIR / "game_outcomes.png", dpi=200, bbox_inches="tight",
                facecolor=PAGE)
    plt.close(fig)


def chart_round_outcomes(d):
    fig, ax = plt.subplots(figsize=(7, 2.8))
    apply_style(ax, grid_axis=None)
    horizontal_bars(ax, ["Draws", "A wins", "B wins"],
                    [d["draws"], d["a_rounds"], d["b_rounds"]],
                    [GRAY, BLUE, ORANGE])
    set_title(ax, "Round outcomes")
    fig.savefig(OUTDIR / "round_outcomes.png", dpi=200, bbox_inches="tight",
                facecolor=PAGE)
    plt.close(fig)


def chart_game_margins(d):
    hist = collections.Counter(g["margin"] for g in d["games"])
    margins = sorted(hist)
    counts = [hist[m] for m in margins]
    colors = [RED if m < 0 else (GRAY if m == 0 else BLUE) for m in margins]

    fig, ax = plt.subplots(figsize=(9, 3.6))
    apply_style(ax, grid_axis="y")
    bars = ax.bar(margins, counts, width=0.72, color=colors, zorder=3)
    # direct-label only the neutral (0) bar - the story is "most games are even"
    if 0 in hist:
        ax.text(0, hist[0] + 8, f"{hist[0]:,}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=INK)
    ax.set_xticks([-10, -5, 0, 5, 10])
    ax.set_xticklabels(["-10", "-5", "0", "+5", "+10"])
    ax.set_xlabel("A round-wins − B round-wins  (negative = B-led)", color=INK_SEC)
    ax.set_ylabel("games", color=INK_SEC)
    ax.set_ylim(0, max(counts) * 1.12)
    set_title(ax, "Game margin distribution")
    fig.savefig(OUTDIR / "game_margins.png", dpi=200, bbox_inches="tight",
                facecolor=PAGE)
    plt.close(fig)


def chart_move_distribution(d):
    a_counts = [d["a_moves"][m] for m in MOVES]
    b_counts = [d["b_moves"][m] for m in MOVES]

    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    apply_style(ax, grid_axis="y")
    x = np.arange(len(MOVES))
    w = 0.36
    ax.bar(x - w / 2, a_counts, w, color=BLUE, label="Agent A",
           edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.bar(x + w / 2, b_counts, w, color=ORANGE, label="Agent B",
           edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(MOVES, color=INK)
    ax.set_ylabel("moves", color=INK_SEC)
    ax.set_ylim(0, max(a_counts + b_counts) * 1.25)
    ax.legend(frameon=False, loc="upper right", fontsize=9,
              labelcolor=INK, borderaxespad=0)
    set_title(ax, "Move distribution")
    fig.savefig(OUTDIR / "move_distribution.png", dpi=200, bbox_inches="tight",
                facecolor=PAGE)
    plt.close(fig)


def compact(v):
    return f"{v/1000:g}K" if v >= 1000 else f"{v:g}"


def chart_cumulative(d):
    rounds = np.arange(1, d["n_rounds"] + 1)
    fig, ax = plt.subplots(figsize=(8, 4.0))
    apply_style(ax, grid_axis="both")
    ax.plot(rounds, d["cum_a"], color=BLUE, linewidth=2,
            solid_capstyle="round", solid_joinstyle="round", label="Agent A", zorder=3)
    ax.plot(rounds, d["cum_b"], color=ORANGE, linewidth=2,
            solid_capstyle="round", solid_joinstyle="round", label="Agent B", zorder=3)

    # end markers with a 2px surface ring; end values nudge apart to avoid collision
    end = d["n_rounds"]
    ax.scatter([end], [d["cum_a"][-1]], s=64, color=BLUE, edgecolors=SURFACE,
               linewidth=1.5, zorder=5)
    ax.scatter([end], [d["cum_b"][-1]], s=64, color=ORANGE, edgecolors=SURFACE,
               linewidth=1.5, zorder=5)
    if d["cum_a"][-1] >= d["cum_b"][-1]:
        ax.text(end, d["cum_a"][-1], f"{d['cum_a'][-1]:,}", va="bottom", ha="left",
                fontsize=10, fontweight="bold", color=INK)
        ax.text(end, d["cum_b"][-1], f"{d['cum_b'][-1]:,}", va="top", ha="left",
                fontsize=10, fontweight="bold", color=INK)
    else:
        ax.text(end, d["cum_b"][-1], f"{d['cum_b'][-1]:,}", va="bottom", ha="left",
                fontsize=10, fontweight="bold", color=INK)
        ax.text(end, d["cum_a"][-1], f"{d['cum_a'][-1]:,}", va="top", ha="left",
                fontsize=10, fontweight="bold", color=INK)

    xt = np.linspace(0, end, 6)
    ax.set_xticks(xt)
    ax.set_xticklabels([compact(v) for v in xt])
    ax.set_xlim(0, end * 1.08)
    ax.set_ylim(0, max(d["cum_a"][-1], d["cum_b"][-1]) * 1.22)
    ax.set_xlabel("round", color=INK_SEC)
    ax.set_ylabel("cumulative round wins", color=INK_SEC)
    ax.legend(frameon=False, loc="upper left", fontsize=9,
              labelcolor=INK, borderaxespad=0)
    set_title(ax, "Cumulative round wins")
    fig.savefig(OUTDIR / "cumulative_score.png", dpi=200, bbox_inches="tight",
                facecolor=PAGE)
    plt.close(fig)


def main():
    global OUTDIR
    ap = argparse.ArgumentParser(description="Plot RPS tournament results")
    ap.add_argument("--results", default=str(DEFAULT_RESULTS),
                    help="path to results JSON")
    ap.add_argument("--outdir", default=str(OUTDIR),
                    help="directory to write PNGs into")
    args = ap.parse_args()

    OUTDIR = Path(args.outdir)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    outdir = OUTDIR

    d = derive(json.loads(Path(args.results).read_text()))
    print(f"games: A {d['a_games']}  B {d['b_games']}  draws {d['d_games']}")
    print(f"rounds: A {d['a_rounds']}  B {d['b_rounds']}  draws {d['draws']}")

    chart_game_outcomes(d)
    chart_round_outcomes(d)
    chart_game_margins(d)
    chart_move_distribution(d)
    chart_cumulative(d)

    for p in sorted(outdir.glob("*.png")):
        print("wrote", p)


if __name__ == "__main__":
    main()
