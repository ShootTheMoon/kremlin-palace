import sys, os, zlib, struct
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png, stats

src = sys.argv[1]
w, h, ch, px = decode_png(src)
s = stats(src)
print(s['file'], 'spread', s['spread'], 'std', s['std'], 'seamV', s['seam_v'], 'seamH', s['seam_h'])
for c in 'RGB':
    print('   %s min %d max %d mean %.1f sd %.2f' % ((c,) + s['channels'][c]))

# 2x2 tiled, downsampled 2x  -> 1024x1024 showing 4 tiles
half = w // 2
outw = half * 2
rows = []
for Y in range(outw):
    line = bytearray()
    sy = (Y % half) * 2
    for X in range(outw):
        sx = (X % half) * 2
        o = (sy * w + sx) * ch
        line += px[o:o + 3]
    rows.append(line)
raw = b''.join(b'\x00' + bytes(r) for r in rows)


def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)


out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', outw, outw, 8, 2, 0, 0, 0)) \
    + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
dst = os.path.splitext(src)[0] + '_x4.png'
open(dst, 'wb').write(out)
print('preview ->', dst)
