import sys, zlib, struct
sys.path.insert(0, r"C:\Work\blender\ovdr_export\kgp_v3")
from check_tiles import decode_png
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
w, h, ch, px = decode_png(src)
a = np.frombuffer(bytes(px), dtype=np.uint8).reshape(h, w, ch)[:, :, :3]
# half-shift roll: the tile seam now runs through the MIDDLE of the image
r = np.roll(np.roll(a, h // 2, axis=0), w // 2, axis=1)
# 2x2 montage of the rolled tile -> also shows tile-to-tile joins at the outer quarter lines
m = np.concatenate([np.concatenate([r, r], axis=1), np.concatenate([r, r], axis=1)], axis=0)
H, W, _ = m.shape
raw = b"".join(b"\x00" + m[y].tobytes() for y in range(H))
def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
open(dst, "wb").write(png)
print("wrote", dst, W, H)
