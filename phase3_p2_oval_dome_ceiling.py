"""3차 P2: 레퍼런스 타원 돔 천장 (뒤 절반 y=0, 앞 절반 y=-28 두 벌).

평천장(12.0~12.3m)에 타원 구멍을 내고 청·백·금 계단식 띠 3단으로 올라가 얕은 돔과 중앙 채광창(트레이서리)으로 닫는다.
평천장 네 모서리와 긴 변에 금장 아칸서스 스크롤, 가장자리 청색 띠.
옛 천장(05, 10 컬렉션과 14의 천장 복제본)은 30x 숨김 컬렉션으로 옮긴다. 샹들리에·조명은 건드리지 않는다.
재실행하면 35 컬렉션을 비우고 다시 만든다. 위에서 볼 때는 35 컬렉션을 숨긴다.
"""
import bpy, bmesh, math
from math import sin, cos, pi, atan2

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
sky = M.get('P3 skylight sky')
if sky is None:
    sky = M.new('P3 skylight sky'); sky.use_nodes = True
pn = sky.node_tree.nodes.get('Principled BSDF')
pn.inputs['Base Color'].default_value = (.55, .76, .96, 1)
pn.inputs['Emission Color'].default_value = (.62, .8, 1, 1)
pn.inputs['Emission Strength'].default_value = 1.6
sky.diffuse_color = (.55, .76, .96, 1)

HIDDEN = '30x | P3 replaced originals (hidden)'
C_CEIL = '35 | P3 - Oval dome ceilings'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
coll = ensure_coll(C_CEIL)
parked = []


def park(o):
    if hidden in o.users_collection:
        return
    o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hidden.objects.link(o)
    parked.append(o.name)


for cname in ('05 | Coffered ceiling crown', '10 | Removable ornamental ceiling'):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects):
            park(o)
c14 = bpy.data.collections.get('14 | NEW HALF - Ceiling and chandeliers')
if c14:
    for o in list(c14.objects):
        n = o.name.lower()
        if o.type in {'MESH', 'CURVE'} and any(t in n for t in ('ceiling', 'medallion', 'petal', 'relief', 'rosette', 'coffer')):
            park(o)


def mesh_obj(name, bm, mats, smooth=False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def curves(name, splines, r, mat, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2 if r >= .03 else 1
    cu.resolution_u = 1; cu.use_fill_caps = True
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for v, p in zip(sp.points, pts):
            v.co = (*p, 1)
        sp.use_cyclic_u = closed
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    return o


NS = 144
ANG = [2 * pi * i / NS for i in range(NS)]


def ell_ring(cy, rx, ry, z, n=NS):
    return [(rx * cos(2 * pi * i / n), cy + ry * sin(2 * pi * i / n), z) for i in range(n)]


def band(name, cy, a, b, mat, smooth=True):
    """Surface between ellipse a=(rx,ry,z) and b=(rx,ry,z)."""
    bm = bmesh.new()
    va = [bm.verts.new((a[0] * cos(t), cy + a[1] * sin(t), a[2])) for t in ANG]
    vb = [bm.verts.new((b[0] * cos(t), cy + b[1] * sin(t), b[2])) for t in ANG]
    for i in range(NS):
        j = (i + 1) % NS
        bm.faces.new((va[i], va[j], vb[j], vb[i]))
    return mesh_obj(name, bm, [mat], smooth)


def ell_frame(theta, rx, ry):
    """Point, unit tangent and unit inward normal on an ellipse."""
    px, py = rx * cos(theta), ry * sin(theta)
    tx, ty = -rx * sin(theta), ry * cos(theta)
    tl = math.hypot(tx, ty); tx, ty = tx / tl, ty / tl
    return px, py, tx, ty, ty, -tx   # inward normal = tangent rotated -90 deg for CCW ellipse


def scroll_splines(pos_fn, w):
    out = []
    for sign in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29 * 2.5 * pi; rr = w * (1 - i / 36)
            pts.append(pos_fn(sign * (w * .8 + rr * cos(t)), rr * sin(t) * .45))
        out.append(pts)
    return out


def spiral(cx, cy, z, r_out, turns, start, direction, n=40):
    return [(cx + r_out * (1 - .8 * t) * cos(start + direction * turns * 2 * pi * t),
             cy + r_out * (1 - .8 * t) * sin(start + direction * turns * 2 * pi * t), z) for t in [i / (n - 1) for i in range(n)]]


_rhombus = None


def rhombus_mesh():
    global _rhombus
    if _rhombus is None:
        _rhombus = bpy.data.meshes.get('P3_unit_rhombus_Sapphire')
        if _rhombus is None:
            bm = bmesh.new()
            vs = [bm.verts.new(p) for p in ((1, -1, 0), (0, -1, 1), (-1, -1, 0), (0, -1, -1), (1, 1, 0), (0, 1, 1), (-1, 1, 0), (0, 1, -1))]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                bm.faces.new([vs[k] for k in f])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            _rhombus = bpy.data.meshes.new('P3_unit_rhombus_Sapphire'); bm.to_mesh(_rhombus); bm.free()
            _rhombus.materials.append(blue)
    return _rhombus


HALF_X, HALF_Y = 16.0, 14.0
Z0 = 12.0
E1 = (10.2, 9.0)   # oval opening in the flat ceiling
E2 = (9.6, 8.4)
E3 = (9.0, 7.8)
E4 = (8.4, 7.2)    # dome springing line
E5 = (4.6, 3.9)    # skylight opening

for cy, tag in ((0.0, 'rear'), (-28.0, 'front')):
    # --- flat ceiling slab with oval opening
    corner_angles = [atan2(sy * HALF_Y, sx * HALF_X) % (2 * pi) for sx in (-1, 1) for sy in (-1, 1)]
    angles = sorted(set([round(a, 9) for a in ANG + corner_angles]))
    bm = bmesh.new(); ib, ob, it, ot = [], [], [], []
    for th in angles:
        c, s = cos(th), sin(th)
        t = min(HALF_X / abs(c) if abs(c) > 1e-9 else 1e9, HALF_Y / abs(s) if abs(s) > 1e-9 else 1e9)
        ix, iy, ox, oy = E1[0] * c, E1[1] * s, c * t, s * t
        ib.append(bm.verts.new((ix, cy + iy, Z0))); ob.append(bm.verts.new((ox, cy + oy, Z0)))
        it.append(bm.verts.new((ix, cy + iy, Z0 + .3))); ot.append(bm.verts.new((ox, cy + oy, Z0 + .3)))
    n = len(angles)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
        bm.faces.new((it[i], ot[i], ot[j], it[j]))
    mesh_obj('P3 ceiling flat slab %s' % tag, bm, [white])

    # --- stepped oval recess
    band('P3 ceiling step1 sapphire fascia %s' % tag, cy, (*E1, Z0), (*E1, 12.6), blue)
    band('P3 ceiling step1 ledge %s' % tag, cy, (*E1, 12.6), (*E2, 12.6), white)
    band('P3 ceiling step2 marble fascia %s' % tag, cy, (*E2, 12.6), (*E2, 13.5), white)
    band('P3 ceiling step2 gilt ledge %s' % tag, cy, (*E2, 13.5), (*E3, 13.5), gold)
    band('P3 ceiling step3 sapphire fascia %s' % tag, cy, (*E3, 13.5), (*E3, 14.0), blue)
    band('P3 ceiling step3 ledge %s' % tag, cy, (*E3, 14.0), (*E4, 14.0), white)
    curves('P3 ceiling step gilt rings %s' % tag,
           [ell_ring(cy, E1[0] - .02, E1[1] - .02, 12.03), ell_ring(cy, E1[0] - .02, E1[1] - .02, 12.57),
            ell_ring(cy, E2[0] - .02, E2[1] - .02, 12.7), ell_ring(cy, E2[0] - .02, E2[1] - .02, 13.4),
            ell_ring(cy, E3[0] - .02, E3[1] - .02, 13.52), ell_ring(cy, E4[0] - .02, E4[1] - .02, 14.02)],
           .035, gold, True)
    curves('P3 ceiling gilt rope ring %s' % tag, [ell_ring(cy, E2[0] - .04, E2[1] - .04, 13.47)], .065, gold, True)

    # Step 2 frieze: scroll pairs alternating with sapphire diamonds.
    scr = []
    K = 36
    for k in range(K):
        th = 2 * pi * k / K
        px, py, tx, ty, nx, ny = ell_frame(th, E2[0], E2[1])
        ox, oy = px + nx * .03, py + ny * .03
        scr += scroll_splines(lambda dt, dz, ox=ox, oy=oy, tx=tx, ty=ty: (ox + tx * dt, cy + oy + ty * dt, 13.05 + dz), .26)
        th2 = th + pi / K
        px, py, tx, ty, nx, ny = ell_frame(th2, E2[0], E2[1])
        d = bpy.data.objects.new('P3 ceiling frieze sapphire diamond %s' % tag, rhombus_mesh()); coll.objects.link(d)
        d.location = (px + nx * .04, cy + py + ny * .04, 13.05); d.scale = (.17, .025, .2)
        d.rotation_euler = (0, 0, atan2(ty, tx))
    curves('P3 ceiling frieze gilt scrolls %s' % tag, scr, .02, gold)

    # --- shallow dome with skylight opening
    bm = bmesh.new(); rings = []
    KD = 10
    for k in range(KD + 1):
        f = k / KD
        rx = E4[0] + (E5[0] - E4[0]) * f; ry = E4[1] + (E5[1] - E4[1]) * f; z = 14.0 + 1.0 * sin(f * pi / 2)
        rings.append([bm.verts.new((rx * cos(t), cy + ry * sin(t), z)) for t in ANG])
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(NS):
            j = (i + 1) % NS
            bm.faces.new((a_[i], a_[j], b_[j], b_[i]))
    mesh_obj('P3 ceiling dome marble %s' % tag, bm, [white], smooth=True)

    def dome_pt(f, th, drop=.03):
        rx = E4[0] + (E5[0] - E4[0]) * f; ry = E4[1] + (E5[1] - E4[1]) * f
        return (rx * cos(th), cy + ry * sin(th), 14.0 + sin(f * pi / 2) - drop)

    curves('P3 ceiling dome gilt ribs %s' % tag, [[dome_pt(f / 12, 2 * pi * r / 16) for f in range(13)] for r in range(16)], .03, gold)
    curves('P3 ceiling dome gilt mid ring %s' % tag, [[dome_pt(.5, t) for t in ANG]], .03, gold, True)
    scr = []
    for r in range(16):
        th = 2 * pi * (r + .5) / 16
        for f in (.27, .74):
            p0 = dome_pt(f, th, .04)
            px, py, tx, ty, nx, ny = ell_frame(th, 1, 1)
            scr += scroll_splines(lambda dt, dz, p0=p0, tx=tx, ty=ty, nx=nx, ny=ny: (p0[0] + tx * dt - nx * dz, p0[1] + ty * dt - ny * dz, p0[2]), .32 if f < .5 else .22)
    curves('P3 ceiling dome gilt scrolls %s' % tag, scr, .02, gold)

    # --- skylight: emissive sky panel behind white-and-gold tracery
    bm = bmesh.new()
    centre = bm.verts.new((0, cy, 15.08))
    rim = [bm.verts.new((E5[0] * 1.04 * cos(t), cy + E5[1] * 1.04 * sin(t), 15.08)) for t in ANG]
    for i in range(NS):
        bm.faces.new((centre, rim[i], rim[(i + 1) % NS]))
    mesh_obj('P3 ceiling skylight sky panel %s' % tag, bm, [sky])
    lobes, outlines = [], []
    lobes.append(ell_ring(cy, E5[0] - .05, E5[1] - .05, 15.0, 96))
    lobes.append(ell_ring(cy, 1.15, .98, 15.0, 48))
    for k in range(8):
        a0 = 2 * pi * k / 8
        cxk, cyk = 2.85 * cos(a0), 2.4 * sin(a0)
        pts = [(cxk + 1.25 * cos(t) * cos(a0) - .72 * sin(t) * sin(a0), cy + cyk + 1.25 * cos(t) * sin(a0) + .72 * sin(t) * cos(a0), 15.0) for t in [q * 2 * pi / 40 for q in range(40)]]
        lobes.append(pts)
        outlines.append([(p[0] * 1.0, p[1], 14.96) for p in pts])
        cxk2, cyk2 = 3.9 * cos(a0 + pi / 8), 3.3 * sin(a0 + pi / 8)
        lobes.append([(cxk2 + .32 * cos(t), cy + cyk2 + .32 * sin(t), 15.0) for t in [q * 2 * pi / 20 for q in range(20)]])
    curves('P3 ceiling skylight marble tracery %s' % tag, lobes, .075, white, True)
    curves('P3 ceiling skylight gilt tracery outline %s' % tag, outlines + [ell_ring(cy, 1.15, .98, 14.95, 48)], .022, gold, True)

    # --- flat ceiling ornament: sapphire perimeter band, gilt lines, acanthus corners and side cartouches
    bm = bmesh.new()
    outer = [(-15.7, cy - 13.7), (15.7, cy - 13.7), (15.7, cy + 13.7), (-15.7, cy + 13.7)]
    inner = [(-14.9, cy - 12.9), (14.9, cy - 12.9), (14.9, cy + 12.9), (-14.9, cy + 12.9)]
    vo = [bm.verts.new((x, y, Z0 - .012)) for x, y in outer]; vi = [bm.verts.new((x, y, Z0 - .012)) for x, y in inner]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    mesh_obj('P3 ceiling sapphire perimeter band %s' % tag, bm, [blue])
    curves('P3 ceiling perimeter gilt lines %s' % tag,
           [[(x, y, Z0 - .02) for x, y in outer], [(x, y, Z0 - .02) for x, y in inner],
            [(x * .97, cy + (y - cy) * .96, Z0 - .02) for x, y in inner]], .03, gold, True)
    corner, side = [], []
    zc = Z0 - .04
    for sx in (-1, 1):
        for sy in (-1, 1):
            # Over the gallery bays (x 12.3-15.5), clear of the column entablature at x +-11.45..12.15.
            ox, oy = sx * 13.9, cy + sy * 10.3
            base_ang = atan2(-sy, -sx)
            corner.append(spiral(ox, oy, zc, 1.35, 1.2, base_ang, sx * sy))
            corner.append(spiral(ox, oy - sy * 2.3, zc, .8, 1.1, base_ang + pi, -sx * sy))
            corner.append(spiral(ox + sx * .2, oy + sy * 1.95, zc, .45, 1.0, base_ang + pi / 2, -sx * sy))
            corner.append([(ox, oy - sy * (1.35 + 2.2 * t), zc) for t in (0, 1)])
        # long-side cartouche over the gallery
        for sy in (-1, 1):
            side.append(spiral(sx * 13.9, cy + sy * 1.0, zc, 1.0, 1.15, sy * pi / 2, sx * sy))
        side.append([(sx * 13.9, cy + y, zc) for y in (-2.2, 2.2)])
    for sy in (-1, 1):
        for sx in (-1, 1):
            side.append(spiral(sx * 1.2, cy + sy * 11.2, zc, .95, 1.15, 0 if sx > 0 else pi, sx * sy))
    curves('P3 ceiling gilt acanthus corners %s' % tag, corner, .08, gold)
    curves('P3 ceiling gilt acanthus corners inner %s' % tag, [[(p[0], p[1], p[2] - .01) for p in s_] for s_ in corner], .025, gold)
    curves('P3 ceiling gilt side cartouches %s' % tag, side, .05, gold)
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d = bpy.data.objects.new('P3 ceiling cartouche sapphire diamond %s' % tag, rhombus_mesh()); coll.objects.link(d)
        d.location = (sx * 13.9, cy + sy * 11.2, Z0 - .05); d.scale = (.35, .03, .45); d.rotation_euler = (pi / 2, 0, 0)

result = {'ceiling_objects': len(coll.objects), 'parked': len(parked), 'scene_objects': len(sc.objects)}
print('P3_P2_RESULT', result)
