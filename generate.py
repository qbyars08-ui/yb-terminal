#!/usr/bin/env python3
"""Young Bull Terminal: static site for GitHub Pages.

Reads positions from data/book-state.json, fetches live prices from Yahoo
Finance via yfinance, renders a self-contained site into docs/.
Zero servers, zero cost. Run by launchd cron or manually via refresh.sh.
"""

import json
import math
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import yfinance as yf

from calendar_yb import (MEMBERS_DAYS, PUBLIC_DAYS, build_calendar,
                         load_catalysts)
from clientjs import TOOLS_JS, TRACKER_JS, TRACKER_POPULAR, VIZ_SECTION
from desknote import (archive_note, desk_note_html, first_sentence,
                      load_desk_note, load_note_archive,
                      notes_page_html, rss_xml)
from missionlog import load_weekly_counts, mission_log_html
from research import (CSS, TICKERS_DIR, build_research, list_research_tickers,
                      parse_frontmatter)
from sections import (EXTRA_CSS, SITE_BASE, calendar_members_html, wire_html,
                      calendar_public_html, cards_html, og_tags,
                      pricing_page_html, request_line_html, scanner_html,
                      tape_html)
from tape import build_tape, load_scout
from thesis import (build_cards, de_dash, fetch_catalysts, fetch_committee,
                    health_badge)
from desk_import import (fetch_desk_json, market_scan_html,
                         proving_ground_html)
from gate import encrypt_payload, gate_page_html
from signals import (badge_transitions, conviction_deltas,
                     merge_snapshot, today_block_html)
from thesis import SECRETS, load_json, parse_env
from track import load_calls, receipts_from_calls

OUT_DIR = Path(__file__).parent / "docs"
DATA_DIR = Path(__file__).parent / "data"
SUBSTACK = "https://youngbullinvests.substack.com"


# ── Data fetching ────────────────────────────────────────────────

def fetch_prices(tickers):
    """Fetch quotes for all tickers via yfinance (handles Yahoo auth)."""
    prices = {}
    print(f"  fetching {len(tickers)} quotes via yfinance...")
    try:
        data = yf.download(tickers, period="2d", interval="1d",
                           group_by="ticker", progress=False, threads=True)
        for t in tickers:
            try:
                if len(tickers) == 1:
                    df = data
                else:
                    df = data[t]
                if df.empty or len(df) < 1:
                    continue
                row = df.iloc[-1]
                price = float(row["Close"].iloc[0]) if hasattr(row["Close"], "iloc") else float(row["Close"])
                if len(df) >= 2:
                    prev_row = df.iloc[-2]
                    prev = float(prev_row["Close"].iloc[0]) if hasattr(prev_row["Close"], "iloc") else float(prev_row["Close"])
                else:
                    prev = price
                if not math.isfinite(price):
                    continue  # NaN close (delisted/halted): no quote beats a fake one
                pct = None
                if prev and math.isfinite(prev):
                    pct = round((price - prev) / prev * 100, 2)
                prices[t] = {"price": round(price, 2), "changePct": pct}
            except Exception as e:
                print(f"  WARN: {t}: {e}")
    except Exception as e:
        print(f"  WARN: yfinance bulk download failed: {e}")
    print(f"  got {len(prices)}/{len(tickers)} quotes")
    return prices


def load_positions():
    """Load Quinn's positions from the local book-state.json."""
    state = json.loads((DATA_DIR / "book-state.json").read_text("utf-8"))
    return {
        "as_of": state.get("as_of", "?"),
        "positions": [
            {"t": t, "weightPct": p.get("weightPct"), "costBasis": p.get("costBasis")}
            for t, p in state.get("positions", {}).items()
        ],
    }


def load_moves():
    """Load existing move history."""
    try:
        return json.loads((DATA_DIR / "moves.json").read_text("utf-8"))
    except (OSError, ValueError):
        return []


# ── Enrichment ───────────────────────────────────────────────────

def enrich(positions, prices):
    rows = []
    for p in positions:
        t = p["t"]
        q = prices.get(t) or {}
        price = q.get("price")
        change = q.get("changePct")
        cost = p.get("costBasis")
        gain = None
        if price is not None and cost:
            gain = (price - cost) / cost * 100
        rows.append({
            "t": t, "weight": p.get("weightPct"), "cost": cost,
            "price": price, "change": change, "gain": gain,
        })
    return rows


def book_stats(rows):
    priced = [r for r in rows if r["change"] is not None]
    green = [r for r in priced if r["change"] >= 0]
    weighted_day = sum((r["change"] or 0) * (r["weight"] or 0) for r in priced)
    total_w = sum(r["weight"] or 0 for r in priced) or 1
    gains = [r for r in rows if r["gain"] is not None]
    weighted_gain = sum(r["gain"] * (r["weight"] or 0) for r in gains)
    gain_w = sum(r["weight"] or 0 for r in gains) or 1
    movers = sorted(priced, key=lambda r: r["change"], reverse=True)
    dummy = {"t": "-", "change": 0, "weight": 0}
    while len(movers) < 3:
        movers.append(dummy)
    return {
        "green": len(green), "priced": len(priced),
        "day": weighted_day / total_w,
        "gain": weighted_gain / gain_w,
        "best": movers[:3], "worst": movers[-3:][::-1],
    }


def market_read(stats):
    day = stats["day"]
    g, n = stats["green"], stats["priced"]
    if day >= 1.5:
        mood = "The book ripped today."
    elif day >= 0.2:
        mood = "Quiet green day for the book."
    elif day > -0.2:
        mood = "Flat tape for the book."
    elif day > -1.5:
        mood = "Red day, nothing structural."
    else:
        mood = "Brutal red day. This is what buying opportunities feel like."
    best, worst = stats["best"][0], stats["worst"][0]
    return (
        f"{mood} {g} of {n} names green, book {day:+.2f}% weighted on the day. "
        f"Top mover {best['t']} {best['change']:+.2f}%, laggard {worst['t']} "
        f"{worst['change']:+.2f}%. Cost basis never moves on a red day. The thesis "
        f"either holds or it does not, and price alone is not the thesis."
    )


# ── Rendering helpers ────────────────────────────────────────────

def fmt(v, spec, dash="-"):
    return format(v, spec) if v is not None else dash

def cls(v):
    if v is None: return ""
    return "up" if v >= 0 else "down"

MOVE_BADGE = {"BOUGHT": "up", "ADDED": "up", "EXITED": "down", "START": ""}


def load_metas():
    """Frontmatter for every research file; one bad file never kills the build."""
    metas = {}
    for t in list_research_tickers():
        try:
            meta, _ = parse_frontmatter(
                (TICKERS_DIR / f"{t}.md").read_text(encoding="utf-8"))
            if meta.get("thesis_short"):
                meta["thesis_short"] = de_dash(str(meta["thesis_short"]))
            metas[t] = meta
        except OSError:
            pass
    return metas


def members_token():
    """Stable unlisted path segment for the members mirror."""
    path = DATA_DIR / "members-path.txt"
    try:
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    except OSError:
        pass
    import secrets
    token = "m-" + secrets.token_urlsafe(9).lower().replace("_", "").replace("-", "")[:12]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    return token


NOTES_LINKS = """
<section>
  <h2>Desk Note Archive <span class="chip" style="border-color:var(--gold);color:var(--gold)">Members</span></h2>
  <div class="sub">The last 30 notes the desk filed live at
  <a href="notes.html">the archive</a>. Add <a href="feed.xml">the members RSS feed</a>
  to your reader and the daily note lands there on its own. The feed URL is part of
  your membership, treat it like a key.</div>
</section>
"""


# ── Main render ──────────────────────────────────────────────────

def render(snap, rows, stats, generated_at, pages, quotes, moves,
           tape_section="", cards_section="", tools_section="",
           desk_section="", members_extras="", calendar_section="",
           wire_section="", book_metas=None):
    # Book table rows
    tr = []
    metas = book_metas or {}
    for r in sorted(rows, key=lambda x: -(x["weight"] or 0)):
        t = r["t"]
        link = (f"<a href='t/{escape(t)}.html'>{escape(t)}</a>"
                if t in pages else escape(t))
        m = metas.get(t) or {}
        sleeve = escape(str(m.get("sleeve") or "")).upper()
        layer = escape(de_dash(str(m.get("layer") or "")))
        tr.append(
            f"<tr><td class='tk'>{link}</td>"
            f"<td class='dim' style='font-size:11px'>{sleeve}</td>"
            f"<td class='dim' style='font-size:11px'>{layer}</td>"
            f"<td>{fmt(r['weight'], '.1f')}%</td>"
            f"<td>${fmt(r['price'], ',.2f')}</td>"
            f"<td class='{cls(r['change'])}'>{fmt(r['change'], '+.2f')}%</td>"
            f"<td class='{cls(r['gain'])}'>{fmt(r['gain'], '+.1f')}%</td></tr>")
    movers_up = " ".join(
        f"<span class='chip up'>{escape(m['t'])} {m['change']:+.1f}%</span>"
        for m in stats["best"])
    movers_dn = " ".join(
        f"<span class='chip down'>{escape(m['t'])} {m['change']:+.1f}%</span>"
        for m in stats["worst"])

    # Moves
    moves_items = ""
    for m in (moves or [])[:10]:
        badge = MOVE_BADGE.get(m["type"], "")
        tk = f" <span class='tk'>{escape(m['t'])}</span>" if m["t"] else ""
        moves_items += (
            f"<div class='move'><span class='chip {badge}'>{escape(m['type'])}</span>"
            f"{tk} <span class='sub'>{escape(m['detail'])} ({escape(m['date'])})</span></div>")

    # Research library chips
    held = {r["t"] for r in rows}
    lib_chips = []
    for t in sorted(pages):
        q = quotes.get(t) or {}
        ch = q.get("changePct")
        pct = f" <span class='{cls(ch)}'>{ch:+.1f}%</span>" if ch is not None else ""
        dot = " &#9679;" if t in held else ""
        lib_chips.append(
            f"<a class='chip' href='t/{escape(t)}.html'>{escape(t)}{dot}{pct}</a>")
    pending = sorted(held - pages)

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Young Bull</title>
<meta name="description" content="A 17-year-old's real money portfolio in the Physical Layer of AI. Every position public. Track your own book alongside mine.">
{og_tags("Young Bull Terminal", "Real money. Every position public. A 17-year-old's book in the Physical Layer of AI.", "terminal.html")}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' fill='%23c8952e'/></svg>">
<style>{CSS}{EXTRA_CSS}</style>
</head><body>

<nav class="yb-nav">
  <div class="yb-nav-inner">
    <a href="index.html" class="brand">Young Bull</a>
    <div class="yb-nav-links">
      <a href="index.html">Desk</a>
      <a href="#book">Book</a>
      <a href="#research">Research</a>
      <a href="#track">Track</a>
      <a href="pricing.html">Pricing</a>
      <a href="{SUBSTACK}" target="_blank" rel="noopener" class="ext">Substack &rarr;</a>
    </div>
  </div>
</nav>

<main>

<div class="tagline">
  <b>Real money. Every position public.</b><br>
  A 17-year-old's book in the Physical Layer of AI.
</div>

<div class="hero-grid">
  <div class="hero-cell"><b class="{cls(stats['gain'])}">{stats['gain']:+.1f}%</b><span>Open gain</span></div>
  <div class="hero-cell"><b>{len(rows)}</b><span>Positions</span></div>
  <div class="hero-cell"><b class="{cls(stats['day'])}">{stats['day']:+.2f}%</b><span>Today</span></div>
  <div class="hero-cell"><b>{stats['green']}/{stats['priced']}</b><span>Green today</span></div>
</div>

<section>
  <h2>The Read</h2>
  <p class="read">{market_read(stats)}</p>
  <div style="margin-top:14px">
    <div>Leaders: {movers_up}</div>
    <div style="margin-top:6px">Laggards: {movers_dn}</div>
  </div>
</section>

{desk_section}

{tape_section}

{wire_section}

{calendar_section}

<section id="book">
  <h2>The Book</h2>
  <div class="sub" style="margin-bottom:12px">Holdings as of {escape(str(snap.get("as_of", "?")))}.
  Real money, real entries. Prices refresh daily.</div>
  <div style="overflow-x:auto">
  <table><thead><tr>
    <th>Ticker</th><th>Sleeve</th><th>Layer</th><th>Weight</th><th>Price</th><th>Today</th><th>Gain</th>
  </tr></thead><tbody>{''.join(tr)}</tbody></table>
  </div>
</section>

{f'''<section>
  <h2>The Moves</h2>
  <div class="sub" style="margin-bottom:10px">Auto-detected from my brokerage snapshot.
  When I buy or sell, it shows up here on its own.</div>
  {moves_items}
</section>''' if moves_items else ''}

{cards_section}

{members_extras}

<section id="track">
  <h2>Track Your Book</h2>
  <div class="sub" style="margin-bottom:16px">Add your positions below. Everything stays
  in your browser, nothing is sent anywhere. Live prices cover our research universe plus the most-traded US names and ETFs. Anything else still tracks, just without a live quote.</div>
  <div class="tracker-form">
    <div class="field"><label>Ticker</label><input id="add-ticker" placeholder="NVDA" autocomplete="off" spellcheck="false"></div>
    <div class="field"><label>Shares</label><input id="add-shares" type="number" placeholder="10" min="0" step="any"></div>
    <div class="field"><label>Avg cost</label><input id="add-cost" type="number" placeholder="125.00" min="0" step="any"></div>
    <button class="btn-gold" onclick="ybAdd()">Add</button>
  </div>
  <div class="tracker-tools">
    <button class="scan-chip" onclick="ybImport()">Import CSV</button>
    <button class="scan-chip" onclick="ybExport()">Export CSV</button>
    <button class="scan-chip" onclick="ybShare()">Share desk</button>
    <input type="file" id="csv-file" accept=".csv" style="display:none">
    <span class="sub" id="tracker-msg"></span>
  </div>
  <div class="sub" style="margin-bottom:10px">CSV header: ticker,shares,cost_basis.
  Share desk copies a link that carries your positions to any device, still
  never touching a server.</div>
  <div id="tracker-summary"></div>
  <div id="tracker-empty" class="tracker-empty">
    No positions yet. Add a ticker above to start tracking your book.
  </div>
  <div style="overflow-x:auto">
  <table id="tracker-table" style="display:none"><thead><tr>
    <th>Ticker</th><th>Shares</th><th>Avg cost</th><th>Price</th><th>Gain</th><th></th>
  </tr></thead><tbody></tbody></table>
  </div>
  <h3 style="margin-top:18px">Watching</h3>
  <div class="sub" style="margin-bottom:8px">Tickers you track without a position.
  Optional target: the row goes gold when price crosses under it.</div>
  <div class="tracker-form">
    <div class="field"><label>Ticker</label><input id="watch-ticker" placeholder="OKLO" autocomplete="off" spellcheck="false"></div>
    <div class="field"><label>Target buy, optional</label><input id="watch-target" type="number" placeholder="40.00" min="0" step="any"></div>
    <button class="btn-gold" onclick="ybWatch()">Watch</button>
  </div>
  <div id="watch-list"></div>
</section>

{tools_section}

<section id="research">
  <h2>Research Library</h2>
  <div class="sub" style="margin-bottom:12px">Every name I have written a real thesis file on.
  Click any ticker. &#9679; = currently held.</div>
  <div>{''.join(lib_chips)}</div>
  {f'<div class="sub" style="margin-top:10px">Held but thesis not written yet: {", ".join(escape(t) for t in pending)}.</div>' if pending else ''}
</section>

<div class="cta-section">
  <h2>The Writing</h2>
  <p>Thesis updates. Morning reads. Conviction calls.<br>
  Free subscribers get the weekly. Paid gets the full research.</p>
  <a class="cta-btn" href="{SUBSTACK}" target="_blank" rel="noopener">Subscribe on Substack</a>
</div>

<footer>Young Bull. Not financial advice. Real positions, real money, real risk.<br>
Generated {escape(generated_at)}.</footer>

</main>

<script>{TRACKER_JS}</script>
<script>{TOOLS_JS}</script>
</body></html>"""


# ── Extras (tape + thesis cards) ─────────────────────────────────

def build_extras(rows, quotes, generated_at, pages):
    """Tape and thesis cards, plus the shared context the tools reuse.
    Each source degrades to blank alone."""
    today = generated_at[:10]
    metas = load_metas()
    committee = fetch_committee(sorted(quotes))  # whole universe, cards use held
    catalysts = fetch_catalysts(today)
    scout = load_scout()
    healths = {r["t"]: health_badge(r.get("price"), r.get("cost")) for r in rows}
    calls, _ = load_calls()
    receipts = receipts_from_calls(calls)
    tape = build_tape(rows, metas, healths, scout)
    cards = build_cards(rows, metas, committee, receipts, catalysts)
    ctx = {"metas": metas, "committee": committee,
           "catalysts": catalysts, "healths": healths,
           "tape_top": tape[0] if tape else None, "scout": scout}
    return tape_html(tape), cards_html(cards, pages), ctx


def load_receipts():
    try:
        data = json.loads((DATA_DIR / "receipts.json").read_text(encoding="utf-8"))
        return data.get("receipts", {})
    except (OSError, ValueError):
        return {}


def load_history():
    try:
        return json.loads((DATA_DIR / "history.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def merge_history(hist, quotes, today):
    """Append today's close for every quoted ticker. Immutable, idempotent:
    rerunning the same day overwrites today's point instead of duplicating."""
    out = {t: dict(days) for t, days in hist.items()}
    for t, q in quotes.items():
        price = q.get("price")
        if price is None:
            continue
        out.setdefault(t, {})[today] = price
    return out


def build_tools_data(rows, metas, committee, catalysts, healths, quotes):
    """Per-ticker coverage data for the client-side tools. Only real fields:
    a name outside the coverage universe ships an empty dict, not a guess."""
    weights = {r["t"]: r.get("weight") for r in rows}
    tickers = {}
    for t in quotes:
        d = {}
        meta = metas.get(t) or {}
        if meta.get("layer"):
            d["layer"] = de_dash(str(meta["layer"]))
        if meta.get("thesis_short"):
            d["thesis"] = de_dash(str(meta["thesis_short"]))
        if t in weights and weights[t] is not None:
            d["held"] = round(weights[t], 1)
            if healths.get(t):
                d["health"] = healths[t]
        com = committee.get(t)
        if com and com.get("conviction") is not None:
            d["conviction"] = com["conviction"]
            if com.get("stance"):
                d["stance"] = com["stance"]
        cat = catalysts.get(t)
        if cat and cat.get("date"):
            d["earnings"] = cat["date"]
        tickers[t] = d
    return {"tickers": tickers}


def members_html(html):
    """Mirror page for the unlisted members path, two directories deep.

    Rewrites asset paths instead of using <base>: a base tag makes every
    in-page anchor (#book, #track) navigate to the public index, which
    bounces paid members off their own page.
    """
    out = (html
           .replace("href='t/", "href='../../t/")
           .replace('href="t/', 'href="../../t/')
           .replace('href="pricing.html"', 'href="../../pricing.html"')
           .replace('href="index.html"', 'href="../../index.html"')
           .replace('href="terminal.html"', 'href="../../terminal.html"')
           .replace("href='pricing.html'", "href='../../pricing.html'")
           .replace("fetch('prices.json')", "fetch('../../prices.json')")
           .replace("fetch('tools-data.json')", "fetch('../../tools-data.json')")
           .replace("fetch('history.json')", "fetch('../../history.json')"))
    return out.replace(
        "<head>", "<head>\n<meta name='robots' content='noindex, nofollow'>", 1)


MIN_QUOTE_COVERAGE = 0.9
REQUIRED_MARKS = ("hero-grid", "id='book'", "id='track'", "id='research'")


def validate_output(html, rows, pages):
    """The truth gate. A build that fails here must not ship; refresh.sh
    keeps the previous good site when generate exits nonzero."""
    problems = []
    priced = sum(1 for r in rows if r.get("price") is not None)
    if rows and priced / len(rows) < MIN_QUOTE_COVERAGE:
        problems.append(f"quote coverage {priced}/{len(rows)} below "
                        f"{MIN_QUOTE_COVERAGE:.0%}: refusing to ship a blank tape")
    for dash in ("—", "–"):
        if dash in html:
            problems.append("em dash or en dash in output (house rule: never)")
            break
    for m in re.findall(r"href=['\"]t/([A-Z.\-]+)\.html", html):
        if m not in pages:
            problems.append(f"dead research link: t/{m}.html not being written")
    for mark in REQUIRED_MARKS:
        if mark.replace("'", '"') not in html and mark not in html:
            problems.append(f"required section missing: {mark}")
    return problems


def write_page(path, html):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(path)


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("Young Bull Terminal build")

    # Load positions from local state (no Vercel dependency)
    snap = load_positions()
    held = [p["t"] for p in snap["positions"]]

    calls, _ = load_calls()
    extra = sorted((set(list_research_tickers()) |
                    {c["t"] for c in calls if c.get("status") != "closed"})
                   - set(held))

    # Fetch prices via yfinance (no Vercel dependency); popular names ride
    # along so the tracker covers what subscribers actually hold
    popular = sorted(set(TRACKER_POPULAR) - set(held) - set(extra))
    quotes = fetch_prices(held + extra + popular)

    rows = enrich(snap["positions"], quotes)
    stats = book_stats(rows)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write prices.json for client-side tracker
    (OUT_DIR / "prices.json").write_text(
        json.dumps(quotes, indent=1, allow_nan=False), encoding="utf-8")

    # Build per-ticker research pages (with badge, sparkline, receipts)
    rows_by_ticker = {r["t"]: r for r in rows}
    today = generated_at[:10]
    hist = merge_history(load_history(), quotes, today)
    healths = {r["t"]: health_badge(r.get("price"), r.get("cost")) for r in rows}
    receipts = load_receipts()
    pages = build_research(OUT_DIR, quotes, rows_by_ticker, generated_at,
                           healths=healths, hist=hist, receipts=receipts)

    # Load existing moves
    moves = load_moves()

    # Build tape + thesis cards (degrade gracefully)
    try:
        tape_section, cards_section, ctx = build_extras(rows, quotes,
                                                        generated_at, pages)
    except Exception as e:
        print(f"  WARN: extras failed, shipping core page only: {e}")
        tape_section, cards_section, ctx = "", "", {}

    # Signal histories: one badge + conviction snapshot per refresh,
    # then transitions and deltas fall out of the diffs (blank day one)
    badge_hist = merge_snapshot(
        load_json(DATA_DIR / "badge-history.json", {}),
        ctx.get("healths", {}), today)
    (DATA_DIR / "badge-history.json").write_text(
        json.dumps(badge_hist, indent=1), encoding="utf-8")
    conv_now = {t: c["conviction"] for t, c in ctx.get("committee", {}).items()
                if c.get("conviction") is not None}
    conv_hist = merge_snapshot(
        load_json(DATA_DIR / "conviction-history.json", {}), conv_now, today)
    (DATA_DIR / "conviction-history.json").write_text(
        json.dumps(conv_hist, indent=1), encoding="utf-8")
    badge_moves = badge_transitions(badge_hist, 7, today)
    conv_deltas = conviction_deltas(conv_hist, 7, today)

    # Pro tools: coverage data + our own snapshot history + scanner
    tools = build_tools_data(rows, ctx.get("metas", {}), ctx.get("committee", {}),
                             ctx.get("catalysts", {}), ctx.get("healths", {}),
                             quotes)
    (OUT_DIR / "tools-data.json").write_text(
        json.dumps(tools, indent=1, allow_nan=False), encoding="utf-8")
    hist_json = json.dumps(hist, indent=1, allow_nan=False)
    (DATA_DIR / "history.json").write_text(hist_json, encoding="utf-8")
    (OUT_DIR / "history.json").write_text(hist_json, encoding="utf-8")
    tools_section = VIZ_SECTION + scanner_html(tools["tickers"], quotes, pages,
                                           conv_deltas=conv_deltas)

    # Desk note (agent-written, may be absent or stale: rendered honestly)
    # + members-only sections. Each degrades to blank alone.
    note = load_desk_note()
    archive_note(note)
    desk_public = desk_note_html(note, today)
    desk_members = desk_note_html(note, today, members=True)
    members_extras = (mission_log_html(load_weekly_counts(today), today)
                      + request_line_html() + NOTES_LINKS)

    # Catalyst calendar: public week, members quarter
    curated = load_catalysts()
    earnings = ctx.get("catalysts", {})
    cal_public = calendar_public_html(
        build_calendar(curated, earnings, today, PUBLIC_DAYS))
    cal_entries = build_calendar(curated, earnings, today, MEMBERS_DAYS)
    cal_members = calendar_members_html(cal_entries, pages)
    upcoming = [e for e in cal_entries if e["date"] >= today]
    today_html = today_block_html(
        ctx.get("tape_top"),
        upcoming[0] if upcoming else None,
        badge_moves,
        first_sentence(note["body"]) if note else "",
        stats["day"] if rows else None)

    # Render index, then gate it: ship fully consistent or not at all
    scout_items = ctx.get("scout") or []
    scan_feed = fetch_desk_json("scan.json")
    bt_feed = fetch_desk_json("backtests.json")
    scan_public = market_scan_html(scan_feed, members=False, today=today)
    scan_members = (market_scan_html(scan_feed, members=True, today=today)
                    + proving_ground_html(bt_feed, today=today))
    html = render(snap, rows, stats, generated_at, pages, quotes, moves,
                  tape_section, cards_section, tools_section,
                  desk_section=desk_public, calendar_section=cal_public,
                  wire_section=wire_html(scout_items, 4) + scan_public,
                  book_metas=ctx.get("metas"))
    m_html = render(snap, rows, stats, generated_at, pages, quotes, moves,
                    tape_section, cards_section, tools_section,
                    desk_section=today_html + desk_members,
                    members_extras=members_extras,
                    calendar_section=cal_members,
                    wire_section=wire_html(scout_items, 12) + scan_members,
                    book_metas=ctx.get("metas"))
    problems = validate_output(html, rows, pages) + validate_output(
        m_html, rows, pages)
    if problems:
        for p in problems:
            print(f"VALIDATION: {p}", file=sys.stderr)
        sys.exit(1)  # refresh.sh keeps the previous good site
    write_page(OUT_DIR / "terminal.html", html)

    # Pricing page
    write_page(OUT_DIR / "pricing.html",
               pricing_page_html(CSS, load_weekly_counts(today)))

    # Members mirror (unlisted URL for paid subs)
    token = members_token()
    members_dir = OUT_DIR / "members" / token
    members_dir.mkdir(parents=True, exist_ok=True)
    archive = load_note_archive()
    notes_html_full = notes_page_html(archive, CSS, "feed.xml")
    try:
        members_pass = parse_env(SECRETS.read_text(encoding="utf-8")).get(
            "MEMBERS_PASS", "")
    except OSError:
        members_pass = ""
    if members_pass:
        # repo is public: the members pages ship encrypted, passcode goes
        # out in the paid welcome email, browser decrypts locally
        write_page(members_dir / "index.html", gate_page_html(
            encrypt_payload(members_html(m_html), members_pass),
            "Young Bull Members"))
        write_page(members_dir / "notes.html", gate_page_html(
            encrypt_payload(notes_html_full, members_pass),
            "Desk Notes | Young Bull Members"))
    else:
        print("WARN: MEMBERS_PASS missing, members pages shipping UNLOCKED")
        write_page(members_dir / "index.html", members_html(m_html))
        write_page(members_dir / "notes.html", notes_html_full)
    members_base = f"{SITE_BASE}members/{token}/"
    (members_dir / "feed.xml").write_text(rss_xml(archive, members_base),
                                          encoding="utf-8")

    # Sitemap for the public pages (members path deliberately absent)
    urls = (["", "terminal.html", "pricing.html", "about.html",
             "reports.html", "research.html", "members.html"]
            + [f"t/{t}.html" for t in sorted(pages)])
    sitemap = ("<?xml version='1.0' encoding='UTF-8'?>\n"
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
               + "".join(f"<url><loc>{SITE_BASE}{u}</loc></url>\n"
                         for u in urls)
               + "</urlset>\n")
    (OUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print(f"OK: index ({len(html):,} bytes, {len(rows)} positions) + "
          f"{len(pages)} research pages + prices.json + sitemap + members/{token}/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
