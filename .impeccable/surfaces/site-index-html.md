---
version: 1
slug: "site-index-html"
primary_target: "site/index.html"
related_targets: []
---

# 대시보드 (site/index.html)

Scope: 단일 페이지 대시보드. Mode: Operate.
Audience/job: 개발자 본인과 링크 받은 지인. 폰·PC 비슷한 비중. 열자마자 이번 주 별 많이 받은 레포와 어제 대비 변화를 고른다.
Constraints: PRODUCT.md 참조. 한국어 UI, 원문 병기 번역, 해커 코스프레(검정+형광) 금지, 폰에서 편해야 함.
Chosen: 역 출발 안내판 (split-flap concourse). Memorable moment: 하루 한 번 갱신된 숫자가 판 단위로 따르륵 넘어가며 오늘 값에 멈춤.

## Direction contract

THESIS: 하루 한 번 갱신되는 역 출발 안내판. 순위표 자체가 페이지의 주인공이고, 흰 카드 그리드·지표 카드 템플릿은 거부한다.

OWN-WORLD: 무광 판 검정 #0B0B0D 위 흰 페인트 글자 #F2F2F2, 브러시드 스틸 프레임 #2A2D31·#3A3E44 바탕, 스틸 라이트 #A7AAAF 라벨, 지연 앰버 #FFB000 = NEW·강조, 취소 레드 #FF6B5E = 하락·실패 (원래 #E5534B는 판 #141518 위 작은 글자에서 4.5:1 미달이라 밝힘), 상승 = 흰 굵은 ▲. 숫자는 고정 칸(판) 안에 가운데 가는 분할선. 응축된 Barlow Condensed(라틴·숫자) + Gothic A1(한글). 둥근 모서리 2px 이하, 발광·형광 없음.

STORY: 들어오면 판이 오늘 값으로 넘어가며 멈춘다 → 순위·변동·7일 증가를 한 줄씩 읽는다 → 아래로 14일 추이, 뜨는 키워드, HN·arXiv 판으로 내려간다 → 제목을 눌러 원문으로 나간다.

FIRST VIEWPORT: 상단 스틸 바(제목, 섹션 링크 레포·키워드·HN·arXiv, 갱신 시각). 그 아래 판 카운터 4칸 띠(1위 7일 증가, 새로 진입, HN 최고점, 뜨는 키워드). 본문은 넓은 판: 순위(2칸 판)·변동 칩·레포+한국어 설명+원문·언어·14일 추이·7일 증가(판 숫자). 데스크톱 오른쪽 좁은 칸에 새로 진입/빠짐 판. 폰은 1열로 쌓고 표는 행을 2줄 카드형 행으로 접는다.

FORM: 역 출발 안내판 challenger (signals-instruments-split-flap-concourse), 다시 굴린 1회차에서 사용자가 선택. seed:4f2a7c75da33dffa
Signature move: 로드 시 순위·숫자 판이 문자 단위로 위에서 아래로 넘어가는 캐스케이드(행마다 시차), prefers-reduced-motion에서는 즉시 최종값.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
