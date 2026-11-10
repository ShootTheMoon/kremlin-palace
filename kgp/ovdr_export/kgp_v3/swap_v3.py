# -*- coding: utf-8 -*-
r"""v2 파츠 1,547개를 '제자리에서' v3 메시·텍스처로 갈아끼운다.

새로 만들지 않는 이유
  * 위치·크기·yaw 는 v2 와 v3 가 바이트 단위로 같다(검증: 차이 0). 옮길 게 없다.
  * 새로 붓다가 CFrame 이 원점으로 떨어진 게 153개였다(2026-09-17 실측).
  * 문짝 148개는 Mobility=Movable 이어야 하는데 Studio 는 중첩 파츠의 Mobility 변경을 거부한다.
  * 분수·문 스크립트가 KGP2_WATER_* / KGP2_Door_* 이름으로 붙잡는다.
  그래서 guid·이름·CFrame·Mobility 는 그대로 두고 아래만 바꾼다 :
    MeshId · TextureId · Material("Basic") · Color(200,200,200) · DoubleSided · Transparency

입력 : meshids_v3.json + items_v3_*.json (kgp_place_v3.py 결과) + 저장된 .ovdrjm
출력 : swap_v3_NN.json  — overdare_instance_update 에 그대로 넣는 100개 단위 묶음
       swap_v3_report.txt

    python swap_v3.py
"""
import io
import json
import os
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
CHUNK = 100                      # overdare_instance_update 한도


def live_parts():
    s = open(PRJ, "rb").read().decode("utf-16-le")
    if s and s[0] == "\ufeff":
        s = s[1:]
    d = json.loads(s)

    def walk(n):
        yield n
        for c in n.get("LuaChildren", []) or []:
            yield from walk(c)
    cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
    return {c["Name"]: c for c in cont["LuaChildren"] if str(c.get("Name", "")).startswith("KGP2_")}


def main():
    items = []
    for f in sorted(glob.glob(os.path.join(HERE, "items_v3_*.json"))):
        items += json.load(io.open(f, encoding="utf-8"))
    live = live_parts()

    ups, missing, same = [], [], 0
    for it in items:
        name2 = it["name"].replace("KGP3_", "KGP2_", 1)
        c = live.get(name2)
        if c is None:
            missing.append(name2)
            continue
        p = it["props"]
        raw = p.get("raw", {})
        props = {
            "MeshId": p["meshId"],
            "TextureId": raw.get("TextureId", ""),
            "Material": p["material"],
            "Color": p["color"],
            "DoubleSided": bool(raw.get("DoubleSided", False)),
        }
        if "transparency" in p:
            props["Transparency"] = p["transparency"]
        if (c.get("MeshId") == props["MeshId"] and c.get("TextureId", "") == props["TextureId"]):
            same += 1
        ups.append({"guid": c["ActorGuid"], "props": props})

    for f in glob.glob(os.path.join(HERE, "swap_v3_*.json")):
        os.remove(f)
    for k in range(0, len(ups), CHUNK):
        io.open(os.path.join(HERE, "swap_v3_%02d.json" % (k // CHUNK)), "w", encoding="utf-8").write(
            json.dumps(ups[k:k + CHUNK], ensure_ascii=False, separators=(",", ":")))

    rep = [
        "갈아끼울 파츠 %d / 살아있는 KGP2 파츠 %d" % (len(ups), len(live)),
        "이미 같은 것 %d" % same,
        "이름 못 찾음 %d %s" % (len(missing), missing[:5]),
        "묶음 %d개 (swap_v3_00.json ...)" % ((len(ups) + CHUNK - 1) // CHUNK),
        "텍스처 있음 %d · DoubleSided %d · 반투명 %d" % (
            sum(1 for u in ups if u["props"]["TextureId"]),
            sum(1 for u in ups if u["props"]["DoubleSided"]),
            sum(1 for u in ups if "Transparency" in u["props"])),
    ]
    io.open(os.path.join(HERE, "swap_v3_report.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
