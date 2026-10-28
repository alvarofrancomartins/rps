#!/usr/bin/env python3
"""Generate the interactive move-by-move explorer from the real results.

Reads normal/, buttered/ and undermined/results.json, extracts a compact
per-game encoding (A moves, B moves, round results, game winner) and writes a
self-contained HTML explorer to game_explorer.html.

No synthetic data: every cell is a real round from the experiment. Shows one
game at a time so each round is legible.

Run:  python3 analysis/make_explorer.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "game_explorer.html"
CONDITIONS = ("normal", "buttered", "undermined", "both")

MOVE_IDX = {"rock": "0", "paper": "1", "scissors": "2"}
RES_IDX = {"A": "0", "B": "1", "draw": "2"}
WIN_CHAR = {"A": "A", "B": "B", "draw": "D"}


def build():
    out = {}
    for name in CONDITIONS:
        d = json.loads((ROOT / name / "results.json").read_text())
        games = d["tournaments"][0]["games"]
        a, b, r, g = [], [], [], []
        for game in games:
            rounds = game["rounds"]
            assert len(rounds) == 10, (name, game["game"], len(rounds))
            a.append("".join(MOVE_IDX[rd["A"]["move"]] for rd in rounds))
            b.append("".join(MOVE_IDX[rd["B"]["move"]] for rd in rounds))
            r.append("".join(RES_IDX[rd["result"]] for rd in rounds))
            g.append(WIN_CHAR[game["winner"]])
        out[name] = {"A": a, "B": b, "R": r, "G": g}
    return out


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>RPS Move Explorer</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap">
<style>
  /* Layout: one left-aligned instrument column; the single data encoding is the move */
  :root{
    --bg:#f9f9f7;
    --surface:#fcfcfb;
    --panel:#f0efeb;
    --ink:#0b0b0b;
    --ink-sec:#52514e;
    --ink-muted:#898781;
    --grid:#e1e0d9;
    --ring:#0b0b0b;
    --move-rock:#0072B2;
    --move-paper:#E69F00;
    --move-scissors:#CC79A7;
    --chip:#f0efeb;
    --chip-border:#dedcd3;
    --focus:#2a78d6;
    color-scheme:light;
  }
  @media (prefers-color-scheme:dark){
    :root:not([data-theme="light"]){
      --bg:#131312;
      --surface:#1a1917;
      --panel:#24231f;
      --ink:#ece9e1;
      --ink-sec:#b5b1a6;
      --ink-muted:#83806f;
      --grid:#2c2b27;
      --ring:#f3f0e8;
      --move-rock:#56B4E9;
      --move-paper:#F0B429;
      --move-scissors:#DE8AB8;
      --chip:#24231f;
      --chip-border:#38362f;
      --focus:#6fb0f5;
      color-scheme:dark;
    }
  }
  :root[data-theme="dark"]{
    --bg:#131312;
    --surface:#1a1917;
    --panel:#24231f;
    --ink:#ece9e1;
    --ink-sec:#b5b1a6;
    --ink-muted:#83806f;
    --grid:#2c2b27;
    --ring:#f3f0e8;
    --move-rock:#56B4E9;
    --move-paper:#F0B429;
    --move-scissors:#DE8AB8;
    --chip:#24231f;
    --chip-border:#38362f;
    --focus:#6fb0f5;
    color-scheme:dark;
  }

  [hidden]{display:none !important}
  body{
    margin:0;
    background:var(--bg);
    color:var(--ink);
    font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
    font-size:15px;
    line-height:1.5;
    padding-left:max(16px,env(safe-area-inset-left,0px));
    padding-right:max(16px,env(safe-area-inset-right,0px));
  }
  .wrap{max-width:760px;margin:0 auto;min-width:0}
  code,.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}

  :focus-visible{outline:2px solid var(--focus);outline-offset:2px}
  @media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}

  header.wrap{padding-block:36px 6px}
  .eyebrow{
    font-family:"IBM Plex Mono",ui-monospace,monospace;
    font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-muted);
  }
  h1{
    font-weight:700;font-size:30px;line-height:1.1;letter-spacing:-.01em;
    margin:10px 0 0;text-wrap:balance;
  }
  .lede{margin:12px 0 0;color:var(--ink-sec);max-width:62ch}

  #summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding-block:22px 2px}
  @media (max-width:680px){#summary{grid-template-columns:1fr}}
  .tile{background:var(--surface);border:1px solid var(--grid);border-radius:10px;padding:14px 16px;min-width:0}
  .tile-label{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--ink-muted);
  }
  .tile-big{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-weight:600;font-size:30px;
    font-variant-numeric:tabular-nums;line-height:1;margin-top:8px;
  }
  .tile-cap{font-size:12px;color:var(--ink-sec);margin-top:4px}
  .tile-bar{height:6px;background:var(--grid);border-radius:3px;margin-top:12px;overflow:hidden}
  .tile-fill{display:block;height:100%;background:var(--ink-sec);border-radius:3px}
  .tile-counts{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
    color:var(--ink-sec);margin-top:10px;font-variant-numeric:tabular-nums;
  }

  #controls{padding-block:22px 4px}
  .chip-row{display:flex;gap:8px;flex-wrap:wrap}
  .chip{
    font:500 13px "IBM Plex Sans",system-ui,sans-serif;color:var(--ink-sec);
    background:var(--chip);border:1px solid var(--chip-border);
    border-radius:999px;padding:7px 15px;cursor:pointer;
  }
  .chip:hover{border-color:var(--ink-muted)}
  .chip.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
  #slider{width:100%;margin-top:18px;accent-color:var(--focus)}
  .nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
  .btn{
    font:500 13px "IBM Plex Sans",system-ui,sans-serif;color:var(--ink);
    background:var(--surface);border:1px solid var(--chip-border);
    border-radius:8px;padding:8px 14px;cursor:pointer;
  }
  .btn:hover{border-color:var(--ink-muted)}
  #play{min-width:96px}
  #play.active{background:var(--ink);color:var(--bg);border-color:var(--ink)}

  .readout{
    display:flex;align-items:center;gap:14px;flex-wrap:wrap;
    padding-block:20px 12px;
  }
  .readout-cond{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
    letter-spacing:.12em;text-transform:uppercase;color:var(--ink-muted);
  }
  .readout-game{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:15px;
    color:var(--ink);font-variant-numeric:tabular-nums;
  }
  .readout-result{
    font:600 13px "IBM Plex Sans",system-ui,sans-serif;color:var(--ink);
    background:var(--panel);border-radius:999px;padding:3px 12px;
  }
  .readout-score{
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:14px;
    color:var(--ink-sec);font-variant-numeric:tabular-nums;
  }

  #legend{display:flex;gap:18px;flex-wrap:wrap;padding-block:14px 10px;align-items:center}
  .legend-item{
    display:flex;align-items:center;gap:6px;
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:var(--ink-sec);
  }
  .swatch{width:14px;height:14px;border-radius:3px;display:inline-block;flex:none}
  .ring-demo{width:14px;height:14px;border-radius:3px;border:2px solid var(--ring);flex:none}
  .eq-demo{
    display:inline-flex;align-items:center;justify-content:center;flex:none;
    width:14px;height:14px;font-weight:700;font-size:14px;color:var(--ink-muted);
  }

  #canvas-wrap{overflow:visible}
  #heat{display:block;max-width:100%}

  #tooltip{
    position:fixed;top:0;left:0;z-index:20;
    background:var(--surface);color:var(--ink);border:1px solid var(--grid);
    border-radius:8px;padding:8px 11px;box-shadow:0 6px 24px rgba(0,0,0,.16);
    pointer-events:none;max-width:280px;
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;line-height:1.5;
  }
  #tooltip .tt-cond{color:var(--ink-muted);text-transform:uppercase;letter-spacing:.08em;font-size:10px}

  footer.wrap{padding-block:22px 44px}
  .note{font-size:13px;color:var(--ink-sec);max-width:64ch}
  .note code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;background:var(--panel);padding:1px 5px;border-radius:4px}
</style>
</head>
<body>

<header class="wrap">
  <div class="eyebrow">Rock · Paper · Scissors — priming experiment</div>
  <h1>Every move, every game</h1>
  <p class="lede">One game at a time, from all 40,000 real games across the four conditions. Ten columns are a game&#39;s ten rounds: Agent A on top, Agent B below. Color is the move; a ring marks the round&#39;s winner, and an equals sign marks a draw.</p>
</header>

<section class="wrap" id="summary" aria-label="Results by condition"></section>

<section class="wrap" id="controls" aria-label="Navigation">
  <div class="chip-row" id="jump">
    <button type="button" class="chip" data-cond="0">Normal</button>
    <button type="button" class="chip" data-cond="1">Buttered</button>
    <button type="button" class="chip" data-cond="2">Undermined</button>
    <button type="button" class="chip" data-cond="3">Both</button>
  </div>
  <input type="range" id="slider" min="0" max="39999" step="1" value="0" aria-label="Game">
  <div class="nav">
    <button type="button" class="btn" id="prev">‹ Prev game</button>
    <button type="button" class="btn" id="play">▶ Play</button>
    <button type="button" class="btn" id="next">Next game ›</button>
  </div>
</section>

<div class="wrap readout">
  <span class="readout-cond" id="readout-cond"></span>
  <span class="readout-game" id="readout-game"></span>
  <span class="readout-result" id="readout-result"></span>
  <span class="readout-score" id="readout-score"></span>
</div>

<div class="wrap">
  <div id="canvas-wrap"><canvas id="heat" aria-label="One game, ten rounds"></canvas></div>
</div>

<div class="wrap" id="legend">
  <div class="legend-item"><span class="swatch" style="background:var(--move-rock)"></span>rock</div>
  <div class="legend-item"><span class="swatch" style="background:var(--move-paper)"></span>paper</div>
  <div class="legend-item"><span class="swatch" style="background:var(--move-scissors)"></span>scissors</div>
  <div class="legend-item"><span class="ring-demo"></span>round winner</div>
  <div class="legend-item"><span class="eq-demo">=</span>draw (same move)</div>
</div>

<footer class="wrap">
  <p class="note"><b>How to read it.</b> Each column is one round of the current game: A&#39;s move on top, B&#39;s below. Color and label are the move; a ring around a cell means that agent won the round, and an <b>=</b> between the two cells means a draw — both played the same move. The line above names the game&#39;s outcome and score. Drag the slider, press Prev/Next, or press Play to walk through the games in order: normal, then buttered, then undermined, then both. &#8220;Normal&#8221; is the unprimed control (the neutral baseline — this data has no neutral-prime run). Drawn directly from <code>normal/</code>, <code>buttered/</code>, <code>undermined/</code> and <code>both/</code> <code>results.json</code>.</p>
</footer>

<div id="tooltip" hidden></div>

<script>
(function(){
  'use strict';
  var DATA = __DATA_JSON__;
  var ORDER = ['normal','buttered','undermined','both'];
  var LABELS = {normal:'Normal (control)', buttered:'Buttered', undermined:'Undermined', both:'Both'};
  var MOVES = ['rock','paper','scissors'];
  var PER = 10000, TOTAL = 40000;
  var PAD = 4, HEADER_H = 22, A_H = 32, GAP = 10, B_H = 32;
  var CELL_H = A_H + GAP + B_H;
  var MONO = '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';

  var canvas = document.getElementById('heat');
  var ctx = canvas.getContext('2d');
  var tooltip = document.getElementById('tooltip');
  var slider = document.getElementById('slider');
  var playBtn = document.getElementById('play');
  var jumpBtns = Array.prototype.slice.call(document.querySelectorAll('#jump .chip'));

  var start = 0, playing = false, timer = null;

  function css(n){ return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }

  function roundW(){
    var w = document.getElementById('canvas-wrap').clientWidth;
    return Math.max(28, Math.min(84, Math.floor((w - PAD * 2) / 10)));
  }

  function lum(hex){
    var h = hex.replace('#','');
    var r = parseInt(h.slice(0,2),16) / 255;
    var g = parseInt(h.slice(2,4),16) / 255;
    var b = parseInt(h.slice(4,6),16) / 255;
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function draw(){
    var rw = roundW();
    var cw = PAD * 2 + 10 * rw;
    var ch = HEADER_H + CELL_H + PAD * 2;
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(ch * dpr);
    canvas.style.width = cw + 'px';
    canvas.style.height = ch + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cw, ch);

    var ink = css('--ink'), inkMuted = css('--ink-muted'), ring = css('--ring'), surface = css('--surface');
    var moveColor = {'0': css('--move-rock'), '1': css('--move-paper'), '2': css('--move-scissors')};
    var showName = rw >= 58;

    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '500 10px ' + MONO;
    ctx.fillStyle = inkMuted;
    for (var r = 0; r < 10; r++) ctx.fillText(String(r + 1), PAD + r * rw + rw / 2, HEADER_H / 2);

    var g = start;
    var c = ORDER[Math.floor(g / PER)], loc = g % PER;
    var A = DATA[c].A[loc], B = DATA[c].B[loc], R = DATA[c].R[loc];
    var yA = HEADER_H + PAD, yB = yA + A_H + GAP;

    for (var r2 = 0; r2 < 10; r2++){
      var x = PAD + r2 * rw;
      var ac = A[r2], bc = B[r2];
      var aLabel = showName ? MOVES[+ac] : 'RPS'[+ac];
      var bLabel = showName ? MOVES[+bc] : 'RPS'[+bc];

      ctx.fillStyle = moveColor[ac];
      ctx.fillRect(x, yA, rw - 1, A_H);
      ctx.fillStyle = moveColor[bc];
      ctx.fillRect(x, yB, rw - 1, B_H);

      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.font = (showName ? '600 11px ' : '700 15px ') + MONO;
      ctx.fillStyle = lum(moveColor[ac]) > 0.55 ? '#171612' : '#ffffff';
      ctx.fillText(aLabel, x + (rw - 1) / 2, yA + A_H / 2);
      ctx.fillStyle = lum(moveColor[bc]) > 0.55 ? '#171612' : '#ffffff';
      ctx.fillText(bLabel, x + (rw - 1) / 2, yB + B_H / 2);

      var res = R[r2];
      if (res === '0' || res === '1'){
        var ry = res === '0' ? yA : yB;
        var h = res === '0' ? A_H : B_H;
        var inset = 2;
        ctx.strokeStyle = surface; ctx.lineWidth = 4;
        ctx.strokeRect(x + inset, ry + inset, rw - 1 - 2 * inset, h - 2 * inset);
        ctx.strokeStyle = ring; ctx.lineWidth = 2.5;
        ctx.strokeRect(x + inset, ry + inset, rw - 1 - 2 * inset, h - 2 * inset);
      } else {
        ctx.fillStyle = inkMuted;
        ctx.font = '700 13px ' + MONO;
        ctx.fillText('=', x + (rw - 1) / 2, yA + A_H + GAP / 2);
      }
    }
  }

  function updateReadout(){
    var g = start, c = ORDER[Math.floor(g / PER)], loc = g % PER;
    var G = DATA[c].G[loc], R = DATA[c].R[loc];
    var aW = 0, bW = 0;
    for (var i = 0; i < R.length; i++){ if (R[i] === '0') aW++; else if (R[i] === '1') bW++; }
    document.getElementById('readout-cond').textContent = LABELS[c];
    document.getElementById('readout-game').textContent = 'game ' + (loc + 1).toLocaleString() + ' of 10,000';
    document.getElementById('readout-result').textContent =
      G === 'A' ? 'A wins' : (G === 'B' ? 'B wins' : 'draw');
    document.getElementById('readout-score').textContent = 'A ' + aW + ' · B ' + bW;
  }

  function go(d){
    start = Math.max(0, Math.min(TOTAL - 1, start + d));
    slider.value = String(start);
    draw(); updateReadout();
  }

  function jump(cond){
    start = cond * PER;
    slider.value = String(start);
    draw(); updateReadout();
    jumpBtns.forEach(function(x){ x.classList.toggle('on', +x.dataset.cond === cond); });
  }

  function el(tag, cls, text){
    var e = document.createElement(tag);
    e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function renderSummary(){
    var box = document.getElementById('summary');
    box.innerHTML = '';
    for (var i = 0; i < ORDER.length; i++){
      var c = ORDER[i];
      var G = DATA[c].G;
      var a = 0, b = 0, d = 0;
      for (var j = 0; j < G.length; j++){
        if (G[j] === 'A') a++; else if (G[j] === 'B') b++; else d++;
      }
      var share = a / (a + b);
      var fill = el('span', 'tile-fill');
      fill.style.width = (share * 100).toFixed(1) + '%';
      var track = el('div', 'tile-bar');
      track.appendChild(fill);

      var tile = el('article', 'tile');
      tile.appendChild(el('div', 'tile-label', LABELS[c]));
      tile.appendChild(el('div', 'tile-big', (share * 100).toFixed(1) + '%'));
      tile.appendChild(el('div', 'tile-cap', 'A share of decided games'));
      tile.appendChild(track);
      tile.appendChild(el('div', 'tile-counts',
        'A ' + a.toLocaleString() + ' · B ' + b.toLocaleString() + ' · ' + d.toLocaleString() + ' draws'));
      box.appendChild(tile);
    }
  }

  function showTooltip(e){
    var rect = canvas.getBoundingClientRect();
    var mx = e.clientX - rect.left, my = e.clientY - rect.top;
    var rw = roundW();
    var col = Math.floor((mx - PAD) / rw);
    if (col < 0 || col > 9){ tooltip.hidden = true; return; }
    var g = start, c = ORDER[Math.floor(g / PER)], loc = g % PER;
    var A = DATA[c].A[loc], B = DATA[c].B[loc], R = DATA[c].R[loc];
    var am = MOVES[+A[col]], bm = MOVES[+B[col]];
    var res = R[col] === '0' ? 'A wins' : (R[col] === '1' ? 'B wins' : 'draw');
    tooltip.innerHTML = '<span class="tt-cond">' + LABELS[c] + '</span> · round ' + (col + 1) +
      '<br>A ' + am + ' · B ' + bm + ' · ' + res;
    tooltip.hidden = false;
    var pad = 14, tx = e.clientX + pad, ty = e.clientY + pad;
    var tw = tooltip.offsetWidth, th = tooltip.offsetHeight;
    if (tx + tw > window.innerWidth - 8) tx = e.clientX - tw - pad;
    if (ty + th > window.innerHeight - 8) ty = e.clientY - th - pad;
    tooltip.style.transform = 'translate(' + Math.max(4, tx) + 'px,' + Math.max(4, ty) + 'px)';
  }

  canvas.addEventListener('mousemove', showTooltip);
  canvas.addEventListener('mouseleave', function(){ tooltip.hidden = true; });
  slider.addEventListener('input', function(){ start = +slider.value; draw(); updateReadout(); });
  document.getElementById('prev').addEventListener('click', function(){ go(-1); });
  document.getElementById('next').addEventListener('click', function(){ go(1); });

  playBtn.addEventListener('click', function(){
    playing = !playing;
    playBtn.textContent = playing ? '❚❚ Pause' : '▶ Play';
    playBtn.classList.toggle('active', playing);
    if (playing){
      timer = setInterval(function(){
        start += 1;
        if (start >= TOTAL) start = 0;
        slider.value = String(start);
        draw(); updateReadout();
      }, 300);
    } else if (timer){ clearInterval(timer); timer = null; }
  });

  jumpBtns.forEach(function(b){
    b.addEventListener('click', function(){ jump(+b.dataset.cond); });
  });

  window.addEventListener('resize', draw);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
  if (window.MutationObserver){
    new MutationObserver(draw).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
  }

  renderSummary();
  slider.max = String(TOTAL - 1);
  jump(0);
})();
</script>
</body>
</html>
'''


def main():
    data = build()
    for name in CONDITIONS:
        g = data[name]["G"]
        a, b, d = g.count("A"), g.count("B"), g.count("D")
        print(f"{name:10} A={a} B={b} draw={d}  A_decisive_share={a/(a+b):.4f}")
    payload = json.dumps(data, separators=(",", ":"))
    html = TEMPLATE.replace("__DATA_JSON__", payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}  ({len(html)/1e6:.2f} MB total, {len(payload)/1e6:.2f} MB data)")


if __name__ == "__main__":
    main()
