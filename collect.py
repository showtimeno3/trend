"""GitHub Trending · Hacker News · arXiv 를 수집해 data/YYYY-MM-DD.json 으로 저장한다."""
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ARXIV_CATEGORY = "cs.AI"
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
            cache.update(zip(new, translate(new)))
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
    key = os.environ.get("DEEPL_API_KEY")
    if key:
        add_korean(snap, lambda texts: deepl_translate(texts, key), translation_cache(out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    print(collect(today, Path(__file__).parent / "data"))
