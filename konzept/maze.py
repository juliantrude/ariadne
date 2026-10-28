import random, sys
from collections import deque
N = 9; C = (4, 4); S = (8, 0)          # Zelle (zeile, spalte); Ziel Mitte, Eingang unten links
def gen(seed):
    rnd = random.Random(seed); open_ = set(); seen = {S}; st = [S]
    while st:
        r, c = st[-1]
        nb = [(r+dr, c+dc) for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)) if 0<=r+dr<N and 0<=c+dc<N and (r+dr, c+dc) not in seen]
        if not nb: st.pop(); continue
        n = rnd.choice(nb); open_.add(frozenset(((r,c), n))); seen.add(n); st.append(n)
    return open_
def nbrs(o, a): return [b for b in [(a[0]+1,a[1]),(a[0]-1,a[1]),(a[0],a[1]+1),(a[0],a[1]-1)] if frozenset((a,b)) in o]
def path(o):
    prev = {S: None}; q = deque([S])
    while q:
        a = q.popleft()
        for b in nbrs(o, a):
            if b not in prev: prev[b] = a; q.append(b)
    p = [C]
    while p[-1] != S: p.append(prev[p[-1]])
    return p[::-1]
def branch(o, onpath, root, first):     # tiefster Ast; liefert Liste bis Sackgassenende, wenn unverzweigt
    seq = [root, first]; cur, last = first, root
    while True:
        nx = [b for b in nbrs(o, cur) if b != last]
        if len(nx) == 0: return seq
        if len(nx) > 1: return None
        last, cur = cur, nx[0]; seq.append(cur)
best = None
for seed in range(4000):
    o = gen(seed); p = path(o); ps = set(p)
    if not 22 <= len(p) <= 32: continue
    dead = []
    for i, a in enumerate(p[2:-3], 2):
        for b in nbrs(o, a):
            if b in ps: continue
            br = branch(o, ps, a, b)
            if br and 3 <= len(br) - 1 <= 5: dead.append((i, br))
    if len(dead) < 2: continue
    # zwei gut getrennte Sackgassen
    for x in range(len(dead)):
        for y in range(x+1, len(dead)):
            if dead[y][0] - dead[x][0] >= 8:
                score = len(p) + (dead[y][0]-dead[x][0])
                if not best or score > best[0]: best = (score, seed, o, p, dead[x][1], dead[y][1])
_, seed, o, p, d1, d2 = best
print("seed", seed, "pfad", len(p), "sackgassen", len(d1)-1, len(d2)-1, file=sys.stderr)
# SVG
Z = 22; X0 = 1; W = N*Z
def cc(a): return (X0 + a[1]*Z + Z/2, X0 + a[0]*Z + Z/2)
L = []
for r in range(N):
    for c in range(N):
        x, y = X0 + c*Z, X0 + r*Z
        if c < N-1 and frozenset(((r,c),(r,c+1))) not in o: L.append(f"M{x+Z} {y}V{y+Z}")
        if r < N-1 and frozenset(((r,c),(r+1,c))) not in o: L.append(f"M{x} {y+Z}H{x+Z}")
# Außenrand mit Eingang unten links
ex = X0 + S[1]*Z
L.append(f"M{ex+Z} {X0+W}H{X0+W}V{X0}H{X0}V{X0+W}")
walls = "".join(L)
def pl(cells, extra=None):
    pts = [cc(a) for a in cells]
    if extra: pts = [extra] + pts
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
sx, sy = cc(S)
main = pl(p, (sx, X0 + W + 14))
dd = [pl(d) for d in (d1, d2)]
ends = [cc(d[-1]) for d in (d1, d2)]
mx, my = cc(C)
svg = f'''<svg class="maze" viewBox="-6 -6 {W+14} {W+30}" fill="none">
  <path d="{walls}" stroke="#1B2226" stroke-width="2.4" stroke-linecap="square"/>
  <g stroke="#B23A26" stroke-width="1.5" stroke-dasharray="2 2.6" opacity=".6" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="{dd[0]}"/><polyline points="{dd[1]}"/></g>
  <polyline points="{main}" stroke="#B23A26" stroke-width="2" stroke-dasharray="4 2.6" stroke-linecap="round" stroke-linejoin="round"/>
  {''.join(f'<g transform="translate({x:.1f},{y:.1f})"><circle r="5.2" fill="#E2B33C" stroke="#9A7414" stroke-width="1"/><circle r="3.4" fill="none" stroke="#9A7414" stroke-width=".7"/><path d="M-2.3 -0.6 A2.4 2.4 0 0 1 -0.6 -2.3" stroke="#FFF3C4" stroke-width=".9" stroke-linecap="round"/></g>' for x, y in ends)}
  <circle cx="{sx:.1f}" cy="{X0+W+14:.1f}" r="3.4" fill="#B23A26"/>
  <g transform="translate({mx:.1f},{my+1:.1f})">
    <rect x="-8" y="-2" width="16" height="8.5" rx="1" fill="#8A5A2B" stroke="#4E3216" stroke-width="1"/>
    <path d="M-8 -2 V-4.5 C-8 -9 8 -9 8 -4.5 V-2 Z" fill="#A06A34" stroke="#4E3216" stroke-width="1"/>
    <path d="M-8 -2 H8 M-4.5 -7.6 V6.5 M4.5 -7.6 V6.5" stroke="#E2B33C" stroke-width="1.3"/>
    <rect x="-1.6" y="-3.4" width="3.2" height="3.6" rx=".5" fill="#E2B33C" stroke="#9A7414" stroke-width=".6"/>
  </g>
</svg>'''
legend = [cc(d1[-1]), cc(d2[-1])]
open("maze.svg", "w").write(svg)
print(svg)
