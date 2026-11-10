# -*- coding: utf-8 -*-
import sys, os, zlib, struct
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png

def write_png(path, w, h, ch, buf):
    raw = bytearray()
    st = w*ch
    for y in range(h):
        raw.append(0)
        raw += buf[y*st:(y+1)*st]
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t+d) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2 if ch==3 else 6, 0, 0, 0)
    open(path,"wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))

src = sys.argv[1]; outdir = sys.argv[2]
w,h,ch,px = decode_png(src)
# ---- 2x2 tiled, native res
W,H = w*2, h*2
buf = bytearray(W*H*ch)
for y in range(H):
    sy = y % h
    row = px[sy*w*ch:(sy+1)*w*ch]
    buf[y*W*ch:(y*W+w)*ch] = row
    buf[(y*W+w)*ch:(y*W+2*w)*ch] = row
write_png(os.path.join(outdir,"view_2x2.png"), W, H, ch, buf)
# ---- 4x4 tiled, downscaled 2x (simulates viewing 1.4 m of wall)
W2,H2 = w*4//2, h*4//2
buf2 = bytearray(W2*H2*ch)
for y in range(H2):
    for x in range(W2):
        acc=[0,0,0]
        for dy in (0,1):
            for dx in (0,1):
                sy=(y*2+dy)%h; sx=(x*2+dx)%w
                o=(sy*w+sx)*ch
                for c in range(3): acc[c]+=px[o+c]
        o2=(y*W2+x)*ch
        for c in range(3): buf2[o2+c]=acc[c]//4
write_png(os.path.join(outdir,"view_4x4_half.png"), W2, H2, ch, buf2)
# ---- contrast stretch of the single tile, to inspect structure
lo=min(min(px[c::ch]) for c in range(3)); hi=max(max(px[c::ch]) for c in range(3))
buf3 = bytearray(w*h*ch)
for i in range(0, w*h*ch, ch):
    for c in range(3):
        buf3[i+c] = max(0,min(255,int((px[i+c]-lo)*255.0/(hi-lo))))
write_png(os.path.join(outdir,"view_stretch.png"), w, h, ch, buf3)
print("lo",lo,"hi",hi,"wrote views")
