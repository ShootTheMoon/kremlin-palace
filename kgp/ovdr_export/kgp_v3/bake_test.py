# -*- coding: utf-8 -*-
r"""레시피만 빈 블렌더에서 굽는다. 팰리스 .blend(66MB)를 안 열어서 몇 초면 끝난다.

    blender.exe -b --factory-startup -P bake_test.py -- <recipes.json> <out_dir> [재질이름 ...]

타일 PNG 옆에 2x2 로 이어붙인 미리보기(<이름>_x2.png)도 쓴다. 이음새가 눈에 보이는지
확인하는 용도다(check_tiles 의 seam 숫자와 같이 본다).
"""
import bpy
import sys
import os
import json

sys.path.append(r"C:\Work\blender")
import kgp_v3_texture as K          # noqa: E402
import numpy as np                  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
recipes = json.load(open(args[0], encoding="utf-8"))
out = args[1]
only = set(args[2:])
sel = [r for r in recipes if not only or r["name"] in only]

for r in sel:
    if bpy.data.materials.get(r["name"]) is None:
        bpy.data.materials.new(r["name"])

ap = K.apply_recipes(sel)
print("@@APPLIED " + json.dumps(ap, ensure_ascii=False))
res = K.bake_tiles([{"name": r["name"], "texture_px": r.get("texture_px", 512)} for r in sel],
                   out_dir=out)
print("@@BAKED " + json.dumps({"ok": list(res["baked"]), "errors": res["errors"]},
                              ensure_ascii=False))

# 2x2 미리보기
for name, path in res["baked"].items():
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    step = 2 if w > 512 else 1
    px = px[::step, ::step]
    big = np.tile(px, (2, 2, 1))
    H, W = big.shape[:2]
    prev = bpy.data.images.new(os.path.basename(path)[:-4] + "_x2", W, H, alpha=False)
    prev.pixels.foreach_set(big.ravel())
    prev.filepath_raw = path[:-4] + "_x2.png"
    prev.file_format = 'PNG'
    prev.save()
    bpy.data.images.remove(img)
    bpy.data.images.remove(prev)
print("@@DONE")
