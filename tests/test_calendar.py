"""Catalyst calendar: curated dated events merged with the earnings table.

Honesty rules: an entry without a parseable date or a what never renders,
text is de-dashed, and nothing is ever inferred. Public sees 7 days,
members see the quarter.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calendar_yb import build_calendar, parse_catalysts

RAW = {
    "catalysts": [
        {"date": "2026-07-20", "t": "CC", "what": "EPA PFAS comment window closes",
         "why": "The contrarian case leans on the rules landing survivable — this ends the comment window.",
         "receipt": "https://youngbullinvests.substack.com/p/nvidia-just-panic-bought-4-billion"},
        {"date": "not-a-date", "t": "MU", "what": "bad row"},
        {"t": "MU", "what": "no date at all"},
        {"date": "2026-07-22", "what": "Young Bull goes paid"},
    ],
}


class TestParseCatalysts(unittest.TestCase):
    def test_valid_rows_kept_malformed_dropped(self):
        rows = parse_catalysts(RAW)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["t"], "CC")
        self.assertEqual(rows[1]["t"], "")  # tickerless event is fine

    def test_em_dash_scrubbed(self):
        rows = parse_catalysts(RAW)
        self.assertNotIn("—", rows[0]["why"])

    def test_garbage_payload_empty(self):
        self.assertEqual(parse_catalysts({}), [])
        self.assertEqual(parse_catalysts({"catalysts": "nope"}), [])


class TestBuildCalendar(unittest.TestCase):
    CURATED = [
        {"date": "2026-07-20", "t": "CC", "what": "EPA PFAS comment window closes",
         "why": "w", "receipt": "https://r"},
        {"date": "2026-07-23", "t": "NOK", "what": "Curated NOK event",
         "why": "", "receipt": ""},
        {"date": "2026-10-30", "t": "MU", "what": "Too far out", "why": "", "receipt": ""},
    ]
    EARNINGS = {
        "NOK": {"date": "2026-07-23", "label": "earnings"},
        "ARM": {"date": "2026-07-29", "label": "earnings"},
        "OLD": {"date": "2026-07-01", "label": "earnings"},
    }

    def test_window_and_sort(self):
        cal = build_calendar(self.CURATED, self.EARNINGS, "2026-07-16", days=92)
        dates = [e["date"] for e in cal]
        self.assertEqual(dates, sorted(dates))
        self.assertNotIn("2026-07-01", dates)   # past dropped
        self.assertNotIn("2026-10-30", dates)   # beyond window dropped

    def test_public_seven_day_window(self):
        cal = build_calendar(self.CURATED, self.EARNINGS, "2026-07-16", days=7)
        self.assertEqual([e["t"] for e in cal], ["CC", "NOK"])
        self.assertNotIn("ARM", [e["t"] for e in cal])  # 07-29 outside 7d

    def test_curated_beats_earnings_on_same_ticker_and_date(self):
        cal = build_calendar(self.CURATED, self.EARNINGS, "2026-07-16", days=92)
        nok = [e for e in cal if e["t"] == "NOK"]
        self.assertEqual(len(nok), 1)
        self.assertEqual(nok[0]["what"], "Curated NOK event")

    def test_earnings_rows_are_labeled_plainly(self):
        cal = build_calendar([], self.EARNINGS, "2026-07-16", days=92)
        arm = [e for e in cal if e["t"] == "ARM"][0]
        self.assertEqual(arm["what"], "Earnings")
        self.assertEqual(arm["why"], "")   # no invented commentary
        self.assertEqual(arm["receipt"], "")

    def test_same_day_included(self):
        cal = build_calendar(
            [{"date": "2026-07-16", "t": "X", "what": "today", "why": "", "receipt": ""}],
            {}, "2026-07-16", days=7)
        self.assertEqual(len(cal), 1)


if __name__ == "__main__":
    unittest.main()
