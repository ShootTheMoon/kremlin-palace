# -*- coding: utf-8 -*-
r"""scene_dump.json -> OVERDARE 배치 JSON (산곡/화성/KRM 형식 그대로). Blender 불필요.

Usage:
    python kgp_place.py                         # 콜리전만 (임포트 전에 바로 쓸 수 있다)
    python kgp_place.py meshids.json            # 벌크 임포트 결과로 메시 배치까지
    python kgp_place.py UGCLocalAssetTable.json # 에셋 테이블에서 이름으로 ID 해석

meshids.json 형식 (overdare_mesh_bulk_import 결과를 그대로 저장해도 된다):
    [{"asset": "KGP_S_...", "meshId": "ovdrassetid://123", "textureId": "ovdrassetid://124"}, ...]

출력: items_col_00.json, items_static_00.json..., items_master_00.json..., unresolved.txt
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DUMP = os.path.join(HERE, "scene_dump.json")
CHUNK = 200                      # overdare_create_instances itemsFile 한도

# locked 는 False 로 둔다. True 면 Studio 뷰포트에서 클릭 선택이 안 된다
# (2026-09-17 : 전부 True 로 넣었다가 맵 손볼 때 아무것도 못 집어서 풀었다).

# ★ 블렌더 -> OVERDARE 축 보정. Studio 의 FBX 임포터는 axis_forward='-Z' 를 그대로 받지 않아
#   메시 내용이 세로축 기준으로 180도(90도 두 번) 돌아서 들어온다. 좌우 방향만 틀어지고
#   위아래는 맞다. 2026-09-17 대궁전 임포트에서 실측하고 전 메시에 +180 을 넣어 맞췄다.
#   콜리전 Part 는 엔진 좌표로 직접 만든 것이라 건드리지 않는다.
MESH_YAW_FIX = 180.0


def load_dump():
    return json.load(io.open(DUMP, encoding="utf-8"))



def shift(d):
    """KGP_X0 / KGP_Z0 가 있으면 전체를 그 원점으로 평행이동한다(회전 없음).
    2026-09-17: 옛 크렘린 실내(KRM)를 지우고 그 자리(X 100650, Z 0)에 앉히려고 넣었다."""
    x0 = os.environ.get("KGP_X0")
    z0 = os.environ.get("KGP_Z0")
    dx = float(x0) - d["x0_cm"] if x0 else 0.0
    dz = float(z0) - d["z0_cm"] if z0 else 0.0
    if dx or dz:
        for grp in ("statics", "instances", "collision"):
            for it in d[grp]:
                p = it["engine_pos"]
                p[0] = round(p[0] + dx, 1)
                p[2] = round(p[2] + dz, 1)
        d["x0_cm"] += dx
        d["z0_cm"] += dz
    return d, dx, dz


def load_ids(path):
    """meshids.json (벌크 임포트 결과) 또는 UGCLocalAssetTable.json 을 받는다."""
    if not path or not os.path.exists(path):
        return {}, {}
    raw = io.open(path, "rb").read()
    txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
    data = json.loads(txt)
    mesh, tex = {}, {}
    if isinstance(data, list):                               # bulk import result
        for r in data:
            name = r.get("asset") or r.get("name") or ""
            if r.get("meshId"):
                mesh[name] = str(r["meshId"])
            if r.get("textureId"):
                tex[name] = str(r["textureId"])
        return mesh, tex
    table = data.get("localAssetList", {})                   # UGCLocalAssetTable
    by_mesh, by_tex = {}, {}
    for cid, v in table.items():
        nm, when = v.get("name", ""), v.get("createdTime", "")
        if v.get("worldAssetType") == "STATIC_MESH":
            by_mesh.setdefault(nm, []).append((when, int(cid)))
        elif v.get("worldAssetType") == "TEXTURE":
            by_tex.setdefault(nm, []).append((when, int(cid)))
    mesh = {k: str(max(v)[1]) for k, v in by_mesh.items()}   # 이름이 겹치면 가장 최근 것
    tex = {k: str(max(v)[1]) for k, v in by_tex.items()}
    return mesh, tex


def resolve(name, ids):
    """벌크 임포트는 에셋 이름을 <번들>_<메시> 로 붙이므로 접미 일치도 받아준다."""
    if name in ids:
        return ids[name]
    for k, v in ids.items():
        if k.endswith(name) or name in k:
            return v
    return ""


def asset_id(v):
    return v if (not v or v.startswith("ovdrassetid://")) else "ovdrassetid://" + v


def mesh_item(name, colour, pos, size, yaw, mesh_id, tex_id):
    yaw = round(((yaw + MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 1)   # 축 보정 포함
    props = {
        "meshId": asset_id(mesh_id), "material": "Basic", "color": colour,
        "position": pos, "orientation": [0.0, yaw, 0.0], "size": size,
        "anchored": True, "mobility": "Static", "castShadow": True,
        "canCollide": False, "canQuery": False, "canTouch": False, "locked": False,
    }
    if tex_id:
        props["raw"] = {"TextureId": asset_id(tex_id)}
    return {"className": "MeshPart", "name": name, "props": props}


def collision_items(d):
    """MeshPart 에는 CollisionFidelity 가 없다. 걷는 면과 레이캐스트는 전부 이 투명 Part 가 맡는다."""
    out = []
    for i, c in enumerate(d["collision"]):
        out.append({"className": "Part", "name": "KGP_COL_%s_%03d" % (c["name"], i),
                    "props": {"position": c["engine_pos"], "size": c["size_cm"],
                              "orientation": [0.0, c["yaw_deg"], 0.0],
                              "anchored": True, "mobility": "Static", "transparency": 1,
                              "canCollide": True, "canQuery": True, "canTouch": False,
                              "castShadow": False, "locked": False, "material": "Plastic"}})
    return out


def static_items(d, mesh_ids, tex_ids, unresolved):
    out = []
    for s in d["statics"]:
        mid = resolve(s["name"], mesh_ids)
        if not mid:
            unresolved.add(s["name"])
        out.append(mesh_item(s["name"], s["colour"], s["engine_pos"], s["size_cm"], 0.0,
                             mid, resolve(s["name"], tex_ids)))
    return out


def master_items(d, mesh_ids, tex_ids, unresolved):
    out = []
    for inst in d["instances"]:
        m = d["masters"][inst["master"]]
        mid = resolve(inst["master"], mesh_ids)
        if not mid:
            unresolved.add(inst["master"])
        sc = inst.get("scale", 1.0)
        size = [round(v * sc, 1) for v in m["size_cm"]]
        out.append(mesh_item(inst["name"], m["colour"], inst["engine_pos"], size,
                             inst["yaw_deg"], mid, resolve(inst["master"], tex_ids)))
    return out


def write(tag, items):
    paths = []
    for i in range(0, len(items), CHUNK):
        p = os.path.join(HERE, "items_%s_%02d.json" % (tag, i // CHUNK))
        json.dump(items[i:i + CHUNK], io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        paths.append((os.path.basename(p), len(items[i:i + CHUNK])))
    return paths


if __name__ == "__main__":
    d, dx, dz = shift(load_dump())
    if dx or dz:
        print("shifted  dx %+.1f  dz %+.1f" % (dx, dz))
    mesh_ids, tex_ids = load_ids(sys.argv[1] if len(sys.argv) > 1 else None)
    unresolved = set()
    made = []
    made += write("col", collision_items(d))
    if mesh_ids:
        made += write("static", static_items(d, mesh_ids, tex_ids, unresolved))
        made += write("master", master_items(d, mesh_ids, tex_ids, unresolved))
    for name, n in made:
        print("%-24s %4d items" % (name, n))
    if unresolved:
        io.open(os.path.join(HERE, "unresolved.txt"), "w", encoding="utf-8").write("\n".join(sorted(unresolved)))
        print("!! %d assets without an id -> unresolved.txt" % len(unresolved))
    print("container:", d.get("container"), " x0:", d["x0_cm"], " z0:", d["z0_cm"])
