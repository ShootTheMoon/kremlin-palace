# Kremlin Palace → OVERDARE 딜리버리

소스: `Kremlin_Grand_Palace_COMPLETE.blend` (저장됨, 67.1 MB)
총 60.3 MB · 전량 재임포트 검증 완료 · **실패 0건**

**임포트는 직접 한다.** 나는 파일만 준비하고, 끝난 뒤 `UGCLocalAssetTable.json` / `.ovdrjm`을 CLI로 읽어 검증한다. Studio 임포트 UI는 조작하지 않는다.

---

## 들어 있는 것

| 폴더 | 내용 | 수량 | 삼각형 | 용량 |
|---|---|---|---|---|
| `01_STATIC` | 월드 좌표 고정 지오메트리 | 88 | 2,058,732 | 38.7 MB |
| `02_INSTANCE_MASTERS` | 반복 오브젝트 원본 | 48 | 67,623 | 8.0 MB |
| `04_DOORS` | 힌지 원점 문 (런타임 개폐용) | 10 | 42,808 | 1.0 MB |
| `03_TEXTURES` | 팔레트 + 생성 에셋 2장 | 3 | — | 4.0 MB |
| `05_COLLISION` | 엔진 Part 정의 (FBX 아님) | 260 / 13청크 | — | — |

부속: `placements.csv` (945행) · `doors.json` · `collision_parts.json` · `import_plan.json` · `KrmDoors.lua`
스크립트: `krm_export.py` · `krm_collision.py` · `krm_verify.py`

## 임포트 순서

### 1단계 — 메시 146개
`import_plan.json` 대로. 파일당 3유닛(MODEL+STATIC_MESH+TEXTURE) = **총 438유닛 → 11세션**.
세션당 13파일 / 2배치. **세션 사이에 Studio를 반드시 재시작한다** (transient world 누수는 재시작에만 리셋).

### 2단계 — MeshPart 배치
- `01_STATIC` 은 전부 **(0,0,0)** 에 놓는다. 월드 좌표로 구웠으므로 맵이 스스로 조립된다.
- `02_INSTANCE_MASTERS` 는 `placements.csv` 945행대로 복제 배치.
- **MeshId 는 반드시 `STATIC_MESH` 에셋 id** — `MODEL` id 는 에디터에선 보이지만 플레이 중 안 보인다.

### 3단계 — 충돌 Part 260개
`05_COLLISION\COL_chunk_00..12.json` 을 `overdare_create_instances` 로 생성.
`Transparency 1` · `CanCollide true` · `Anchored true`.
**Part 는 네이티브 프리미티브라 퍼블리시 에셋을 0개 쓴다.**

| 그룹 | 개수 | 내용 |
|---|---|---|
| FLOOR | 4 | 홀 · 좌우 복도 · 응접실 |
| WALL | 15 | 외벽 (정문 개구부는 비워 둠 + 상인방) |
| STAIR | 178 | 쌍곡선 계단, 한 단 17 cm |
| COLUMN | 55 | 기둥 |
| DECK / RAIL | 3 / 3 | 갤러리 바닥 + 추락 방지 난간 |
| PROP | 2 | 분수 수반 · 천사상 받침 |

### 4단계 — 문 개폐
`04_DOORS` 10개를 MeshPart 로 만들고 이름을 `KrmDoors.lua` 의 key 와 맞춘 뒤
`KrmDoors.initAll(workspace)` → `KrmDoors.swingPair(L, R, true)`.

| 문 | 개수 | 각도 | 시간 |
|---|---|---|---|
| 정문 | 2 | ±92° | 1.667 s → 4.583 s |
| 윙 포털 | 4 | ±90° | 1.25 s → 3.25 s |
| 윙 끝문 | 4 | (소스 키 없음, 원하면 값만 채우면 됨) | — |

## 좌표 규약

`X = x*100` · `Y = z*100` · `Z = y*100` · `yaw = -degrees(rot_z)`
(Blender m Z-up → OVERDARE cm Y-up. FBX 는 `axis_up='Y', axis_forward='-Z'`)

## 검증된 것

| 항목 | 결과 |
|---|---|
| 재임포트 파일 | 146 / 실패 **0** |
| 삼각형 수 | 매니페스트와 **전부 일치** |
| 파일당 메시 | 전부 1개 |
| 파일당 재질 | 전부 1개 |
| 최대 tris/파일 | 29,148 < 공식 30,000 |
| 텍스처 | 2.20 / 1.77 / 0.006 MB — 전부 15 MB 이하 |
| 월드 범위 | X −30~30 m · Y −59~14 m · Z 0~15 m (소스와 동일) |
| 배치 좌표 | 표본 12개 오차 **0 m** |
| 계단 한 단 | 17.1 cm (걸어 올라갈 수 있음) |

## 엔진에서만 확인 가능한 것 3가지

1. **yaw 부호** — Blender +Z 회전을 부호 뒤집어 넣었다. 비대칭 오브젝트 하나(기사상)와 문 하나로 확인.
2. **`UnitExtent` 는 half-extent** — 소스 치수와 비교할 땐 2배. 안 그러면 정상 임포트가 50% 축소로 보인다.
3. **정문은 93.2° 이상 못 연다** — 옆 사파이어 기둥이 막는다(소스를 92°로 잡은 이유). 기둥을 뚫으면 각도를 줄일 것.

## 알려진 품질 손실

**형태는 손실 없다.** 데시메이트 안 썼고, 캡 넘는 9개는 최장축 공간 분할로 원본 그대로 쪼갰다. 셰이딩도 원본 유지.

**재질은 크게 떨어진다.** 이 맵은 100% 절차적으로 지어 재활용할 텍스처가 0장이다(생성 에셋 2세트 제외). 그래서 단색·절차 재질 20개를 512² 팔레트 한 장에 담고 UV 를 슬롯 중심 한 점으로 보냈다. 잃은 것:

- 대리석 결(P8a 월드 좌표 실핏줄), 금장 거칠기 변화
- 금속성 (금장 0.72 · 철 0.7 · 거울 0.85) → 평면 확산광
- 발광 (촛불 4.0 · 채광창 1.6 · 창유리 1.2)
- 투과 (물 IOR 1.333 · 유리) → 불투명

**베이크는 하지 않기로 했다.** 근거: 이 Blender 에 Cycles 가 없어(`render_engines_available: ["BLENDER_EEVEE"]`) `bpy.ops.object.bake` 가 실행 불가이고, 가시 메시 1,751개 중 **1,216개(69%)에 UV 가 아예 없다**. 과거 OVERDARE 맵 중 절차적 재질을 베이크한 사례도 없다 — 베를린은 스캔 텍스처 재사용 + 단색 스와치, 시부야는 PIL 오프라인 래스터라이즈, 창덕궁·화성은 KHS PBR 세트를 그대로 썼다.

→ 대신 엔진 쪽에서 `Material = Enum.Material.Metal` 같은 속성과 조명으로 보완하는 편이 비용 0 에 효과가 크다.

**조명 116개와 낮/밤 프리셋은 안 나간다.** 엔진에서 새로 세워야 한다.

**정점 1,196,755개.** OVERDARE 는 삼각형이 아니라 정점을 세고 화면당 권장치가 70,000 이다. 홀 전체가 한 화면에 들어오면 크게 넘으니 실기기 프레임을 보고 원거리 장식부터 줄일 것.

## 남은 것

- [ ] 스폰 지점
- [ ] 유리·물 MeshPart 에 `Transparency` 지정 (팔레트는 불투명)
- [ ] 조명 배치
