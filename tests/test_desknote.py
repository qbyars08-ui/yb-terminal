"""THE DESK NOTE: agent-written daily read, rendered honestly.

The note file is written by the FABLE OS content shift at 15:00. The
terminal only ever renders what is actually on disk: a dated note renders
with its date, a stale note says so, a missing or malformed note renders
nothing. Public page gets the first sentence, members get the full note.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from desknote import (desk_note_html, first_sentence, note_age_days,
                      parse_desk_note)

NOTE = """---
date: 2026-07-15
---
The book gave back ground today and the tape did not care about anyone's
feelings. MU slid with the memory complex even as the HBM shortage story
tightened. That is the trade: the bottleneck thesis gets cheaper while the
evidence for it gets stronger. Nothing in today's move touches the entry
math on any held name.
"""


class TestParseDeskNote(unittest.TestCase):
    def test_valid_note_parses_date_and_body(self):
        note = parse_desk_note(NOTE)
        self.assertEqual(note["date"], "2026-07-15")
        self.assertIn("bottleneck thesis", note["body"])

    def test_missing_date_is_rejected(self):
        # an undated note could silently pretend to be fresh: refuse it
        self.assertIsNone(parse_desk_note("---\nauthor: desk\n---\nA note."))

    def test_malformed_date_is_rejected(self):
        self.assertIsNone(parse_desk_note("---\ndate: July 15\n---\nA note."))

    def test_empty_body_is_rejected(self):
        self.assertIsNone(parse_desk_note("---\ndate: 2026-07-15\n---\n\n"))

    def test_no_frontmatter_is_rejected(self):
        self.assertIsNone(parse_desk_note("Just a bare paragraph."))

    def test_em_dashes_are_scrubbed(self):
        note = parse_desk_note(
            "---\ndate: 2026-07-15\n---\nPrice fell — thesis held.")
        self.assertNotIn("—", note["body"])
        self.assertIn("thesis held", note["body"])


class TestFirstSentence(unittest.TestCase):
    def test_takes_first_sentence_only(self):
        self.assertEqual(
            first_sentence("Red day. Nothing structural. Move on."),
            "Red day.")

    def test_decimal_numbers_do_not_split(self):
        s = "MU closed at $132.50 on the day. More context."
        self.assertEqual(first_sentence(s), "MU closed at $132.50 on the day.")

    def test_single_sentence_returned_whole(self):
        self.assertEqual(first_sentence("One line only"), "One line only")

    def test_newlines_collapse(self):
        self.assertEqual(first_sentence("Split\nacross lines. Next."),
                         "Split across lines.")


class TestNoteAge(unittest.TestCase):
    def test_same_day_is_zero(self):
        self.assertEqual(note_age_days("2026-07-15", "2026-07-15"), 0)

    def test_yesterday_is_one(self):
        self.assertEqual(note_age_days("2026-07-14", "2026-07-15"), 1)

    def test_garbage_is_none(self):
        self.assertIsNone(note_age_days("not-a-date", "2026-07-15"))


class TestDeskNoteHtml(unittest.TestCase):
    def note(self):
        return parse_desk_note(NOTE)

    def test_missing_note_renders_nothing(self):
        self.assertEqual(desk_note_html(None, "2026-07-15"), "")
        self.assertEqual(desk_note_html(None, "2026-07-15", members=True), "")

    def test_public_gets_first_sentence_only(self):
        html = desk_note_html(self.note(), "2026-07-15")
        self.assertIn("gave back ground today", html)
        self.assertNotIn("bottleneck thesis", html)

    def test_public_teases_members_via_pricing(self):
        html = desk_note_html(self.note(), "2026-07-15")
        self.assertIn("pricing.html", html)

    def test_members_get_full_note_and_no_tease(self):
        html = desk_note_html(self.note(), "2026-07-15", members=True)
        self.assertIn("bottleneck thesis", html)
        self.assertNotIn("pricing.html", html)

    def test_date_always_shown(self):
        for members in (False, True):
            html = desk_note_html(self.note(), "2026-07-16", members=members)
            self.assertIn("2026-07-15", html)

    def test_stale_note_says_so(self):
        fresh = desk_note_html(self.note(), "2026-07-16")
        stale = desk_note_html(self.note(), "2026-07-19")
        self.assertNotIn("last note the desk filed", fresh)
        self.assertIn("last note the desk filed", stale)

    def test_body_is_escaped(self):
        note = parse_desk_note(
            "---\ndate: 2026-07-15\n---\n<script>alert(1)</script> day.")
        for members in (False, True):
            html = desk_note_html(note, "2026-07-15", members=members)
            self.assertNotIn("<script>", html)

    def test_never_contains_em_dash(self):
        note = parse_desk_note(
            "---\ndate: 2026-07-15\n---\nRed day — but the thesis held. Fine.")
        for members in (False, True):
            self.assertNotIn("—", desk_note_html(note, "2026-07-15",
                                                  members=members))


if __name__ == "__main__":
    unittest.main()
