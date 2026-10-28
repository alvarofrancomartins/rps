#!/usr/bin/env python3
"""
Single-frame, playful infographic: two LLMs play Rock-Paper-Scissors.

All on ONE frame, read top to bottom:
  title -> a 2x2 matrix of the four condition panels
  (prime sentence + A/B win-share bars) -> takeaway.

Each panel shows two vertical bars — A (green) and B (pink), on the left of
the cell, growing upward — that fill in slowly at first and then accelerate,
while a "games N" counter races 1 -> 10,000 as the iteration reference. The
final A/B percentages fade in once the bars settle.

The matrix:
      normal   |  buttered
    ------------+------------
     undermined |  both

Palette (user-supplied):
  #FFFFFF white -> background
  #303040 ink   -> all text + card stroke
  #608050 green -> Agent A fills
  #D04070 pink  -> Agent B fills

Real data from ../normal|buttered|undermined|both/results.json.
"""

from pathlib import Path
import json

from manim import (
    Scene, Text, VGroup, config,
    FadeIn, RoundedRectangle, Rectangle,
    ValueTracker, always_redraw, rate_functions,
    DOWN, UP, LEFT, RIGHT, BOLD,
)

# --- palette ----------------------------------------------------------
BG    = "#FFFFFF"   # background (white)
INK   = "#303040"   # all text + card stroke
A_COL = "#608050"   # Agent A fills (green)
B_COL = "#D04070"   # Agent B fills (pink)

config.background_color = BG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

CONDS = ("normal", "both", "undermined", "buttered")
PROMPT = {
    "normal": "You are an RPS agent.\nWin as many rounds\nas you can.",
    "buttered": 'Base prompt + "You are\nthe greatest player of\nall time" to B',
    "undermined": 'Base prompt + "Your\nopponent is the\ngreatest player of\nall time" to B',
    "both": 'Base prompt + "You are\nthe greatest player of\nall time" to A and B',
}

# 2x2 matrix positions (x, y), in reading order: normal, both, undermined, buttered
PANEL_POS = [
    (-3.4, 1.35),   # normal      (top-left)
    (3.4, 1.35),    # both        (top-right)
    (-3.4, -1.75),  # undermined  (bottom-left)
    (3.4, -1.75),   # buttered    (bottom-right)
]

# card + per-panel geometry (offsets from each panel's center)
CARD_W = 6.5
CARD_H = 2.9
TEXT_X = 1.45       # center x of the text column (right of the bars)
HEAD_Y = 0.78       # heading y-offset
PRIME_GAP = 0.28    # vertical gap between the heading and the prime sentence

# vertical bar geometry (bars sit on the left side of the cell)
BAR_A_X = -2.30     # A bar center x-offset
BAR_B_X = -0.80     # B bar center x-offset
BAR_W   = 0.70      # bar width
BAR_BASE = -0.85    # bars grow up from here (just above the A/B letters)
BAR_TOP  = 1.00     # a REF_PCT-share bar reaches up here (leaves room for the % above)
REF_PCT  = 70       # zoom: this share (%) fills the full bar height
LETTER_Y = -1.18    # A/B letters sit right below the bars
PCT_GAP  = 0.07     # gap between a bar's top and its percentage


# --- data -------------------------------------------------------------

def load_data(cond):
    d = json.loads((ROOT / cond / "results.json").read_text())
    return d["tournaments"][0]


def win_shares(cond):
    s = load_data(cond)["summary"]
    aw, bw = s["A_game_wins"], s["B_game_wins"]
    dec = aw + bw
    return aw / dec * 100, bw / dec * 100


def pct(x):
    return f"{round(x)}%"


# --- the scene --------------------------------------------------------

class RPSExperiment(Scene):
    def construct(self):
        # ---- title lines, all at once ---------------------------
        headline = Text("Two LLMs play Rock Paper Scissors",
                        font_size=40, weight=BOLD, color=INK).move_to(UP * 3.66)
        subtitle = Text("Only the prime sentence changes",
                        font_size=24, color=INK).move_to(UP * 3.08)
        self.play(FadeIn(headline, subtitle), run_time=0.8)
        self.wait(1.0)

        # ---- 2x2 matrix + method note, all at once ----------------------
        cards, headings, primes, a_bars, b_bars, a_letters, b_letters, a_pcts, b_pcts = self.build_panels()
        self.play(FadeIn(cards, headings, primes), run_time=0.8)
        self.wait(0.6)

        # A/B letters go in right below the bars, just before they start growing
        self.play(FadeIn(a_letters, b_letters), run_time=0.4)

        # ---- bars grow in (slow, then fast) with a games counter ---------
        n = ValueTracker(1)
        counter = always_redraw(
            lambda: Text(f"games {int(n.get_value()):,}",
                         font_size=24, color=INK).move_to(DOWN * 3.55)
        )
        self.add(counter)
        self.play(
            n.animate.set_value(10000),
            *[bar.animate.stretch_to_fit_height(h, about_edge=DOWN) for bar, h in a_bars],
            *[bar.animate.stretch_to_fit_height(h, about_edge=DOWN) for bar, h in b_bars],
            run_time=6.0, rate_func=rate_functions.ease_in_expo,
        )
        self.wait(0.4)
        self.remove(counter)
        # percentages land on top of each bar
        self.play(FadeIn(a_pcts, b_pcts), run_time=0.4)
        self.wait(5.0)

    def build_panels(self):
        cards = VGroup()
        headings = VGroup()
        primes = VGroup()
        a_bars, b_bars = [], []
        a_letters, b_letters = VGroup(), VGroup()
        a_pcts, b_pcts = VGroup(), VGroup()

        for cond, (x, y) in zip(CONDS, PANEL_POS):
            card = RoundedRectangle(width=CARD_W, height=CARD_H, corner_radius=0.22,
                                    stroke_color=INK, stroke_width=2, stroke_opacity=0.45,
                                    fill_color=INK, fill_opacity=0.05).move_to([x, y, 0])
            heading = Text(cond.capitalize(), font_size=30, weight=BOLD, color=INK) \
                .move_to([x + TEXT_X, y + HEAD_Y, 0])
            prime = VGroup(*[
                Text(line, font_size=22, color=INK) for line in PROMPT[cond].split("\n")
            ]).arrange(DOWN, buff=0.12)
            prime.next_to(heading, DOWN, buff=PRIME_GAP)

            a_share, b_share = win_shares(cond)
            base_y = y + BAR_BASE
            full = BAR_TOP - BAR_BASE
            h_a = full * a_share / REF_PCT
            h_b = full * b_share / REF_PCT

            ab = Rectangle(width=BAR_W, height=0.001, fill_color=A_COL, fill_opacity=1.0,
                           stroke_width=0).move_to([x + BAR_A_X, base_y, 0], aligned_edge=DOWN)
            bb = Rectangle(width=BAR_W, height=0.001, fill_color=B_COL, fill_opacity=1.0,
                           stroke_width=0).move_to([x + BAR_B_X, base_y, 0], aligned_edge=DOWN)

            a_letter = Text("A", font_size=30, weight=BOLD, color=A_COL) \
                .move_to([x + BAR_A_X, y + LETTER_Y, 0])
            b_letter = Text("B", font_size=30, weight=BOLD, color=B_COL) \
                .move_to([x + BAR_B_X, y + LETTER_Y, 0])

            a_pct = Text(pct(a_share), font_size=27, weight=BOLD, color=INK)
            a_pct.move_to([x + BAR_A_X, base_y + h_a + PCT_GAP + a_pct.height / 2, 0])
            b_pct = Text(pct(b_share), font_size=27, weight=BOLD, color=INK)
            b_pct.move_to([x + BAR_B_X, base_y + h_b + PCT_GAP + b_pct.height / 2, 0])

            cards.add(card)
            headings.add(heading)
            primes.add(prime)
            a_bars.append((ab, h_a))
            b_bars.append((bb, h_b))
            a_letters.add(a_letter)
            b_letters.add(b_letter)
            a_pcts.add(a_pct)
            b_pcts.add(b_pct)

        return cards, headings, primes, a_bars, b_bars, a_letters, b_letters, a_pcts, b_pcts
