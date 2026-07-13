"""Public track record: every call scored, losers on the same page as winners.

Open calls score price-at-call -> live quote at refresh time.
Closed calls score price-at-call -> the exit-day price, frozen forever.
A call with any missing number simply does not score. Blank beats fake.
"""

import json
from pathlib import Path

CALLS_FILE = Path(__file__).parent / "data" / "calls.json"


def load_calls():
    try:
        data = json.loads(CALLS_FILE.read_text(encoding="utf-8"))
        return data.get("calls", []), data.get("unscored", [])
    except (OSError, ValueError):
        return [], []


def score_calls(calls, quotes):
    """Score each call against live quotes. Best first, unscorable last."""
    rows = []
    for c in calls:
        at_call = c.get("price_at_call")
        if c.get("status") == "closed":
            now = c.get("price_at_close")
        else:
            now = (quotes.get(c["t"]) or {}).get("price")
        pct = None
        if at_call and now is not None:
            pct = (now - at_call) / at_call * 100
        rows.append({**c, "price_now": now, "pct": pct})
    return sorted(rows, key=lambda r: (r["pct"] is None, -(r["pct"] or 0)))


def receipts_from_calls(calls):
    """Earliest public bull call per ticker -> the entry receipt for its card."""
    rec = {}
    for c in calls:
        if c.get("direction") != "bull":
            continue
        t = c["t"]
        if t not in rec or c["call_date"] < rec[t]["date"]:
            rec[t] = {"date": c["call_date"], "title": c["title"],
                      "url": c["url"], "price": c.get("price_at_call")}
    return rec


def record_stats(rows):
    bull = [r["pct"] for r in rows
            if r["direction"] == "bull" and r["pct"] is not None]
    avoid = [r["pct"] for r in rows
             if r["direction"] == "avoid" and r["pct"] is not None]
    return {
        "bull_scored": len(bull),
        "bull_winners": sum(1 for p in bull if p >= 0),
        "bull_losers": sum(1 for p in bull if p < 0),
        "bull_avg_pct": sum(bull) / len(bull) if bull else None,
        "avoid_scored": len(avoid),
        "avoid_aged_well": sum(1 for p in avoid if p < 0),
    }
