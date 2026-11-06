---
name: 개발 트렌드
description: 하루 한 번 갱신되는 역 출발 안내판 형태의 개발 트렌드 대시보드
colors:
  steel: "#2a2d31"
  steel-2: "#33373c"
  steel-3: "#4a4e55"
  board: "#141518"
  flap: "#0b0b0d"
  seam: "#26282c"
  ink: "#f2f2f2"
  ink-dim: "#dcdde0"
  label: "#a7aaaf"
  amber: "#ffb000"
  red: "#ff6b5e"
typography:
  counter:
    fontFamily: "'Barlow Condensed', 'Gothic A1', sans-serif"
    fontSize: "64px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.02em"
    fontFeature: "tnum"
  headline:
    fontFamily: "'Gothic A1', system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    letterSpacing: "0.02em"
  title:
    fontFamily: "'Barlow Condensed', 'Gothic A1', sans-serif"
    fontSize: "21px"
    fontWeight: 700
    letterSpacing: "0.03em"
  body:
    fontFamily: "'Gothic A1', system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "'Gothic A1', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'Gothic A1', system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    letterSpacing: "0.02em"
  label-cond:
    fontFamily: "'Barlow Condensed', 'Gothic A1', sans-serif"
    fontSize: "16px"
    fontWeight: 700
    letterSpacing: "0.06em"
rounded:
  flap: "2px"
  board: "3px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "20px"
  page-mobile: "12px"
  page: "20px"
components:
  board:
    backgroundColor: "{colors.board}"
    rounded: "{rounded.board}"
    padding: "18px 20px 20px"
  flap-tile:
    backgroundColor: "{colors.flap}"
    textColor: "{colors.ink}"
    typography: "{typography.counter}"
    rounded: "{rounded.flap}"
    width: "0.78em"
    height: "1.18em"
  move-chip-up:
    backgroundColor: "{colors.flap}"
    textColor: "{colors.ink}"
    typography: "{typography.label-cond}"
    rounded: "{rounded.flap}"
    padding: "3px 8px"
  move-chip-down:
    backgroundColor: "{colors.flap}"
    textColor: "{colors.red}"
    typography: "{typography.label-cond}"
    rounded: "{rounded.flap}"
    padding: "3px 8px"
  move-chip-new:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.flap}"
    typography: "{typography.label-cond}"
    rounded: "{rounded.flap}"
    padding: "3px 8px"
  warn-note:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.flap}"
    rounded: "{rounded.flap}"
    padding: "6px 10px"
  nav-link:
    textColor: "{colors.label}"
    typography: "{typography.label-cond}"
    padding: "10px 12px"
    height: "44px"
---

# Design System: 개발 트렌드

## Overview

**Creative North Star: "역 출발 안내판 (The Split-Flap Concourse)"**

이 시스템은 기차역 대합실의 출발 안내판이다. 브러시드 스틸 프레임(여기서는 평평한 스틸 면) 위에 무광 검정 판(board)이 박혀 있고, 숫자는 글자마다 고정된 판 칸(flap tile)에 흰 페인트로 칠해져 있으며 가운데를 가는 분할선이 가로지른다. 순위표 자체가 페이지의 주인공이고, 다른 모든 것은 그 판을 받치는 프레임이다.

밀도는 높지만 차분하다. 강조는 안내판 문법을 따른다: 지연 앰버는 NEW·주목, 취소 레드는 하락·실패, 상승은 별도 색 없이 흰 굵은 삼각형. 발광, 형광, 네온, 그라디언트 강조는 없다. 깊이는 그림자가 아니라 스틸 → 판 → 칸의 명도 단계로 만든다.

움직임은 하루 한 번의 사건이다. 데이터가 로드되면 숫자 칸이 문자 단위로 위에서 아래로 넘어가며(행마다 시차) 오늘 값에 멈춘다. 그 외에는 정지 상태이며, `prefers-reduced-motion`에서는 즉시 최종값을 보여준다.

**Key Characteristics:**
- 스틸 프레임 위 무광 검정 판, 판 안에 글자 단위 칸
- 응축된 라틴·숫자(Barlow Condensed) + 한글(Gothic A1) 이중 서체
- 앰버 = 주목/NEW, 레드 = 하락/실패, 흰 ▲ = 상승; 색만으로 구분하지 않음
- 모서리 3px 이하, 발광 없음, 그림자는 칸의 물성에만
- 숫자 판 캐스케이드가 유일한 장식적 움직임

## Colors

차가운 무채색 스틸·검정 단계 위에 신호색 두 개(앰버, 레드)만 얹은 안내판 팔레트.

### Primary
- **지연 앰버 (Delay Amber)** (`amber`): NEW 칩과 경고 띠의 바탕, 1위 증가 수치·키워드 증가율 판의 글자색, 순위표 14일 스파크라인, 포커스 링, 링크 hover 밑줄, 텍스트 선택 바탕. 한 화면에서 "지금 봐야 할 것"에만 쓴다.

### Secondary
- **취소 레드 (Cancel Red)** (`red`): 순위 하락 칩의 글자·삼각형. 원래 안내판 레드 #E5534B는 판 위 작은 글자에서 4.5:1에 못 미쳐 의도적으로 밝힌 값이다.

### Neutral
- **페인트 화이트 (Paint White)** (`ink`): 판 칸 글자, 레포 이름, 본문 제목, 상승 칩. 상승은 이 흰색 + 굵은 ▲로만 표현한다.
- **흐린 페인트 (Faded Paint)** (`ink-dim`): 레포 한국어 설명 등 판 위 2차 본문.
- **스틸 라이트 (Steel Light)** (`label`): 판 제목(h2), 표 머리, 메타 정보, 원문 병기, 내비게이션 기본 상태, 변동 없음 칩.
- **스틸 프레임 (Steel Frame)** (`steel`): 페이지 바탕과 상단 바. 원래 계약은 브러시드 스틸 텍스처였으나, 반복 줄무늬 텍스처가 slop 검출에 걸려 평평한 스틸로 내렸다. 상단 바만 #34383d → `steel`의 아주 옅은 세로 음영을 가진다.
- **스틸 2 / 스틸 3** (`steel-2`, `steel-3`): `steel-3`은 판 테두리, 표 머리 구분선, 카운터 띠 사이 2px 홈, 스크롤바 손잡이.
- **판 검정 (Board Black)** (`board`): 모든 섹션 판의 바탕.
- **칸 검정 (Flap Black)** (`flap`): 판 칸 아래쪽 절반, 칩 바탕, NEW·경고 위 글자색.
- **이음매 (Seam)** (`seam`): 판 안의 행 구분선과 그래프 눈금선.

### Named Rules
**The Two Signals Rule.** 신호색은 앰버와 레드 둘뿐이다. 세 번째 강조색(초록 상승, 파랑 링크 등)을 들이지 않는다.

**The No Glow Rule.** 어떤 색도 빛나지 않는다. 형광, 네온, text-shadow 발광, 검정+형광 "해커" 조합은 이 세계에 없다.

## Typography

**Display Font:** Barlow Condensed (with Gothic A1, sans-serif) — 숫자, 레포 이름, 칩, 내비게이션, 축 라벨
**Body Font:** Gothic A1 (with system-ui, sans-serif) — 한국어 제목·설명·라벨 전부

**Character:** 응축된 산세리프 숫자는 안내판 칸에 꽉 차는 기계적 리듬을 주고, Gothic A1은 같은 무게감으로 한글을 받친다. 숫자는 항상 `tabular-nums`.

### Hierarchy
- **Counter** (600, 64px, 모바일 34px, line-height 1): 상단 카운터 띠의 판 숫자와 뜨는 키워드 단어(700, 앰버).
- **Flap 크기 단계** (600): 순위 28px(모바일 22px), 7일 증가 22px(모바일 17px), 키워드 증가율 22px, HN 점수 20px. 칸은 글자 크기에 비례(`em`)해 커진다.
- **Headline** (800, 19px): 판 제목, `label` 색. 옆의 `small` 설명은 12px 500.
- **Title** (Barlow Condensed 700, 21px, 0.03em): 순위표 레포 이름. 사이드 판에서는 18px, 키워드 단어는 22px.
- **Body** (400, 15px, 1.5): 기본 본문, HN·arXiv 제목(700). 레포 설명은 14px.
- **Label** (700, 12–13px, 0.02em): 표 머리, 카운터 라벨, 메타·원문 병기(12px, 400).
- **Label-cond** (Barlow Condensed 600–700, 15–17px, 0.06–0.12em): 언어, 칩, arXiv 분류, 내비게이션, 그래프 축.

### Named Rules
**The Two Scripts Rule.** 라틴 문자와 숫자는 Barlow Condensed, 한글은 Gothic A1. 응축 스택은 언제나 Gothic A1을 폴백으로 둬서 한글이 섞여도 무너지지 않게 한다.

**The Tabular Rule.** 숫자는 전부 `tabular-nums`. 판 칸이든 아니든 자릿수가 흔들리지 않는다.

## Layout

최대 폭 1280px, 좌우 20px 여백(모바일 12px)의 단일 세로 흐름. 섹션 판 사이 간격 20px(모바일 12px). 상단 바는 sticky, 최소 높이 60px.

- 상단: 4칸 카운터 띠(모바일 2×2). 칸 사이는 `steel-3` 2px 홈으로 나뉜 하나의 판.
- 본문 첫 줄: 넓은 순위표 판 + 오른쪽 300px 사이드 칸(새로 진입/빠짐, sticky). 1000px 이하에서 1열로 내려가고 사이드는 2열, 640px 이하에서 1열.
- 그 아래: 14일 추이 그래프(전폭), 키워드(최소 280px 자동 열), HN·arXiv 2열(1000px 이하 1열).
- 640px 이하에서 순위표는 표 머리를 숨기고 각 행을 2줄 그리드 행(순위 | 레포 / 순위 | 변동·추이·증가)으로 접는다. 언어 열은 숨긴다.
- 행 리듬: 표 셀 12px 10px, 목록 행 10–12px 위아래, 판 안쪽 18px 20px 20px(모바일 14px 12px).
- 섹션 링크 대상은 `scroll-margin-top: 72px`로 sticky 바 아래에 멈춘다.

## Elevation & Depth

평평한 명도 층위 시스템이다. 깊이는 스틸(가장 밝음) → 판(어두움) → 칸(가장 어두움)의 순서로 내려가며 표현하고, 판에는 그림자가 없다. 그림자는 칸의 물리적 질감에만 쓴다.

### Shadow Vocabulary
- **칸 질감** (`box-shadow: inset 0 1px 0 #2b2d32, 0 1px 2px rgba(0,0,0,.5)`): 판 칸 위쪽 가장자리의 얇은 하이라이트와 아래 1px 접지 그림자. 칸이 판에 박혀 있다는 느낌만 준다.

### Named Rules
**The Flat Board Rule.** 판(섹션)은 그림자 없이 `steel-3` 1px 테두리로만 프레임에서 분리된다. 떠 있는 카드는 없다.

## Shapes

모서리는 거의 직각이다. 판 3px, 칸·칩·경고 띠 2px, 포커스 링 1px. 테두리는 1px 실선(`steel-3` 바깥, `seam` 안쪽 행). 칸의 형태가 이 시스템의 시그니처다: 폭 0.78em, 높이 1.18em의 세로 직사각형, 위 절반 #1b1c20 / 아래 절반 `flap`의 두 톤, 정중앙 1px 검정 분할선(카운터 크기에서는 2px). 칸 사이 간격 0.09em.

## Components

### 판 칸 (Flap Tile) — 시그니처
글자 하나당 칸 하나. 숫자·기호(+, 콤마, %)가 모두 각자의 칸에 들어간다. 자리 맞춤용 빈 칸은 같은 칸을 글자 없이 보여준다. 읽기 도구에는 칸이 아닌 완성된 문자열 하나만 전달한다(시각 칸은 `aria-hidden`). 톤 변형: 기본 흰색, 앰버(1위 증가, 키워드 증가율).

**움직임:** 로드 후 각 숫자 칸이 4–8회 다른 숫자를 거쳐 최종값에 멈춘다. 한 번 넘김은 70ms `ease-out`(세로 0.25배에서 펴지며 밝기 0.6 → 1), 칸마다 18ms 시차(최대 900ms). `prefers-reduced-motion: reduce`에서는 애니메이션 없이 최종값.

### 판 (Board)
- **Corner Style:** 3px
- **Background:** `board`
- **Shadow Strategy:** 없음 (Elevation 참조)
- **Border:** 1px `steel-3`
- **Internal Padding:** 18px 20px 20px, 모바일 14px 12px
- 제목은 `label` 색 800 굵기, 보조 설명은 같은 줄 기준선 정렬의 작은 글씨.

### 변동 칩 (Move Chip)
- **Style:** `flap` 바탕, Barlow Condensed 700 16px, 2px 모서리, 3px 8px.
- **State:** 상승 = 흰색 + 위 삼각형(인라인 SVG 9px), 하락 = 레드 + 아래 삼각형, NEW = 앰버 바탕에 `flap` 글자, 변동 없음 = `label` 색 대시. 사이드 판의 "N위"/"어제 N위"도 같은 칩을 쓴다.

### 경고 띠 (Warn Note)
앰버 바탕, `flap` 글자 13px 700, 2px 모서리, 6px 10px. "수집 실패", "N일 전 데이터"처럼 데이터 정직성을 알릴 때만.

### 분류 태그 (Category Tag)
arXiv 분류. `flap` 바탕에 앰버 Barlow Condensed 15px, 3px 7px, 2px 모서리.

### Navigation
상단 스틸 바 안. Barlow Condensed 600 17px(모바일 16px), 0.12em 자간, `label` 색, 최소 44px 터치 높이. hover 시 `ink`로 밝아지고 밑줄 없음. 갱신 시각은 오른쪽 13px `label`, 모바일에서는 다음 줄 전폭.

### 링크
기본 밑줄 없음, hover 시 앰버 밑줄(offset 3px). 메타 안 보조 링크(댓글 수)는 상시 `steel-3` 밑줄. 포커스는 전역 2px 앰버 아웃라인, offset 2px.

### 추이 그래프
직접 그린 SVG. 눈금선은 `seam`, 선 3px 둥근 끝. 시리즈 색은 `ink`, `amber`, `label`, `red`, `ink`(5번째는 10 8 점선)로 팔레트 안에서만 고른다. 행 안 스파크라인은 92×26px, 앰버 2px, 모든 행이 같은 축척. 연속 기록 3일 미만이면 선 대신 "기록 N일" 글자.

## Do's and Don'ts

### Do:
- **Do** 새 숫자 지표는 판 칸(flap tile)으로 그리고 `tabular-nums`를 유지한다.
- **Do** 새 섹션은 `board` 바탕 + 1px `steel-3` 테두리 + 3px 모서리의 판으로 만든다.
- **Do** 상승·하락은 삼각형 기호와 색을 함께 써서 색만으로 구분하지 않는다.
- **Do** 작은 글자 위 신호색은 판 바탕에서 4.5:1 이상을 확인한다(레드를 #FF6B5E로 밝힌 이유).
- **Do** 라틴·숫자는 Barlow Condensed, 한글은 Gothic A1로 나눈다.
- **Do** 움직임을 추가하면 `prefers-reduced-motion`에서 즉시 최종 상태가 되게 한다.

### Don't:
- **Don't** 흰 카드 그리드나 지표 카드 템플릿을 쓴다. 이 세계는 검정 판 위의 안내판이다.
- **Don't** 검정 바탕에 형광·네온 글자를 쓰거나 발광 효과를 넣는다.
- **Don't** 앰버·레드 외의 강조색(초록 상승 등)을 들인다.
- **Don't** 모서리를 3px보다 둥글게 하거나 판에 떠 있는 그림자를 준다.
- **Don't** 스틸 프레임에 반복 줄무늬 텍스처를 다시 넣는다. 평평한 스틸로 둔다.
