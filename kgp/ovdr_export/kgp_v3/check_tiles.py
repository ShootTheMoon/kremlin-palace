# -*- coding: utf-8 -*-
"""구운 타일이 실제로 무늬를 갖고 있는지 잰다.

평탄한 조명 아래서는 색 변화가 곧 '무늬'다. v2 의 Ivory marble 은 스프레드가 9/255 였고
그래서 게임에서 단색 돌덩이로 보였다. 합격선은 아래 MIN_SPREAD.

PIL 이 없어서 PNG 를 직접 푼다(8bit, colortype 2/6 만).
"""

import zlib
import struct
import os
import sys
import glob

MIN_SPREAD = 40      # 채널 최대-최소
MIN_STD = 6.0        # 표준편차


def decode_png(path):
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png")
    i, idat = 8, b""
    w = h = bd = ct = None
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        typ = d[i + 4:i + 8]
        body = d[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        i += 12 + ln
    if bd != 8 or ct not in (2, 6):
        raise ValueError("unsupported png bd=%s ct=%s" % (bd, ct))
    ch = 3 if ct == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * ch
    out = bytearray()
    prev = bytearray(stride)
    o = 0
    for _ in range(h):
        f = raw[o]; o += 1
        line = bytearray(raw[o:o + stride]); o += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            b = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    return w, h, ch, out


def stats(path):
    w, h, ch, px = decode_png(path)
    res = {}
    for name, off in (("R", 0), ("G", 1), ("B", 2)):
        vals = px[off::ch]
        n = len(vals)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        res[name] = (min(vals), max(vals), round(mean, 1), round(var ** 0.5, 2))
    spread = max(res[c][1] - res[c][0] for c in "RGB")
    std = max(res[c][3] for c in "RGB")
    # 타일 이음새 : 좌우 끝열 / 위아래 끝행 차이
    def row(y):
        return px[y * w * ch:(y + 1) * w * ch]
    top, bot = row(0), row(h - 1)
    seam_v = sum(abs(top[k] - bot[k]) for k in range(0, len(top), ch)) / w
    left = [px[(y * w) * ch] for y in range(h)]
    right = [px[(y * w + w - 1) * ch] for y in range(h)]
    seam_h = sum(abs(left[k] - right[k]) for k in range(h)) / h
    return {"file": os.path.basename(path), "size": "%dx%d" % (w, h),
            "spread": spread, "std": round(std, 2),
            "seam_v": round(seam_v, 1), "seam_h": round(seam_h, 1),
            "channels": res,
            "ok": spread >= MIN_SPREAD and std >= MIN_STD}


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else r"C:\Work\blender\ovdr_export\kgp_v3\_tex"
    files = sorted(glob.glob(os.path.join(d, "*.png")))
    print("%-44s %-10s %6s %6s %6s %6s  %s" % ("tile", "size", "spread", "std", "seamV", "seamH", "ok"))
    bad = 0
    for f in files:
        try:
            s = stats(f)
        except Exception as e:                      # noqa: BLE001
            print("%-44s  ERROR %s" % (os.path.basename(f), e))
            bad += 1
            continue
        print("%-44s %-10s %6d %6.2f %6.1f %6.1f  %s"
              % (s["file"], s["size"], s["spread"], s["std"], s["seam_v"], s["seam_h"],
                 "ok" if s["ok"] else "FLAT"))
        if not s["ok"]:
            bad += 1
    print("\n%d tiles, %d below threshold (spread>=%d, std>=%.0f)"
          % (len(files), bad, MIN_SPREAD, MIN_STD))
