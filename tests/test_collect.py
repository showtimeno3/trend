import unittest
from pathlib import Path

from collect import hn_item, parse_arxiv, parse_trending, run_source

FIX = Path(__file__).parent / "fixtures"


class SourcesTest(unittest.TestCase):
    def test_arxiv_parse(self):
        p = parse_arxiv((FIX / "arxiv.xml").read_text(encoding="utf-8"))
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0]["url"], "https://arxiv.org/abs/2610.42147v1")
        self.assertEqual(p[0]["cat"], "cs.AI")
        self.assertGreaterEqual(p[0]["n_authors"], 1)
        self.assertTrue(p[0]["first_author"])
        self.assertNotIn("\n", p[1]["title"])

    def test_hn_item_without_url(self):
        it = hn_item({"id": 1, "title": "Ask HN: x", "score": 5, "descendants": 2})
        self.assertEqual(it["url"], "https://news.ycombinator.com/item?id=1")
        self.assertEqual(it["domain"], "news.ycombinator.com")
        self.assertEqual((it["points"], it["comments"]), (5, 2))

    def test_hn_item_domain(self):
        it = hn_item({"id": 2, "title": "t", "url": "https://www.example.com/a", "score": 1})
        self.assertEqual(it["domain"], "example.com")
        self.assertEqual(it["comments"], 0)

    def test_run_source_isolates_errors(self):
        self.assertEqual(run_source("repos", lambda: [1]), {"repos": [1]})
        self.assertIn("error", run_source("repos", lambda: 1 / 0))
        self.assertIn("error", run_source("repos", lambda: []))


class TrendingTest(unittest.TestCase):
    def setUp(self):
        self.repos = parse_trending((FIX / "trending.html").read_text(encoding="utf-8"))

    def test_count_and_rank(self):
        self.assertEqual(len(self.repos), 3)
        self.assertEqual([r["rank"] for r in self.repos], [1, 2, 3])

    def test_fields(self):
        r = self.repos[0]
        self.assertEqual(r["name"], "Nutlope/hallmark")
        self.assertEqual(r["stars"], 45209)
        self.assertEqual(r["stars_week"], 11566)
        self.assertEqual(r["lang"], "CSS")
        self.assertIn("Claude Code", r["desc"])

    def test_missing_desc_and_lang(self):
        r = self.repos[2]
        self.assertEqual(r["name"], "AgriciDaniel/claude-seo")
        self.assertEqual((r["desc"], r["lang"]), ("", ""))

    def test_garbage_returns_empty(self):
        self.assertEqual(parse_trending("<html>nothing</html>"), [])


if __name__ == "__main__":
    unittest.main()
