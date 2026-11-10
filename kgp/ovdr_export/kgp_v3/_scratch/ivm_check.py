# -*- coding: utf-8 -*-
"""Extra analysis of a baked tile: channel stats, tone histogram, hue-vs-value check."""
import sys, os
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png, stats

p = sys.argv[1]
w, h, ch, px = decode_png(p)
s = stats(p)
print("spread %d  std %.2f  seamV %.1f  seamH %.1f" % (s["spread"], s["std"], s["seam_v"], s["seam_h"]))
for c in "RGB":
    mn, mx, me, sd = s["channels"][c]
    print("  %s  min %3d  max %3d  mean %6.1f  sd %5.2f" % (c, mn, mx, me, sd))

R = px[0::ch]; G = px[1::ch]; B = px[2::ch]
n = len(R)
lum = [(R[i] * 2 + G[i] * 5 + B[i]) / 8.0 for i in range(n)]
sl = sorted(lum)


def pct(f):
    return sl[min(n - 1, int(f * n))]


print("  tone percentiles: " + " ".join("p%02d=%3d" % (q, pct(q / 100.0))
                                        for q in (1, 5, 10, 25, 50, 75, 90, 95, 99)))
# histogram in 16 bins over the occupied range
lo, hi = sl[0], sl[-1]
bins = [0] * 16
for v in lum:
    bins[min(15, int((v - lo) / (hi - lo + 1e-9) * 16))] += 1
print("  histogram %d..%d:" % (lo, hi))
for i, b in enumerate(bins):
    a = lo + (hi - lo) * i / 16.0
    print("    %3d-%3d %5.2f%% %s" % (a, a + (hi - lo) / 16.0, 100.0 * b / n, "#" * int(200.0 * b / n)))
# hue vs value: warm field should be warmer than the veins
t1, t2 = pct(0.10), pct(0.85)
dark = [i for i in range(n) if lum[i] <= t1]
light = [i for i in range(n) if lum[i] >= t2]


def rb(idx):
    return (sum(R[i] for i in idx) / len(idx), sum(G[i] for i in idx) / len(idx),
            sum(B[i] for i in idx) / len(idx))


dr, dg, db = rb(dark)
lr, lg, lb = rb(light)
print("  darkest 10%%  R%.1f G%.1f B%.1f   R-B = %.1f" % (dr, dg, db, dr - db))
print("  lightest 15%% R%.1f G%.1f B%.1f   R-B = %.1f" % (lr, lg, lb, lr - lb))
print("  hue break (warm field minus cool vein, in R-B): %.1f levels" % ((lr - lb) - (dr - db)))
