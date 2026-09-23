# 크렘린 대궁전 — Sapphire & Gold

첨부된 14개 이미지의 색상과 공간 구성을 참고한 편집 가능한 궁전 3D 환경입니다. 실측 복원 모델이 아닌 참고 이미지 기반의 창작 모델이며, 세부 조각상과 장식은 단순화되어 있습니다.

프로젝트: https://higgsfield.ai/3d-jutsu/3f7e2946-1af7-4aa3-a936-acf16af7ab64

## 구성
- 중앙 대홀: 32 × 28 m, 높이 12 m
- 2층 회랑: 바닥 높이 5.12 m
- 좌우 32단 곡선 계단, 중앙 분수와 날개 조각상
- 청색 기둥, 금장 몰딩, 체크 바닥, 장미창, 샹들리에
- 양쪽 의전 복도, 티 테이블 4세트와 회랑 소파
- 내부 / 조감 / 회랑 카메라 3개

## 사용
`Kremlin_Grand_Palace.blend`를 Blender에서 열어 컬렉션별로 수정할 수 있습니다. 숫자패드 0으로 내부 카메라를 확인합니다. `10 | Removable ornamental ceiling` 컬렉션을 숨기면 위에서 실내를 볼 수 있습니다. GLB는 다른 3D 도구로 가져오기 위한 모델입니다. 재질과 조명 표현은 뷰어에 따라 달라질 수 있습니다.

게임 엔진용 충돌체, 내비게이션 메시, 캐릭터 이동 코드는 포함하지 않습니다. 분수 물줄기는 정적인 장식입니다.

`build_palace.py`와 `refine_palace.py`는 순서대로 실행하는 재생성 스크립트입니다. 첫 스크립트는 현재 장면의 오브젝트를 비우므로 새 Blender 파일에서 실행하세요. Higgsfield Blender 5.2 환경에서 제작했습니다.

## 폴더

| 경로 | 내용 |
|---|---|
| `*.py` | 궁전 생성·보강 스크립트 (`build_palace` → `refine_palace` → `complete_palace` → `phase3_p*`) |
| `PHASE*_README.md` · `*_PASSPORT.md` | 단계별 작업 기록과 장면 명세 |
| `OVERDARE/` | OVERDARE 이관 세트 — FBX 146개, 배치표, 콜리전 Part 정의, 문 스크립트, 임포트 절차 ([OVERDARE/README.md](OVERDARE/README.md)) |

`.blend` 원본·체크포인트, GLB, 렌더는 용량 때문에
[`sources` 릴리스](https://github.com/ShootTheMoon/kremlin-palace/releases/tag/sources)에 있다.
