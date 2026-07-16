"""Members lane wiring: desk note atop the tape, mission log + request line
only on the members mirror. The public index must never leak members-only
sections or the members path itself."""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import book_stats, render
from sections import request_line_html


class TestRequestLine(unittest.TestCase):
    def test_links_subscriber_chat(self):
        html = request_line_html()
        self.assertIn("https://youngbullinvests.substack.com/chat", html)

    def test_says_requests_feed_the_agent_queue(self):
        self.assertIn("agent queue", request_line_html().lower())

    def test_no_em_dash(self):
        self.assertNotIn("—", request_line_html())


def _fixtures():
    rows = [{"t": "MU", "weight": 12.0, "cost": 100.0, "price": 110.0,
             "change": -1.2, "gain": 10.0}]
    snap = {"as_of": "2026-07-15", "positions": []}
    stats = book_stats(rows)
    return snap, rows, stats


class TestRenderPlacement(unittest.TestCase):
    def render(self, **kw):
        snap, rows, stats = _fixtures()
        return render(snap, rows, stats, "2026-07-15 13:00 UTC",
                      pages=set(), quotes={}, moves=[], **kw)

    def test_desk_section_renders_above_the_tape(self):
        html = self.render(desk_section="<section id='desk-note'>DN</section>",
                           tape_section="<section id='tape'>TAPE</section>")
        self.assertLess(html.index("id='desk-note'"), html.index("id='tape'"))

    def test_members_extras_render_when_passed(self):
        html = self.render(members_extras="<section id='mission-log'>ML</section>")
        self.assertIn("id='mission-log'", html)

    def test_public_render_has_no_members_sections(self):
        html = self.render()
        self.assertNotIn("mission-log", html)
        self.assertNotIn("request-line", html)


if __name__ == "__main__":
    unittest.main()
