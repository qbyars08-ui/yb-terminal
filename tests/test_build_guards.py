"""v1 build guards: the page ships fully consistent or it does not ship.

members_html rewrites asset paths for the mirror (no <base> tag: base breaks
in-page anchors, bouncing members to the public index). validate_output is
the render-time truth gate: a build with missing quotes, em dashes, or dead
internal links must fail loudly so refresh.sh keeps the last good site.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import members_html, validate_output


PAGE = """<!doctype html><html><head><title>Young Bull</title></head><body>
<nav><a href="#book">Book</a><a href="pricing.html">Pricing</a></nav>
<a href='t/MU.html'>MU</a>
<script>fetch('prices.json').then(function(r){return r.json()})
fetch('tools-data.json');fetch('history.json')</script>
</body></html>"""


class TestMembersHtml(unittest.TestCase):
    def test_asset_paths_rewritten(self):
        out = members_html(PAGE)
        self.assertIn("href='../../t/MU.html'", out)
        self.assertIn('href="../../pricing.html"', out)
        self.assertIn("fetch('../../prices.json')", out)
        self.assertIn("fetch('../../tools-data.json')", out)
        self.assertIn("fetch('../../history.json')", out)

    def test_anchors_untouched(self):
        out = members_html(PAGE)
        self.assertIn('href="#book"', out)
        self.assertNotIn("<base", out)

    def test_noindex_injected(self):
        self.assertIn("noindex", members_html(PAGE))


def rows(n_priced, n_total):
    out = []
    for i in range(n_total):
        out.append({"t": f"T{i}", "price": 10.0 if i < n_priced else None,
                    "change": -1.0 if i < n_priced else None,
                    "cost": 5.0, "gain": 100.0 if i < n_priced else None,
                    "weight": 5.0})
    return out


GOOD = ("<html><head></head><body><div class='hero-grid'></div>"
        "<section id='book'></section>"
        "<section id='research'></section>"
        "<a href='t/T0.html'>x</a><a href='pricing.html'>p</a></body></html>")


class TestCardsLinkOnlyRealPages(unittest.TestCase):
    def test_no_link_for_ticker_without_research_page(self):
        from sections import cards_html
        cards = [
            {"t": "MU", "health": "", "gain": None, "weight": 1, "price": None,
             "change": None, "thesis_short": "", "layer": "", "sleeve": "",
             "conviction": None, "stance": "", "receipt": None, "catalyst": None},
            {"t": "LUMN", "health": "", "gain": None, "weight": 1, "price": None,
             "change": None, "thesis_short": "", "layer": "", "sleeve": "",
             "conviction": None, "stance": "", "receipt": None, "catalyst": None},
        ]
        out = cards_html(cards, pages={"MU"})
        self.assertIn("href='t/MU.html'", out)
        self.assertNotIn("t/LUMN.html", out)
        self.assertIn("LUMN", out)  # still shown, just not linked


class TestValidateOutput(unittest.TestCase):
    def test_good_build_passes(self):
        probs = validate_output(GOOD, rows(19, 19), pages={"T0"})
        self.assertEqual(probs, [])

    def test_low_quote_coverage_fails(self):
        probs = validate_output(GOOD, rows(9, 19), pages={"T0"})
        self.assertTrue(any("quote coverage" in p for p in probs))

    def test_em_dash_fails(self):
        probs = validate_output(GOOD + "—", rows(19, 19), pages={"T0"})
        self.assertTrue(any("em dash" in p for p in probs))

    def test_dead_research_link_fails(self):
        html = GOOD.replace("t/T0.html", "t/GONE.html")
        probs = validate_output(html, rows(19, 19), pages={"T0"})
        self.assertTrue(any("GONE" in p for p in probs))

    def test_missing_section_fails(self):
        html = GOOD.replace("id='book'", "id='notbook'")
        probs = validate_output(html, rows(19, 19), pages={"T0"})
        self.assertTrue(any("book" in p for p in probs))


if __name__ == "__main__":
    unittest.main()
