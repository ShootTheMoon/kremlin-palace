# -*- coding: utf-8 -*-
r"""임포트 뒤 에셋 id 해석 (v3). 정확 일치만 한다.

Studio 의 에셋 이름 규칙 (2026-09-17 프로브·실측으로 확인):
  * FBX 에 메시가 여러 개면  ->  "<파일이름>_<메시오브젝트이름>_<YYYYMMDDHHMMSS>"
  * FBX 에 메시가 하나뿐이면 ->  "<파일이름>_<YYYYMMDDHHMMSS>"   (메시 이름이 안 붙는다)
  * 텍스처는 FBX 에 박힌 이미지 이름을 쓴다.

v2 와 다른 점 : v2 는 텍스처가 트라이포 소품 2개뿐이라 "Color_<uuid>" 로만 찾았다.
v3 는 재질 22개가 전부 구운 타일을 갖고, 이름이 "KGPTEX3_<재질이름>" 이다.
트라이포 2종만 원본 컬러맵("Color_<uuid>")을 그대로 쓴다 — 굽지도 UV 도 안 건드렸다.

사용:  python build_meshids_v3.py
출력:  meshids_v3.json  ·  unresolved.txt
"""
import io
import json
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = os.environ.get("KGP_ASSET_TABLE",
                     r"C:\Work\onlyonetap\UGCLocalAssetTable.json")
STAMP = re.compile(r"_\d{14}$")
TOKEN = re.compile(r"(KGP3M\d{4})")
UUID = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


def safe_tex_name(mat_name):
    """kgp_v3_texture.bake_tiles 가 쓰는 것과 같은 규칙."""
    s = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in mat_name)[:48]
    return "KGPTEX3_" + s


def main():
    scene = json.load(io.open(os.path.join(HERE, "scene_v3.json"), encoding="utf-8"))
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
    snap = os.path.join(HERE, "assets_before_v3.json")
    if os.path.exists(snap):
        before = set(json.load(io.open(snap, encoding="utf-8"))["ids"])
    else:
        print("!! assets_before_v3.json 이 없다. 임포트 전에 스냅샷을 찍어두면 v2 에셋과 "
              "섞이지 않는다. 지금은 KGP3 접두로만 거른다.")

    # 트라이포 소품 2종은 v3 에서 손대지 않았으니 v2 때 올라간 원본 컬러맵을 그대로 쓴다.
    # 그래서 텍스처는 '전체 테이블'에서 이름별 최신 것을 따로 모아 둔다.
    tex_all = {}
    for cid, v in tbl.items():
        if v.get("worldAssetType") == "TEXTURE":
            k = STAMP.sub("", v.get("name", ""))
            when = v.get("createdTime", "")
            if k not in tex_all or when > tex_all[k][0]:
                tex_all[k] = (when, cid)
    tex_all = {k: v[1] for k, v in tex_all.items()}

    cand = collections.defaultdict(list)
    tex = {}
    for cid, v in tbl.items():
        if before and cid in before:
            continue
        nm = v.get("name", "")
        ty = v.get("worldAssetType")
        when = v.get("createdTime", "")
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
        print("!! 중복 발행 %d건. 같은 메시가 여러 번 올라갔다(되돌릴 수 없다). 최신 것을 쓴다."
              % len(dups))
        for k in sorted(dups)[:5]:
            print("   ", k, dups[k])

    # 트라이포 2종 + 분수 제트(nomat)는 v2 와 바이트 단위로 같은 메시라 다시 올리지 않았다.
    # v3 -> v2 메시 대응은 인스턴스 이름으로 1:1 검증했다(배치 차이 0).
    reuse = {}
    rp = os.path.join(HERE, "_reuse_v2.json")
    if os.path.exists(rp):
        reuse = {r["mesh"]: r for r in json.load(io.open(rp, encoding="utf-8"))}

    out, missing, notex = [], [], []
    for m, matname in sorted(want.items()):
        if m in reuse:
            r = reuse[m]
            rec = {"mesh": m, "meshId": r["meshId"], "mat": matname, "reused_v2": True}
            if r.get("textureId"):
                rec["textureId"] = r["textureId"]
            elif matname != "nomat":
                notex.append(matname)
            out.append(rec)
            continue
        lst = cand.get(m)
        if not lst:
            missing.append(m)
            continue
        rec = {"mesh": m, "meshId": max(lst)[1], "mat": matname}
        tid = None
        u = UUID.search(matname)
        if u:                                   # 트라이포 소품 : v2 때 올라간 원본 컬러맵
            tid = tex.get("Color_" + u.group(1)) or tex_all.get("Color_" + u.group(1))
        if tid is None:                          # 나머지 : 이번에 구운 타일(새 에셋에서만)
            tid = tex.get(safe_tex_name(matname))
        if tid:
            rec["textureId"] = tid
        elif matname != "nomat":
            notex.append(matname)
        out.append(rec)

    json.dump(out, io.open(os.path.join(HERE, "meshids_v3.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("해석 %d / %d  (텍스처 붙은 것 %d)"
          % (len(out), len(want), sum(1 for r in out if r.get("textureId"))))
    print("새 STATIC_MESH 총 %d개 -> 고유 메시 %d개"
          % (sum(len(v) for v in cand.values()), len(cand)))
    print("새 TEXTURE %d개" % len(tex))
    if notex:
        c = collections.Counter(notex)
        print("!! 텍스처 못 찾은 재질 %d종 :" % len(c))
        for k, n in c.most_common():
            print("     %-40s (메시 %d개)  찾던 이름: %s" % (k, n, safe_tex_name(k)))

    up = os.path.join(HERE, "unresolved.txt")
    if missing:
        io.open(up, "w", encoding="utf-8").write("\n".join(missing))
        print("!! 못 찾은 메시 %d개 -> unresolved.txt" % len(missing))
        sys.exit(1)
    if os.path.exists(up):
        os.remove(up)
    print("전부 해석됨")


if __name__ == "__main__":
    main()
