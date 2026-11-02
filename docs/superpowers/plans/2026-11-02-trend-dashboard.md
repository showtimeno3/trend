# 개발 트렌드 대시보드 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Trending · Hacker News · arXiv 를 매일 수집해 시안 D 형태의 정적 대시보드를 GitHub Pages에 배포한다.

**Architecture:** `collect.py`가 하루 스냅샷 `data/YYYY-MM-DD.json`을 쓰고, `build.py`가 최근 90일 스냅샷으로 화면용 `site/history.json`을 계산한다. `site/index.html`은 그 JSON을 fetch해 순수 JS로 렌더한다. GitHub Actions가 매일 collect → 커밋 → build → Pages 배포.

**Tech Stack:** Python 3.12 표준 라이브러리만 (urllib, re, html, json, xml.etree, unittest), 순수 HTML/CSS/JS, GitHub Actions, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-11-02-trend-dashboard-design.md`

## Global Constraints

- 외부 Python 패키지 금지. 표준 라이브러리만. JS 라이브러리도 없음 (그래프는 직접 SVG).
- 화면 문구는 한국어만.
- 소스별 실패 격리: 한 소스 실패가 다른 소스 저장/표시나 배포를 막지 않는다.
- 개수: Trending 25 (페이지가 주는 만큼), HN 10, arXiv 10. arXiv 분야 상수 `ARXIV_CATEGORY = "cs.AI"`.
- 스케줄: cron `0 0 * * *` (09:00 KST) + `workflow_dispatch`.
- 보관: build는 최근 90일 파일만 읽음. 파일 삭제 안 함.
- 레포 공개. Actions 권한 `contents: write`, `pages: write`, `id-token: write`.
- 커밋 메시지는 한국어.
- 테스트 실행: `python -m unittest -v` (레포 루트).

## 데이터 형식 (모든 Task 공통)

스냅샷 `data/YYYY-MM-DD.json`:
```json
{"date": "2026-11-02",
 "github": {"repos": [{"rank": 1, "name": "owner/repo", "desc": "...", "lang": "Python", "stars": 45209, "stars_week": 11566}]},
 "hn": {"items": [{"title": "...", "url": "https://...", "domain": "example.com", "points": 120, "comments": 33, "hn_url": "https://news.ycombinator.com/item?id=1"}]},
 "arxiv": {"papers": [{"title": "...", "first_author": "Kim", "n_authors": 5, "cat": "cs.AI", "url": "https://arxiv.org/abs/..."}]}}
```
실패한 소스는 해당 키 값이 `{"error": "<메시지>"}`. `desc`/`lang`은 없으면 `""`.

`site/history.json`:
```json
{"updated": "2026-11-02",
 "dates14": ["2026-10-20", "... 14개, 오름차순, 마지막=오늘"],
 "github": {"date": "2026-11-02", "stale_days": 0,
   "repos": [{"rank": 1, "name": "...", "desc": "...", "lang": "...", "stars": 0, "stars_week": 0,
              "move": 2, "is_new": false, "spark": [null, 10, 25]}],
   "entered": [{"name": "...", "rank": 2}], "dropped": [{"name": "...", "rank": 6}],
   "top5": ["owner/repo", "..."]},
 "hn": {"date": "...", "stale_days": 0, "items": []},
 "arxiv": {"date": "...", "stale_days": 0, "papers": []},
 "keywords": {"ready": true, "items": [{"word": "agent", "today": 12, "avg": 3.5, "change_pct": 243}]}}
```
- `move`: 이전 순위 − 오늘 순위 (양수=상승). 비교 기준 스냅샷이 없으면 `null`. `is_new`: 기준 스냅샷엔 있었는데 그 목록에 없던 레포.
- `spark`: `dates14` 각 날짜의 누적 증가량 (그날 stars − 창 안 첫 기록 stars), 기록 없으면 `null`.
- 한 번도 성공 못 한 소스: `{"error": "수집 실패"}`. `stale_days` > 0 이면 화면이 경고 표시.

## Review Focus

- Trending HTML 구조 변경 → 파서가 0개 반환: collect는 이를 실패(`error`)로 기록해야 함 (빈 성공으로 저장 금지). Task 1 테스트로 고정.
- 설명/언어 없는 레포 (Trending에 흔함) → `""`로 저장, 파서가 죽지 않음. Task 1.
- 첫날 / 이전 스냅샷 모두 실패 → `move=null`, 전부 NEW 아님, 화면 "–". Task 3.
- 중간에 하루 빠진 날 (수집 실패 또는 Trending 이탈) → spark `null` 로 선이 끊김, 0으로 그리지 않음. Task 3, Task 4.
- HN 항목에 `url` 없음 (Ask HN) → `url`은 hn_url, `domain`은 `news.ycombinator.com`. Task 2.

---

### Task 1: 레포 초기화 + Trending 파서

**Files:**
- Create: `collect.py`, `tests/__init__.py`, `tests/test_collect.py`, `tests/fixtures/trending.html`, `.gitignore`, `README.md`

**Interfaces:**
- Produces: `parse_trending(html: str) -> list[dict]` (스냅샷 `github.repos` 항목 형식, `rank` 1부터)

- [ ] **Step 1: `git init`, `.gitignore` (`__pycache__/`, `site/history.json`), 픽스처 준비.** `curl -sL "https://github.com/trending?since=weekly"` 결과에서 `<article class="Box-row">` 블록 3개만 남겨 `tests/fixtures/trending.html`로 저장. 그 중 하나는 `<p>` 설명과 `itemprop="programmingLanguage"`를 지워 "설명·언어 없음" 경우를 만든다. 픽스처의 실제 이름/숫자를 테스트 기대값에 쓴다.

- [ ] **Step 2: 실패하는 테스트 작성** (`tests/test_collect.py`)

```python
class TrendingTest(unittest.TestCase):
    def setUp(self):
        self.repos = parse_trending(Path("tests/fixtures/trending.html").read_text(encoding="utf-8"))
    def test_count_and_rank(self):
        self.assertEqual(len(self.repos), 3)
        self.assertEqual([r["rank"] for r in self.repos], [1, 2, 3])
    def test_fields(self):
        r = self.repos[0]
        self.assertEqual(r["name"], "<픽스처 첫 레포 owner/repo>")
        self.assertIsInstance(r["stars"], int)        # "45,209" → 45209
        self.assertIsInstance(r["stars_week"], int)   # "11,566 stars this week" → 11566
    def test_missing_desc_and_lang(self):
        r = self.repos[<지운 블록 index>]
        self.assertEqual((r["desc"], r["lang"]), ("", ""))
    def test_garbage_returns_empty(self):
        self.assertEqual(parse_trending("<html>nothing</html>"), [])
```

- [ ] **Step 3: 실행해 실패 확인** — `python -m unittest -v` → ImportError/NameError.

- [ ] **Step 4: `parse_trending` 구현.** `re`로 `<article class="Box-row">…</article>` 블록을 자르고 블록마다: 이름 = `href="/(owner/repo)/stargazers"`, 전체 별 = 그 stargazers `<a>` 안 마지막 숫자, 주간 = `([\d,]+) stars this week`, 설명 = 첫 `<p …>` 텍스트 (`html.unescape` + 공백 정리), 언어 = `itemprop="programmingLanguage">(.*?)<`. 이름이나 주간 별을 못 찾은 블록은 건너뜀.

- [ ] **Step 5: 통과 확인** — `python -m unittest -v` → OK.

- [ ] **Step 6: 커밋** — `git add -A && git commit -m "Trending 파서 추가"`

### Task 2: HN · arXiv 수집과 스냅샷 저장

**Files:**
- Modify: `collect.py`
- Create: `tests/fixtures/arxiv.xml` (실제 API 응답에서 entry 2개만 남김)
- Test: `tests/test_collect.py`

**Interfaces:**
- Consumes: `parse_trending`
- Produces:
  - `parse_arxiv(xml_text: str) -> list[dict]` (스냅샷 `arxiv.papers` 형식)
  - `hn_item(raw: dict) -> dict` (Firebase item JSON → 스냅샷 `hn.items` 형식)
  - `run_source(key: str, fn: Callable[[], list]) -> dict` → 성공 `{key: list}`, 예외 또는 빈 list면 `{"error": str}` (예외를 삼키고 로그만 출력)
  - `collect(today: str, out_dir: Path) -> Path` — 세 소스 실행, `out_dir/today.json` 덮어쓰기, 경로 반환
  - 실행: `python collect.py` (오늘 날짜는 KST 기준 `datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()`)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
def test_arxiv_parse(self):
    p = parse_arxiv(Path("tests/fixtures/arxiv.xml").read_text(encoding="utf-8"))
    self.assertEqual(len(p), 2)
    self.assertTrue(p[0]["url"].startswith("http"))
    self.assertGreaterEqual(p[0]["n_authors"], 1)
    self.assertNotIn("\n", p[0]["title"])   # 제목 줄바꿈 정리
def test_hn_item_without_url(self):
    it = hn_item({"id": 1, "title": "Ask HN: x", "score": 5, "descendants": 2})
    self.assertEqual(it["url"], "https://news.ycombinator.com/item?id=1")
    self.assertEqual(it["domain"], "news.ycombinator.com")
def test_hn_item_domain(self):
    self.assertEqual(hn_item({"id": 2, "title": "t", "url": "https://www.example.com/a", "score": 1})["domain"], "example.com")
def test_run_source_isolates_errors(self):
    self.assertEqual(run_source("repos", lambda: [1]), {"repos": [1]})
    self.assertIn("error", run_source("repos", lambda: 1 / 0))
    self.assertIn("error", run_source("repos", lambda: []))   # 0개 = 구조 변경으로 간주
```

- [ ] **Step 2: 실행해 실패 확인.**

- [ ] **Step 3: 구현.** HTTP는 `urllib.request` + `User-Agent` 헤더 + `timeout=20`. HN: `https://hacker-news.firebaseio.com/v0/topstories.json` 앞 10개 id → `item/{id}.json`. arXiv: `http://export.arxiv.org/api/query?search_query=cat:{ARXIV_CATEGORY}&sortBy=submittedDate&sortOrder=descending&max_results=10`, Atom 네임스페이스 `{http://www.w3.org/2005/Atom}`, 분야는 `arxiv:primary_category@term`. `domain`은 `urlparse().netloc`에서 `www.` 제거. JSON은 `ensure_ascii=False, indent=1`.

- [ ] **Step 4: 통과 확인** — `python -m unittest -v` → OK. 실제 수집 1회: `python collect.py` → `data/<오늘>.json` 생성, 세 키 모두 error 아님 확인.

- [ ] **Step 5: 커밋** — `git add -A && git commit -m "HN, arXiv 수집과 스냅샷 저장 추가"` (첫 실제 스냅샷 포함)

### Task 3: build.py — 화면용 계산

**Files:**
- Create: `build.py`, `tests/test_build.py`

**Interfaces:**
- Consumes: 스냅샷 형식 (위 "데이터 형식")
- Produces:
  - `load_snapshots(data_dir: Path, today: str, days: int = 90) -> list[dict]` (날짜 오름차순)
  - `build_history(snaps: list[dict]) -> dict` (`history.json` 형식, `updated` = 마지막 스냅샷 날짜)
  - `tokenize(text: str) -> list[str]`
  - 실행: `python build.py` → `site/history.json`

- [ ] **Step 1: 실패하는 테스트 작성.** 헬퍼 `snap(date, repos=None, hn=None, arxiv=None)`로 메모리 스냅샷을 만든다 (repos는 `(name, stars, stars_week)` 튜플 목록 → rank 순서대로; `None`이면 그 소스 `{"error": "x"}`).

```python
def test_move_against_last_successful(self):
    h = build_history([snap("d1", repos=[("a",10,5),("b",10,4)]),
                       snap("d2"),                                   # github 실패
                       snap("d3", repos=[("b",12,6),("c",1,1)])])
    r = {x["name"]: x for x in h["github"]["repos"]}
    self.assertEqual(r["b"]["move"], 1)
    self.assertTrue(r["c"]["is_new"])
    self.assertEqual(h["github"]["dropped"], [{"name": "a", "rank": 1}])
    self.assertEqual(h["github"]["entered"], [{"name": "c", "rank": 2}])
def test_first_day_has_no_move(self):
    h = build_history([snap("d1", repos=[("a",10,5)])])
    self.assertIsNone(h["github"]["repos"][0]["move"])
    self.assertFalse(h["github"]["repos"][0]["is_new"])
def test_spark_gaps_are_null(self):
    h = build_history([snap("d1", repos=[("a",100,1)]), snap("d2", repos=[("x",1,1)]), snap("d3", repos=[("a",130,1)])])
    a = next(x for x in h["github"]["repos"] if x["name"] == "a")
    self.assertEqual(a["spark"][-3:], [0, None, 30])
    self.assertEqual(len(a["spark"]), 14)
def test_stale_source_uses_last_good(self):
    h = build_history([snap("2026-11-01", hn=[{"title": "t"}]), snap("2026-11-02", hn=None)])
    self.assertEqual(h["hn"]["stale_days"], 1)
    self.assertEqual(len(h["hn"]["items"]), 1)
def test_never_succeeded(self):
    self.assertEqual(build_history([snap("d1", arxiv=None)])["arxiv"], {"error": "수집 실패"})
def test_keywords_need_7_prior_days(self):
    self.assertFalse(build_history([snap(f"d{i}") for i in range(7)])["keywords"]["ready"])
def test_tokenize(self):
    self.assertEqual(tokenize("Show HN: The Rust-based LLM agent, in C++!"), ["rust-based", "llm", "agent", "c++"])
```

- [ ] **Step 2: 실행해 실패 확인.**

- [ ] **Step 3: 구현 규칙.**
  - 날짜 테스트에 "d1" 같은 문자열을 쓰므로 `build_history`는 날짜를 문자열 정렬만 하고 파싱하지 않음. `stale_days`만 `date.fromisoformat` 사용 (파싱 실패 시 0).
  - "기준 스냅샷" = 마지막 github 성공 스냅샷 직전의 github 성공 스냅샷.
  - `dates14` = 마지막 14개 스냅샷 날짜 (14개 미만이면 있는 만큼, spark는 14칸 맞추도록 앞을 `null`로 채움).
  - `top5` = 오늘 repos 중 `stars_week` 상위 5개 이름.
  - `tokenize`: 소문자, `re.findall(r"[a-z][a-z0-9+#.\-]*[a-z0-9+#]|[a-z]", …)`, 2자 이상, `STOPWORDS`(영어 기본 불용어 + `show`, `hn`, `ask`, `via`, `using`, `new` 등 빌더가 채움) 제외.
  - 키워드: 텍스트 = HN 제목 + repo desc + arXiv 제목. 오늘 빈도 vs 직전 7개 스냅샷 평균. `ready` = 직전 스냅샷 ≥ 7. 후보 = 오늘 빈도 ≥ 3. `change_pct = round((today - avg) / max(avg, 1) * 100)`. 상위 8개. 준비 안 되면 `items: []`.

- [ ] **Step 4: 통과 확인** — `python -m unittest -v` → OK. `python build.py` → `site/history.json` 생성.

- [ ] **Step 5: 커밋** — `git commit -m "화면용 history 계산(build.py) 추가"`

### Task 4: site/index.html — 시안 D 렌더

**Files:**
- Create: `site/index.html` (CSS·JS 인라인, 한 파일)

**Interfaces:**
- Consumes: `site/history.json` 형식

시안: https://claude.ai/artifact/DZYr9r6bJLrzCt1GoNUKNp 의 아트보드 "D. 풀 + HN, arXiv". 볼 수 없으면 아래가 기준.

- [ ] **Step 1: 구조와 스타일.** 위→아래: 헤더(제목 "개발 트렌드 대시보드", 갱신일, 섹션 이동 링크 레포/키워드/HN/arXiv) → 요약 카드 4개 → [14일 그래프 | 새로 진입·순위에서 빠짐] → 레포 표(순위, 변동, 레포+설명, 언어, 14일 추이, 7일 증가) → 뜨는 키워드 → [HN | arXiv]. 색: 바탕 `#f7f7f5`, 카드 `#fff` + `1px solid #e4e4e0` + radius 10px, 글자 `#17181c`, 보조 `#5b5f68`, 강조 `#c2410c`, 상승 `#0f6b62`, 하락 `#9a3412`, NEW `#1d4ed8`. 그래프 5색 `#1d4ed8 #c2410c #0f766e #7c3aed #a16207`. 글꼴 Google Fonts `Noto Sans KR`, 숫자 `JetBrains Mono`. 폭 max 1160px, 2단 영역은 `flex-wrap`으로 폰에서 쌓이고 표는 `overflow-x: auto`.
- [ ] **Step 2: 렌더 JS.** `fetch("history.json")` → 각 섹션 렌더. 모든 외부 텍스트는 `textContent`로 넣음 (`innerHTML`에 데이터 금지 — XSS 방지). 변동: `move>0` "▲ n", `<0` "▼ n", `0` "–", `null` "–", `is_new` "NEW". 카드 4개 문구는 스펙 4.2.1. `stale_days>0` 섹션 위에 "오늘 수집 실패 · N일 전 데이터", `error` 섹션은 "수집 실패"만. 키워드 `ready=false` → "데이터 쌓는 중 (7일 필요)".
- [ ] **Step 3: SVG.** 그래프 viewBox 640×220, `null`에서 선을 끊는다 (`null` 기준으로 구간을 나눠 polyline 여러 개). y축 최대 = top5 spark 최댓값 (0이면 1). 미니 추이선 96×28 같은 규칙.
- [ ] **Step 4: 수동 확인.** `python build.py && python -m http.server -d site 8000` → 브라우저 `http://localhost:8000` 에서 6개 섹션 표시, 폭 390px에서 가로 스크롤 없음(표 박스 제외), 콘솔 에러 없음. 실패 경우: `history.json`의 `hn`을 `{"error":"수집 실패"}`로 손으로 바꿔 경고 표시 확인 후 원복.
- [ ] **Step 5: 커밋** — `git commit -m "대시보드 페이지 추가"`

### Task 5: GitHub Actions + 배포

**Files:**
- Create: `.github/workflows/daily.yml`
- Modify: `README.md` (설치 없음, 로컬 실행법, Pages 설정법 한국어 몇 줄)

- [ ] **Step 1: 워크플로 작성.** 트리거 `schedule: cron "0 0 * * *"` + `workflow_dispatch` + `push` (branch `main`, `paths-ignore: ["data/**"]` — 코드 변경 시 재배포, 봇의 데이터 커밋으로 재실행 안 되게). job 1개: checkout → `actions/setup-python@v5` (3.12) → `python -m unittest` → `python collect.py` → data 변경 있으면 `github-actions[bot]`로 커밋·푸시 (메시지 `"데이터: <날짜> 스냅샷"`) → `python build.py` → `actions/upload-pages-artifact@v3` (path `site`) → `actions/deploy-pages@v4`. `permissions: contents: write, pages: write, id-token: write`. `concurrency: group: daily, cancel-in-progress: false`. collect 단계는 소스 실패로 job을 실패시키지 않음 (collect.py는 소스 오류에도 exit 0).
- [ ] **Step 2: 사용자 확인 후 GitHub 공개 레포 생성·푸시.** 외부 공개 동작이므로 레포 이름을 사용자에게 확인. `gh repo create <이름> --public --source . --push`. 그 뒤 Settings › Pages › Source = "GitHub Actions" (또는 `gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow`).
- [ ] **Step 3: 수동 실행 확인.** `gh workflow run daily.yml` → `gh run watch` 성공 → Pages URL 열어 화면 확인.
- [ ] **Step 4: 커밋** — README 갱신분 `git commit -m "자동 수집·배포 워크플로 추가"` 후 push.
