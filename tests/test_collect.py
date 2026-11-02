import unittest
from pathlib import Path

from collect import parse_trending

FIX = Path(__file__).parent / "fixtures"


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
