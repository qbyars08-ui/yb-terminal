"""Ticker page upgrades: server-side sparkline, receipts timeline, stubs.

The sparkline draws only from our own snapshot history and refuses to draw
with fewer than 3 real points. Receipts render chronologically and only
from the committed receipts index. Coverage names without a research file
get a stub page so no card or scanner row ever links dead.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research import receipts_html, spark_svg, stub_tickers


class TestSparkSvg(unittest.TestCase):
    DAYS = {"2026-07-01": 100.0, "2026-07-02": 110.0, "2026-07-03": 105.0}

    def test_draws_polyline_with_three_points(self):
        svg = spark_svg(self.DAYS)
        self.assertIn("<svg", svg)
        self.assertIn("polyline", svg)

    def test_under_three_points_draws_nothing(self):
        self.assertEqual(spark_svg({"2026-07-01": 100.0}), "")
        self.assertEqual(spark_svg({}), "")

    def test_up_series_green_down_series_red(self):
        up = spark_svg({"a": 1.0, "b": 2.0, "c": 3.0})
        dn = spark_svg({"a": 3.0, "b": 2.0, "c": 1.0})
        self.assertIn("#22c55e", up)
        self.assertIn("#ef4444", dn)

    def test_flat_series_does_not_crash(self):
        svg = spark_svg({"a": 5.0, "b": 5.0, "c": 5.0})
        self.assertIn("polyline", svg)


class TestReceiptsHtml(unittest.TestCase):
    RECEIPTS = [
        {"date": "2026-03-21", "title": "The $25k post",
         "url": "https://youngbullinvests.substack.com/p/a"},
        {"date": "2026-06-25", "title": "Micron Just Reported",
         "url": "https://youngbullinvests.substack.com/p/b"},
    ]

    def test_chronological_linked_list(self):
        html = receipts_html(self.RECEIPTS)
        self.assertIn("2026-03-21", html)
        self.assertLess(html.index("2026-03-21"), html.index("2026-06-25"))
        self.assertIn("https://youngbullinvests.substack.com/p/b", html)

    def test_empty_receipts_render_nothing(self):
        self.assertEqual(receipts_html([]), "")

    def test_titles_escaped(self):
        html = receipts_html([{"date": "2026-01-01", "title": "<b>x</b>",
                               "url": "https://y"}])
        self.assertNotIn("<b>x</b>", html)


class TestStubTickers(unittest.TestCase):
    def test_held_and_receipt_names_without_files_get_stubs(self):
        out = stub_tickers(research={"MU", "ANET"},
                           held={"MU", "LUMN", "NOK"},
                           receipt_names={"SKHY", "ANET"})
        self.assertEqual(out, ["LUMN", "NOK", "SKHY"])

    def test_nothing_missing_means_no_stubs(self):
        self.assertEqual(stub_tickers({"MU"}, {"MU"}, {"MU"}), [])


if __name__ == "__main__":
    unittest.main()
