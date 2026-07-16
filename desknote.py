"""THE DESK NOTE: the agent-written daily read, rendered honestly.

FABLE OS's 15:00 content shift writes data/desk-note.md (frontmatter date,
3-6 sentences in Quinn's voice, grounded only in that day's real feed).
This module only renders what is actually on disk: a dated note shows its
date, a stale note says so out loud, a missing or malformed note renders
nothing. The public page gets the first sentence; members get the full note.
"""

import re
from datetime import datetime
from html import escape
from pathlib import Path

from research import parse_frontmatter
from thesis import de_dash

NOTE_FILE = Path(__file__).parent / "data" / "desk-note.md"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# a note this old is yesterday's cadence, not a failure; older means the
# writer has been quiet and the page must not pretend otherwise
STALE_AFTER_DAYS = 2


def parse_desk_note(text):
    """Frontmatter date + body, or None. An undated note could silently
    pretend to be fresh, so no valid date means no note at all."""
    meta, body = parse_frontmatter(text)
    date = str(meta.get("date") or "").strip()
    body = de_dash(body).strip()
    if not DATE_RE.match(date) or not body:
        return None
    return {"date": date, "body": body}


def load_desk_note(path=NOTE_FILE):
    try:
        return parse_desk_note(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def first_sentence(body):
    """The public teaser: first sentence, whitespace collapsed."""
    flat = " ".join(body.split())
    m = re.search(r"[.!?](?=\s|$)", flat)
    return flat[:m.end()] if m else flat


def note_age_days(note_date, today):
    try:
        return (datetime.strptime(today, "%Y-%m-%d")
                - datetime.strptime(note_date, "%Y-%m-%d")).days
    except ValueError:
        return None


def desk_note_html(note, today, members=False):
    """One section, date always visible. Public teases, members read."""
    if not note:
        return ""
    age = note_age_days(note["date"], today)
    stale = ""
    if age is None or age > STALE_AFTER_DAYS:
        stale = ("<div class='sub' style='margin-top:8px'>This is the last "
                 "note the desk filed. Nothing newer has landed, and this "
                 "page never pretends otherwise.</div>")
    date_chip = f"<span class='chip'>{escape(note['date'])}</span>"
    if members:
        paras = "".join(f"<p class='read' style='margin-bottom:10px'>{escape(p)}</p>"
                        for p in re.split(r"\n\s*\n", note["body"]) if p.strip())
        body = paras + stale
        sub = ("The machine desk writes this after the close, grounded only "
               "in the day's real feed. Members read the whole thing.")
    else:
        tease = escape(first_sentence(note["body"]))
        body = (f"<p class='read'>{tease}</p>"
                f"<div class='sub' style='margin-top:8px'>That is the public "
                f"line. <a href='pricing.html'>Members read the full note</a>."
                f"</div>" + stale)
        sub = ("One agent-written read per day on what the tape means for "
               "the Physical-Layer theses. No fabricated numbers, ever.")
    return (f"<section id='desk-note'><h2>The Desk Note {date_chip}</h2>"
            f"<div class='sub' style='margin-bottom:8px'>{sub}</div>"
            f"{body}</section>")
