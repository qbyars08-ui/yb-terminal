"""THE TAPE: what changed today, one honest line per name, zero LLM cost.

Every number in a tape line is real (live change, real gain on cost,
Quinn's own thesis_short). Templates only choose the frame, never invent.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tape import build_tape, match_headline, move_bucket, parse_scout, tape_line


class TestMoveBucket(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(move_bucket(4.2), "ripped")
        self.assertEqual(move_bucket(3.0), "ripped")
        self.assertEqual(move_bucket(1.2), "up")
        self.assertEqual(move_bucket(0.3), "flat")
        self.assertEqual(move_bucket(-0.3), "flat")
        self.assertEqual(move_bucket(-1.2), "down")
        self.assertEqual(move_bucket(-3.0), "dumped")
        self.assertEqual(move_bucket(-6.0), "dumped")

    def test_none_is_blank(self):
        self.assertEqual(move_bucket(None), "")


class TestTapeLine(unittest.TestCase):
    def line(self, change=-4.0, gain=50.0, thesis="HBM is the AI bottleneck",
             health="INTACT"):
        row = {"t": "MU", "change": change, "gain": gain}
        meta = {"thesis_short": thesis}
        return tape_line(row, meta, health)

    def test_red_day_intact_reframes_to_thesis(self):
        line = self.line(change=-4.0, gain=50.0, health="INTACT")
        self.assertIn("HBM is the AI bottleneck", line)
        self.assertIn("+50%", line)

    def test_no_thesis_no_editorial(self):
        # without a thesis file the line states the move and nothing else
        line = self.line(thesis="", health="")
        self.assertNotIn("thesis", line.lower())

    def test_broken_health_is_said_plainly(self):
        line = self.line(change=-5.0, gain=-40.0, health="BROKEN")
        self.assertIn("BROKEN", line)

    def test_never_contains_em_dash(self):
        for change, gain, health in [(-4, 50, "INTACT"), (4, -20, "STRESSED"),
                                     (0.1, 5, "INTACT"), (-8, -40, "BROKEN")]:
            self.assertNotIn("—", self.line(change, gain, health=health))

    def test_missing_change_returns_blank(self):
        self.assertEqual(self.line(change=None), "")


class TestScout(unittest.TestCase):
    SCOUT = """# YB CONTENT SCOUT
Updated: 2026-07-13 14:35

## Post ideas, scored against the Physical-Layer beats
| score | source | title |
|---|---|---|
| 6 | SemiAnalysis | [Scaling the Memory Wall: The Rise and Roadmap of HBM](https://semianalysis.com/hbm) |
| 5 | Temple8 Capital | [Data Center Cooling Play With A July Catalyst](https://temple8.com/cooling) |
| 3 | r/stocks | [SK Hynix Shares Tumble After Debut](https://reddit.com/x) |

## Alerts
- HOT topic
"""

    def test_parse_scout(self):
        items = parse_scout(self.SCOUT)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["score"], 6)
        self.assertEqual(items[0]["title"],
                         "Scaling the Memory Wall: The Rise and Roadmap of HBM")
        self.assertEqual(items[0]["url"], "https://semianalysis.com/hbm")
        self.assertEqual(items[1]["source"], "Temple8 Capital")

    def test_parse_garbage_returns_empty(self):
        self.assertEqual(parse_scout("no table here"), [])

    def test_match_headline_by_keyword(self):
        items = parse_scout(self.SCOUT)
        meta = {"thesis_short": "HBM is the AI bottleneck",
                "kill_vectors": ["hbm-oversupply", "hynix-cost-edge"],
                "tags": ["hbm", "compute-memory"]}
        hit = match_headline("MU", meta, items)
        self.assertIsNotNone(hit)
        self.assertIn("Memory Wall", hit["title"])

    def test_match_headline_by_ticker_name(self):
        items = parse_scout(self.SCOUT)
        # no keyword overlap, but title contains the ticker itself
        hit = match_headline("HBM", {}, items)
        self.assertIsNotNone(hit)

    def test_no_match_returns_none(self):
        items = parse_scout(self.SCOUT)
        meta = {"thesis_short": "satellite direct to cell",
                "kill_vectors": ["regulatory-spectrum-loss"], "tags": ["satellite"]}
        self.assertIsNone(match_headline("ASTS", meta, items))


class TestWireQuality(unittest.TestCase):
    ITEMS = [{"score": 6, "source": "X", "title": "Chipco earnings beat, stock up on Nasdaq debut", "url": "https://x.com/1"},
             {"score": 5, "source": "Y", "title": "Scaling the Memory Wall: HBM roadmap", "url": "https://y.com/2"}]

    def test_generic_finance_words_never_match(self):
        meta = {"tags": ["gpu-cloud"], "kill_vectors": ["earnings-miss", "stock-dilution"]}
        self.assertIsNone(match_headline("NBIS", meta, self.ITEMS))

    def test_wire_headline_not_repeated_across_tape(self):
        rows = [{"t": "MU", "change": -4.0, "gain": 10.0, "weight": 10},
                {"t": "PENG", "change": -1.0, "gain": 5.0, "weight": 4}]
        metas = {"MU": {"tags": ["hbm"]}, "PENG": {"tags": ["hbm"]}}
        tape = build_tape(rows, metas, {}, self.ITEMS)
        wires = [i["wire"]["url"] for i in tape if i["wire"]]
        self.assertEqual(len(wires), len(set(wires)))
        self.assertEqual(tape[0]["wire"]["url"], "https://y.com/2")  # biggest mover keeps it
        self.assertIsNone(tape[1]["wire"])


class TestBuildTape(unittest.TestCase):
    def test_sorted_by_abs_move_and_complete(self):
        rows = [
            {"t": "MU", "change": -4.8, "gain": 53.0, "weight": 12.9},
            {"t": "WYY", "change": 0.1, "gain": -8.0, "weight": 7.1},
            {"t": "OUST", "change": 9.2, "gain": 12.0, "weight": 8.4},
        ]
        metas = {"MU": {"thesis_short": "HBM is the AI bottleneck"}}
        tape = build_tape(rows, metas, {"MU": "INTACT"}, [])
        self.assertEqual([i["t"] for i in tape], ["OUST", "MU", "WYY"])
        self.assertTrue(all("line" in i for i in tape))

    def test_unpriced_rows_skipped(self):
        rows = [{"t": "IQMX", "change": None, "gain": None, "weight": 3.0}]
        self.assertEqual(build_tape(rows, {}, {}, []), [])


if __name__ == "__main__":
    unittest.main()
