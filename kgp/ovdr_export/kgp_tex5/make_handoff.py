# -*- coding: utf-8 -*-
r"""라운드 5 텍스처 전달 준비 (블렌더 헤드리스).

  * _test_r5 의 PNG 4장을 KGPTEX5_<재질>.png 로 복사 (옛 KGPTEX3_* 과 이름이 겹치지 않게)
  * 전/후 비교 시트 compare_r5.png (왼쪽 = 지금 게임, 오른쪽 = 새 것, 각 타일 2x2 반복)

    blender.exe -b --factory-startup -P make_handoff.py
"""
import os
import shutil

import bpy
import numpy as np

V3 = r"C:\Work\blender\ovdr_export\kgp_v3"
OUT = os.path.dirname(os.path.abspath(__file__))
MATS = ["Antique_gilded_bronze", "Sapphire_stone", "Ivory_marble", "Blue_grey_marble"]
CELL = 384


def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def cell(px):
    big = np.tile(px, (2, 2, 1))
    step = max(1, big.shape[0] // CELL)
    return big[::step, ::step][:CELL, :CELL]


rows = []
for m in MATS:
    shutil.copyfile(os.path.join(V3, "_test_r5", "KGPTEX3_%s.png" % m), os.path.join(OUT, "KGPTEX5_%s.png" % m))
    old = cell(load(os.path.join(V3, "_tex", "KGPTEX3_%s.png" % m)))
    new = cell(load(os.path.join(V3, "_test_r5", "KGPTEX3_%s.png" % m)))
    gap = np.ones((CELL, 12, 4), np.float32) * np.array([0.12, 0.12, 0.12, 1.0], np.float32)
    rows.append(np.concatenate([old, gap, new], axis=1))
    rows.append(np.ones((12, rows[-1].shape[1], 4), np.float32) * np.array([0.12, 0.12, 0.12, 1.0], np.float32))
sheet = np.concatenate(rows[:-1], axis=0)
H, W = sheet.shape[:2]
im = bpy.data.images.new("compare_r5", W, H, alpha=False)
im.pixels.foreach_set(sheet.ravel())
im.filepath_raw = os.path.join(OUT, "compare_r5.png")
im.file_format = 'PNG'
im.save()
print("@@ done", W, H)
