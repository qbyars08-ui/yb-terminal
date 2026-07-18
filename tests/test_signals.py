"""Member signals: badge transitions, conviction deltas, the TODAY block.

All derived from data the machine already computes daily. A name with no
history yet produces no signal; day one of tracking says so instead of
inventing a baseline.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from signals import (badge_transitions, conviction_deltas, merge_snapshot,
                     today_block_html)


class TestMergeSnapshot(unittest.TestCase):
    def test_appends_and_overwrites_same_day(self):
        hist = {"MU": {"2026-07-17": "INTACT"}}
        out = merge_snapshot(hist, {"MU": "STRESSED", "OSS": "STRESSED"},
                             "2026-07-18")
        self.assertEqual(out["MU"], {"2026-07-17": "INTACT",
                                     "2026-07-18": "STRESSED"})
        self.assertEqual(out["OSS"], {"2026-07-18": "STRESSED"})
        # rerun same day overwrites
        out2 = merge_snapshot(out, {"MU": "INTACT"}, "2026-07-18")
        self.assertEqual(out2["MU"]["2026-07-18"], "INTACT")

    def test_blank_values_never_stored(self):
        out = merge_snapshot({}, {"MU": "", "OSS": None}, "2026-07-18")
        self.assertEqual(out, {})

    def test_input_not_mutated(self):
        hist = {"MU": {"2026-07-17": "INTACT"}}
        merge_snapshot(hist, {"MU": "STRESSED"}, "2026-07-18")
        self.assertEqual(hist["MU"], {"2026-07-17": "INTACT"})


class TestBadgeTransitions(unittest.TestCase):
    HIST = {
        "OSS": {"2026-07-14": "INTACT", "2026-07-16": "STRESSED",
                "2026-07-18": "STRESSED"},
        "MU": {"2026-07-14": "INTACT", "2026-07-18": "INTACT"},
        "NEW": {"2026-07-18": "INTACT"},
    }

    def test_finds_downgrade_with_date(self):
        moves = badge_transitions(self.HIST, days=7, today="2026-07-18")
        self.assertEqual(len(moves), 1)
        m = moves[0]
        self.assertEqual((m["t"], m["frm"], m["to"], m["date"]),
                         ("OSS", "INTACT", "STRESSED", "2026-07-16"))
        self.assertEqual(m["kind"], "down")

    def test_upgrade_is_kind_up(self):
        hist = {"LPKFF": {"2026-07-15": "STRESSED", "2026-07-17": "INTACT"}}
        moves = badge_transitions(hist, days=7, today="2026-07-18")
        self.assertEqual(moves[0]["kind"], "up")

    def test_old_transitions_outside_window_dropped(self):
        moves = badge_transitions(self.HIST, days=1, today="2026-07-18")
        self.assertEqual(moves, [])

    def test_single_day_history_yields_nothing(self):
        self.assertEqual(
            badge_transitions({"NEW": {"2026-07-18": "INTACT"}},
                              days=7, today="2026-07-18"), [])


class TestConvictionDeltas(unittest.TestCase):
    HIST = {"MU": {"2026-07-11": 63, "2026-07-18": 68},
            "WYY": {"2026-07-18": 54}}

    def test_delta_needs_two_points(self):
        deltas = conviction_deltas(self.HIST, days=7, today="2026-07-18")
        self.assertEqual(deltas, {"MU": 5})

    def test_flat_delta_omitted(self):
        deltas = conviction_deltas({"MU": {"2026-07-11": 68,
                                           "2026-07-18": 68}},
                                   days=7, today="2026-07-18")
        self.assertEqual(deltas, {})


class TestTodayBlock(unittest.TestCase):
    def test_composes_only_real_pieces(self):
        html = today_block_html(
            top_mover={"t": "MU", "change": -4.3,
                       "line": "Thesis unchanged: HBM is the bottleneck."},
            next_event={"date": "2026-07-20", "t": "CC",
                        "what": "EPA PFAS comment window closes"},
            badge_moves=[{"t": "OSS", "frm": "INTACT", "to": "STRESSED",
                          "date": "2026-07-16", "kind": "down"}],
            note_first="The book bled but nothing broke.",
            day_pct=-1.2)
        self.assertIn("MU", html)
        self.assertIn("EPA PFAS", html)
        self.assertIn("OSS", html)
        self.assertIn("INTACT", html)
        self.assertNotIn("—", html)

    def test_empty_inputs_render_nothing(self):
        self.assertEqual(today_block_html(None, None, [], "", None), "")


if __name__ == "__main__":
    unittest.main()
