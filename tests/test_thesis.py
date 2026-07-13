"""Thesis card rules: health badge, committee freshness, card assembly.

The health badge is rule-based from live price vs the cost anchor.
Blank beats fake: any missing input renders as empty, never a guess.
"""

import unittest
from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thesis import (build_cards, de_dash, fresh_committee, health_badge,
                    nearest_catalysts, parse_env)


class TestHealthBadge(unittest.TestCase):
    def test_gain_is_intact(self):
        self.assertEqual(health_badge(price=150, cost=100), "INTACT")

    def test_small_drawdown_is_intact(self):
        # -14.9% on cost: normal volatility, thesis anchor holds
        self.assertEqual(health_badge(price=85.1, cost=100), "INTACT")

    def test_boundary_minus_15_is_intact(self):
        self.assertEqual(health_badge(price=85, cost=100), "INTACT")

    def test_mid_drawdown_is_stressed(self):
        self.assertEqual(health_badge(price=80, cost=100), "STRESSED")

    def test_boundary_minus_30_is_stressed(self):
        self.assertEqual(health_badge(price=70, cost=100), "STRESSED")

    def test_deep_drawdown_is_broken(self):
        self.assertEqual(health_badge(price=69.9, cost=100), "BROKEN")

    def test_missing_price_is_blank(self):
        self.assertEqual(health_badge(price=None, cost=100), "")

    def test_missing_cost_is_blank(self):
        self.assertEqual(health_badge(price=100, cost=None), "")

    def test_zero_cost_is_blank(self):
        self.assertEqual(health_badge(price=100, cost=0), "")


class TestFreshCommittee(unittest.TestCase):
    NOW = datetime(2026, 7, 13, 23, 0, tzinfo=timezone.utc)

    def row(self, ticker="MU", conviction=68, stance="bull", hours_old=1):
        ts = self.NOW - timedelta(hours=hours_old)
        return {"ticker": ticker, "aggregated_conviction": conviction,
                "current_stance": stance,
                "updated_at": ts.isoformat().replace("+00:00", "+00:00")}

    def test_fresh_row_kept(self):
        out = fresh_committee([self.row()], now=self.NOW)
        self.assertEqual(out, {"MU": {"conviction": 68, "stance": "bull"}})

    def test_stale_row_dropped(self):
        out = fresh_committee([self.row(hours_old=72)], now=self.NOW)
        self.assertEqual(out, {})

    def test_null_updated_at_dropped(self):
        row = self.row()
        row["updated_at"] = None
        self.assertEqual(fresh_committee([row], now=self.NOW), {})

    def test_null_conviction_dropped(self):
        row = self.row()
        row["aggregated_conviction"] = None
        self.assertEqual(fresh_committee([row], now=self.NOW), {})

    def test_garbage_timestamp_dropped(self):
        row = self.row()
        row["updated_at"] = "not-a-date"
        self.assertEqual(fresh_committee([row], now=self.NOW), {})


class TestParseEnv(unittest.TestCase):
    def test_parses_keys_ignores_comments(self):
        text = "# comment\nSUPABASE_URL=https://x.supabase.co\nKEY=abc # not stripped\n\nBAD LINE\n"
        env = parse_env(text)
        self.assertEqual(env["SUPABASE_URL"], "https://x.supabase.co")
        self.assertIn("KEY", env)
        self.assertNotIn("BAD LINE", env)


class TestDeDash(unittest.TestCase):
    def test_em_dash_with_spaces_becomes_comma(self):
        self.assertEqual(de_dash("IP toll — royalty 2x"), "IP toll, royalty 2x")

    def test_bare_em_and_en_dash(self):
        self.assertEqual(de_dash("a—b and c–d"), "a, b and c, d")

    def test_clean_text_untouched(self):
        self.assertEqual(de_dash("no dashes, just commas"),
                         "no dashes, just commas")


class TestNearestCatalysts(unittest.TestCase):
    ROWS = [
        {"ticker": "NOK", "report_date": "2026-07-23"},
        {"ticker": "NOK", "report_date": "2026-10-22"},
        {"ticker": "ARM", "report_date": "2026-07-29"},
        {"ticker": "MU", "report_date": "2026-06-25"},
    ]

    def test_earliest_future_per_ticker(self):
        out = nearest_catalysts(self.ROWS, today="2026-07-13")
        self.assertEqual(out["NOK"], {"date": "2026-07-23", "label": "earnings"})
        self.assertEqual(out["ARM"]["date"], "2026-07-29")

    def test_past_dates_dropped(self):
        out = nearest_catalysts(self.ROWS, today="2026-07-13")
        self.assertNotIn("MU", out)

    def test_missing_fields_dropped(self):
        out = nearest_catalysts([{"ticker": "X"}, {"report_date": "2027-01-01"}],
                                today="2026-07-13")
        self.assertEqual(out, {})


class TestBuildCards(unittest.TestCase):
    def setUp(self):
        self.rows = [{"t": "MU", "price": 700.0, "cost": 456.9, "change": -4.8,
                      "gain": 53.2, "weight": 12.9}]
        self.meta = {"MU": {"thesis_short": "HBM is the AI bottleneck",
                            "layer": "Compute & Memory", "sleeve": "anchor"}}
        self.committee = {"MU": {"conviction": 68, "stance": "bull"}}
        self.receipts = {"MU": {"date": "2026-06-25", "title": "Micron Just Reported",
                                "url": "https://youngbullinvests.substack.com/p/micron"}}
        self.catalysts = {"MU": {"date": "2026-09-24", "label": "FQ4 earnings"}}

    def test_full_card(self):
        cards = build_cards(self.rows, self.meta, self.committee,
                            self.receipts, self.catalysts)
        c = cards[0]
        self.assertEqual(c["t"], "MU")
        self.assertEqual(c["health"], "INTACT")
        self.assertEqual(c["conviction"], 68)
        self.assertEqual(c["stance"], "bull")
        self.assertEqual(c["receipt"]["url"],
                         "https://youngbullinvests.substack.com/p/micron")
        self.assertEqual(c["catalyst"]["date"], "2026-09-24")
        self.assertEqual(c["thesis_short"], "HBM is the AI bottleneck")

    def test_missing_everything_degrades_blank(self):
        cards = build_cards(self.rows, {}, {}, {}, {})
        c = cards[0]
        self.assertEqual(c["thesis_short"], "")
        self.assertIsNone(c["conviction"])
        self.assertIsNone(c["receipt"])
        self.assertIsNone(c["catalyst"])
        self.assertEqual(c["health"], "INTACT")  # price rules need no metadata

    def test_sorted_by_weight_desc(self):
        rows = self.rows + [{"t": "WYY", "price": 9.0, "cost": 9.77, "change": 1.0,
                             "gain": -7.9, "weight": 20.0}]
        cards = build_cards(rows, {}, {}, {}, {})
        self.assertEqual([c["t"] for c in cards], ["WYY", "MU"])


if __name__ == "__main__":
    unittest.main()
