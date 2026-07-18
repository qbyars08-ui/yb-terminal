"""yb-desk absorption: market scan + proving ground, rendered honestly.

The data comes from the desk agents' deployed JSON. Every section carries
its own as-of stamp, flags itself when stale, and renders nothing at all
when the feed is missing. Numbers pass through untouched."""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from desk_import import market_scan_html, proving_ground_html, staleness

SCAN = {
    "updated": "2026-07-18T15:06:00+00:00",
    "universe": "NASDAQ/NYSE/AMEX, price > $5, volume > 2M, cap > $2B",
    "scans": [
        {"id": "momentum", "title": "Momentum leaders",
         "note": "Price above a rising EMA structure, RSI 55-75",
         "totalMatches": 255,
         "rows": [{"ticker": "SLS", "company": "SLS Co", "price": 13.19,
                   "changePct": 12.26, "relVol": 2.5, "rsi": 71.0, "cap": "2.5B"}]},
        {"id": "volume", "title": "Unusual volume", "note": "3x normal volume",
         "totalMatches": 18,
         "rows": [{"ticker": "MTZ", "company": "MasTec", "price": 329.59,
                   "changePct": -3.29, "relVol": 4.0, "rsi": 44.0, "cap": "26B"}]},
    ],
}

BT = {
    "updated": "2026-07-17T15:07:00+00:00", "period": "2y",
    "engine": "momentum engine, 10bps slippage",
    "strategies": [
        {"id": "ema_crossover", "description": "EMA 8/21 crossover",
         "agg": {"names": 19, "medianStrategyPct": 125.5,
                 "medianBuyHoldPct": 293.5, "beatBuyHold": 2,
                 "avgWinRatePct": 42.0, "avgTrades": 9.1},
         "best": {"ticker": "RKLB", "strategyPct": 1370.2},
         "worst": {"ticker": "LUMN", "strategyPct": -32.3},
         "rows": []},
    ],
}


class TestStaleness(unittest.TestCase):
    def test_fresh(self):
        self.assertEqual(staleness("2026-07-18T15:06:00+00:00",
                                   today="2026-07-18"), "")

    def test_stale_labeled(self):
        out = staleness("2026-07-09T22:43:00+00:00", today="2026-07-18")
        self.assertIn("9 days", out)

    def test_garbage_is_stale_unknown(self):
        self.assertIn("unknown", staleness("not-a-date", today="2026-07-18"))


class TestMarketScan(unittest.TestCase):
    def test_members_renders_rows(self):
        html = market_scan_html(SCAN, members=True, today="2026-07-18")
        self.assertIn("Momentum leaders", html)
        self.assertIn("SLS", html)
        self.assertIn("255", html)          # totalMatches shown
        self.assertIn("What screened, not what to buy", html)
        self.assertNotIn("—", html)

    def test_public_gets_counts_not_tickers(self):
        html = market_scan_html(SCAN, members=False, today="2026-07-18")
        self.assertIn("255", html)
        self.assertNotIn("SLS", html)       # rows are the paid part
        self.assertIn("pricing.html", html)

    def test_missing_feed_renders_nothing(self):
        self.assertEqual(market_scan_html(None, members=True,
                                          today="2026-07-18"), "")
        self.assertEqual(market_scan_html({"scans": []}, members=True,
                                          today="2026-07-18"), "")


class TestProvingGround(unittest.TestCase):
    def test_members_table_passthrough_numbers(self):
        html = proving_ground_html(BT, today="2026-07-18")
        self.assertIn("ema_crossover", html.replace("ema_crossover", "ema_crossover"))
        self.assertIn("+125.5%", html)
        self.assertIn("+293.5%", html)
        self.assertIn("2/19", html)
        self.assertIn("RKLB", html)
        self.assertIn("most of them lose to just holding", html.lower())

    def test_missing_renders_nothing(self):
        self.assertEqual(proving_ground_html(None, today="2026-07-18"), "")

    def test_desk_em_dashes_scrubbed(self):
        bt = {"updated": "2026-07-18T00:00:00+00:00", "period": "2y",
              "engine": "engine", "strategies": [
                  {"id": "x", "description": "EMA cross — bread & butter",
                   "agg": {}, "best": {}, "worst": {}, "rows": []}]}
        self.assertNotIn("—", proving_ground_html(bt, today="2026-07-18"))


if __name__ == "__main__":
    unittest.main()
