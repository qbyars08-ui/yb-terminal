"""Member signals derived from the machine's own daily records.

Badge history and conviction history accumulate one snapshot per refresh
(same pattern as price history). Transitions and deltas come from diffing
those records; nothing here invents a baseline, so day one of tracking
simply produces no signals.
"""

from datetime import datetime, timedelta
from html import escape


def merge_snapshot(hist, today_values, today):
    """Append today's value per ticker. Immutable, idempotent per day,
    blanks never stored."""
    out = {t: dict(days) for t, days in hist.items()}
    for t, v in today_values.items():
        if v in ("", None):
            continue
        out.setdefault(t, {})[today] = v
    return out


def _window_start(today, days):
    d = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days)
    return d.strftime("%Y-%m-%d")

SEVERITY = {"INTACT": 0, "STRESSED": 1, "BROKEN": 2}


def badge_transitions(hist, days, today):
    """Health badge changes inside the window, worst news first."""
    start = _window_start(today, days)
    moves = []
    for t, series in hist.items():
        dates = sorted(series)
        for prev_d, cur_d in zip(dates, dates[1:]):
            frm, to = series[prev_d], series[cur_d]
            if frm == to or cur_d < start:
                continue
            moves.append({"t": t, "frm": frm, "to": to, "date": cur_d,
                          "kind": "down" if SEVERITY.get(to, 0) >
                          SEVERITY.get(frm, 0) else "up"})
    return sorted(moves, key=lambda m: (m["kind"] != "down", m["date"]))


def conviction_deltas(hist, days, today):
    """Machine-desk conviction change over the window, per ticker.
    Needs two real points; flat moves are not a signal."""
    start = _window_start(today, days)
    deltas = {}
    for t, series in hist.items():
        window = {d: v for d, v in series.items() if d >= start}
        if len(window) < 2:
            continue
        dates = sorted(window)
        delta = window[dates[-1]] - window[dates[0]]
        if delta:
            deltas[t] = delta
    return deltas


def today_block_html(top_mover, next_event, badge_moves, note_first, day_pct):
    """The first screenful for members: what actually needs their eyes.
    Every row is optional; nothing real to show means no block at all."""
    rows = []
    for m in badge_moves[:3]:
        arrow = "&#9660;" if m["kind"] == "down" else "&#9650;"
        cls = "down" if m["kind"] == "down" else "up"
        rows.append(
            f"<div class='today-row'><span class='today-tag {cls}'>{arrow} BADGE</span>"
            f"<span><b class='tk'>{escape(m['t'])}</b> went {escape(m['frm'])} to "
            f"{escape(m['to'])} on {escape(m['date'])}</span></div>")
    if next_event:
        tk = f"<b class='tk'>{escape(next_event['t'])}</b> " if next_event.get("t") else ""
        rows.append(
            f"<div class='today-row'><span class='today-tag gold'>NEXT</span>"
            f"<span>{tk}{escape(next_event['what'])}, {escape(next_event['date'])}</span></div>")
    if top_mover and top_mover.get("change") is not None:
        rows.append(
            f"<div class='today-row'><span class='today-tag'>MOVER</span>"
            f"<span><b class='tk'>{escape(top_mover['t'])}</b> "
            f"{top_mover['change']:+.2f}%. {escape(top_mover.get('line') or '')}</span></div>")
    if note_first:
        rows.append(
            f"<div class='today-row'><span class='today-tag'>DESK</span>"
            f"<span>{escape(note_first)}</span></div>")
    if not rows:
        return ""
    day = (f" <span class='{'up' if day_pct >= 0 else 'down'}'>"
           f"{day_pct:+.2f}% today</span>" if day_pct is not None else "")
    return (f"<section id='today'><h2>Today at the Desk{day}</h2>"
            + "".join(rows) + "</section>")
