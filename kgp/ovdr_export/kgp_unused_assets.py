# -*- coding: utf-8 -*-
r"""크렘린 대궁전 작업에서 올린 에셋 중 게임(레벨)이 더 이상 참조하지 않는 것 목록.

에셋 이름 접두 KGP (KGP_, KGP2_, KGP3*, KGPTEX*) 인 STATIC_MESH / TEXTURE 를 모으고,
레벨 전체의 MeshId · TextureId 문자열과 대조한다. 에셋 삭제 API 가 없어서 지우지는 않는다 —
스튜디오 에셋 관리자에서 사람이 지워야 한다.

    python kgp_unused_assets.py   ->  kgp_unused_assets.md / .json
"""
import io, json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"

raw = open(TBL, "rb").read()
txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
tbl = json.loads(txt)["localAssetList"]
lvl = open(PRJ, "rb").read().decode("utf-16-le")
used = set(re.findall(r"ovdrassetid://(\d+)", lvl))

rows = []
for cid, v in tbl.items():
    nm = v.get("name", "")
    if not nm.startswith("KGP"):
        continue
    rows.append({"id": cid, "name": nm, "type": v.get("worldAssetType"), "created": v.get("createdTime", ""),
                 "used": cid in used})
unused = [r for r in rows if not r["used"]]
by = collections.Counter((r["type"], r["used"]) for r in rows)


def family(n):
    for p in ("KGPTEX5", "KGPTEX3B", "KGPTEX3", "KGPTEX", "KGP3SM", "KGP3S", "KGP3EM", "KGP3E", "KGP3CM", "KGP3C", "KGP3K", "KGP3", "KGP2", "KGP_"):
        if n.startswith(p):
            return p
    return "KGP?"


fam = collections.Counter((family(r["name"]), r["type"]) for r in unused)
lines = ["# 크렘린 대궁전 — 안 쓰는 에셋 목록", "",
         "레벨이 참조하지 않는 KGP 계열 에셋. 에셋 삭제 API 가 없어 스튜디오 에셋 관리자에서 직접 지워야 한다.",
         "", "| 구분 | 개수 |", "|---|---|"]
for (t, u), n in sorted(by.items()):
    lines.append("| %s %s | %d |" % (t, "사용 중" if u else "안 씀", n))
lines += ["", "## 안 쓰는 것 (계열별)", "", "| 계열 | 종류 | 개수 |", "|---|---|---|"]
for (f, t), n in sorted(fam.items()):
    lines.append("| %s | %s | %d |" % (f, t, n))
lines += ["", "## 전체 목록", "", "| contentId | 이름 | 종류 | 만든 때 |", "|---|---|---|---|"]
for r in sorted(unused, key=lambda r: r["created"]):
    lines.append("| %s | %s | %s | %s |" % (r["id"], r["name"], r["type"], r["created"]))
io.open(os.path.join(HERE, "kgp_unused_assets.md"), "w", encoding="utf-8").write("\n".join(lines))
json.dump(unused, io.open(os.path.join(HERE, "kgp_unused_assets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("KGP assets", len(rows), "| used", len(rows) - len(unused), "| unused", len(unused))
for (t, u), n in sorted(by.items()):
    print(" ", t, "used" if u else "unused", n)
for (f, t), n in sorted(fam.items()):
    print("   unused", f, t, n)
