import bpy, sys, os, math
from collections import deque

SC = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch"
PX = 1024
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CODEFILE = argv[0] if argv else os.path.join(SC, 'mat_code.py')
TAG = argv[1] if len(argv) > 1 else 'v2'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.render.bake.margin = 16
scene.render.bake.use_clear = True

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
ob = bpy.context.active_object
if not ob.data.uv_layers:
    ob.data.uv_layers.new(name='UVMap')

src = open(CODEFILE, 'r', encoding='utf-8').read()


def build(name):
    mat = bpy.data.materials.new(name)
    g = {'bpy': bpy, 'mat': mat}
    exec(compile(src, CODEFILE, 'exec'), g)
    return mat


def find(mat, label):
    for n in mat.node_tree.nodes:
        if n.label == label:
            return n
    return None


def bake(mat, float_buf):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    img = bpy.data.images.new('bk_' + mat.name, PX, PX, alpha=False, float_buffer=float_buf)
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    mat.node_tree.nodes.active = tex
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
    return img


def quant(vals, qs):
    s = sorted(vals)
    n = len(s)
    return [s[min(n - 1, int(q * n))] for q in qs]


# ---------- probe a scalar signal (linear floats) ----------
def probe(label, title):
    mat = build('probe_' + label)
    node = find(mat, label)
    bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    for l in list(mat.node_tree.links):
        if l.to_node == bsdf and l.to_socket.name == 'Base Color':
            mat.node_tree.links.remove(l)
    mat.node_tree.links.new(node.outputs[0], bsdf.inputs['Base Color'])
    img = bake(mat, True)
    px = list(img.pixels)
    v = px[0::4]
    n = len(v)
    mean = sum(v) / n
    sd = (sum((x - mean) ** 2 for x in v) / n) ** 0.5
    qs = [0.01, 0.05, 0.10, 0.20, 0.25, 0.35, 0.50, 0.65, 0.75, 0.80, 0.90, 0.95, 0.99]
    qv = quant(v, qs)
    print('--- %s (%s) n=%d' % (title, label, n))
    print('    mean %.4f  sd %.4f  min %.4f  max %.4f' % (mean, sd, min(v), max(v)))
    print('    ' + '  '.join('p%02d=%.4f' % (int(q * 100), x) for q, x in zip(qs, qv)))
    return v


# ---------- count fleck blobs toroidally ----------
def blobs(v, thr=0.5):
    w = PX
    seen = bytearray(w * w)
    on = bytearray(1 if x > thr else 0 for x in v)
    cov = sum(on) / float(w * w)
    cnt = 0
    areas = []
    for i in range(w * w):
        if on[i] and not seen[i]:
            cnt += 1
            a = 0
            dq = deque([i])
            seen[i] = 1
            while dq:
                p = dq.popleft()
                a += 1
                y, x = divmod(p, w)
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    q = (ny % w) * w + (nx % w)
                    if on[q] and not seen[q]:
                        seen[q] = 1
                        dq.append(q)
            areas.append(a)
    return cnt, cov, areas


# ---------- final colour bake ----------
def final():
    mat = build('final_' + TAG)
    img = bake(mat, False)
    p = os.path.join(SC, '_out', 'Sapphire_stone_%s.png' % TAG)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    print('saved', p)


def final_fit(gvals, qs_ramp=(0.04, 0.18, 0.42, 0.68, 0.96, 0.999), qs_cl=(0.35, 0.85)):
    pos = quant(gvals, qs_ramp)
    cl = quant(gvals, qs_cl)
    mat = build('fit_' + TAG)
    cr = find(mat, 'RAMP')
    els = cr.color_ramp.elements
    print('    RAMP stops -> ' + ', '.join('%.4f' % x for x in pos[:len(els)]))
    order = sorted(range(len(els)), key=lambda i: els[i].position)
    for k, i in enumerate(order):
        els[i].position = pos[min(k, len(pos) - 1)]
    r3 = find(mat, 'CLUSTER')
    if r3 is not None:
        print('    CLUSTER From Min %.4f  From Max %.4f' % (cl[0], cl[1]))
        r3.inputs['From Min'].default_value = cl[0]
        r3.inputs['From Max'].default_value = cl[1]
    img = bake(mat, False)
    p = os.path.join(SC, '_out', 'Sapphire_stone_%s.png' % TAG)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    print('saved', p)


mode = argv[2] if len(argv) > 2 else 'all'
G = None
if mode in ('all', 'probe', 'fit'):
    G = probe('GROUND', 'ground signal m2')
    fm = probe('FLECKMASK', 'fleck mask m5')
    tile_m = 3.0
    for thr in (0.05, 0.28, 0.5):
        c, cov, areas = blobs(fm, thr)
        areas.sort()
        med = areas[len(areas) // 2] if areas else 0
        d = 2 * (med / math.pi) ** 0.5
        big = areas[int(len(areas) * 0.9)] if areas else 0
        db = 2 * (big / math.pi) ** 0.5
        print('    thr %.2f: %d blobs/tile = %.2f per m2, cov %.4f, median d %.1fpx=%.1fcm, p90 d %.1fpx=%.1fcm'
              % (thr, c, c / (tile_m * tile_m), cov, d, d / PX * tile_m * 100, db, db / PX * tile_m * 100))
if mode == 'fit':
    final_fit(G)
if mode in ('all', 'final'):
    final()
