"""FMP earnings-calendar feed for the catalyst calendar.

Honesty rules: no key on disk means no feed and no guesses; a malformed
row is dropped, never repaired; the in-house Supabase table always
outranks FMP on the same ticker. The fetch itself degrades to {} on any
failure so a bad vendor day can never break the refresh.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from earnings_fmp import fmp_key_from_env, merge_earnings, parse_fmp_calendar

PAYLOAD = [
    {"symbol": "MU", "date": "2026-09-29"},
    {"symbol": "MU", "date": "2026-12-22"},          # later print: ignored
    {"symbol": "nvda", "date": "2026-08-26"},         # case normalized
    {"symbol": "ZZZZ", "date": "2026-08-01"},         # not covered: dropped
    {"symbol": "AMD", "date": "not-a-date"},          # malformed: dropped
    {"symbol": "", "date": "2026-08-05"},             # no symbol: dropped
    {"symbol": "TSM", "date": "2026-07-01"},          # past: dropped
    "garbage-row",
]
UNIVERSE = {"MU", "NVDA", "AMD", "TSM", "NOK"}


class TestParseFmpCalendar(unittest.TestCase):
    def test_earliest_future_date_per_covered_ticker(self):
        out = parse_fmp_calendar(PAYLOAD, UNIVERSE, "2026-07-20")
        self.assertEqual(out["MU"], {"date": "2026-09-29", "label": "earnings"})
        self.assertEqual(out["NVDA"], {"date": "2026-08-26", "label": "earnings"})

    def test_uncovered_malformed_and_past_rows_dropped(self):
        out = parse_fmp_calendar(PAYLOAD, UNIVERSE, "2026-07-20")
        self.assertEqual(set(out), {"MU", "NVDA"})

    def test_garbage_payload_empty(self):
        self.assertEqual(parse_fmp_calendar(None, UNIVERSE, "2026-07-20"), {})
        self.assertEqual(parse_fmp_calendar({"err": 1}, UNIVERSE, "2026-07-20"), {})


class TestMergeEarnings(unittest.TestCase):
    def test_supabase_outranks_fmp_on_same_ticker(self):
        sb = {"NOK": {"date": "2026-07-23", "label": "earnings"}}
        fmp = {"NOK": {"date": "2026-07-24", "label": "earnings"},
               "MU": {"date": "2026-09-29", "label": "earnings"}}
        merged = merge_earnings(sb, fmp)
        self.assertEqual(merged["NOK"]["date"], "2026-07-23")
        self.assertEqual(merged["MU"]["date"], "2026-09-29")

    def test_merge_never_mutates_inputs(self):
        sb = {"NOK": {"date": "2026-07-23", "label": "earnings"}}
        fmp = {"MU": {"date": "2026-09-29", "label": "earnings"}}
        merge_earnings(sb, fmp)
        self.assertEqual(sb, {"NOK": {"date": "2026-07-23", "label": "earnings"}})
        self.assertEqual(fmp, {"MU": {"date": "2026-09-29", "label": "earnings"}})


class TestFmpKey(unittest.TestCase):
    def test_missing_key_is_empty_string(self):
        self.assertEqual(fmp_key_from_env("A=1\nB=2\n"), "")

    def test_key_read_when_present(self):
        self.assertEqual(fmp_key_from_env("FMP_API_KEY=abc123\n"), "abc123")


if __name__ == "__main__":
    unittest.main()
