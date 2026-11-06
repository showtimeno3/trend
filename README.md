# 개발 트렌드 대시보드

GitHub Trending(주간 별 증가), Hacker News 인기 글, arXiv 최신 논문(`cs.AI`)을 매일 수집해 한 페이지로 보여준다.
Python 표준 라이브러리만 쓰므로 설치할 패키지가 없다 (Python 3.12+).

## 로컬 실행

```sh
python collect.py                       # data/YYYY-MM-DD.json 저장 (같은 날 재실행 시 덮어씀)
python build.py                         # 최근 90일 → site/history.json
python -m http.server -d site 8000      # http://localhost:8000
python -m unittest -v                   # 테스트
```

## 자동화

`.github/workflows/daily.yml` 이 매일 08:17 KST 에 (GitHub 사정으로 늦어질 수 있음) 수집 → `data/` 커밋 → 빌드 → GitHub Pages 배포를 한다.
Actions 탭에서 수동 실행(workflow_dispatch)도 된다. 코드만 push 하면 수집 없이 재배포만 한다.

처음 한 번: 레포 Settings › Pages › Source 를 **GitHub Actions** 로 설정.

## 설정

- arXiv 분야, 개수: `collect.py` 상단 `ARXIV_CATEGORY`, `HN_COUNT`, `ARXIV_COUNT`
- 한국어 번역: 레포 Settings › Secrets and variables › Actions 에 `GEMINI_API_KEY`(기본)와 `DEEPL_API_KEY`(예비) 추가.
  Gemini가 실패·누락한 문구만 DeepL로 보낸다. 둘 다 없거나 실패하면 원문만 표시. 모델 순서는 `collect.py` 의 `GEMINI_MODELS`.
  최근 30일 스냅샷에 이미 있는 문구는 다시 번역하지 않고 재사용한다 (DeepL 한도 절약).
  로컬: `DEEPL_API_KEY=... python collect.py`
- 키워드 불용어: `build.py` 의 `STOPWORDS`
- 키워드 트렌드는 스냅샷이 8일치(오늘 + 직전 7일) 쌓여야 나온다.
