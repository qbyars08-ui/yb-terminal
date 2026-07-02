"""Auto-detect Quinn's buys and sells by diffing the daily positions snapshot.

No input from Quinn, ever: he trades in his brokerage, positions.json updates,
this module notices. Signals used (trade-only, immune to price drift):
- ticker appears        -> BOUGHT (new position)
- ticker disappears     -> EXITED
- costBasis changes     -> ADDED / AVERAGED (avg cost only moves on a real buy)
Weight changes alone are ignored, they move with price, not trades.

State lives in data/ (committed with the site so history survives).
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
STATE = DATA_DIR / "book-state.json"
MOVES = DATA_DIR / "moves.json"
MAX_MOVES = 60


def _load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def detect_moves(snap):
    """Diff snapshot vs stored state. Returns list of all recorded moves, newest first."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    as_of = str(snap.get("as_of", "?"))
    current = {p["t"]: p for p in snap.get("positions", [])}
    state = _load(STATE, None)
    moves = _load(MOVES, [])

    if state is None:
        moves.insert(0, {"date": as_of, "type": "START",
                         "t": "", "detail": "trade tracking armed, baseline recorded"})
    elif state.get("as_of") != as_of:
        prev = state.get("positions", {})
        new = []
        for t, p in current.items():
            if t not in prev:
                w = p.get("weightPct")
                new.append({"date": as_of, "type": "BOUGHT", "t": t,
                            "detail": f"new position{f', {w:.1f}% of book' if w else ''}"})
            else:
                a, b = prev[t].get("costBasis"), p.get("costBasis")
                if a and b and abs(b - a) / a > 0.005:
                    verb = "added, avg cost" if b > a else "averaged, avg cost"
                    new.append({"date": as_of, "type": "ADDED", "t": t,
                                "detail": f"{verb} ${a:,.2f} -> ${b:,.2f}"})
        for t in prev:
            if t not in current:
                new.append({"date": as_of, "type": "EXITED", "t": t,
                            "detail": "position closed"})
        moves = new + moves

    moves = moves[:MAX_MOVES]
    MOVES.write_text(json.dumps(moves, indent=1), encoding="utf-8")
    STATE.write_text(json.dumps({"as_of": as_of, "positions": current}, indent=1),
                     encoding="utf-8")
    return moves
