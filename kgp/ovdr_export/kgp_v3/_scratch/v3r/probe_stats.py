# -*- coding: utf-8 -*-
"""Percentile probe: decode a baked PNG and report the LINEAR distribution per channel.
Used to place ColorRamp stops on the range the driver actually occupies.
"""
import sys, os
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png, stats


def srgb_to_lin(u):
    u = u / 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


LIN = [srgb_to_lin(i) for i in range(256)]

path = sys.argv[1]
w, h, ch, px = decode_png(path)
print(os.path.basename(path))
for name, off in (("R", 0), ("G", 1), ("B", 2)):
    vals = sorted(px[off::ch])
    n = len(vals)
    lv = [LIN[v] for v in px[off::ch]]
    m = sum(lv) / n
    sd = (sum((x - m) ** 2 for x in lv) / n) ** 0.5
    qs = [0.2, 1, 5, 16, 50, 84, 95, 99, 99.8]
    out = " ".join("p%g=%.4f" % (q, LIN[vals[min(n - 1, int(n * q / 100.0))]]) for q in qs)
    print("  %s lin mean=%.4f sd=%.4f  %s" % (name, m, sd, out))
    # 8-bit view
    b = px[off::ch]
    bm = sum(b) / n
    bsd = (sum((v - bm) ** 2 for v in b) / n) ** 0.5
    print("      8bit min=%d max=%d mean=%.1f std=%.2f" % (min(b), max(b), bm, bsd))
s = stats(path)
print("  SPREAD=%d STD=%.2f seam_v=%.1f seam_h=%.1f  %s"
      % (s["spread"], s["std"], s["seam_v"], s["seam_h"], "ok" if s["ok"] else "FLAT"))
