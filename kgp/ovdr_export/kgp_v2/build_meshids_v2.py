# -*- coding: utf-8 -*-
r"""임포트 뒤 에셋 id 해석. 정확 일치만 한다(v1 의 부분일치 fallback 은 442개 이름에서 위험하다).

Studio 의 에셋 이름 규칙 (2026-09-17 프로브·실측으로 확인):
  * FBX 에 메시가 여러 개면  ->  "<파일이름>_<메시오브젝트이름>_<YYYYMMDDHHMMSS>"
  * FBX 에 메시가 하나뿐이면 ->  "<파일이름>_<YYYYMMDDHHMMSS>"   (메시 이름이 안 붙는다)
  * 텍스처는 FBX 에 박힌 원본 이미지 이름을 쓴다 ("Color_<uuid>", "NormalGL_<uuid>").

사용:  python build_meshids_v2.py
출력:  meshids_v2.json  ·  unresolved.txt
"""
import io, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
STAMP = re.compile(r"_\d{14}$")
TOKEN = re.compile(r"(KGP2M\d{4})")

scene = json.load(io.open(os.path.join(HERE, "scene_v2.json"), encoding="utf-8"))
want, single = {}, {}
for f in scene["files"]:
    for m in f["meshes"]:
        want[m] = f["mat"]
    if len(f["meshes"]) == 1:
        single[f["stem"]] = f["meshes"][0]

raw = io.open(TBL, "rb").read()
txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
tbl = json.loads(txt)["localAssetList"]

before = set()
snap = os.path.join(HERE, "assets_before_v2.json")
if os.path.exists(snap):
    before = set(json.load(io.open(snap, encoding="utf-8"))["ids"])

cand = collections.defaultdict(list)
tex = {}
for cid, v in tbl.items():
    if before and cid in before:
        continue
    nm, ty, when = v.get("name", ""), v.get("worldAssetType"), v.get("createdTime", "")
    if ty == "STATIC_MESH":
        m = TOKEN.search(nm)
        if m:
            cand[m.group(1)].append((when, cid))
        else:
            stem = STAMP.sub("", nm)
            if stem in single:
                cand[single[stem]].append((when, cid))
    elif ty == "TEXTURE":
        tex[STAMP.sub("", nm)] = cid

dups = {k: v for k, v in cand.items() if len(v) > 1}
if dups:
    print("!! 중복 발행 %d건. 같은 메시가 여러 번 올라갔다(되돌릴 수 없다). 최신 것을 쓴다." % len(dups))
    for k in sorted(dups)[:5]:
        print("   ", k, dups[k])

uuid_of = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
out, missing = [], []
for m, matname in sorted(want.items()):
    lst = cand.get(m)
    if not lst:
        missing.append(m)
        continue
    rec = {"mesh": m, "meshId": max(lst)[1], "mat": matname}
    u = uuid_of.search(matname)
    if u:
        tid = tex.get("Color_" + u.group(1))
        if tid:
            rec["textureId"] = tid
    out.append(rec)

json.dump(out, io.open(os.path.join(HERE, "meshids_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("해석 %d / %d  (텍스처 붙은 것 %d)" % (len(out), len(want), sum(1 for r in out if r.get("textureId"))))
print("새 STATIC_MESH 총 %d개 -> 고유 메시 %d개" % (sum(len(v) for v in cand.values()), len(cand)))
up = os.path.join(HERE, "unresolved.txt")
if missing:
    io.open(up, "w", encoding="utf-8").write("\n".join(missing))
    print("!! 못 찾은 메시 %d개 -> unresolved.txt" % len(missing))
    sys.exit(1)
if os.path.exists(up):
    os.remove(up)
print("전부 해석됨")
