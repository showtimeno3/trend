"""GitHub Trending · Hacker News · arXiv 를 수집해 data/YYYY-MM-DD.json 으로 저장한다."""
import html
import re

ARTICLE_RE = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
NAME_RE = re.compile(r'href="/([^/"]+/[^/"]+)/stargazers"[^>]*>(.*?)</a>', re.S)
WEEK_RE = re.compile(r"([\d,]+) stars this week")
DESC_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
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
