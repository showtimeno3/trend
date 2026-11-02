import unittest

from build import build_history, tokenize


def snap(date, repos=None, hn=None, arxiv=None):
    def src(key, items):
        return {"error": "x"} if items is None else {key: items}
    rs = None if repos is None else [
        {"rank": i + 1, "name": n, "desc": "", "lang": "", "stars": s, "stars_week": w}
        for i, (n, s, w) in enumerate(repos)]
    return {"date": date, "github": src("repos", rs), "hn": src("items", hn), "arxiv": src("papers", arxiv)}


class BuildTest(unittest.TestCase):
    def test_move_against_last_successful(self):
        h = build_history([snap("2026-10-02", repos=[("a", 10, 5), ("b", 10, 4)]),
                           snap("2026-10-03"),
                           snap("2026-10-04", repos=[("b", 12, 6), ("c", 1, 1)])])
        r = {x["name"]: x for x in h["github"]["repos"]}
        self.assertEqual(r["b"]["move"], 1)
        self.assertFalse(r["b"]["is_new"])
        self.assertTrue(r["c"]["is_new"])
        self.assertIsNone(r["c"]["move"])
        self.assertEqual(h["github"]["dropped"], [{"name": "a", "rank": 1}])
        self.assertEqual(h["github"]["entered"], [{"name": "c", "rank": 2}])

    def test_first_day_has_no_move(self):
        h = build_history([snap("2026-10-02", repos=[("a", 10, 5)])])
        r = h["github"]["repos"][0]
        self.assertIsNone(r["move"])
        self.assertFalse(r["is_new"])
        self.assertEqual(h["github"]["entered"], [])

    def test_spark_gaps_are_null(self):
        h = build_history([snap("2026-10-02", repos=[("a", 100, 1)]),
                           snap("2026-10-03", repos=[("x", 1, 1)]),
                           snap("2026-10-04", repos=[("a", 130, 1)])])
        a = next(x for x in h["github"]["repos"] if x["name"] == "a")
        self.assertEqual(len(a["spark"]), 14)
        self.assertEqual(a["spark"][-3:], [0, None, 30])
        self.assertEqual(a["spark"][:11], [None] * 11)
        self.assertEqual(len(h["dates14"]), 14)

    def test_missing_file_day_breaks_line(self):
        h = build_history([snap("2026-10-01", repos=[("a", 100, 1)]), snap("2026-10-05", repos=[("a", 140, 1)])])
        self.assertEqual(h["dates14"][-1], "2026-10-05")
        self.assertEqual(len(h["dates14"]), 14)
        self.assertEqual(h["github"]["repos"][0]["spark"][-5:], [0, None, None, None, 40])

    def test_top5_by_stars_week(self):
        h = build_history([snap("2026-10-02", repos=[(f"r{i}", 1, i) for i in range(7)])])
        self.assertEqual(h["github"]["top5"], ["r6", "r5", "r4", "r3", "r2"])

    def test_stale_source_uses_last_good(self):
        h = build_history([snap("2026-11-01", hn=[{"title": "t"}]), snap("2026-11-02", hn=None)])
        self.assertEqual(h["hn"]["stale_days"], 1)
        self.assertEqual(h["hn"]["date"], "2026-11-01")
        self.assertEqual(len(h["hn"]["items"]), 1)

    def test_never_succeeded(self):
        self.assertEqual(build_history([snap("2026-10-02", arxiv=None)])["arxiv"], {"error": "수집 실패"})

    def test_keywords_need_7_prior_days(self):
        k = build_history([snap(f"2026-10-{i+1:02d}") for i in range(7)])["keywords"]
        self.assertEqual(k, {"ready": False, "items": []})

    def test_keywords_change(self):
        full = lambda d, t: snap(d, repos=[("r", 1, 1)], hn=[{"title": t}], arxiv=[{"title": "x"}])
        old = [full(f"2026-10-{i+1:02d}", "rust db") for i in range(7)]
        new = full("2026-10-08", "agent agent agent rust")
        k = build_history(old + [new])["keywords"]
        self.assertTrue(k["ready"])
        self.assertEqual(k["items"][0], {"word": "agent", "today": 3, "avg": 0.0, "change_pct": 300})
        self.assertNotIn("rust", [x["word"] for x in k["items"]])  # 오늘 1회 < 3

    def test_keywords_skip_partial_days(self):
        full = lambda d, t: snap(d, repos=[("r", 1, 1)], hn=[{"title": t}], arxiv=[{"title": "x"}])
        old = [full(f"2026-10-{i+1:02d}", "agent") for i in range(7)]
        broken = snap("2026-10-08")                       # 모든 소스 실패: 평균에서 제외
        today = full("2026-10-09", "agent agent agent")
        k = build_history(old + [broken, today])["keywords"]
        self.assertTrue(k["ready"])
        self.assertEqual(k["items"][0]["avg"], 1.0)
        partial = snap("2026-10-10", hn=[{"title": "agent agent agent"}])   # 오늘 일부 실패
        self.assertFalse(build_history(old + [today, partial])["keywords"]["ready"])

    def test_tokenize(self):
        self.assertEqual(tokenize("Show HN: The Rust-based LLM agent, in C++!"),
                         ["rust-based", "llm", "agent", "c++"])


if __name__ == "__main__":
    unittest.main()
