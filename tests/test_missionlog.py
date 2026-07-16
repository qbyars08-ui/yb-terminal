"""MISSION LOG: what the machine did this week, counted, never quoted.

Feeds from FABLE-OS's own action log (the file behind status/system.md).
Only whitelisted action shapes are counted into fixed category labels;
everything else is dropped. Raw log text must never reach the page: the
log can contain alert payloads and personal notification fragments.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from missionlog import (categorize, mission_log_html, parse_actions,
                        weekly_counts)

LOG = """2026-07-15 16:18 auto-restarted com.youngbull.fable-content-shift (was FAILING (exit 1))
2026-07-15 18:08 notified Quinn: 4 new alert(s)
2026-07-15 18:08 texted Quinn: FABLE OS yb-presence: threads post FAILED x5
2026-07-15 15:12 digest texted: FABLE OS 2026-07-15 morning brief
2026-07-15 15:05 staged desk note for the Terminal (2026-07-15)
2026-07-15 15:05 staged a Substack Note draft
2026-07-08 09:00 notified Quinn: 1 new alert(s)
garbage line without a stamp
2026-07-14 06:47 auto-restarted com.youngbull.terminal-refresh (was FAILING (exit 1))
"""


class TestParseActions(unittest.TestCase):
    def test_parses_stamped_lines(self):
        entries = parse_actions(LOG)
        self.assertEqual(entries[0]["date"], "2026-07-15")
        self.assertIn("auto-restarted", entries[0]["msg"])

    def test_garbage_lines_skipped(self):
        entries = parse_actions(LOG)
        self.assertEqual(len(entries), 8)
        self.assertTrue(all(e["date"] for e in entries))

    def test_empty_text(self):
        self.assertEqual(parse_actions(""), [])


class TestCategorize(unittest.TestCase):
    def test_restarts_are_fixes(self):
        self.assertEqual(categorize("auto-restarted com.x (was FAILING)"),
                         "fixes")
        self.assertEqual(categorize("auto-restart of com.x FAILED to launch"),
                         "fixes")

    def test_desk_note_is_its_own_category(self):
        self.assertEqual(categorize("staged desk note for the Terminal"),
                         "desknote")

    def test_staged_drafts_are_content(self):
        self.assertEqual(categorize("staged a Substack Note draft"), "content")
        self.assertEqual(categorize("staged an X thread draft"), "content")

    def test_notifications_are_monitoring(self):
        self.assertEqual(categorize("notified Quinn: 4 new alert(s)"),
                         "monitoring")
        self.assertEqual(categorize("texted Quinn: anything at all"),
                         "monitoring")

    def test_digest_is_briefings(self):
        self.assertEqual(categorize("digest texted: morning brief"),
                         "briefings")

    def test_unknown_actions_are_dropped(self):
        self.assertIsNone(categorize("text suppressed: daily cap reached"))
        self.assertIsNone(categorize("did something new and unclassified"))


class TestWeeklyCounts(unittest.TestCase):
    def test_counts_by_category_inside_window(self):
        counts = weekly_counts(parse_actions(LOG), "2026-07-15")
        self.assertEqual(counts["fixes"], 2)
        self.assertEqual(counts["monitoring"], 2)  # notified + texted
        self.assertEqual(counts["briefings"], 1)
        self.assertEqual(counts["desknote"], 1)
        self.assertEqual(counts["content"], 1)

    def test_old_entries_excluded(self):
        counts = weekly_counts(parse_actions(LOG), "2026-07-15")
        # the 07-08 notification is 7 days old: outside the window
        self.assertEqual(counts["monitoring"], 2)

    def test_empty_log(self):
        self.assertEqual(weekly_counts([], "2026-07-15"), {})


class TestMissionLogHtml(unittest.TestCase):
    def counts(self):
        return weekly_counts(parse_actions(LOG), "2026-07-15")

    def test_labels_and_counts_render(self):
        html = mission_log_html(self.counts(), "2026-07-15")
        self.assertIn("Pipelines self-healed", html)
        self.assertIn("Desk notes filed", html)

    def test_raw_log_text_never_leaks(self):
        html = mission_log_html(self.counts(), "2026-07-15")
        for fragment in ("yb-presence", "threads post FAILED",
                         "com.youngbull", "texted Quinn"):
            self.assertNotIn(fragment, html)

    def test_empty_counts_render_nothing(self):
        self.assertEqual(mission_log_html({}, "2026-07-15"), "")

    def test_never_contains_em_dash(self):
        self.assertNotIn("—", mission_log_html(self.counts(), "2026-07-15"))


if __name__ == "__main__":
    unittest.main()
