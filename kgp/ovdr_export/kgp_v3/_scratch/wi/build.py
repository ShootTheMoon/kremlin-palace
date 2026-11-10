# -*- coding: utf-8 -*-
import bpy, os

SCR = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\wi"
OUT = os.path.join(SCR, "out")
os.makedirs(OUT, exist_ok=True)
PX = 512
NAME = "Wrought_iron"
SRC = os.path.join(SCR, "recipe.py")


def to_srgb(x):
    if x <= 0.0:
        return 0
    v = x * 12.92 if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055
    return max(0, min(255, int(round(v * 255.0))))


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 1
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
ob = bpy.context.object
mat = bpy.data.materials.new(NAME)
ob.data.materials.append(mat)

code = open(SRC, "r", encoding="utf-8").read()
exec(code, {"bpy": bpy, "mat": mat})

nt = mat.node_tree
img = bpy.data.images.new("bake", PX, PX, alpha=False, float_buffer=True)
tn = nt.nodes.new('ShaderNodeTexImage')
tn.image = img
nt.nodes.active = tn
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)

px = list(img.pixels)
n = PX * PX
ch8 = {}
print("---- %s ----" % NAME)
for ci, cn in ((0, 'R'), (1, 'G'), (2, 'B')):
    v = px[ci::4]
    s8 = [to_srgb(a) for a in v]
    ch8[cn] = s8
    mean = sum(s8) / n
    sd = (sum((a - mean) ** 2 for a in s8) / n) ** 0.5
    ss = sorted(s8)
    print("%s sRGB min%3d max%3d mean%6.1f sd%6.2f spread%4d | p1 %3d p5 %3d p25 %3d p50 %3d p75 %3d p95 %3d p99 %3d"
          % (cn, ss[0], ss[-1], mean, sd, ss[-1] - ss[0],
             ss[int(n * 0.01)], ss[int(n * 0.05)], ss[int(n * 0.25)],
             ss[int(n * 0.5)], ss[int(n * 0.75)], ss[int(n * 0.95)], ss[int(n * 0.99)]))

R, G, B = ch8['R'], ch8['G'], ch8['B']
warm = sum(1 for i in range(n) if R[i] > B[i])
warm3 = sum(1 for i in range(n) if R[i] - B[i] >= 3)
warm10 = sum(1 for i in range(n) if R[i] - B[i] >= 10)
print("R>B %.2f%%  R-B>=3 %.2f%%  R-B>=10 %.2f%%  max(R-B)=%d"
      % (100.0 * warm / n, 100.0 * warm3 / n, 100.0 * warm10 / n,
         max(R[i] - B[i] for i in range(n))))

BLK = 32
nb = PX // BLK
blk = []
for by in range(nb):
    for bx in range(nb):
        s = 0
        for y in range(by * BLK, (by + 1) * BLK):
            base = y * PX
            for x in range(bx * BLK, (bx + 1) * BLK):
                s += B[base + x]
        blk.append(s / (BLK * BLK))
bm = sum(blk) / len(blk)
lo = (sum((a - bm) ** 2 for a in blk) / len(blk)) ** 0.5
tot_m = sum(B) / n
tot = (sum((a - tot_m) ** 2 for a in B) / n) ** 0.5
hi = max(0.0, tot * tot - lo * lo) ** 0.5
print("B std total %.2f  low-freq %.2f  high-freq %.2f  hi/lo %.2f" % (tot, lo, hi, hi / max(lo, 1e-6)))

top = B[0:PX]
bot = B[(PX - 1) * PX:PX * PX]
sv_ = sum(abs(top[k] - bot[k]) for k in range(PX)) / PX
left = [B[y * PX] for y in range(PX)]
right = [B[y * PX + PX - 1] for y in range(PX)]
sh_ = sum(abs(left[k] - right[k]) for k in range(PX)) / PX
print("seam_v %.2f seam_h %.2f (B channel, in-memory)" % (sv_, sh_))

sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.view_settings.gamma = 1.0
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.color_depth = '8'
sc.render.image_settings.compression = 15
dst = os.path.join(OUT, NAME + ".png")
img.save_render(filepath=dst, scene=sc)
print("saved", dst)
