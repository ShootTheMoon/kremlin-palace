# -*- coding: utf-8 -*-
r"""KGP v3 헤드리스 드라이버.

GUI 블렌더를 소켓 애드온 너머로 굴리면 베이크·씬전환·파일열기에서 죽는다(2026-09-17 실측).
무거운 건 전부 여기로 몰아서 -b 로 돌린다.

    blender.exe -b "<blend>" -P kgp_v3_run.py -- <mode> [recipes.json]

mode
    baseline   현재 재질 그대로 타일을 굽는다. 어느 재질이 얼마나 '단색'인지 재는 용도.
    build      레시피 적용 -> 굽기 -> 박스 UV -> 재연결 -> .blend 저장(별도 파일)
    export     build 결과 blend 를 열어 FBX/배치표를 낸다 (kgp_export_v3 를 부른다)
"""

import bpy
import sys
import os
import json

HERE = r"C:\Work\blender"
if HERE not in sys.path:
    sys.path.append(HERE)

import kgp_v3_texture as K          # noqa: E402

OUT_ROOT = r"C:\Work\blender\ovdr_export\kgp_v3"
BUILT_BLEND = os.path.join(OUT_ROOT, "KGP_v3_textured.blend")


def argv_after_dashes():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def log(tag, obj):
    print("@@%s %s" % (tag, json.dumps(obj, ensure_ascii=False)))


def main():
    args = argv_after_dashes()
    mode = args[0] if args else "baseline"
    os.makedirs(OUT_ROOT, exist_ok=True)

    mats = K.exported_materials()
    log("SCENE", {"file": bpy.data.filepath, "objects": len(K.exported_objects()),
                  "materials": len(mats)})

    if mode == "baseline":
        specs = [{"name": n, "texture_px": 512} for n in sorted(mats)]
        res = K.bake_tiles(specs, out_dir=os.path.join(OUT_ROOT, "_tex_baseline"))
        log("BAKED", {"ok": len(res["baked"]), "errors": res["errors"]})
        return

    if mode in ("build", "export"):
        recipes = []
        if len(args) > 1:
            recipes = json.load(open(args[1], encoding="utf-8"))
        if mode == "build":
            if not recipes:
                log("ABORT", {"why": "no recipes given"})
                return
            ap = K.apply_recipes(recipes)
            log("APPLIED", ap)

            specs = [{"name": r["name"], "texture_px": r.get("texture_px", 512)}
                     for r in recipes if r["name"] in ap["applied"]]
            # 레시피가 없는 재질도 단색 타일이라도 구워서 전부 텍스처를 갖게 한다
            covered = {s["name"] for s in specs}
            for n in sorted(mats):
                if n not in covered:
                    specs.append({"name": n, "texture_px": 512})
            res = K.bake_tiles(specs, out_dir=os.path.join(OUT_ROOT, "_tex"))
            log("BAKED", {"ok": len(res["baked"]), "errors": res["errors"]})

            tile_by_mat = {r["name"]: float(r.get("tile_metres") or 2.0) for r in recipes}
            uv = K.box_uv_all(tile_by_mat, default_tile=2.0)
            log("UV", uv)

            relinked = K.relink_baked(res["baked"])
            log("RELINK", {"n": len(relinked)})

            bpy.ops.wm.save_as_mainfile(filepath=BUILT_BLEND, copy=False)
            log("SAVED", {"blend": BUILT_BLEND})
            return

        # export
        import kgp_export_v3 as E
        E.run()
        log("EXPORTED", {"out": OUT_ROOT})
        return

    log("ABORT", {"why": "unknown mode %r" % mode})


main()
