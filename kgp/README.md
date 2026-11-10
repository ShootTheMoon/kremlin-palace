# KGP — 대궁전을 OVERDARE 로 옮길 때 쓴 스크립트

`OVERDARE/` 의 `krm_export.py` 딜리버리 이후, 작업 PC 에서 대궁전을 ONLY ONE SHOT 레벨에
실제로 붓고 고치면서 쓴 스크립트 115개다. 익스포트를 네 번(v1 → v2 → v3 → v3c) 다시 냈고,
그 사이에 충돌 보강·텍스처 5라운드·기사상 분할·계단 끝 마감·떠 있는 판 제거가 끼어 있다.

결과와 절차는 [overdare-handover-docs](https://github.com/ShootTheMoon/overdare-handover-docs) 의
`pipeline/KGP_이관_명세서.md` · `pipeline/IMPORT_ORDER_KGP.md` · `pipeline/kgp_unused_assets.md` 에 있다.
여기는 그 문서들이 가리키는 **코드**다.

## 배치

작업 PC 의 폴더 모양을 그대로 옮겼다. 스크립트끼리 서로를 절대 경로로 부르기 때문이다
(`sys.path.append(r"C:\Work\blender")` 뒤에 `import kgp_export_v3`).

```
kgp/                      ← 작업 PC 의 blender\ 루트
  kgp_export*.py          익스포터 v1 · v2 · v3 · v3c
  kgp_v3_run.py           v3 헤드리스 드라이버
  kgp_v3_texture.py       재질 무늬를 타일 텍스처로 굽고 UV 를 깐다
  kgp_phys_scan.py        충돌 누락 전수 조사 (수평 단면 vs 충돌 Part)
  kgp_float_scan*.py      공중에 뜬 조각 조사
  kgp_fix_stray.py        홀 한가운데로 넘친 판을 뺀 메시 재출력
  kgp_knight_*.py         기사상 통짜 / 5조각 재출력
  kgp_stair_end_*.py      계단 끝면 실측과 마감 장식
  ovdr_export/            ← 작업 PC 의 blender\ovdr_export\
    kremlin_grand_palace_v1/   v1 배치 · 2차 콜리전 생성
    kgp_v2/                    v2 배치 · id 해석 · v1 삭제 · 스크립트/Mobility 패치
    kgp_v3/                    v3 배치 · v2→v3 제자리 교체 · 레시피 조립 · 타일 검사
      knight_fix/              기사 18체 2조각 → 5조각 교체
      _scratch/                굽기 레시피 실험 (아래 참고)
    kgp_v3c/                   v3 가 빠뜨린 커브 511개분 배치와 대조
    kgp_phys/                  충돌 2차 보강 생성기와 대조
    kgp_tex5/                  텍스처 5라운드 교체
    kgp_stair_end/             계단 끝 장식 배치와 확인
    kgp_fix_stray/             떠 있는 판 제거본 교체와 확인
    kgp_unused_assets.py       레벨이 더 이상 참조하지 않는 KGP 에셋 목록
    _missing_*.py · _curve_xform.py · _verify_v3c.py   v3c 를 내기 전후의 누락 조사
```

각 파일 머리의 독스트링에 무엇을 왜 하는지 적혀 있다. 이 표보다 그쪽이 정본이다.

## 알아둘 것

- **경로를 바꿨다.** 원본의 사용자 프로필 경로를 `C:\Work\` 로 치환했다 (107곳 / 67파일).
  `C:\Work\blender\...` 는 이 폴더, `C:\Work\onlyonetap\...` 는 게임 프로젝트 폴더를 뜻한다.
  그대로 돌리려면 자기 경로로 다시 바꿔야 한다.
- **산출물은 없다.** 스크립트가 읽고 쓰는 FBX · 텍스처 · `scene_v*.json` · `meshids_v*.json` ·
  `swap_*.json` 은 올리지 않았다. 원본 `KGP_v3_textured.blend` 도 없다.
- **`_scratch/` 는 손대지 않은 실험 기록이다.** 재질 레시피를 굽고 재 보던 조각들이라
  단독으로 실행되지 않는 것이 많다 (`mat`, `nodes` 같은 바깥 변수를 전제로 한 본문 조각).
  최종본은 `kgp_v3/recipes_r2_src.py` · `recipes_r5_src.py` 다.
- 레벨 파일(`.ovdrjm`)을 직접 고치는 스크립트가 섞여 있다
  (`patch_*.py`, `swap_*.py`, `delete_v1_offline.py`). 돌리기 전에 백업부터.
