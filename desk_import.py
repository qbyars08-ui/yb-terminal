"""Absorb the yb-desk product into the Terminal: market scan + proving ground.

The desk's agents keep publishing their JSON to the yb-desk Pages site on
their own schedule; the Terminal fetches the DEPLOYED files at refresh time
(never a possibly-stale local clone) and renders them with their own as-of
stamps. A missing or empty feed renders nothing. Numbers pass through
untouched; this module formats, it never computes returns.
"""

import json
import urllib.request
from datetime import datetime
from html import escape

from thesis import de_dash

DESK_BASE = "https://qbyars08-ui.github.io/yb-desk/data/"
TIMEOUT = 15


def fetch_desk_json(name):
    """One deployed desk feed. Any failure returns None."""
    try:
        req = urllib.request.Request(DESK_BASE + name,
                                     headers={"User-Agent": "yb-terminal/2.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"WARN: desk feed {name} unavailable: {e}")
        return None


def staleness(updated_iso, today):
    """'' when fresh (<=3 days), otherwise an honest age label."""
    try:
        when = datetime.fromisoformat(str(updated_iso).replace("Z", "+00:00"))
        age = (datetime.strptime(today, "%Y-%m-%d").date() - when.date()).days
    except (ValueError, TypeError):
        return " <span class='stale'>age unknown</span>"
    if age <= 3:
        return ""
    return f" <span class='stale'>{age} days old</span>"


def _asof(updated):
    return escape(str(updated or "")[:16].replace("T", " "))


def market_scan_html(scan, members, today):
    """Twice-daily whole-market screens. Members see the names; the public
    sees the counts and where the names live."""
    if not scan or not scan.get("scans"):
        return ""
    stamp = staleness(scan.get("updated"), today)
    head = (f"<section id='scan'><h2>Market Scan</h2>"
            f"<div class='sub' style='margin-bottom:10px'>The desk screens the "
            f"whole market twice a day: {escape(de_dash(str(scan.get('universe') or '')))}. "
            f"What screened, not what to buy. As of {_asof(scan.get('updated'))}"
            f"{stamp}.</div>")
    blocks = []
    for s in scan["scans"]:
        title = (f"<div class='scan-head'>{escape(de_dash(str(s.get('title') or '')))} "
                 f"<span class='dim'>({s.get('totalMatches', 0)} matches)</span></div>"
                 f"<div class='sub' style='margin-bottom:6px'>{escape(de_dash(str(s.get('note') or '')))}</div>")
        if not members:
            blocks.append(title)
            continue
        rows = "".join(
            f"<div class='wire-row'><span class='tk' style='width:56px;flex-shrink:0'>"
            f"{escape(r['ticker'])}</span>"
            f"<span style='flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>"
            f"{escape(r.get('company') or '')}</span>"
            f"<span>${r['price']:,.2f}</span>"
            f"<span class='{'up' if (r.get('changePct') or 0) >= 0 else 'down'}'>"
            f"{(r.get('changePct') or 0):+.2f}%</span>"
            f"<span class='dim'>{escape(str(r.get('cap') or ''))}</span></div>"
            for r in (s.get("rows") or [])[:8])
        blocks.append(title + rows)
    tail = ("" if members else
            "<div class='sub' style='margin-top:8px'>The names behind these counts "
            "are on the members desk. <a href='pricing.html'>$99 a year, founding."
            "</a></div>")
    return head + "".join(blocks) + tail + "</section>"


def proving_ground_html(bt, today):
    """The backtest wall: six classic strategies against just holding the
    book's names. The desk publishes it because most of them lose, and that
    honesty is the product."""
    if not bt or not bt.get("strategies"):
        return ""
    stamp = staleness(bt.get("updated"), today)
    rows = []
    for s in bt["strategies"]:
        a = s.get("agg") or {}
        best, worst = s.get("best") or {}, s.get("worst") or {}
        rng = ""
        if best.get("ticker") and worst.get("ticker"):
            rng = (f"best {escape(best['ticker'])} {best.get('strategyPct', 0):+.1f}%, "
                   f"worst {escape(worst['ticker'])} {worst.get('strategyPct', 0):+.1f}%")
        rows.append(
            f"<tr><td><b>{escape(s.get('id') or '')}</b>"
            f"<div class='dim' style='font-size:11px'>{escape(de_dash(str(s.get('description') or '')))}</div></td>"
            f"<td>{a.get('medianStrategyPct', 0):+.1f}%</td>"
            f"<td>{a.get('medianBuyHoldPct', 0):+.1f}%</td>"
            f"<td>{s.get('agg', {}).get('beatBuyHold', 0)}/{a.get('names', 0)}</td>"
            f"<td>{a.get('avgWinRatePct', 0):.1f}%</td>"
            f"<td style='font-size:11px'>{rng}</td></tr>")
    return (f"<section id='proving'><h2>Proving Ground</h2>"
            f"<div class='sub' style='margin-bottom:10px'>{escape(de_dash(str(bt.get('period') or '')))} "
            f"window, six classic strategies backtested on the book's names with real "
            f"slippage, in the open. Most of them lose to just holding. That is the "
            f"point. As of {_asof(bt.get('updated'))}{stamp}.</div>"
            f"<div style='overflow-x:auto'><table><thead><tr><th>Strategy</th>"
            f"<th>Median result</th><th>Just holding</th><th>Beat holding</th>"
            f"<th>Win rate</th><th>Range</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>"
            f"<div class='sub' style='margin-top:8px'>Simulated on history by "
            f"{escape(de_dash(str(bt.get('engine') or 'the momentum engine')))}. History is not "
            f"the future, and this is not advice.</div></section>")
