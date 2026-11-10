# -*- coding: utf-8 -*-
# usage: python measure.py <tile.png> [tile_metres] [--montage out.png] [--probe]
import sys, os, zlib, struct, random, math
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png, stats

S2L = [0.0] * 256
for i in range(256):
    c = i / 255.0
    S2L[i] = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    f = int(math.floor(k)); c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def write_png(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    hdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', hdr)
                           + chunk(b'IDAT', zlib.compress(bytes(raw), 6)) + chunk(b'IEND', b''))


def main():
    path = sys.argv[1]
    tm = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    mont = None
    probe = '--probe' in sys.argv
    if '--montage' in sys.argv:
        mont = sys.argv[sys.argv.index('--montage') + 1]

    w, h, ch, px = decode_png(path)
    s = stats(path)
    print('== %s  %dx%d' % (os.path.basename(path), w, h))
    print('   spread %d   std %.2f   seam_v %.1f   seam_h %.1f   ok=%s'
          % (s['spread'], s['std'], s['seam_v'], s['seam_h'], s['ok']))
    for c in 'RGB':
        mn, mx, mean, sd = s['channels'][c]
        print('   %s  min %3d  max %3d  mean %6.1f  sd %5.2f' % (c, mn, mx, mean, sd))

    if probe:
        vals = sorted(S2L[v] for v in px[0::ch])
        n = len(vals)
        mean = sum(vals) / n
        sd = (sum((v - mean) ** 2 for v in vals) / n) ** 0.5
        print('   LINEAR probe: mean %.4f  sd %.4f  min %.4f  p1 %.4f  p5 %.4f  p50 %.4f  p95 %.4f  p99 %.4f  max %.4f'
              % (mean, sd, vals[0], pct(vals, .01), pct(vals, .05), pct(vals, .5),
                 pct(vals, .95), pct(vals, .99), vals[-1]))
        return

    # --- luminance of the final tile, percentiles of the factor-equivalent ---
    lum = [0.0] * (w * h)
    for i in range(w * h):
        o = i * ch
        lum[i] = 0.2126 * px[o] + 0.7152 * px[o + 1] + 0.0722 * px[o + 2]
    sl = sorted(lum)
    print('   sRGB luminance: mean %.1f  p1 %.1f  p5 %.1f  p50 %.1f  p95 %.1f  p99 %.1f'
          % (sum(lum) / len(lum), pct(sl, .01), pct(sl, .05), pct(sl, .5), pct(sl, .95), pct(sl, .99)))

    # --- patch lottery : random wrap-around patches of physical size ---
    ppm = w / tm
    random.seed(12345)
    print('   patch lottery (mean sRGB luminance over random wrap patches):')
    for cm in (8, 20, 40):
        k = max(2, int(round(cm / 100.0 * ppm)))
        means = []
        for _ in range(500):
            x0 = random.randrange(w); y0 = random.randrange(h)
            t = 0.0
            for dy in range(k):
                yy = (y0 + dy) % h
                base = yy * w
                for dx in range(k):
                    t += lum[base + (x0 + dx) % w]
            means.append(t / (k * k))
        means.sort()
        lo, hi = means[0], means[-1]
        p5, p95 = pct(means, .05), pct(means, .95)
        sd = (sum((m - sum(means) / len(means)) ** 2 for m in means) / len(means)) ** 0.5
        print('     %2d cm (%3d px): min %6.1f  max %6.1f  ratio %.2f:1 | p5 %6.1f p95 %6.1f ratio %.2f:1 | sd %5.2f'
              % (cm, k, lo, hi, hi / max(lo, 1e-6), p5, p95, p95 / max(p5, 1e-6), sd))

    if mont:
        # 3x3 montage downsampled 3x -> same size as one tile
        step = 3
        ow = w
        oh = h
        buf = bytearray(ow * oh * 3)
        for oy in range(oh):
            sy = (oy * step) % h
            for ox in range(ow):
                sx = (ox * step) % w
                so = (sy * w + sx) * ch
                do = (oy * ow + ox) * 3
                buf[do] = px[so]; buf[do + 1] = px[so + 1]; buf[do + 2] = px[so + 2]
        write_png(mont, ow, oh, buf)
        print('   montage ->', mont)
        # plus a 1x view at half res
        one = mont.replace('.png', '_1x.png')
        hw = w // 2
        b2 = bytearray(hw * hw * 3)
        for oy in range(hw):
            for ox in range(hw):
                so = ((oy * 2) * w + ox * 2) * ch
                do = (oy * hw + ox) * 3
                b2[do] = px[so]; b2[do + 1] = px[so + 1]; b2[do + 2] = px[so + 2]
        write_png(one, hw, hw, b2)
        print('   1x view ->', one)


main()
