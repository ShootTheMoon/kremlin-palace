# KRM_Palace — 크렘린궁 내부 맵 + 3맵 스왑 구조 (ONLY ONE SHOT)

## Context

`onlyoneshot` 에 **3맵 투표제**를 넣으려면 세 번째 맵이 필요하다. 사용자가 정한 주제는
**크렘린궁 내부 3실**이고, 방침은 **"최대한 생성하지 말고 스케치팹에서 가져와 블렌더로 조립"** 이다.

지금 상태를 실제로 열어보고 확인한 것:

- `Workspace` 에 살아 있는 맵은 `JSN_Sangok` (3,396 파츠) 하나뿐이다.
  `Changdeokgung Place` 는 3파츠짜리 껍데기고, `Gyeongbokgung Place`(253) ·
  `Hwaseong Place`(150) · `Hwaseong Collision`(992) 는 **`ServerStorage` 에 처박혀 있다.**
- 어제 프레임 문제로 화성을 `ServerStorage` 로 옮긴 뒤 **"아예 안 보인다"** 는 보고가 있었는데,
  그건 버그가 아니라 `ServerStorage` 가 서버 전용(클라 복제 안 됨)이라 **정상 동작**이다.
  즉 지금의 "비활성화"는 되돌릴 방법이 없는 편도 조치다. **스왑 구조가 없어서 생긴 문제다.**
- 그래서 이번 작업 범위를 **맵 + 맵 스왑 구조** 로 잡았다 (사용자 선택).

목표 결과물: `KRM_Palace` 맵 하나 + 어떤 맵이든 켜고 끌 수 있는 `MapService`.

---

## 실측 근거 (이번에 직접 확인함 — 추측 아님)

### 단위 환산
`CaptureServer.lua:57` 의 `X_MIN..X_MAX = -73053..-47053` (26,000 유닛)이
`MovementSpeedServer_6.lua:4` 의 주석 "JSN_Sangok 259 x 271m" 와 대응한다.
→ **1 m = 100 스터드.** `ViewmodelConfig` 의 `MELEE.RANGE = 380` = **3.8 m** 도 이걸로 맞는다.

### 방 3개 (사용자 확정: 파세트궁 + 블라디미르 + 테렘궁, **실측 그대로**)

| 방 | 실측 | 스터드 | 출처 |
|---|---|---|---|
| **파세트궁 대홀** (Грановитая палата) | **22.25 × 22.25 m**, 495 m², 볼트 최고 **9.0 m**, **중앙 기둥 1개** | 2225 × 2225, h 900 | `ref/README.md:166`, 도판 `06_파세트궁/0_실측도면/RZ2_tab12.jpg` 의 **План + Разрез** (평면 중앙의 정사각 기둥 + 단면의 십자볼트가 그 기둥에서 뻗는 게 그림에 그대로 있다) |
| **블라디미르 홀** (Владимирский зал) | **16 × 16 m** 정사각 + 네 모서리 니치 → **팔각으로 읽힌다**, 16각 텐트볼트, **창이 하나도 없다** — 빛은 **직경 6 m 유리 천창**뿐, 높이 ~18 m | 1600 × 1600, 천창 ⌀600, h ~1800 | 아래 출처 |
| **테렘궁 거주층** (거실) | 도판 `План жилого этажа` 의 **일자 앙필라드** — 방들이 한 줄로 꿰여 있다. 스케일바 планов 0–20 m | 도판에서 실측해 확정 (Phase 1) | `07_테렘궁/0_실측도면/RZ2_tab12.jpg` |

**결정적으로 유리한 사실:** 블라디미르 홀은 실제로 **파세트궁·테렘궁·게오르기옙스키 홀을 잇는 교차점**이다.
즉 **허브 앤 스포크** 배치가 역사적으로 정확하면서 동시에 FPS 3레인 구조가 된다. 지어낼 필요가 없다.

### 실내 비주얼 레퍼런스 (직접 열어봄)
- `05_대크렘린궁/_indoor/*.jpg` (14장, 2025년 국빈 만찬 촬영) — **파세트궁 실내**다.
  금바탕에 앉은 차르 프레스코, 황토·금 벽면, **적갈색 테두리 띠**. 텍스처 원본으로 그대로 쓸 수 있다.
- `07_테렘궁/_indoor/*.jpg` (17장) — **청록색 볼트 + 적·금 당초 문양 + 어두운 조각 액자의 이콘 +
  벽을 두르는 나무 벤치 + 어두운 널마루.** "거실"의 색조는 이 사진들이 확정한다.

출처: [Большой Кремлёвский дворец — Wikipedia](https://ru.wikipedia.org/wiki/%D0%91%D0%BE%D0%BB%D1%8C%D1%88%D0%BE%D0%B9_%D0%9A%D1%80%D0%B5%D0%BC%D0%BB%D1%91%D0%B2%D1%81%D0%BA%D0%B8%D0%B9_%D0%B4%D0%B2%D0%BE%D1%80%D0%B5%D1%86) · [Залы БКД — progulkipomoskve](https://progulkipomoskve.ru/zaly_bolshogo_kremlevskogo_dvorca) · [Владимирский зал — artparquet](https://artparquet.ru/obekty/bolshoy-kremlevskiy-dvorets-vladimirskiy-zal.html)

### ⚠ 스케치팹으로 되는 것과 안 되는 것 (검색으로 확인)
**통짜 "크렘린 내부" 모델은 없다.** `orthodox fresco wall` → 1건(불가리아 보야나 교회).
**벽·볼트·바닥 같은 구조 셸은 스케치팹이 못 준다 → 블렌더로 직접 만든다.**
반면 **소품은 충분하다** (아래 Phase 2 표). 그래서 "최대한 스케치팹" 은
**소품 100% 스케치팹 / 구조 셸만 자체 제작** 으로 해석해 진행한다.

### 규모에 대한 정직한 경고
3실 + 통로 = **약 1,000 m²**. de_dust2(약 5,000 m²)의 1/5 이고 `JSN_Sangok`(259×271 m)의 1/70 이다.
5v5 로는 **매우 좁다.** 다만 1히트 킬 냉병기 게임이라 좁은 게 오히려 맞을 수 있고,
좁다는 건 곧 **프레임 여유**(어제 화성 제거로 28→35.9 fps 를 얻은 그 문제)다.
그래서 이대로 짓되, **역사적으로 실재하는 연결부**로 동선을 늘린다 — 이건 "방"이 아니라 통로다:
- **성스러운 현관(Святые сени)** — 파세트궁 앞방
- **황금 계단(Золотое крыльцо)** — 테렘궁 4층으로 올라가는 계단
- 블라디미르 홀 **2단 아치 회랑** — 18 m 층고를 위아래 2개 층으로 쓴다

일단 지어서 뛰어보고 좁으면 그때 조정한다 (사용자 선택: 실측으로 짓고 플레이 후 조정 — 아님.
사용자는 "실측 그대로" 를 골랐으므로 **치수는 건드리지 않고 통로만 조정한다**).

---

## 배치 (허브 앤 스포크)

```
                    [테렘궁 앙필라드 — 거실]
                     낮은 볼트 h~4m, 청록·금, 페치카
                     좁고 어두움. 근접 유리
                              │  황금 계단
                              │
   [파세트궁 대홀] ─ 성스러운 ─ ● 블라디미르 홀 ─ (막다른 벽 / 관전 니치)
    22.25m 정사각      현관      16m 팔각 · 창 없음
    중앙 기둥 1개               천창 ⌀6m 만 빛
    볼트 9m                     상·하 2층 회랑
    RED 스폰                    중립 · 점령지                BLUE 스폰
```

- **RED 스폰 = 파세트궁**, **BLUE 스폰 = 테렘궁 앙필라드 끝**, **점령지 = 블라디미르 홀 중앙**
  (천창 아래 = 맵에서 유일하게 밝은 원형 바닥. 조명이 곧 목표 지시가 된다)
- 파세트궁 **중앙 기둥**은 495 m² 정사각형 방의 유일한 엄폐물이다 — 이 방의 전투 성격을 혼자 정한다
- 테렘궁 앙필라드는 문이 일렬이라 **한 줄 시야** — 활(국궁)이 유리, 칼은 방을 하나씩 따야 한다
- 블라디미르 홀 상단 회랑 = 고저차. 아래로 뛰어내릴 수 있게 낙하 데미지 없음(현재 그대로)

맵 원점은 블라디미르 홀 중앙 = `(0, 0, 0)`. 전체 바운딩 약 **6,000 × 3,000 스터드 (60 × 30 m)**.

---

## Phase 0 — 프로젝트 뼈대

```
Desktop\Kremlin\
  KRM_Palace.blend          작업 씬 (컬렉션: 00_REF / 10_SHELL / 20_PROPS / 30_COLLISION / 90_EXPORT)
  _sketchfab\<uid>_<name>\  원본 다운로드 (절대 손대지 않음)
  _export\                  overdare_convert.py 출력 FBX
  ATTRIBUTION.md            에셋별 저작자·라이선스·URL — CC-BY 이행 의무
  BUILD_LOG.md
```

**라이선스 규칙 (프로젝트는 비상업이지만 그래도 지킨다):**
- ✅ **CC0 / CC-BY** 우선
- ⚠ **CC-BY-NC** 는 비상업이므로 가능 — 단 `ATTRIBUTION.md` 에 NC 표시
- ❌ **ShareAlike(-SA) 는 쓰지 않는다.** 맵 전체가 SA 로 전염될 수 있다
- 다운로드 즉시 `ATTRIBUTION.md` 에 한 줄 기록. 나중에 몰아서 하면 반드시 빠진다

`ref/` 도판 2장(`RZ2_tab12.jpg`)을 `00_REF` 에 **Empty(Image)** 로 배치하고 스케일바 0–20 m 로
정확히 맞춘다 — 이후 모든 평면 치수는 이 이미지 위에서 뜬다.

## Phase 1 — 구조 셸 (블렌더 자체 제작 · 스케치팹 불가)

방마다 **셸 = 바닥 + 벽 + 볼트 + 문틀** 이며, 전부 도판 위에서 뜬다.

1. **파세트궁**: 2225 스터드 정사각 → 중앙에 각기둥 1개 → 4분할 십자볼트 4매.
   단면 도판(`Разрез`)의 아치 프로파일을 커브로 따서 스핀. 볼트 정점 900.
2. **블라디미르 홀**: 1600 정사각 → 모서리 4개를 니치로 깎아 팔각 → **16각 텐트볼트**를
   `Screw`/`Spin` 으로 세우고 정점에 ⌀600 오큘러스를 뚫는다. 중간 높이에 회랑 슬래브 + 아치 열주.
3. **테렘궁**: 도판 `План жилого этажа` 를 트레이스 → 벽 두께 그대로 → 각 방 **낮은 그로인 볼트**.
   `_indoor` 사진의 나무 널마루 방향(장변)까지 맞춘다.

**폴리 예산:** 셸 전체 ≤ 120k tris. 볼트는 세그먼트를 아끼고 노멀맵으로 벌지 않는다
(OVERDARE 는 머티리얼 1개·텍스처 1장 규칙이라 노멀맵이 안 붙는다 — [[overdare-fbx-conversion]]).

**텍스처:** 벽·볼트는 `_indoor` 사진에서 뜬 **타일링 가능한 문양 텍스처**를 굽는다 (PIL, 1024px).
파세트궁 = 황토·금 프레스코 + 적갈 띠 / 블라디미르 = 옅은 분홍 대리석 + 금 / 테렘 = 청록 + 적·금 당초.

## Phase 2 — 스케치팹 소품 수확

검색으로 **실재를 확인한** 후보 (면수는 원본, 전부 다운로드 가능):

| 용도 | 모델 | UID | 면수 | 라이선스 |
|---|---|---|---|---|
| 샹들리에 (블라디미르 홀 주인공) | Chandelier — MikhailKadilnikov | *Phase 2에서 재조회* | 5,056 | CC-BY |
| **페치카 (테렘궁 거실 핵심)** | Russian stove - automapping | *재조회* | 11,518 | CC-BY |
| 페치카 (저폴리 대안) | Old Soviet Stove (Pechka) | *재조회* | 1,712 | CC-BY |
| 기둥·필라스터 | Noble Interior Column | *재조회* | 10,330 | CC-BY |
| 옥좌 | Throne — Folkeir | `bfc6d2989bb0411d9572733d35c3e6d1` | 11,559 | CC-BY |
| 옥좌 (저폴리) | Throne — DINOWAAA | `26308310bb294600817c5cf44d756e50` | 3,899 | CC-BY |
| **벽 벤치 (테렘 필수)** | Medieval Old Wooden Bench | `76017263f0ea4d46915c0f48edc04923` | 2,040 | CC-BY |
| 벤치 (초저폴리, 다량 배치용) | wooden_bench — sam_ogon | `facb38d569024ec882a57a8a09c02216` | 216 | CC-BY |
| 촛대 (저폴리) | Candelabra — bitgem | `89f71a03a338491c92ada680e6f51749` | 447 | CC-BY |
| 촛대 (히어로) | Medieval Candelabra — xtoomer | `01cf47f8e3174f1e9d7aa926256cbcef` | 11,986 | CC-BY |
| **이콘 (테렘 벽면)** | Икона Богородица с Христом | `eb6f9f0bf68943a2b5d85ce40fe2c6f9` | 15,692 | CC-BY |
| 이콘 (초저폴리) | Luke of Simferopol icon | `791ed95a3e694d53becfe882c7f5d90f` | 428 | CC-BY |
| 받침대 | Classical Museum Pedestals Pack | *재조회* | 4,722 | — |
| 만찬 소품 | Palace Bottle Assets | *재조회* | 11,176 | — |

추가로 검색할 것: `russian door`, `carpet rug`, `banquet table`, `oil lamp`, `tapestry`.
**검색 요령(실측):** 긴 문장은 "No models found" 가 뜬다. **1~2 단어**로만 검색한다.

**수확 후 반드시 하는 것:**
1. `_sketchfab\` 원본 보존 → 사본으로 작업
2. **Decimate** — 소품 1개당 **≤ 3,000 tris** 목표 (셸 제외 소품 총합 ≤ 150k)
3. 스케일 정규화 — 스케치팹 모델은 스케일이 제각각이다. **1 m = 100 스터드**로 맞춘다
4. 머티리얼 통합 — OVERDARE 는 **머티리얼 하나가 임포트 단위**다. 소품당 머티리얼 1개로 합친다
5. `-SA` 라이선스면 즉시 폐기하고 대체품을 찾는다

## Phase 3 — 배치 · 조명

- 소품은 **링크드 더플리케이트**(`Alt+D`)로 깐다. 벤치 12개가 메시 12벌이 되면 안 된다
- 조명은 **텍스처에 굽지 않는다.** OVERDARE 에서 파츠 조명으로 처리
  (블라디미르 = 천창 1개 + 샹들리에 / 파세트 = 창 6 + 촛대 / 테렘 = 창 + 페치카 발광)
- 시야 차단: 문 위치가 곧 전투 리듬이다. 문 폭은 도판대로 두되 **문짝은 달지 않는다**(열림 처리 없음)

## Phase 4 — OVERDARE FBX 내보내기

**기존 파이프라인을 그대로 재사용한다** — `Desktop\MeshTest\overdare_convert.py`
(`convert(asset, strategy, part_names)`; 머티리얼별 분리 → 데시메이트 대신 **공간 이분할**로
tri 상한을 맞춘다 → 텍스처 1장 정규화 → 검증). 규칙·함정은 [[overdare-fbx-conversion]] 참조:
**메시당 ≤30,000 tris / FBX당 ≤200 메시 / 텍스처 512 권장 / 콜라이더는 FBX 에 못 넣는다.**

- `overdare_mesh_bulk_import` 는 입력을 묶어버리므로 **호출 1회에 파일 1개**만 먹인다
- **콜리전은 엔진 Part 로 따로 만든다.** 단, 어제 census 에서 `JSN_Sangok` 이 보이지 않는
  콜리전 프록시를 **1,669개** 들고 있는 게 확인됐다. **같은 실수를 반복하지 않는다** —
  KRM 은 벽·바닥이 평면이라 **박스 프록시 40개 이하**로 끝난다. 목표: **KRM_Palace 총 파츠 ≤ 600**

## Phase 5 — 엔진 조립

`Workspace.KRM_Palace` 모델 아래에 **맵에 딸린 것을 전부 넣는다**:

```
KRM_Palace/
  KRM_SHELL_*        (메시)
  KRM_PROP_*         (메시)
  KRM_COL_*          (박스 콜라이더, Transparency=1)
  KRM_Spawn_Red      SpawnLocation   ← 파세트궁
  KRM_Spawn_Blue     SpawnLocation   ← 테렘궁 앙필라드 끝
  Arena_Bound_North / South / East / West   ★ 맵 안으로 들어간다
```

기존 스크립트 중 **고칠 필요가 없는 것** (읽어서 확인함):
- `TeamServer.snapToGround()` — 레이캐스트 기반이라 이미 맵 무관 (주석에도 "새 맵을 넣어도 그대로 동작")
- `TeamServer.findSpawn()` — 맵 안에서 못 찾으면 `Workspace` 전체를 뒤지는 폴백이 있다
- `CaptureServer.useArenaBounds()` — `Arena_Bound_*` 4개가 있으면 **하드코딩 좌표를 무시하고** 그걸 쓴다
  → **이게 스왑의 후크다.** 벽을 맵 안에 넣으면 점령지가 알아서 따라온다
- `BoundaryServer` — 같은 벽 4개를 쓴다

## Phase 6 — 맵 스왑 구조 (`MapService`)

현재 맵 이름이 **하드코딩된 곳** (grep 으로 확인, 여기만 고치면 된다):

| 파일 | 줄 | 내용 |
|---|---|---|
| `TeamServer.lua` | 89 | `Workspace:FindFirstChild("JSN_Sangok")` |
| `CaptureServer.lua` | 56–59 | `MAP_NAME` + 하드코딩 X/Z 범위 |
| `SeamFiller.lua` | 24 | `MAP_NAME` — 산곡 지형 전용이므로 **맵이 산곡일 때만 돌게 가드** |
| `MovementSpeedServer_6.lua` | — | 259×271 m 기준으로 올려둔 이동속도. **60 m 실내에선 너무 빠르다** |

**새 파일 1개**: `ReplicatedStorage/MapService` (ModuleScript)

```lua
M.MAPS = {
  JSN_Sangok   = { models = {"JSN_Sangok"},                              speed = 1.00, seam = true  },
  KRM_Palace   = { models = {"KRM_Palace"},                              speed = 0.72, seam = false },
  Hwaseong     = { models = {"Hwaseong Place", "Hwaseong Collision"},    speed = 1.00, seam = false },
}
M.activate(name)   -- 나머지 전부 ServerStorage 로, 고른 것만 Workspace 로
M.current()        -- 지금 Workspace 에 있는 맵 이름
```

설계 요점:
- **`models` 는 배열이다.** 화성이 `Place` + `Collision` 두 모델로 쪼개져 있어서 필수다
- 스왑은 **경기 사이 재정비 구간(`RESTART_DELAY = 20`)에만** 한다.
  3,396 파츠 모델을 재부모화하면 프레임이 튄다 — 전투 중엔 절대 안 한다
- `ServerStorage` 에 있으면 클라에 안 보이는 게 정상이다. **이 서비스만이 유일한 비활성화 경로**가
  되도록 하고, 손으로 옮기지 않는다 (이번 "안 보인다" 사고의 재발 방지)
- `speed` 배수를 `MovementSpeedServer` 가 읽게 한다. 실내 맵에서 산곡 속도로 뛰면 방을 지나쳐버린다
- `SeamFiller` 는 `seam` 플래그가 false 면 즉시 return
- 투표 UI 는 **이번 범위 밖**(사용자 선택). `MapService.activate()` 를 노출만 해두고
  당장은 서버에서 고정 호출한다

## Phase 7 — 검증

1. **블렌더**: `_export` FBX 를 다시 임포트해 스케일·원점 확인. 방 한 변이 2225 스터드인지 실측
2. **임포트 전 `overdare_stop`.** 플레이 중 쓰기 = Studio 메인 스레드 정지 (2026-08-25 재현됨)
3. 백업: `onlyoneshot_BEFORE_KRM_<날짜>.ovdrjm`
4. `overdare_screenshot` 으로 3실을 각각 눈으로 확인 (3D 뷰포트는 찍힌다 — UI 만 안 찍힌다)
5. **파츠 카운트 census** — `KRM_Palace` 총 파츠와 투명 파츠 비율을 찍는다. 목표 ≤600 / 투명 ≤10%
6. **프레임 A/B** — `KRM_Palace` 활성 vs `JSN_Sangok` 활성. 어제 쓴 `PerfProbe` 를 그대로 재사용
7. `MapService.activate()` 를 세 맵에 대해 돌려 **Workspace ↔ ServerStorage 왕복이 무손실**인지 확인
8. 실제 플레이: 스폰 2개 · 경계벽 · 점령지가 블라디미르 홀 안에 열리는지
9. **최종 판단은 사용자가 눈으로 한다.** 스스로 승인하지 않는다

---

## 범위 밖

- **3맵 투표 UI** — 사용자 선택으로 제외. `MapService` API 만 준비한다
- 로비 UI 추가 수정 (별건으로 진행 중)
- `JSN_Sangok` 의 1,669개 투명 콜리전 프록시 정리 (다음 최적화 과제)
- 게오르기옙스키 홀, 대성당 등 나머지 크렘린 실내
- 문 여닫기, 파괴 가능 오브젝트
