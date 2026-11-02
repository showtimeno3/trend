"""최근 90일 스냅샷(data/*.json)으로 화면용 site/history.json 을 만든다."""
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
WINDOW = 14
KEYWORD_DAYS = 7
KEYWORD_MIN = 3
KEYWORD_TOP = 8
TOKEN_RE = re.compile(r"[a-z][a-z0-9+#.\-]*[a-z0-9+#]|[a-z]")
STOPWORDS = set("""
a an the and or but if of in on at to for from by with without into onto over under about as is are was were be been
being it its this that these those there here we you your our my me i he she they them their his her not no yes do does
did done can could will would should may might must than then so such very more most less least just also only even
how what why when where who whom which while all any each every some many much few other another new via using use
used based show hn ask tell vs up down out off again once one two three via how-to you're it's i'm don't
towards toward through across between among per non pre multi large small via approach method methods paper study
""".split())


def tokenize(text: str) -> list[str]:
    words = (w.rstrip(".-") for w in TOKEN_RE.findall(text.lower()))
    return [w for w in words if len(w) >= 2 and w not in STOPWORDS]


def load_snapshots(data_dir: Path, today: str, days: int = 90) -> list[dict]:
    start = (date.fromisoformat(today) - timedelta(days=days - 1)).isoformat()
    paths = sorted(p for p in data_dir.glob("*.json") if start <= p.stem <= today)
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def _ok(s: dict, src: str, key: str):
    return s.get(src, {}).get(key)


def _stale(today: str, then: str) -> int:
    try:
        return (date.fromisoformat(today) - date.fromisoformat(then)).days
    except ValueError:
        return 0


def _latest(snaps: list[dict], src: str, key: str) -> dict:
    for s in reversed(snaps):
        items = _ok(s, src, key)
        if items:
            return {"date": s["date"], "stale_days": _stale(snaps[-1]["date"], s["date"]), key: items}
    return {"error": "수집 실패"}


def _github(snaps: list[dict], dates14: list[str]) -> dict:
    good = [s for s in snaps if _ok(s, "github", "repos")]
    if not good:
        return {"error": "수집 실패"}
    cur = good[-1]
    prev = {r["name"]: r["rank"] for r in _ok(good[-2], "github", "repos")} if len(good) > 1 else None
    stars_by_date = {s["date"]: {r["name"]: r["stars"] for r in _ok(s, "github", "repos")} for s in good}
    repos = []
    for r in _ok(cur, "github", "repos"):
        raw = [stars_by_date.get(d, {}).get(r["name"]) for d in dates14]
        base = next((v for v in raw if v is not None), None)
        spark = [None if v is None else v - base for v in raw]
        was = prev.get(r["name"]) if prev is not None else None
        repos.append({**r,
                      "move": None if was is None else was - r["rank"],
                      "is_new": prev is not None and was is None,
                      "spark": spark})
    cur_names = {r["name"] for r in repos}
    top5 = [r["name"] for r in sorted(repos, key=lambda r: -r["stars_week"])[:5]]
    return {
        "date": cur["date"],
        "stale_days": _stale(snaps[-1]["date"], cur["date"]),
        "repos": repos,
        "entered": [{"name": r["name"], "rank": r["rank"]} for r in repos if r["is_new"]],
        "dropped": [{"name": n, "rank": k} for n, k in sorted((prev or {}).items(), key=lambda x: x[1])
                    if n not in cur_names],
        "top5": top5,
    }


def _words(s: dict) -> Counter:
    texts = [i.get("title", "") for i in _ok(s, "hn", "items") or []]
    texts += [r.get("desc", "") for r in _ok(s, "github", "repos") or []]
    texts += [p.get("title", "") for p in _ok(s, "arxiv", "papers") or []]
    return Counter(tokenize(" ".join(texts)))


def _complete(s: dict) -> bool:
    return all(_ok(s, src, key) for src, key in (("github", "repos"), ("hn", "items"), ("arxiv", "papers")))


def _keywords(snaps: list[dict]) -> dict:
    # 세 소스가 모두 성공한 날만 비교 (일부 실패한 날은 빈도가 낮아져 왜곡됨)
    full = [s for s in snaps if _complete(s)]
    if not _complete(snaps[-1]) or len(full) - 1 < KEYWORD_DAYS:
        return {"ready": False, "items": []}
    today = _words(full[-1])
    prior = [_words(s) for s in full[-1 - KEYWORD_DAYS:-1]]
    items = []
    for word, n in today.items():
        if n < KEYWORD_MIN:
            continue
        avg = sum(c[word] for c in prior) / KEYWORD_DAYS
        items.append({"word": word, "today": n, "avg": round(avg, 1),
                      "change_pct": round((n - avg) / max(avg, 1) * 100)})
    items.sort(key=lambda x: (-x["change_pct"], -x["today"], x["word"]))
    return {"ready": True, "items": items[:KEYWORD_TOP]}


def build_history(snaps: list[dict]) -> dict:
    snaps = sorted(snaps, key=lambda s: s["date"])
    last = date.fromisoformat(snaps[-1]["date"])
    # 달력 기준 14일: 스냅샷 파일이 없는 날도 칸을 남겨 선이 끊기게
    dates14 = [(last - timedelta(days=WINDOW - 1 - i)).isoformat() for i in range(WINDOW)]
    return {
        "updated": snaps[-1]["date"],
        "dates14": dates14,
        "github": _github(snaps, dates14),
        "hn": _latest(snaps, "hn", "items"),
        "arxiv": _latest(snaps, "arxiv", "papers"),
        "keywords": _keywords(snaps),
    }


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    snaps = load_snapshots(ROOT / "data", today)
    if not snaps:
        raise SystemExit("data/ 에 스냅샷이 없음. 먼저 python collect.py 실행")
    out = ROOT / "site" / "history.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(build_history(snaps), ensure_ascii=False), encoding="utf-8")
    print(out)
