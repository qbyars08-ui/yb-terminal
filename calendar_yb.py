"""Catalyst calendar: every dated event the desk actually knows about.

Two sources, both real: hand-curated rows in data/catalysts.json (the 15:00
content shift appends verified dates there; a date it cannot verify stays
out) and the machine's earnings_calendar table (already fetched per refresh).
Nothing is inferred. A malformed row is dropped, never repaired into a guess.

Named calendar_yb because stdlib owns the name calendar.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from thesis import de_dash

CATALYSTS_FILE = Path(__file__).parent / "data" / "catalysts.json"

PUBLIC_DAYS = 7
MEMBERS_DAYS = 92


def _valid_date(s):
    try:
        date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def parse_catalysts(payload):
    """Curated rows -> clean entries. Missing date or what = dropped."""
    rows = payload.get("catalysts")
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        d, what = r.get("date"), r.get("what")
        if not what or not _valid_date(d):
            continue
        out.append({
            "date": d,
            "t": str(r.get("t") or "").upper(),
            "what": de_dash(str(what)),
            "why": de_dash(str(r.get("why") or "")),
            "receipt": str(r.get("receipt") or ""),
        })
    return out


def load_catalysts(path=CATALYSTS_FILE):
    try:
        return parse_catalysts(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return []


def build_calendar(curated, earnings, today, days):
    """Merged, windowed, date-sorted. A curated row on the same ticker+date
    outranks the bare earnings row (it carries the why and the receipt)."""
    start = date.fromisoformat(today)
    end = start + timedelta(days=days)
    entries = list(curated)
    taken = {(e["t"], e["date"]) for e in curated}
    for t, cat in (earnings or {}).items():
        d = cat.get("date")
        if not _valid_date(d) or (t, d) in taken:
            continue
        entries.append({"date": d, "t": t, "what": "Earnings",
                        "why": "", "receipt": ""})
    windowed = [e for e in entries
                if start <= date.fromisoformat(e["date"]) <= end]
    return sorted(windowed, key=lambda e: (e["date"], e["t"]))
