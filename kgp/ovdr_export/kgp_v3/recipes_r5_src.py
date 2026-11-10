# -*- coding: utf-8 -*-
r"""라운드 5 — '더러워 보이는' 네 재질을 깨끗하게 다시 쓴다 -> recipes_r5.json

사용자 피드백(2026-09-19, 실기 스크린샷) : "텍스쳐가 더러움".
실측한 원인
  * 금장        : 명암 폭 전체를 저주파 얼룩에 썼다(짙은 갈색 반점 + 균열선) → 때 묻은 황동
  * 사파이어    : 짙은 남색 반점과 흰 얼룩이 크게 번진다 → 얼룩 위장무늬
  * 아이보리    : 베이지 바탕 + 지도 등고선 같은 회색 선 → 누렇게 바랜 벽
  * 청회색      : 어두운 구름 얼룩 → 물 얼룩
방향 : 명암 변화는 '넓고 부드럽게, 폭은 작게', 무늬는 '가늘고 드물게'. 검정·흰색 쪽 극단을 쓰지 않는다.
결은 4D 노이즈의 0.5 등고선(|Fac-0.5| 이 작은 곳)만 가늘게 뽑는다 — 선이 끊기지 않고 타일이 이어진다.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recipes_r2_src import HELPERS     # noqa: E402

VEIN = r'''
def vein(vec, w, n, width, dist=1.2, detail=3.0):
    """가는 결 마스크(0..1). n : 타일당 굵은 굴곡 수, width : Fac 폭(작을수록 가늘다)."""
    f = noise4(vec, w, n, detail=detail, rough=0.55, dist=dist)
    d = mm('ABSOLUTE', mm('SUBTRACT', f.outputs['Fac'], 0.5))
    return remap(d, 0.0, width, 1.0, 0.0)

def fade(vec, w, n, lo, hi):
    """결이 나타났다 사라지게 하는 저주파 마스크."""
    return remap(noise4(vec, w, n, detail=2.0, rough=0.5).outputs['Fac'], lo, hi)
'''

GOLD = r'''
vec, w = torus()
# 넓고 부드러운 광택 굴곡 — 명암 폭을 좁게(그림자색이 갈색으로 떨어지지 않게)
sheen = noise4(vec, w, 2.4, detail=3.0, rough=0.5)
col = ramp(remap(sheen.outputs['Fac'], 0.30, 0.70), [
    (0.00, (0.600, 0.370, 0.070)),
    (0.50, (0.760, 0.510, 0.120)),
    (1.00, (0.890, 0.650, 0.210))])
# 결 방향 헤어라인(아주 옅게)
vb, wb = torus(ru=1.0, rv=0.08)
hair = noise4(vb, wb, 90.0, detail=2.0, rough=0.5)
col = mix(remap(hair.outputs['Fac'], 0.42, 0.58, 0.0, 0.10), col, (0.930, 0.760, 0.330))
col = mix(remap(hair.outputs['Fac'], 0.42, 0.58, 0.10, 0.0), col, (0.520, 0.340, 0.080))
# 가끔 밝게 번쩍이는 넓은 하이라이트
glint = noise4(vec, w, 3.0, detail=1.0, rough=0.5)
col = mix(remap(glint.outputs['Fac'], 0.58, 0.68, 0.0, 0.12), col, (0.930, 0.720, 0.280))
finish(col)
'''

SAPPHIRE = r'''
vec, w = torus()
depth = noise4(vec, w, 2.4, detail=3.0, rough=0.5)
col = ramp(remap(depth.outputs['Fac'], 0.28, 0.72), [
    (0.00, (0.010, 0.030, 0.200)),
    (0.55, (0.018, 0.050, 0.300)),
    (1.00, (0.035, 0.090, 0.420))])
# 가는 밝은 결 두 겹(굵은 것 옅게, 가는 것 더 옅게)
v1 = mm('MULTIPLY', vein(vec, w, 3.0, 0.014), fade(vec, w, 2.0, 0.42, 0.60))
col = mix(mm('MULTIPLY', v1, 0.45), col, (0.120, 0.230, 0.650))
v2 = vein(vec, w, 7.0, 0.008, dist=2.0)
col = mix(mm('MULTIPLY', v2, 0.25), col, (0.090, 0.170, 0.520))
# 드문 금 반점(라피스의 황철석) — 작고 드물게
fl = voro4(vec, w, 60.0, feature='F1')
spark = mm('MULTIPLY', remap(fl.outputs['Distance'], 0.0, 0.05, 1.0, 0.0),
           remap(sep_r(fl.outputs['Color']), 0.93, 0.97))
col = mix(spark, col, (0.850, 0.640, 0.220))
finish(col)
'''

IVORY = r'''
vec, w = torus()
cloud = noise4(vec, w, 2.2, detail=3.0, rough=0.5)
col = mix(remap(cloud.outputs['Fac'], 0.30, 0.70),
          (0.790, 0.780, 0.755), (0.850, 0.842, 0.818))
# 카라라풍 : 굵은 결 하나(옅은 회색) + 가는 잔결(더 옅게), 둘 다 드문드문
v1 = mm('MULTIPLY', vein(vec, w, 2.2, 0.010), fade(vec, w, 1.6, 0.44, 0.60))
col = mix(mm('MULTIPLY', v1, 0.75), col, (0.420, 0.430, 0.455))
v2 = mm('MULTIPLY', vein(vec, w, 5.0, 0.006, dist=2.0), fade(vec, w, 2.5, 0.46, 0.62))
col = mix(mm('MULTIPLY', v2, 0.45), col, (0.520, 0.530, 0.555))
finish(col)
'''

BLUEGREY = r'''
vec, w = torus()
cloud = noise4(vec, w, 2.4, detail=3.0, rough=0.5)
col = mix(remap(cloud.outputs['Fac'], 0.30, 0.70),
          (0.215, 0.275, 0.385), (0.250, 0.315, 0.435))
v1 = mm('MULTIPLY', vein(vec, w, 2.4, 0.012), fade(vec, w, 1.8, 0.42, 0.60))
col = mix(mm('MULTIPLY', v1, 0.65), col, (0.580, 0.650, 0.760))
v2 = vein(vec, w, 6.0, 0.006, dist=2.0)
col = mix(mm('MULTIPLY', v2, 0.22), col, (0.470, 0.540, 0.650))
finish(col)
'''

NEW = {
    "Antique gilded bronze": (2.0, 1024, GOLD),
    "Sapphire stone":        (3.0, 1024, SAPPHIRE),
    "Ivory marble":          (6.0, 1024, IVORY),
    "Blue grey marble":      (2.5, 1024, BLUEGREY),
}


def main():
    out = [{"name": n, "tile_metres": t, "texture_px": px, "code": HELPERS + VEIN + body, "source": "r5-clean"}
           for n, (t, px, body) in NEW.items()]
    io.open(os.path.join(HERE, "recipes_r5.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("recipes_r5.json :", len(out))


if __name__ == "__main__":
    main()
