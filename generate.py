#!/usr/bin/env python3
"""Young Bull Terminal: nightly static dashboard for paid subscribers.

Fetches the public book snapshot + live prices from youngbullinvests.com,
renders a single self-contained dark-theme index.html into site/.
Zero dependencies, zero servers. Run by cron, deployed as static files.

Fails loudly and leaves the previous docs/index.html untouched on any error,
so a bad fetch never blanks the page paid subs are looking at.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from research import CSS, build_research, list_research_tickers

BASE = "https://youngbullinvests.com"
OUT_DIR = Path(__file__).parent / "docs"
TIMEOUT = 20


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "yb-terminal/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def load_data():
    snap = fetch_json(f"{BASE}/positions.json")
    positions = snap.get("positions") or []
    if not positions:
        raise ValueError("positions.json returned no positions")
    held = [p["t"] for p in positions]
    extra = [t for t in list_research_tickers() if t not in held]
    live = fetch_json(f"{BASE}/api/prices?symbols={','.join(held + extra)}")
    if not live.get("ok") or not live.get("prices"):
        # library symbols may not all quote; retry with held only before failing
        live = fetch_json(f"{BASE}/api/prices?symbols={','.join(held)}")
    if not live.get("ok"):
        raise ValueError(f"prices API not ok: {live}")
    return snap, live


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
            "t": t,
            "weight": p.get("weightPct"),
            "cost": cost,
            "price": price,
            "change": change,
            "gain": gain,
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
    return {
        "green": len(green),
        "priced": len(priced),
        "day": weighted_day / total_w,
        "gain": weighted_gain / gain_w,
        "best": movers[:3],
        "worst": movers[-3:][::-1],
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
    best = stats["best"][0]
    worst = stats["worst"][0]
    return (
        f"{mood} {g} of {n} names green, book {day:+.2f}% weighted on the day. "
        f"Top mover {best['t']} {best['change']:+.2f}%, laggard {worst['t']} "
        f"{worst['change']:+.2f}%. Cost basis never moves on a red day. The thesis "
        f"either holds or it does not, and price alone is not the thesis."
    )


def fmt(v, spec, dash="-"):
    return format(v, spec) if v is not None else dash


def cls(v):
    if v is None:
        return ""
    return "up" if v >= 0 else "down"


def render(snap, rows, stats, generated_at, pages, quotes):
    tr = []
    for r in sorted(rows, key=lambda x: -(x["weight"] or 0)):
        t = r["t"]
        cell = (f"<a href='t/{escape(t)}.html'>{escape(t)}</a>"
                if t in pages else escape(t))
        tr.append(
            f"<tr><td class='tk'>{cell}</td>"
            f"<td>{fmt(r['weight'], '.1f')}%</td>"
            f"<td>${fmt(r['cost'], ',.2f')}</td>"
            f"<td>${fmt(r['price'], ',.2f')}</td>"
            f"<td class='{cls(r['change'])}'>{fmt(r['change'], '+.2f')}%</td>"
            f"<td class='{cls(r['gain'])}'>{fmt(r['gain'], '+.1f')}%</td></tr>"
        )
    movers_up = " ".join(
        f"<span class='chip up'>{escape(m['t'])} {m['change']:+.1f}%</span>"
        for m in stats["best"]
    )
    movers_dn = " ".join(
        f"<span class='chip down'>{escape(m['t'])} {m['change']:+.1f}%</span>"
        for m in stats["worst"]
    )
    held = {r["t"] for r in rows}
    lib_chips = []
    for t in sorted(pages):
        q = quotes.get(t) or {}
        ch = q.get("changePct")
        pct = f" <span class='{cls(ch)}'>{ch:+.1f}%</span>" if ch is not None else ""
        mark = " &#9679;" if t in held else ""
        lib_chips.append(f"<a class='chip' href='t/{escape(t)}.html'>{escape(t)}{mark}{pct}</a>")
    pending = sorted(held - pages)
    pending_html = ""
    if pending:
        pending_html = (
            "<div class='sub' style='margin-top:10px'>Held, thesis file not written yet: "
            + ", ".join(escape(t) for t in pending)
            + ". Rule 5 says every position needs one. They are coming.</div>")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Young Bull Terminal</title>
<style>{CSS}</style></head><body><main>
<h1>YOUNG BULL TERMINAL</h1>
<div class="sub">Generated {escape(generated_at)}. Holdings as of
{escape(str(snap.get("as_of", "?")))}. Real money, real entries, verified daily.
Free for everyone until July 22, 2026. After that, paid subscribers only.</div>

<section><h2>The Read</h2><p class="read">{market_read(stats)}</p></section>

<section><h2>The Book, Live</h2>
<div class="stats">
  <div class="stat"><b class="{cls(stats['day'])}">{stats['day']:+.2f}%</b><span>Today (weighted)</span></div>
  <div class="stat"><b class="{cls(stats['gain'])}">{stats['gain']:+.1f}%</b><span>Open gain (weighted)</span></div>
  <div class="stat"><b>{stats['green']}/{stats['priced']}</b><span>Green today</span></div>
</div>
<table><thead><tr><th>Ticker</th><th>Weight</th><th>Avg cost</th><th>Live</th>
<th>Today</th><th>Gain</th></tr></thead><tbody>{''.join(tr)}</tbody></table></section>

<section><h2>Today's Tape</h2>
<div>Leaders: {movers_up}</div><div style="margin-top:8px">Laggards: {movers_dn}</div></section>

<section><h2>Research Library</h2>
<div class="sub" style="margin-bottom:10px">Every name I have written a real thesis file on.
Click any ticker. &#9679; = currently held. Held names in the book table above link to the
same pages.</div>
<div>{''.join(lib_chips)}</div>{pending_html}</section>

<footer>Young Bull Terminal. Not advice, it is my book and my machine. Free preview
until July 22, 2026, then this becomes a paid-subscriber perk. Built and refreshed
automatically by the same AI stack that runs Young Bull.</footer>
</main></body></html>"""


def main():
    snap, live = load_data()
    quotes = live.get("prices") or {}
    rows = enrich(snap["positions"], quotes)
    stats = book_stats(rows)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_by_ticker = {r["t"]: r for r in rows}
    pages = build_research(OUT_DIR, quotes, rows_by_ticker, generated_at)
    html = render(snap, rows, stats, generated_at, pages, quotes)
    tmp = OUT_DIR / "index.html.tmp"
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(OUT_DIR / "index.html")
    print(f"OK: index ({len(html)} bytes, {len(rows)} positions) + {len(pages)} research pages")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
