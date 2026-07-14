"""Pro tools data: history maintenance + per-ticker coverage data.

Everything shipped to the client is real: layers and theses from the
research files, conviction from the machine desk, earnings dates from the
calendar table, history from the Terminal's own committed daily snapshots.
A ticker without coverage gets NO fields, never a guess.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import build_tools_data, merge_history


class TestMergeHistory(unittest.TestCase):
    def test_appends_today_for_quoted_tickers(self):
        hist = {"MU": {"2026-07-12": 979.3}}
        out = merge_history(hist, {"MU": {"price": 937.0},
                                   "AAPL": {"price": 317.31}}, "2026-07-13")
        self.assertEqual(out["MU"]["2026-07-13"], 937.0)
        self.assertEqual(out["AAPL"], {"2026-07-13": 317.31})
        self.assertEqual(out["MU"]["2026-07-12"], 979.3)  # past untouched

    def test_same_day_rerun_overwrites_not_duplicates(self):
        hist = {"MU": {"2026-07-13": 979.3}}
        out = merge_history(hist, {"MU": {"price": 937.0}}, "2026-07-13")
        self.assertEqual(out["MU"], {"2026-07-13": 937.0})

    def test_unquoted_ticker_keeps_history_gains_nothing(self):
        hist = {"RAAQ": {"2026-07-01": 10.4}}
        out = merge_history(hist, {}, "2026-07-13")
        self.assertEqual(out["RAAQ"], {"2026-07-01": 10.4})

    def test_input_not_mutated(self):
        hist = {"MU": {"2026-07-12": 979.3}}
        merge_history(hist, {"MU": {"price": 937.0}}, "2026-07-13")
        self.assertEqual(hist, {"MU": {"2026-07-12": 979.3}})


class TestBuildToolsData(unittest.TestCase):
    def setUp(self):
        self.rows = [{"t": "MU", "weight": 12.9, "price": 937.0, "cost": 456.9,
                      "change": -4.3, "gain": 105.1}]
        self.metas = {"MU": {"thesis_short": "HBM is the AI bottleneck",
                             "layer": "Compute & Memory"}}
        self.committee = {"MU": {"conviction": 68, "stance": "bull"}}
        self.catalysts = {"MU": {"date": "2026-09-24", "label": "earnings"},
                          "ASML": {"date": "2026-07-15", "label": "earnings"}}
        self.healths = {"MU": "INTACT"}
        self.quotes = {"MU": {"price": 937.0, "changePct": -4.3},
                       "AAPL": {"price": 317.31, "changePct": 0.63},
                       "ASML": {"price": 1000.0, "changePct": 1.0}}

    def build(self):
        return build_tools_data(self.rows, self.metas, self.committee,
                                self.catalysts, self.healths, self.quotes)

    def test_covered_ticker_gets_everything_real(self):
        d = self.build()["tickers"]["MU"]
        self.assertEqual(d["layer"], "Compute & Memory")
        self.assertEqual(d["held"], 12.9)
        self.assertEqual(d["health"], "INTACT")
        self.assertEqual(d["conviction"], 68)
        self.assertEqual(d["stance"], "bull")
        self.assertEqual(d["earnings"], "2026-09-24")
        self.assertEqual(d["thesis"], "HBM is the AI bottleneck")

    def test_uncovered_ticker_gets_no_invented_fields(self):
        d = self.build()["tickers"]["AAPL"]
        self.assertEqual(d, {})  # quoted, but zero coverage claims

    def test_partially_covered_gets_only_real_fields(self):
        d = self.build()["tickers"]["ASML"]
        self.assertEqual(d, {"earnings": "2026-07-15"})

    def test_em_dash_scrubbed_from_layer(self):
        self.metas["MU"]["layer"] = "Compute — Memory"
        d = self.build()["tickers"]["MU"]
        self.assertNotIn("—", d["layer"])


if __name__ == "__main__":
    unittest.main()
