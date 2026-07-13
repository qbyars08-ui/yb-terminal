"""THE TAPE: the daily open-the-tab reason, built from data already on hand.

One item per held name: today's move plus one line that frames the move
against Quinn's written thesis. Templates pick the frame from (move bucket,
health badge); every number in the output is a real number from the feed.
No LLM anywhere in this path, so refresh cost stays zero.

Scout headlines (FABLE-OS yb-scout.md, peer Substack RSS + HN) are joined
by keyword so a name under news pressure shows what the wire is saying.
"""

import re
from pathlib import Path

SCOUT_FILE = Path.home() / "Quinn/FABLE-OS/status/yb-scout.md"

# generic words that would join everything to everything
STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "after", "over",
    "into", "cost", "edge", "loss", "risk", "play", "tech", "new", "big",
    "failure", "ramp", "raise", "share", "capital", "customer", "act",
    # generic finance words that would join every name to every headline
    "earnings", "revenue", "stock", "stocks", "market", "markets", "nasdaq",
    "debut", "shares", "price", "miss", "beat", "guide", "guidance", "cut",
    "growth", "dilution", "concentration", "competition", "overhang",
}


def move_bucket(change):
    if change is None:
        return ""
    if change >= 3:
        return "ripped"
    if change >= 0.75:
        return "up"
    if change > -0.75:
        return "flat"
    if change > -3:
        return "down"
    return "dumped"


def _pct(v):
    return f"{v:+.0f}%" if v is not None else ""


def tape_line(row, meta, health):
    """One honest line. Real numbers only; the template just picks the frame."""
    change = row.get("change")
    if change is None:
        return ""
    gain = row.get("gain")
    thesis = str(meta.get("thesis_short") or "").rstrip(".")
    bucket = move_bucket(change)
    on_cost = f", {_pct(gain)} on my cost" if gain is not None else ""

    if not thesis:
        return f"{change:+.2f}% today{on_cost}."

    if health == "BROKEN":
        return (f"{change:+.2f}% today, {_pct(gain)} from my entry. Badge says "
                f"BROKEN. The call was: {thesis}. Either I was wrong or the "
                f"market is, and I keep that score in public either way.")
    if health == "STRESSED":
        return (f"{change:+.2f}% today, {_pct(gain)} on my cost. This one wears "
                f"a STRESSED badge and has to earn it back. Thesis on trial: "
                f"{thesis}.")
    if bucket in ("dumped", "down"):
        return (f"{change:+.2f}% today{on_cost}. Thesis unchanged: {thesis}. "
                f"Price moved. The bottleneck did not.")
    if bucket in ("ripped", "up"):
        return (f"{change:+.2f}% today{on_cost}. Thesis: {thesis}. Green days "
                f"do not prove a thesis either. Receipts do.")
    return (f"Flat, {change:+.2f}%{on_cost}. Thesis: {thesis}. Nothing to do "
            f"today, which is usually the job.")


ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*\|")


def parse_scout(text):
    """Pull scored headline rows out of the scout markdown table."""
    items = []
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if m:
            items.append({"score": int(m.group(1)), "source": m.group(2),
                          "title": m.group(3), "url": m.group(4)})
    return items


def load_scout():
    try:
        return parse_scout(SCOUT_FILE.read_text(encoding="utf-8"))
    except OSError:
        return []


def _tokens(ticker, meta):
    toks = {ticker.lower()}
    for field in ("tags", "kill_vectors"):
        for entry in meta.get(field) or []:
            toks.update(str(entry).lower().split("-"))
    return {t for t in toks if len(t) >= 3 and t not in STOPWORDS}


def match_headline(ticker, meta, items):
    """Best-scored headline sharing a real keyword with this name, else None."""
    toks = _tokens(ticker, meta)
    for item in sorted(items, key=lambda i: -i["score"]):
        words = set(re.findall(r"[a-z0-9]+", item["title"].lower()))
        if toks & words:
            return item
    return None


def build_tape(rows, metas, healths, scout_items):
    """Tape items biggest move first. Unpriced names stay off the tape."""
    tape, used_urls = [], set()
    for r in sorted([r for r in rows if r.get("change") is not None],
                    key=lambda r: -abs(r["change"])):
        meta = metas.get(r["t"]) or {}
        fresh = [i for i in scout_items if i["url"] not in used_urls]
        wire = match_headline(r["t"], meta, fresh)
        if wire:
            used_urls.add(wire["url"])
        tape.append({
            "t": r["t"],
            "change": r["change"],
            "gain": r.get("gain"),
            "weight": r.get("weight"),
            "line": tape_line(r, meta, healths.get(r["t"], "")),
            "wire": wire,
        })
    return tape
