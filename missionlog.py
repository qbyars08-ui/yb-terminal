"""MISSION LOG: what the machine did this week, counted, never quoted.

Reads FABLE OS's own action log (FABLE-OS/logs/actions.log, the file behind
status/system.md). Only whitelisted action shapes count, into fixed category
labels; anything unrecognized is dropped. Raw log text never reaches the
page: the log carries alert payloads and personal notification fragments,
and the members page gets counts only.
"""

import re
from datetime import datetime
from html import escape
from pathlib import Path

ACTIONS_FILE = Path.home() / "Quinn/FABLE-OS/logs/actions.log"

LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (.+)$")

WINDOW_DAYS = 7

# fixed display labels; the log's own words never render
CATEGORIES = (
    ("desknote", "Desk notes filed"),
    ("content", "Drafts staged for review"),
    ("reviews", "Reviews run"),
    ("fixes", "Pipelines self-healed"),
    ("briefings", "Morning briefings compiled"),
    ("monitoring", "Health alerts triaged"),
)

_RULES = (
    ("desknote", ("staged desk note",)),
    ("content", ("staged a ", "staged an ", "drafted ")),
    ("reviews", ("review run", "ran review", "code review")),
    ("fixes", ("auto-restarted ", "auto-restart of ")),
    ("briefings", ("digest texted",)),
    ("monitoring", ("notified quinn:", "texted quinn:")),
)


def parse_actions(text):
    entries = []
    for line in text.splitlines():
        m = LINE_RE.match(line.strip())
        if m:
            entries.append({"date": m.group(1), "time": m.group(2),
                            "msg": m.group(3)})
    return entries


def categorize(msg):
    """Whitelist only. Unrecognized actions are dropped, not guessed at."""
    low = msg.lower()
    if low.startswith("text suppressed"):
        return None
    for key, needles in _RULES:
        if any(n in low for n in needles):
            return key
    return None


def _within_window(date, today, days=WINDOW_DAYS):
    try:
        delta = (datetime.strptime(today, "%Y-%m-%d")
                 - datetime.strptime(date, "%Y-%m-%d")).days
    except ValueError:
        return False
    return 0 <= delta < days


def weekly_counts(entries, today, days=WINDOW_DAYS):
    counts = {}
    for e in entries:
        if not _within_window(e["date"], today, days):
            continue
        key = categorize(e["msg"])
        if key:
            counts[key] = counts.get(key, 0) + 1
    return counts


def load_weekly_counts(today, path=ACTIONS_FILE):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    return weekly_counts(parse_actions(text), today)


def mission_log_html(counts, today):
    """Members-only section: fixed labels and counts, nothing else."""
    rows = [(label, counts[key]) for key, label in CATEGORIES
            if counts.get(key)]
    if not rows:
        return ""
    cells = "".join(
        f"<div class='stat'><b>{n}</b><span>{escape(label)}</span></div>"
        for label, n in rows)
    return (f"<section id='mission-log'><h2>Mission Log "
            f"<span class='chip'>last 7 days</span></h2>"
            f"<div class='sub' style='margin-bottom:12px'>What the machine did "
            f"on its own this week. The same agent fleet that runs my book runs "
            f"this site: it scouts, drafts, heals its own pipelines, and files "
            f"the Desk Note above. Counted from the system's action log as of "
            f"{escape(today)}. Categories only, never raw logs.</div>"
            f"<div class='stats'>{cells}</div></section>")
