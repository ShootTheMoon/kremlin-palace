# -*- coding: utf-8 -*-
import math, random

def s2l(u8):
    u = u8 / 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

def l2s(x):
    x = max(0.0, min(1.0, x))
    v = x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return v * 255.0

# measured driver shape (dbg3 R), in sigma units, p -> z
ZP = [(0.5, -2.632), (1, -2.363), (2, -2.072), (5, -1.665), (16, -0.994),
      (50, 0.0), (84, 1.012), (95, 1.647), (98, 1.990), (99, 2.211), (99.5, 2.413)]

MEAN, SD = 0.4835, 0.04726

STOPS = [
    (0.359, (10, 20, 52)),
    (0.405, (20, 44, 100)),
    (0.4365, (28, 58, 124)),
    (0.4835, (40, 78, 146)),
    (0.5313, (56, 104, 170)),
    (0.5613, (72, 124, 190)),
    (0.598, (104, 158, 225)),
]
LSTOPS = [(p, tuple(s2l(c) for c in rgb)) for p, rgb in STOPS]

def ramp(d):
    if d <= LSTOPS[0][0]:
        return LSTOPS[0][1]
    if d >= LSTOPS[-1][0]:
        return LSTOPS[-1][1]
    for i in range(len(LSTOPS) - 1):
        a, ca = LSTOPS[i]
        b, cb = LSTOPS[i + 1]
        if a <= d <= b:
            t = (d - a) / (b - a)
            return tuple(ca[k] + t * (cb[k] - ca[k]) for k in range(3))

random.seed(7)
N = 300000
acc = [[], [], []]
for _ in range(N):
    d = random.gauss(MEAN, SD)
    c = ramp(d)
    for k in range(3):
        acc[k].append(round(l2s(c[k])))
for k, nm in enumerate('RGB'):
    v = acc[k]
    m = sum(v) / N
    sd = (sum((x - m) ** 2 for x in v) / N) ** 0.5
    print('%s min=%3d max=%3d mean=%6.1f std=%6.2f spread=%3d' % (nm, min(v), max(v), m, sd, max(v) - min(v)))
