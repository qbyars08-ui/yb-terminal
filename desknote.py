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


# ── Archive + members RSS ────────────────────────────────────────

ARCHIVE_DIR = Path(__file__).parent / "data" / "desk-notes"
ARCHIVE_LIMIT = 30


def archive_note(note, archive_dir=ARCHIVE_DIR):
    """Persist the current note under its own date. Idempotent: rerunning
    the same day rewrites the same file, so history never duplicates."""
    if not note:
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"{note['date']}.md").write_text(
        f"---\ndate: {note['date']}\n---\n{note['body']}\n", encoding="utf-8")


def load_note_archive(archive_dir=ARCHIVE_DIR, limit=ARCHIVE_LIMIT):
    """Newest first, malformed files skipped, capped at limit."""
    if not Path(archive_dir).is_dir():
        return []
    notes = []
    for p in Path(archive_dir).glob("*.md"):
        try:
            parsed = parse_desk_note(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if parsed:
            notes.append(parsed)
    notes.sort(key=lambda n: n["date"], reverse=True)
    return notes[:limit]


def _rfc822(date_str):
    return (datetime.strptime(date_str, "%Y-%m-%d")
            .strftime("%a, %d %b %Y 13:35:00 GMT"))


def rss_xml(notes, members_base):
    """Members-only RSS: static XML, full note text, feed URL never linked
    from any public page. The base already carries the unlisted token."""
    items = []
    for n in notes:
        link = f"{members_base}notes.html#{n['date']}"
        items.append(
            "<item>"
            f"<title>Desk Note, {escape(n['date'])}</title>"
            f"<link>{escape(link)}</link>"
            f"<guid isPermaLink=\"false\">yb-desk-note-{escape(n['date'])}</guid>"
            f"<pubDate>{_rfc822(n['date'])}</pubDate>"
            f"<description>{escape(n['body'])}</description>"
            "</item>")
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<rss version=\"2.0\">\n<channel>\n"
        "<title>Young Bull Desk Notes (Members)</title>\n"
        f"<link>{escape(members_base)}</link>\n"
        "<description>The note the desk files every trading day. Members "
        "only; this feed URL is your key, do not share it.</description>\n"
        + "\n".join(items) + "\n</channel>\n</rss>\n")


def notes_page_html(notes, css, feed_href):
    """Members archive page: last 30 notes, anchored by date."""
    blocks = []
    for n in notes:
        paras = "".join(f"<p>{escape(p.strip())}</p>"
                        for p in n["body"].split("\n\n") if p.strip())
        blocks.append(
            f"<section id=\"{escape(n['date'])}\"><h2>{escape(n['date'])}</h2>"
            f"<div class='read'>{paras}</div></section>")
    inner = ("".join(blocks)
             or "<section><div class='sub'>No notes archived yet. The desk "
                "files one every trading day at 15:00.</div></section>")
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name='robots' content='noindex, nofollow'>
<title>Desk Notes | Young Bull Members</title>
<style>{css}</style></head><body><main>
<div class="sub" style="margin-bottom:16px"><a href="index.html">&larr; Members Terminal</a>
&middot; <a href="{escape(feed_href)}">RSS feed</a> (add it to your reader, the daily
note lands there on its own)</div>
<h1>THE DESK NOTES</h1>
<div class="sub" style="margin-bottom:16px">The last {ARCHIVE_LIMIT} notes the desk
filed, newest first. Members only.</div>
{inner}
<footer>Young Bull. Not advice, it is my book and my machine.</footer>
</main></body></html>"""
