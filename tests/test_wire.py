"""The Wire: scout-fed news section. Real headlines with real links only;
an empty scout renders nothing. Polymarket rows surface as the odds board
because market-implied probability is the foresight edge."""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sections import wire_html

ITEMS = [
    {"score": 7, "source": "r/hardware",
     "title": "Memory chip shortage to peak in 2027, warns SK Hynix",
     "url": "https://reddit.com/x"},
    {"score": 6, "source": "SemiAnalysis",
     "title": "Scaling the Memory Wall: The Rise and Roadmap of HBM",
     "url": "https://semianalysis.com/hbm"},
    {"score": 5, "source": "Polymarket",
     "title": "Italy Senate approves Nuclear Power Bill by August 31? (33% yes)",
     "url": "https://polymarket.com/event/italy"},
    {"score": 3, "source": "Polymarket",
     "title": "Will any state enact a data center moratorium? (30% yes)",
     "url": "https://polymarket.com/event/moratorium"},
    {"score": 3, "source": "HN", "title": "Grid story", "url": "https://hn.x/1"},
]


class TestWireHtml(unittest.TestCase):
    def test_renders_headlines_and_odds_split(self):
        html = wire_html(ITEMS, limit=3)
        self.assertIn("SK Hynix", html)
        self.assertIn("SemiAnalysis", html)
        self.assertIn("33% yes", html)          # odds board always included
        self.assertIn("https://semianalysis.com/hbm", html)

    def test_limit_applies_to_headlines_not_odds(self):
        html = wire_html(ITEMS, limit=2)
        self.assertNotIn("Grid story", html)    # beyond limit
        self.assertIn("moratorium", html)       # odds rows ride separately

    def test_empty_scout_renders_nothing(self):
        self.assertEqual(wire_html([], limit=5), "")

    def test_no_em_dash(self):
        self.assertNotIn("—", wire_html(ITEMS, limit=5))


if __name__ == "__main__":
    unittest.main()
