"""GitHub Trending · Hacker News · arXiv 를 수집해 data/YYYY-MM-DD.json 으로 저장한다."""
import html
import json
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ARXIV_CATEGORY = "cs.AI"
# 앞에서부터 시도. 무료 키는 최신 Flash가 자주 503(과부하). -latest 별칭은 모델 폐기에 버팀.
GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
HN_COUNT = 10
ARXIV_COUNT = 10
UA = {"User-Agent": "trend-dashboard (+https://github.com)"}
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

ARTICLE_RE = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
NAME_RE = re.compile(r'href="/([^/"]+/[^/"]+)/stargazers"[^>]*>(.*?)</a>', re.S)
WEEK_RE = re.compile(r"([\d,]+) stars this week")
DESC_RE = re.compile(r"<p(?:\s[^>]*)?>(.*?)</p>", re.S)  # <path> 와 구분
LANG_RE = re.compile(r'itemprop="programmingLanguage">(.*?)<', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _text(fragment: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub("", fragment)).split())


def _int(s: str) -> int:
    return int(s.replace(",", ""))


def parse_trending(page: str) -> list[dict]:
    repos = []
    for block in ARTICLE_RE.findall(page):
        name, week = NAME_RE.search(block), WEEK_RE.search(block)
        if not name or not week:
            continue
        stars = re.findall(r"[\d,]+", _text(name.group(2)))
        desc, lang = DESC_RE.search(block), LANG_RE.search(block)
        repos.append({
            "rank": len(repos) + 1,
            "name": name.group(1),
            "desc": _text(desc.group(1)) if desc else "",
            "lang": _text(lang.group(1)) if lang else "",
            "stars": _int(stars[-1]) if stars else 0,
            "stars_week": _int(week.group(1)),
        })
    return repos


def parse_arxiv(xml_text: str) -> list[dict]:
    papers = []
    for e in ET.fromstring(xml_text).iter(ATOM + "entry"):
        authors = [a.findtext(ATOM + "name", "") for a in e.findall(ATOM + "author")]
        cat = e.find(ARXIV_NS + "primary_category")
        link = next((l.get("href") for l in e.findall(ATOM + "link") if l.get("rel") == "alternate"),
                    e.findtext(ATOM + "id", ""))
        papers.append({
            "title": " ".join(e.findtext(ATOM + "title", "").split()),
            "first_author": authors[0] if authors else "",
            "n_authors": len(authors),
            "cat": cat.get("term", "") if cat is not None else "",
            "url": link,
        })
    return papers


def hn_item(raw: dict) -> dict:
    hn_url = f"https://news.ycombinator.com/item?id={raw['id']}"
    url = raw.get("url") or hn_url
    domain = urlparse(url).netloc.removeprefix("www.")
    return {
        "title": raw.get("title", ""),
        "url": url,
        "domain": domain,
        "points": raw.get("score", 0),
        "comments": raw.get("descendants", 0),
        "hn_url": hn_url,
    }


def run_source(key: str, fn) -> dict:
    try:
        items = fn()
        if not items:
            raise ValueError("0개 수집 (페이지 구조 변경 가능성)")
        return {key: items}
    except Exception as exc:  # 소스 하나 실패가 나머지를 막지 않게
        print(f"[{key}] 수집 실패: {exc!r}", file=sys.stderr)
        return {"error": repr(exc)}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def fetch_github() -> list[dict]:
    return parse_trending(_get("https://github.com/trending?since=weekly"))


def fetch_hn(get=None) -> list[dict]:
    get = get or _get
    base = "https://hacker-news.firebaseio.com/v0/"
    items = []
    # 글 하나 실패(삭제·타임아웃)는 건너뛰고 다음 글로 채운다
    for i in json.loads(get(base + "topstories.json"))[:HN_COUNT * 2]:
        try:
            raw = json.loads(get(f"{base}item/{i}.json"))
        except Exception as exc:
            print(f"[hn] item {i} 건너뜀: {exc!r}", file=sys.stderr)
            continue
        if raw:
            items.append(hn_item(raw))
        if len(items) == HN_COUNT:
            break
    return items


def fetch_arxiv() -> list[dict]:
    return parse_arxiv(_get(
        "https://export.arxiv.org/api/query?search_query=cat:" + ARXIV_CATEGORY
        + f"&sortBy=submittedDate&sortOrder=descending&max_results={ARXIV_COUNT}"))


GEMINI_PROMPT = """아래 JSON 배열의 각 text를 자연스러운 한국어로 번역하라.
- 레포 이름(owner/repo), 제품·라이브러리 이름, 코드, 기술 약어는 원문 그대로 둔다.
- 설명을 덧붙이거나 요약하지 말고 번역만 한다.
출력은 JSON 배열 하나만: [{"id": 0, "ko": "..."}]. 입력의 모든 id를 포함한다.
"""


def _post_json(url: str, body: dict, key: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                                 headers={**UA, "Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def gemini_translate(texts: list[str], key: str, models=None, post=None, wait: float = 5) -> list:
    """번역 결과를 texts 순서로. 모델이 빠뜨린 항목은 None. 모든 모델이 실패하면 예외."""
    post = post or _post_json
    body = {"contents": [{"parts": [{"text": GEMINI_PROMPT + json.dumps(
                [{"id": i, "text": t} for i, t in enumerate(texts)], ensure_ascii=False)}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    last = None
    for n, model in enumerate(models or GEMINI_MODELS):
        if n:
            time.sleep(wait)
        try:
            raw = post(GEMINI_URL.format(model=model), body, key)["candidates"][0]["content"]["parts"][0]["text"]
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            got = {item["id"]: item["ko"] for item in json.loads(raw)
                   if isinstance(item, dict) and isinstance(item.get("ko"), str)}
        except Exception as exc:  # 503·폐기된 모델·형식 오류 모두 다음 모델로
            print(f"[번역] {model} 실패: {exc!r}", file=sys.stderr)
            last = exc
            continue
        print(f"[번역] Gemini {model}: {len(got)}/{len(texts)}개", file=sys.stderr)
        return [got.get(i) for i in range(len(texts))]
    raise RuntimeError(f"Gemini 모든 모델 실패: {last!r}")


def translate_chain(texts: list[str], translators) -> list:
    """앞 번역기가 실패하거나 빠뜨린 항목만 다음 번역기로 넘긴다."""
    out = [None] * len(texts)
    for tr in translators:
        todo = [i for i, v in enumerate(out) if v is None]
        if not todo:
            break
        try:
            for i, v in zip(todo, tr([texts[i] for i in todo])):
                out[i] = v
        except Exception as exc:
            print(f"[번역] 번역기 실패, 다음으로: {exc!r}", file=sys.stderr)
    return out


def deepl_translate(texts: list[str], key: str) -> list[str]:
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    out = []
    for i in range(0, len(texts), 50):  # DeepL 요청당 최대 50개
        req = urllib.request.Request(
            f"https://{host}/v2/translate",
            data=json.dumps({"text": texts[i:i + 50], "target_lang": "KO"}).encode(),
            headers={**UA, "Authorization": f"DeepL-Auth-Key {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            out += [t["text"] for t in json.loads(resp.read())["translations"]]
    return out


# (소스 키, 목록 키, 원문 필드, 번역 필드)
KO_FIELDS = [("github", "repos", "desc", "desc_ko"), ("hn", "items", "title", "title_ko"),
             ("arxiv", "papers", "title", "title_ko")]


def translation_cache(data_dir: Path, days: int = 30) -> dict[str, str]:
    """최근 스냅샷들의 원문 → 번역 쌍. DeepL 한도(일회성)를 아끼려고 같은 문구는 재사용한다."""
    cache = {}
    for p in sorted(data_dir.glob("*.json"))[-days:]:
        try:
            snap = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for src, key, field, ko in KO_FIELDS:
            for item in snap.get(src, {}).get(key, []):
                if item.get(field) and item.get(ko):
                    cache[item[field]] = item[ko]
    return cache


def add_korean(snap: dict, translate, cache: dict | None = None) -> None:
    cache = dict(cache or {})
    targets = [(item, field, ko) for src, key, field, ko in KO_FIELDS
               for item in snap[src].get(key, []) if item.get(field)]
    new = list(dict.fromkeys(item[field] for item, field, ko in targets if item[field] not in cache))
    if new:
        try:
            cache.update((k, v) for k, v in zip(new, translate(new)) if v)
        except Exception as exc:  # 번역 실패해도 원문(과 캐시된 번역)만으로 저장
            print(f"[번역] 실패, 새 문구 {len(new)}개는 원문만 저장: {exc!r}", file=sys.stderr)
    print(f"[번역] 새로 번역 {len(new)}개, 재사용 {len(targets) - len(new)}개", file=sys.stderr)
    for item, field, ko in targets:
        if item[field] in cache:
            item[ko] = cache[item[field]]


def collect(today: str, out_dir: Path) -> Path:
    snap = {
        "date": today,
        "github": run_source("repos", fetch_github),
        "hn": run_source("items", fetch_hn),
        "arxiv": run_source("papers", fetch_arxiv),
    }
    gkey, dkey = os.environ.get("GEMINI_API_KEY"), os.environ.get("DEEPL_API_KEY")
    translators = []
    if gkey:
        translators.append(lambda texts: gemini_translate(texts, gkey))
    if dkey:  # 예비. 일회성 한도라 Gemini가 실패·누락한 것만 보낸다.
        def deepl(texts):
            print(f"[번역] DeepL 예비 사용: {len(texts)}개, {sum(map(len, texts))}자", file=sys.stderr)
            return deepl_translate(texts, dkey)
        translators.append(deepl)
    if translators:
        add_korean(snap, lambda texts: translate_chain(texts, translators), translation_cache(out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    print(collect(today, Path(__file__).parent / "data"))
