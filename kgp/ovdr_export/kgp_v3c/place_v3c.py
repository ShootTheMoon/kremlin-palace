# -*- coding: utf-8 -*-
r"""v3c 임포트 뒤 : 에셋 id 해석 -> 새 파츠 items + 베리·토피어리 제자리 교체 목록.

  에셋 이름 규칙 (v2·v3 실측과 같음)
    다중 메시 FBX -> "<파일이름>_<메시이름>_<YYYYMMDDHHMMSS>" / 단일 메시 -> "<파일이름>_<stamp>"
  텍스처
    * 베리·토피어리 : 이번에 이름을 바꿔 넣은 KGPTEX3B_* (새 에셋)
    * 나머지 재질   : v3 때 올라간 텍스처를 재질 이름으로 찾아 그대로 쓴다 (meshids_v3.json)
  역할별 속성
    static    : Basic + (200,200,200) + TextureId + DoubleSided(커브는 대개 열린 리본·관)
    door_leaf : 위와 같고 Movable — KgpGateServer 가 문짝과 같이 돌린다
    water     : 물방울. 텍스처 없이 물줄기(KGP2_WATER_jet)와 같은 색·재질·투명도, Movable
    retex     : 새로 만들지 않고 살아 있는 파츠의 MeshId·TextureId 만 바꾼다

    python place_v3c.py            (KGP_ASSET_TABLE 환경변수로 테이블 경로를 바꿀 수 있다)
출력 : items_v3c_NN.json (200개씩) · retex_update.json · meshids_v3c.json
"""
import io, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = os.environ.get("KGP_ASSET_TABLE", r"C:\Work\onlyonetap\UGCLocalAssetTable.json")
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
V3_IDS = os.path.join(HERE, "..", "kgp_v3", "meshids_v3.json")
STAMP = re.compile(r"_\d{14}$")
TOKEN = re.compile(r"(KGP3CM\d{4})")
RETEX = ("P3 berry red", "P3 topiary green")
CHUNK = 200


def safe(m):
    return "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in m)[:48]


def main():
    sc = json.load(io.open(os.path.join(HERE, "scene_v3c.json"), encoding="utf-8"))
    want, single = {}, {}
    for f in sc["files"]:
        for m in f["meshes"]:
            want[m] = f["mat"]
        if len(f["meshes"]) == 1:
            single[f["stem"]] = f["meshes"][0]

    raw = io.open(TBL, "rb").read()
    txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
    tbl = json.loads(txt)["localAssetList"]
    before = set(json.load(io.open(os.path.join(HERE, "assets_before_v3c.json"), encoding="utf-8"))["ids"])

    cand, tex_new = collections.defaultdict(list), {}
    for cid, v in tbl.items():
        if cid in before:
            continue
        nm, ty, when = v.get("name", ""), v.get("worldAssetType"), v.get("createdTime", "")
        if ty == "STATIC_MESH":
            m = TOKEN.search(nm)
            if m:
                cand[m.group(1)].append((when, cid))
            elif STAMP.sub("", nm) in single:
                cand[single[STAMP.sub("", nm)]].append((when, cid))
        elif ty == "TEXTURE":
            tex_new[STAMP.sub("", nm)] = cid

    tex_mat = {}
    for r in json.load(io.open(V3_IDS, encoding="utf-8")):
        if r.get("textureId"):
            tex_mat.setdefault(r["mat"], r["textureId"])
    for m in RETEX:
        tid = tex_new.get("KGPTEX3B_" + safe(m))
        if tid:
            tex_mat[m] = tid

    dups = {k: v for k, v in cand.items() if len(v) > 1}
    if dups:
        print("!! 중복 발행 %d건 — 최신 것을 쓴다" % len(dups))
    ids, missing = {}, []
    for m in want:
        if m in cand:
            ids[m] = max(cand[m])[1]
        else:
            missing.append(m)
    json.dump([{"mesh": m, "meshId": ids.get(m), "mat": want[m], "textureId": tex_mat.get(want[m])}
               for m in sorted(want)], io.open(os.path.join(HERE, "meshids_v3c.json"), "w", encoding="utf-8"), indent=1)
    print("메시 해석 %d / %d" % (len(ids), len(want)))
    if missing:
        print("!! 못 찾은 메시 %d개:" % len(missing), missing[:8])
        sys.exit(1)
    for m in RETEX:
        print("  %s 텍스처: %s" % (m, "새 에셋 " + tex_mat[m] if m in tex_mat and tex_mat[m] in tex_new.values() else "!! 못 찾음"))

    # 물줄기 파츠의 재질·색·투명도를 그대로 따른다
    s = open(PRJ, "rb").read().decode("utf-16-le")
    if s[0] == "\ufeff":
        s = s[1:]
    d = json.loads(s)
    def walk(n):
        yield n
        for c in n.get("LuaChildren", []) or []:
            yield from walk(c)
    cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
    live = {c["Name"]: c for c in cont["LuaChildren"]}
    jet = live.get("KGP2_WATER_jet")
    jet_mat = jet["Material"] if jet else "Neon"
    jet_col = [round(jet["Color"][k]) for k in "RGB"] if jet else [214, 242, 255]
    jet_tr = jet.get("Transparency", 0.45) if jet else 0.45

    items, retex, notex = [], [], collections.Counter()
    for i in sc["instances"]:
        mid = "ovdrassetid://" + ids[i["mesh"]]
        tid = tex_mat.get(i["mat"])
        if i["role"] == "retex":
            c = live.get(i["name"])
            if c is None:
                print("!! 재텍스처 대상 없음:", i["name"])
                continue
            retex.append({"guid": c["ActorGuid"], "props": {"MeshId": mid, "TextureId": "ovdrassetid://" + tid}})
            continue
        props = {"meshId": mid, "position": i["engine_pos"], "orientation": [0.0, i["yaw_deg"], 0.0],
                 "size": i["size_cm"], "anchored": True, "castShadow": True,
                 "canCollide": False, "canQuery": False, "canTouch": False, "locked": False,
                 "mobility": "Movable" if i["role"] in ("door_leaf", "water") else "Static"}
        if i["role"] == "water":
            props.update(material=jet_mat, color=jet_col, transparency=jet_tr)
            props["raw"] = {"DoubleSided": True}
        else:
            props.update(material="Basic", color=[200, 200, 200])
            props["raw"] = {"DoubleSided": True}
            if tid:
                props["raw"]["TextureId"] = "ovdrassetid://" + tid
            else:
                notex[i["mat"]] += 1
        items.append({"className": "MeshPart", "name": i["name"], "props": props})

    for f in os.listdir(HERE):
        if f.startswith("items_v3c_"):
            os.remove(os.path.join(HERE, f))
    for k in range(0, len(items), CHUNK):
        io.open(os.path.join(HERE, "items_v3c_%02d.json" % (k // CHUNK)), "w", encoding="utf-8").write(
            json.dumps(items[k:k + CHUNK], ensure_ascii=False, indent=1))
    io.open(os.path.join(HERE, "retex_update.json"), "w", encoding="utf-8").write(
        json.dumps(retex, separators=(",", ":")))
    roles = collections.Counter(i["role"] for i in sc["instances"])
    print("새 파츠 %d (%s) · 제자리 교체 %d · 묶음 %d" % (len(items), dict(roles), len(retex),
                                                  (len(items) + CHUNK - 1) // CHUNK))
    if notex:
        print("!! 텍스처 없는 재질:", dict(notex))


if __name__ == "__main__":
    main()
