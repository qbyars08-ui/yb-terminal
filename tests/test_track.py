"""Track record math. Honesty is the product: losers count, blanks stay blank."""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from track import record_stats, score_calls


def call(t="MU", direction="bull", price_at_call=100.0, status="open",
         price_at_close=None, **kw):
    c = {"t": t, "call_date": "2026-03-21", "direction": direction,
         "price_at_call": price_at_call, "status": status,
         "title": "x", "url": "https://example.com"}
    if price_at_close is not None:
        c["price_at_close"] = price_at_close
        c["closed_date"] = "2026-07-10"
    c.update(kw)
    return c


class TestScoreCalls(unittest.TestCase):
    def test_open_call_scores_to_live_quote(self):
        rows = score_calls([call()], {"MU": {"price": 150.0}})
        self.assertAlmostEqual(rows[0]["pct"], 50.0)
        self.assertEqual(rows[0]["price_now"], 150.0)

    def test_open_call_without_quote_stays_blank(self):
        rows = score_calls([call()], {})
        self.assertIsNone(rows[0]["pct"])
        self.assertIsNone(rows[0]["price_now"])

    def test_closed_call_scores_to_exit_price_not_live(self):
        rows = score_calls([call(status="closed", price_at_close=80.0)],
                           {"MU": {"price": 999.0}})
        self.assertAlmostEqual(rows[0]["pct"], -20.0)
        self.assertEqual(rows[0]["price_now"], 80.0)

    def test_missing_call_price_never_scores(self):
        rows = score_calls([call(price_at_call=None)], {"MU": {"price": 150.0}})
        self.assertIsNone(rows[0]["pct"])

    def test_loser_math_is_exact(self):
        rows = score_calls([call(t="WOLF", price_at_call=57.41, status="closed",
                                 price_at_close=35.25)], {})
        self.assertAlmostEqual(rows[0]["pct"], -38.60, places=2)

    def test_sorted_best_first(self):
        rows = score_calls([
            call(t="A", price_at_call=100), call(t="B", price_at_call=100),
            call(t="C", price_at_call=100),
        ], {"A": {"price": 110.0}, "C": {"price": 90.0}})
        self.assertEqual([r["t"] for r in rows], ["A", "C", "B"])  # blanks last


class TestRecordStats(unittest.TestCase):
    def rows(self):
        return score_calls([
            call(t="A", price_at_call=100),                       # +50 open
            call(t="B", price_at_call=100, status="closed", price_at_close=80.0),
            call(t="C", price_at_call=100),                       # unpriced now
            call(t="D", direction="avoid", price_at_call=100),    # avoid, -10
        ], {"A": {"price": 150.0}, "D": {"price": 90.0}})

    def test_stats_split_bull_and_avoid(self):
        s = record_stats(self.rows())
        self.assertEqual(s["bull_scored"], 2)     # A and B; C has no quote
        self.assertEqual(s["bull_winners"], 1)
        self.assertEqual(s["bull_losers"], 1)
        self.assertAlmostEqual(s["bull_avg_pct"], 15.0)  # (+50 - 20) / 2
        self.assertEqual(s["avoid_scored"], 1)
        self.assertEqual(s["avoid_aged_well"], 1)  # it fell after the avoid call

    def test_empty_is_all_zero(self):
        s = record_stats([])
        self.assertEqual(s["bull_scored"], 0)
        self.assertIsNone(s["bull_avg_pct"])


if __name__ == "__main__":
    unittest.main()
