# -*- coding: utf-8 -*-
r"""5조각 기사상 임포트 뒤 : 기사 18체의 옛 2조각(_p0,_p1)을 새 5조각으로 바꾼다.

  * 에셋 이름 : 다중 메시 FBX 라 "KGP3_knight_parts_KGP3K000N_<YYYYMMDDHHMMSS>".
  * 새 파츠 90개(18 × 5)를 만들 items 파일과, 지울 옛 파츠 36개의 guid 를 뽑는다.
  * 텍스처는 v2 때 올라간 원본 컬러맵(46360300). 트라이포 메시는 열린 셸이라 DoubleSided.

출력 : knight_parts_items.json (overdare_create_instances itemsFile) · knight_old_guids.json
"""
import io, json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
TEX = "ovdrassetid://46360300"

spec = json.load(io.open(os.path.join(HERE, "knight_parts_place.json"), encoding="utf-8"))

raw = io.open(TBL, "rb").read()
txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
tbl = json.loads(txt)["localAssetList"]
found = collections.defaultdict(list)
for cid, v in tbl.items():
    m = re.fullmatch(r"KGP3_knight_parts_(KGP3K\d{4})_\d{14}", v.get("name", ""))
    if m and v.get("worldAssetType") == "STATIC_MESH":
        found[m.group(1)].append((v.get("createdTime", ""), cid))
ids = {}
for p in spec["pieces"]:
    lst = sorted(found.get(p["mesh"], []))
    if not lst:
        raise SystemExit("에셋 없음: %s — 임포트 먼저" % p["mesh"])
    if len(lst) > 1:
        print("!! %s 가 %d번 올라갔다. 최신 것을 쓴다." % (p["mesh"], len(lst)))
    ids[p["mesh"]] = "ovdrassetid://" + lst[-1][1]
print("assets:", ids)

items = []
for k in spec["place"]:
    p, y, sz = k["engine_pos"], k["yaw_deg"], k["size_cm"]
    items.append({"className": "MeshPart", "name": k["name"], "props": {
        "meshId": ids[k["mesh"]], "material": "Basic", "color": [200, 200, 200],
        "position": p, "orientation": [0.0, y, 0.0], "size": sz,
        "anchored": True, "mobility": "Static", "castShadow": True,
        "canCollide": False, "canQuery": False, "canTouch": False, "locked": False,
        "raw": {"TextureId": TEX, "DoubleSided": True}}})
io.open(os.path.join(HERE, "knight_parts_items.json"), "w", encoding="utf-8").write(json.dumps(items, indent=1))

s = open(PRJ, "rb").read().decode("utf-16-le")
if s[0] == "\ufeff":
    s = s[1:]
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
live = {c["Name"]: c["ActorGuid"] for c in cont["LuaChildren"]}
old = sorted({live[n] for k in spec["place"] for n in k["old"] if n in live})
io.open(os.path.join(HERE, "knight_old_guids.json"), "w", encoding="utf-8").write(json.dumps(old))
print("new parts %d · old parts to delete %d" % (len(items), len(old)))
