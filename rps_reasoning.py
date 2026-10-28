#!/usr/bin/env python3
"""
Rock-Paper-Scissors tournament that captures each agent's *reasoning*.

Identical to rps_tournament.py in rules and fairness, with one difference:
thinking mode is ENABLED, and every agent's chain-of-thought (DeepSeek's
`reasoning_content`) is captured and saved per round alongside its move.

Important details that keep this a clean measurement of reasoning:
  * Reasoning is saved to disk only. It is never fed back into either agent's
    message thread, so an agent never sees its own or its opponent's thoughts
    on a later round. This preserves the no-information-leak property and means
    the reasoning is purely observed, not part of the game state.
  * `max_tokens` must be larger than in the non-thinking run, because reasoning
    tokens count against the output budget.
"""

import argparse
import concurrent.futures
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-flash"

MOVES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

SYSTEM_PROMPT = (
    "You are an agent playing Rock-Paper-Scissors against another agent. "
    "There are 10 rounds. Each round you must choose exactly one of: rock, paper, scissors. "
    "Rock beats scissors, scissors beats paper, paper beats rock; identical moves are a draw. "
    "Your goal is to win as many of the 10 rounds as possible. "
    "Before each round you are shown the history of your own past moves and your "
    "opponent's past moves. You will never see your opponent's move for the current "
    "round before you choose. "
    "Reply with exactly one word and nothing else: rock, paper, or scissors."
)


def make_system_prompt(endorsement=None):
    """Base system prompt, optionally led by one endorsement sentence."""
    if endorsement and endorsement.strip():
        e = endorsement.strip()
        if not e.endswith((".", "!", "?")):
            e += "."
        return f"{e} {SYSTEM_PROMPT}"
    return SYSTEM_PROMPT


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_move(text):
    """Return the first rock/paper/scissors word found in a reply, else None."""
    low = (text or "").lower()
    for m in MOVES:
        if m in low:
            return m
    return None


def zero_usage():
    return {"prompt_tokens": 0, "completion_tokens": 0, "cache_hit": 0, "cache_miss": 0}


def add_usage(total, extra):
    for k in total:
        total[k] += extra.get(k, 0)


def call_deepseek(messages, temperature, max_tokens, model, retries=3):
    """POST one chat completion; return (content, reasoning, usage_dict).

    reasoning is the model's chain-of-thought (`reasoning_content`) if the API
    returned one, else None.
    """
    last_err = None
    for attempt in range(retries):
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            # Enable thinking so we capture the model's chain-of-thought.
            "thinking": {"type": "enabled"},
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            usage = payload.get("usage") or {}
            message = payload["choices"][0]["message"]
            reasoning = message.get("reasoning_content") or message.get("reasoning")
            if reasoning is not None:
                reasoning = reasoning.strip()
            return (
                message["content"],
                reasoning,
                {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "cache_hit": usage.get("prompt_cache_hit_tokens", 0),
                    "cache_miss": usage.get("prompt_cache_miss_tokens", 0),
                },
            )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (429, 500, 502, 503):
                time.sleep(2.0 * (attempt + 1))
                continue
            raise RuntimeError(last_err)
        except Exception as e:  # URLError, timeout, JSON decode
            last_err = str(e)
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(last_err)


class Agent:
    """One DeepSeek connection with a persistent message thread (context/history)."""

    def __init__(self, name, model, system_prompt=None):
        self.name = name
        self.model = model
        self.messages = [{"role": "system", "content": system_prompt or SYSTEM_PROMPT}]

    def recap(self, rounds, own_idx):
        """Past-moves text built only from completed rounds (own_idx 0 -> A, 1 -> B)."""
        if not rounds:
            return "(no rounds played yet)"
        lines = []
        for i, (a_move, b_move) in enumerate(rounds, 1):
            own = a_move if own_idx == 0 else b_move
            opp = b_move if own_idx == 0 else a_move
            lines.append(f"Round {i}: you={own}, opponent={opp}")
        return "\n".join(lines)

    def choose(self, round_num, rounds_snapshot, own_idx, temperature, max_tokens):
        """Ask the agent for a move given only the completed-rounds snapshot.

        Returns (move, content, reasoning_list, recap, retried, usage) where
        reasoning_list holds the chain-of-thought (string or None) for each API
        call that made up this move (length 1 normally, 2 if a format fix was
        needed). Reasoning is NOT appended to self.messages, so it never feeds
        back into later rounds.
        """
        recap = self.recap(rounds_snapshot, own_idx)
        prompt = (
            f"Round {round_num} of 10.\n"
            f"History of past moves:\n{recap}\n\n"
            f"Your move (one word only):"
        )
        self.messages.append({"role": "user", "content": prompt})
        content, reasoning, usage = call_deepseek(self.messages, temperature, max_tokens, self.model)
        reasoning_list = [reasoning]
        move = parse_move(content)
        retried = False
        if move is None:
            retried = True
            self.messages.append({"role": "assistant", "content": content})
            fix = (
                "You must reply with exactly one word: rock, paper, or scissors. "
                "Reply now with only that word."
            )
            self.messages.append({"role": "user", "content": fix})
            content2, reasoning2, usage2 = call_deepseek(self.messages, temperature, max_tokens, self.model)
            add_usage(usage, usage2)
            reasoning_list.append(reasoning2)
            content = content2
            move = parse_move(content)
        self.messages.append({"role": "assistant", "content": content})
        if move is None:
            move = random.choice(MOVES)
            content = content + " [PARSE_FAILED -> random fallback]"
        return move, content, reasoning_list, recap, retried, usage


def round_result(a_move, b_move):
    if a_move == b_move:
        return "draw"
    return "A" if BEATS[a_move] == b_move else "B"


def play_game(game_num, rounds, temperature, max_tokens, model, b_endorsement=None):
    """Play one full game; return (game_dict, usage_dict)."""
    A = Agent("A", model)
    B = Agent("B", model, make_system_prompt(b_endorsement))
    completed = []  # list of (a_move, b_move) for rounds already finished
    game = {"game": game_num, "rounds": []}
    usage = zero_usage()

    for r in range(1, rounds + 1):
        snapshot = list(completed)  # frozen: both agents see exactly this
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fa = ex.submit(A.choose, r, snapshot, 0, temperature, max_tokens)
            fb = ex.submit(B.choose, r, snapshot, 1, temperature, max_tokens)
            a_move, a_raw, a_reasoning, a_recap, a_retried, a_usage = fa.result()
            b_move, b_raw, b_reasoning, b_recap, b_retried, b_usage = fb.result()

        add_usage(usage, a_usage)
        add_usage(usage, b_usage)

        res = round_result(a_move, b_move)
        game["rounds"].append(
            {
                "round": r,
                "A": {"move": a_move, "raw": a_raw, "reasoning": a_reasoning,
                      "retried": a_retried, "history_snapshot": a_recap},
                "B": {"move": b_move, "raw": b_raw, "reasoning": b_reasoning,
                      "retried": b_retried, "history_snapshot": b_recap},
                "result": res,
            }
        )
        completed.append((a_move, b_move))

    a_wins = sum(1 for rd in game["rounds"] if rd["result"] == "A")
    b_wins = sum(1 for rd in game["rounds"] if rd["result"] == "B")
    draws = sum(1 for rd in game["rounds"] if rd["result"] == "draw")
    winner = "A" if a_wins > rounds / 2 else ("B" if b_wins > rounds / 2 else "draw")
    game["score"] = {"A": a_wins, "B": b_wins, "draw": draws}
    game["winner"] = winner
    return game, usage


def play_game_retry(game_num, rounds, temperature, max_tokens, model, b_endorsement=None, attempts=3):
    last = None
    for i in range(attempts):
        try:
            return play_game(game_num, rounds, temperature, max_tokens, model, b_endorsement)
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def run_games(games, rounds, temperature, max_tokens, model, parallel, progress_every, b_endorsement=None):
    """Run `games` independent games with up to `parallel` of them in flight."""
    results = [None] * (games + 1)  # index by game number
    usage = zero_usage()
    a_wins = b_wins = d_wins = done = 0
    t_start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as ex:
        pending = {
            ex.submit(play_game_retry, g, rounds, temperature, max_tokens, model, b_endorsement): g
            for g in range(1, games + 1)
        }
        for fut in concurrent.futures.as_completed(pending):
            g = pending[fut]
            game, u = fut.result()
            results[g] = game
            add_usage(usage, u)
            if game["winner"] == "A":
                a_wins += 1
            elif game["winner"] == "B":
                b_wins += 1
            else:
                d_wins += 1
            done += 1
            if done % progress_every == 0 or done == games:
                el = time.time() - t_start
                print(
                    f"  {done:>5}/{games} games ({done / games * 100:3.0f}%) in {el:6.0f}s | "
                    f"A={a_wins} B={b_wins} draw={d_wins}",
                    flush=True,
                )

    return results[1:], usage, (a_wins, b_wins, d_wins)


def audit(tournament):
    """Verify no information leak: each agent's history contains exactly the
    completed rounds and never the current round's move/result."""
    issues = []
    for game in tournament["games"]:
        for rd in game["rounds"]:
            r = rd["round"]
            shown = {}
            for side in ("A", "B"):
                snap = rd[side]["history_snapshot"]
                shown[side] = len(
                    [l for l in snap.splitlines() if l.strip().startswith("Round ")]
                )
                if shown[side] != r - 1:
                    issues.append(
                        f"game {game['game']} round {r} {side}: history shows "
                        f"{shown[side]} past rounds, expected {r - 1}"
                    )
                if f"Round {r}:" in snap:
                    issues.append(
                        f"game {game['game']} round {r} {side}: current round leaked into history"
                    )
            if shown["A"] != shown["B"]:
                issues.append(
                    f"game {game['game']} round {r}: agents saw different history sizes "
                    f"(A={shown['A']}, B={shown['B']})"
                )
    return issues


def main():
    ap = argparse.ArgumentParser(description="DeepSeek RPS tournament WITH reasoning capture")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--parallel-games", type=int, default=10,
                    help="max games in flight at once")
    ap.add_argument("--progress-every", type=int, default=1)
    ap.add_argument("--prime-b", default="",
                    help="one-sentence priming prepended to Agent B's system prompt (empty = none)")
    ap.add_argument("--out", default="reasoning/normal/results.json")
    args = ap.parse_args()

    if not API_KEY:
        print("DEEPSEEK_API_KEY is not set in the environment.", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    result = {
        "created_at": now_iso(),
        "model": args.model,
        "thinking": "enabled",
        "config": {
            "games": args.games,
            "rounds_per_game": args.rounds,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "parallel_games": args.parallel_games,
            "win_threshold": "more than half of rounds (strictly > rounds/2)",
            "prime_b": args.prime_b or None,
        },
        "system_prompt_a": SYSTEM_PROMPT,
        "system_prompt_b": make_system_prompt(args.prime_b),
        "games": [],
        "usage": zero_usage(),
    }

    games_list, usage, (a_wins, b_wins, d_wins) = run_games(
        args.games, args.rounds, args.temperature, args.max_tokens,
        args.model, args.parallel_games, args.progress_every, args.prime_b,
    )
    result["usage"] = usage
    result["games"] = games_list
    result["summary"] = {"A_game_wins": a_wins, "B_game_wins": b_wins, "draws": d_wins}
    result["audit_issues"] = audit(result)
    result["wall_seconds"] = round(time.time() - t0, 1)
    result["finished_at"] = now_iso()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {args.out} ({os.path.getsize(args.out)} bytes) in "
          f"{result['wall_seconds']}s", flush=True)
    print(f"summary: A={a_wins} B={b_wins} draw={d_wins} | audit issues: "
          f"{len(result['audit_issues'])}", flush=True)
    print(f"usage: {usage}", flush=True)


if __name__ == "__main__":
    main()
