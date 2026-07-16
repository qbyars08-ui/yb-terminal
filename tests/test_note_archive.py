"""Desk note archive + members RSS: static, honest, last 30 notes."""

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from desknote import archive_note, load_note_archive, notes_page_html, rss_xml


def note(date, body="The book did a thing today. It matters."):
    return {"date": date, "body": body}


class TestArchiveNote(unittest.TestCase):
    def test_writes_dated_file_idempotently(self):
        with tempfile.TemporaryDirectory() as d:
            archive_note(note("2026-07-15"), Path(d))
            archive_note(note("2026-07-15"), Path(d))  # rerun same day
            files = list(Path(d).glob("*.md"))
            self.assertEqual([f.name for f in files], ["2026-07-15.md"])
            self.assertIn("date: 2026-07-15", files[0].read_text())

    def test_none_note_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            archive_note(None, Path(d))
            self.assertEqual(list(Path(d).glob("*")), [])


class TestLoadArchive(unittest.TestCase):
    def test_newest_first_capped(self):
        with tempfile.TemporaryDirectory() as d:
            for i in range(1, 36):
                archive_note(note(f"2026-06-{i:02d}" if i <= 30
                                  else f"2026-07-{i-30:02d}"), Path(d))
            notes = load_note_archive(Path(d), limit=30)
            self.assertEqual(len(notes), 30)
            self.assertEqual(notes[0]["date"], "2026-07-05")
            self.assertGreater(notes[0]["date"], notes[-1]["date"])

    def test_malformed_file_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "junk.md").write_text("no frontmatter here")
            archive_note(note("2026-07-15"), Path(d))
            self.assertEqual(len(load_note_archive(Path(d))), 1)

    def test_missing_dir_is_empty(self):
        self.assertEqual(load_note_archive(Path("/nonexistent-xyz")), [])


class TestRss(unittest.TestCase):
    BASE = "https://example.io/site/members/m-tok/"

    def test_valid_channel_with_items(self):
        xml = rss_xml([note("2026-07-15"), note("2026-07-14")], self.BASE)
        self.assertIn("<rss version=\"2.0\">", xml)
        self.assertEqual(xml.count("<item>"), 2)
        self.assertIn("Wed, 15 Jul 2026", xml)
        self.assertIn(f"{self.BASE}notes.html#2026-07-15", xml)

    def test_body_escaped(self):
        xml = rss_xml([note("2026-07-15", "MU <up> & away.")], self.BASE)
        self.assertIn("&lt;up&gt; &amp; away", xml)

    def test_empty_archive_still_valid_feed(self):
        xml = rss_xml([], self.BASE)
        self.assertIn("<channel>", xml)
        self.assertNotIn("<item>", xml)


class TestNotesPage(unittest.TestCase):
    def test_lists_notes_with_anchors(self):
        html = notes_page_html([note("2026-07-15"), note("2026-07-14")],
                               "CSSBLOB", "feed.xml")
        self.assertIn("id=\"2026-07-15\"", html)
        self.assertLess(html.index("2026-07-15"), html.index("2026-07-14"))
        self.assertIn("feed.xml", html)


if __name__ == "__main__":
    unittest.main()
