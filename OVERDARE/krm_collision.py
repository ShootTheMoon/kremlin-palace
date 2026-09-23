# Kremlin Palace -> OVERDARE collision Parts
#   blender.exe --background <blend> --python krm_collision.py
#
# OVERDARE has no UCX: colliders cannot ride in the FBX (Studio crashes).
# Engine Parts are native primitives -> they cost ZERO published assets.
# Emits collision_parts.json for overdare_create_instances, in OVERDARE cm Y-up.

import bpy, os, json, math, re
from mathutils import Vector

ROOT = r"C:\Users\29\Desktop\Kremlin_Palace_Phase3\OVERDARE"
OUT = os.path.join(ROOT, "05_COLLISION")
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.frame_set(sc.frame_start)
dg = bpy.context.evaluated_depsgraph_get()

log = []
def P(*a):
    s = " ".join(str(x) for x in a); log.append(s); print("[COL]", s, flush=True)

def wverts(o):
    ev = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    except Exception:
        return []
    if me is None: return []
    vs = [o.matrix_world @ v.co for v in me.vertices]
    bpy.data.meshes.remove(me)
    return vs

def aabb(vs):
    return (Vector((min(p.x for p in vs), min(p.y for p in vs), min(p.z for p in vs))),
            Vector((max(p.x for p in vs), max(p.y for p in vs), max(p.z for p in vs))))

def oriented_box(vs):
    """Real frame from geometry: yaw from the dominant horizontal edge direction.
    (A 45-degree slab read as an AABB inflates >40% and walls off doorways.)"""
    import itertools
    xs = [p.x for p in vs]; ys = [p.y for p in vs]; zs = [p.z for p in vs]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    best, bestyaw = None, 0.0
    for deg in range(0, 90, 5):                      # 5도 간격 탐색
        a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
        u = [ (p.x-cx)*ca + (p.y-cy)*sa for p in vs]
        v = [-(p.x-cx)*sa + (p.y-cy)*ca for p in vs]
        area = (max(u)-min(u)) * (max(v)-min(v))
        if best is None or area < best[0]:
            best = (area, min(u), max(u), min(v), max(v)); bestyaw = a
    _, u0, u1, v0, v1 = best
    ca, sa = math.cos(bestyaw), math.sin(bestyaw)
    mu, mv = (u0+u1)/2, (v0+v1)/2
    ox = cx + mu*ca - mv*sa
    oy = cy + mu*sa + mv*ca
    return (Vector((ox, oy, (min(zs)+max(zs))/2)),
            Vector((u1-u0, v1-v0, max(zs)-min(zs))),
            math.degrees(bestyaw))

parts = []
def emit(group, name, centre, size, yaw=0.0, pad=0.0):
    if min(size) <= 0.0: return
    s = Vector((max(size.x, 0.05)+pad, max(size.y, 0.05)+pad, max(size.z, 0.05)+pad))
    parts.append({
        "group": group, "name": name,
        # Blender m Z-up -> OVERDARE cm Y-up
        "X_cm": round(centre.x*100, 1), "Y_cm": round(centre.z*100, 1), "Z_cm": round(centre.y*100, 1),
        "SizeX_cm": round(s.x*100, 1), "SizeY_cm": round(s.z*100, 1), "SizeZ_cm": round(s.y*100, 1),
        "yaw_deg": round(-yaw, 2),
        "Anchored": True, "CanCollide": True, "Transparency": 1.0, "Material": "Plastic"})

vis = [o for o in sc.objects if o.type == 'MESH' and o.visible_get()]
byname = {o.name: o for o in vis}

# ---------------------------------------------------------------- 1. 바닥
FLOORS = [
    ("hall",          -16.0, 16.0, -42.0, 14.0, 0.0),
    ("corridor_L",    -30.0, -16.0, 8.1, 13.9, 0.0),
    ("corridor_R",     16.0, 30.0, 8.1, 13.9, 0.0),
    ("drawing_room",  -11.0, 11.0, -58.25, -42.25, 0.0),
]
for nm, x0, x1, y0, y1, z in FLOORS:
    c = Vector(((x0+x1)/2, (y0+y1)/2, z - 0.25))
    emit("FLOOR", "COL_FLOOR_" + nm, c, Vector((x1-x0, y1-y0, 0.5)))
P("floors", len(FLOORS))

# ---------------------------------------------------------------- 2. 외벽 (실내 경계)
WALLS = [   # (이름, x0,x1, y0,y1, ztop)
    ("hall_L",      -16.2, -15.7, -42.25, 14.0, 12.0),
    ("hall_R",       15.7,  16.2, -42.25, 14.0, 12.0),
    ("hall_rear",   -16.2,  16.2,  13.7,  14.2, 12.0),
    ("entrance",    -16.2,  16.2, -42.3, -41.7, 12.0),
    ("droom_L",     -11.5, -11.0, -58.5, -42.25, 10.2),
    ("droom_R",      11.0,  11.5, -58.5, -42.25, 10.2),
    ("droom_back",  -11.5,  11.5, -58.5, -58.0, 10.2),
    ("corrL_outer", -30.1, -29.6,   8.1,  13.9,  6.0),
    ("corrR_outer",  29.6,  30.1,   8.1,  13.9,  6.0),
    ("corrL_inner", -30.1, -16.0,   8.0,   8.3,  6.0),
    ("corrR_inner",  16.0,  30.1,   8.0,   8.3,  6.0),
    ("corrL_back",  -30.1, -16.0,  13.6,  13.9,  6.0),
    ("corrR_back",   16.0,  30.1,  13.6,  13.9,  6.0),
]
for nm, x0, x1, y0, y1, zt in WALLS:
    emit("WALL", "COL_WALL_" + nm,
         Vector(((x0+x1)/2, (y0+y1)/2, zt/2)), Vector((x1-x0, y1-y0, zt)))
P("walls", len(WALLS))
# 정문 개구부는 벽에서 비운다 -> 문 좌우 두 조각으로 교체
parts[:] = [p for p in parts if p["name"] != "COL_WALL_entrance"]
for tag, x0, x1 in (("entrance_L", -16.2, -3.05), ("entrance_R", 3.05, 16.2)):
    emit("WALL", "COL_WALL_" + tag, Vector(((x0+x1)/2, -42.0, 6.0)), Vector((x1-x0, 0.6, 12.0)))
emit("WALL", "COL_WALL_entrance_head", Vector((0.0, -42.0, 10.6)), Vector((6.1, 0.6, 2.8)))

# ---------------------------------------------------------------- 3. 계단
# 쌍곡선 계단을 박스 하나로 잡으면 오히려 길을 막는다. Z 밴드로 썰어
# 밴드마다 oriented box 하나 -> 실제로 걸어 올라갈 수 있는 계단이 된다.
steps = [o for o in vis
         if re.search(r"stair|tread|stringer", o.name, re.I)
         and not re.search(r"ceiling|carpet|fascia|ledge", o.name, re.I)]
BANDS = 30                                  # 소스가 30단
made = 0
for o in steps:
    ev = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    except Exception:
        continue
    if me is None or not me.polygons:
        if me: bpy.data.meshes.remove(me)
        continue
    M = o.matrix_world
    fc = [(M @ p.center, [M @ me.vertices[i].co for i in p.vertices]) for p in me.polygons]
    bpy.data.meshes.remove(me)
    zs = [c.z for c, _ in fc]
    z0, z1 = min(zs), max(zs)
    if z0 > 6.0:                            # 천장 장식은 충돌 대상이 아니다
        continue
    if (z1 - z0) < 0.35:                    # 평평한 판은 통짜로
        vs = [v for _, vv in fc for v in vv]
        c, s, yaw = oriented_box(vs)
        emit("STAIR", "COL_STAIR_" + o.name[:30], c, s, yaw); made += 1
        continue
    n = max(2, min(BANDS, int(round((z1 - z0) / 0.17))))
    h = (z1 - z0) / n
    for b in range(n):
        lo, hi = z0 + b * h, z0 + (b + 1) * h + 1e-6
        band = [v for c, vv in fc if lo <= c.z < hi for v in vv]
        if len(band) < 4:
            continue
        # XY 는 밴드에 속한 면에서, Z 는 밴드 구간으로 고정한다.
        # (세로로 긴 면은 중심이 한 밴드에 있어도 정점이 계단 전체를 가로질러
        #  박스가 5 m 두께가 돼 버린다 — 실제로 512 cm 박스가 나왔다)
        cc, ss, yy = oriented_box(band)
        ss.z = hi - lo
        cc.z = (lo + hi) / 2
        emit("STAIR", "COL_STAIR_%s_b%02d" % (o.name[:22], b), cc, ss, yy)
        made += 1
P("stairs", made, "boxes from", len(steps), "objects")

# ---------------------------------------------------------------- 4. 기둥 (XY로 군집)
colparts = [o for o in vis if re.search(r"column|shaft|pier", o.name, re.I)]
clusters = {}
for o in colparts:
    vs = wverts(o)
    if not vs: continue
    mn, mx = aabb(vs)
    if (mx.z - mn.z) < 0.3 and (mx - mn).length < 1.2:
        continue
    key = (round((mn.x+mx.x)/2, 0), round((mn.y+mx.y)/2, 0))
    e = clusters.setdefault(key, [mn.copy(), mx.copy()])
    for i in range(3):
        e[0][i] = min(e[0][i], mn[i]); e[1][i] = max(e[1][i], mx[i])
for (kx, ky), (mn, mx) in sorted(clusters.items()):
    s = mx - mn
    if max(s.x, s.y) > 4.0:      # 벽에 붙은 긴 띠는 기둥이 아니다
        continue
    emit("COLUMN", "COL_COL_%+05.1f_%+06.1f" % (kx, ky), (mn+mx)/2, s)
P("columns", sum(1 for p in parts if p["group"] == "COLUMN"), "from", len(colparts), "objects")

# ---------------------------------------------------------------- 5. 갤러리 바닥 / 발코니
DECKS = [
    ("gallery_L", -16.0, -11.4, -42.0, 14.0, 5.1),
    ("gallery_R",  11.4,  16.0, -42.0, 14.0, 5.1),
    ("balcony_rear", -12.2, 12.2,  2.0,  8.0, 5.12),
]
for nm, x0, x1, y0, y1, z in DECKS:
    emit("DECK", "COL_DECK_" + nm, Vector(((x0+x1)/2, (y0+y1)/2, z-0.15)),
         Vector((x1-x0, y1-y0, 0.3)))
    # 난간 (떨어짐 방지)
    for side, xx in (("i", x0 if x0 > 0 else x1), ):
        emit("RAIL", "COL_RAIL_" + nm, Vector((xx, (y0+y1)/2, z+0.55)),
             Vector((0.15, y1-y0, 1.1)))
P("decks", len(DECKS))

# ---------------------------------------------------------------- 6. 분수
for nm in ("P7 water basin body", "P3 angel plinth"):
    o = byname.get(nm)
    if not o: continue
    vs = wverts(o)
    if not vs: continue
    mn, mx = aabb(vs)
    emit("PROP", "COL_FOUNTAIN_" + nm.split()[-1], (mn+mx)/2, mx-mn)
P("fountain", sum(1 for p in parts if p["group"] == "PROP"))

# ---------------------------------------------------------------- 출력
groups = {}
for p in parts:
    groups[p["group"]] = groups.get(p["group"], 0) + 1
# overdare_create_instances 용 20개 단위 청크
CH = 20
chunks = [parts[i:i+CH] for i in range(0, len(parts), CH)]
for i, ch in enumerate(chunks):
    json.dump(ch, open(os.path.join(OUT, "COL_chunk_%02d.json" % i), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
json.dump({"total": len(parts), "by_group": groups, "chunks": len(chunks), "parts": parts},
          open(os.path.join(ROOT, "collision_parts.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
open(os.path.join(OUT, "_log.txt"), "w", encoding="utf-8").write("\n".join(log))
P("TOTAL", len(parts), json.dumps(groups), "chunks", len(chunks))
