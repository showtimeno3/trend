"""GitHub Trending · Hacker News · arXiv 를 수집해 data/YYYY-MM-DD.json 으로 저장한다."""
import html
import json
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


def fetch_hn() -> list[dict]:
    base = "https://hacker-news.firebaseio.com/v0/"
    ids = json.loads(_get(base + "topstories.json"))[:HN_COUNT]
    return [hn_item(json.loads(_get(f"{base}item/{i}.json"))) for i in ids]


def fetch_arxiv() -> list[dict]:
    return parse_arxiv(_get(
        "https://export.arxiv.org/api/query?search_query=cat:" + ARXIV_CATEGORY
        + f"&sortBy=submittedDate&sortOrder=descending&max_results={ARXIV_COUNT}"))


def collect(today: str, out_dir: Path) -> Path:
    snap = {
        "date": today,
        "github": run_source("repos", fetch_github),
        "hn": run_source("items", fetch_hn),
        "arxiv": run_source("papers", fetch_arxiv),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


if __name__ == "__main__":
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    print(collect(today, Path(__file__).parent / "data"))
